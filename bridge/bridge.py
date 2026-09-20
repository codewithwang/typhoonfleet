"""The Bridge, v0: the fleet-level dispatcher (target-state-v3 §3.1).

It routes, it does not do. One request in -> classify to a ship from the manifests -> check the
manifest's autonomy tier and RULE 0 flag -> dispatch -> one decision-log row. No routing logic
beyond ships/*.yaml: a new ship is a new manifest, never a code change here.

    bridge.py route "security review eidos" --authorization F --profile F [--ship id] [--dry-run] [--yes]
    bridge.py ships
    bridge.py log [--n 10]

Classification: the manifests' `triggers` are matched first (deterministic, no model). Exactly one
ship -> confidence 0.9. None or several -> one Haiku pass over the manifest summaries (botlib).
Confidence under 0.6 -> the top two are printed and nothing is dispatched (Harry decides).
Tiers: L0/L1 dispatch; L2 needs --yes (a human at the keyboard); L3+ is refused here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import yaml  # noqa: E402
from botlib.intake_log import IntakeLog  # noqa: E402

LOG = IntakeLog(HERE / "state" / "intake.sqlite")
HAIKU = "claude-haiku-4-5-20251001"
ALLOWED_TIERS = {"L0", "L1", "L2"}


def ships() -> dict[str, dict]:
    out = {}
    for f in sorted((HERE / "ships").glob("*.yaml")):
        m = yaml.safe_load(open(f))
        out[m["id"]] = m
    return out


def classify(text: str, fleet: dict[str, dict]) -> tuple[str | None, float, bool, list[str]]:
    """-> (ship id, confidence, escalated_to_model, top candidates)."""
    t = text.lower()
    hits = {sid: sum(1 for k in m.get("triggers", []) if k.lower() in t) for sid, m in fleet.items()}
    ranked = sorted((s for s in hits if hits[s]), key=lambda s: -hits[s])
    if len(ranked) == 1:
        return ranked[0], 0.9, False, ranked
    if len(ranked) > 1 and hits[ranked[0]] > hits[ranked[1]]:
        return ranked[0], 0.75, False, ranked[:2]
    # ambiguous or no trigger: one Haiku pass over the manifest summaries
    try:
        from botlib.llm_json import call_json
        roster = "\n".join(f"- {sid}: {m['name']} ({m['squadron']}, {m['capability']}): {m['what']}" for sid, m in fleet.items())
        res = call_json(model=HAIKU, max_tokens=200,
                        system="You route a request to exactly one ship of an agent fleet. Answer JSON only: {\"ship\": id or null, \"confidence\": 0..1, \"why\": short}.",
                        user=f"Ships:\n{roster}\n\nRequest: {text}\n\nPick the one ship whose `what` answers the request, or null if none does.")
        sid = res.get("ship") if res.get("ship") in fleet else None
        conf = float(res.get("confidence") or 0)
        return sid, conf, True, ([sid] if sid else []) + [s for s in ranked if s != sid][:1]
    except Exception as e:  # noqa: BLE001
        print(f"model classify unavailable ({e}); trigger ranking only")
        return (ranked[0] if ranked else None), (0.5 if ranked else 0.0), False, ranked[:2]


def guard(m: dict, args) -> str | None:
    """Return a refusal reason or None."""
    tier = str(m.get("autonomy_tier", "L3"))
    if tier not in ALLOWED_TIERS:
        return f"tier {tier} is not dispatchable from the Bridge (L0-L2 only)"
    if tier == "L2" and not args.yes:
        return "tier L2 needs a human approval: re-run with --yes"
    if m.get("requires_approval") and not args.yes:
        return "manifest requires approval: re-run with --yes"
    if m.get("rule0"):
        if not args.authorization:
            return "RULE 0: this ship needs --authorization <engagements/*.authorization.yaml>"
        p = Path(args.authorization)
        if not p.is_absolute():
            p = Path(m.get("dispatch", {}).get("cwd", ".")) / p
        if not p.exists():
            return f"RULE 0: authorization file not found: {p}"
        doc = yaml.safe_load(open(p)) or {}
        if (doc.get("attestation") or {}).get("owner_confirmed") is not True:
            return "RULE 0: attestation.owner_confirmed is not true"
        try:
            if dt.date.fromisoformat(str(doc.get("expiry"))) < dt.date.today():
                return f"RULE 0: authorization expired {doc.get('expiry')}"
        except ValueError:
            return "RULE 0: authorization expiry is not a date"
    for req in m.get("dispatch", {}).get("requires", []):
        if not getattr(args, req, None):
            return f"ship needs --{req}"
    return None


def dispatch(m: dict, args) -> tuple[int, str]:
    fill = {"authorization": args.authorization or "", "profile": args.profile or ""}
    cmd = [c.format(**fill) for c in m["dispatch"]["command"]]
    if args.dry_run:
        return 0, "DRY RUN: " + " ".join(cmd)
    r = subprocess.run(cmd, cwd=m["dispatch"].get("cwd"), capture_output=True, text=True, timeout=60 * int(m.get("budget", {}).get("max_minutes", 30)))
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    return r.returncode, tail or (r.stderr.strip()[-200:] if r.stderr else "")


def route(text: str, args) -> int:
    fleet = ships()
    if args.ship:
        sid, conf, esc, cands = (args.ship if args.ship in fleet else None), 1.0, False, [args.ship]
    else:
        sid, conf, esc, cands = classify(text, fleet)
    if not sid or conf < 0.6:
        msg = (f"no ship covers this (model confidence {conf:.2f})" if not sid else f"ask Harry: top {cands} (confidence {conf:.2f})")
        LOG.record(chat_id=None, source=args.source, text=text, intent=sid or "", confidence=conf, escalated=esc, action=msg, tools=[])
        print(f"RECEIPT: not dispatched. {msg}")
        return 4
    m = fleet[sid]
    why = guard(m, args)
    if why:
        LOG.record(chat_id=None, source=args.source, text=text, intent=sid, confidence=conf, escalated=esc, action=f"refused: {why}", tools=[sid])
        print(f"RECEIPT: {sid} ({m['squadron']}/{m['capability']}, {m['autonomy_tier']}) refused. {why}")
        return 5
    rc, tail = dispatch(m, args)
    outcome = f"{'ok' if rc == 0 else 'exit ' + str(rc)}: {tail[:200]}"
    rid = LOG.record(chat_id=None, source=args.source, text=text, intent=sid, confidence=conf, escalated=esc,
                     action=("dry-run " if args.dry_run else "dispatched ") + outcome, tools=[sid],
                     capture_id=f"{sid}-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
    print(f"RECEIPT: {sid} ({m['squadron']}/{m['capability']}, {m['autonomy_tier']}, confidence {conf:.2f}{', model' if esc else ''}) -> {outcome}")
    print(f"decision-log row {rid}; reports: {m.get('report_dir')}; Console page: {m.get('console', {}).get('page')}")
    return rc


def main(argv=None):
    p = argparse.ArgumentParser(prog="bridge")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("route")
    r.add_argument("text")
    r.add_argument("--ship")
    r.add_argument("--authorization")
    r.add_argument("--profile")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--yes", action="store_true")
    r.add_argument("--source", default="bridge-cli")
    s = sub.add_parser("ships")
    lg = sub.add_parser("log")
    lg.add_argument("--n", type=int, default=10)
    a = p.parse_args(argv)
    if a.cmd == "ships":
        for sid, m in ships().items():
            print(f"{sid:18} {m['squadron']:9} {m['capability']:3} {m['autonomy_tier']:3} rule0={'y' if m.get('rule0') else 'n'} {m['status']:8} {m['name']}")
        return 0
    if a.cmd == "log":
        import sqlite3
        LOG.init_db()
        con = sqlite3.connect(LOG.db_path)
        for row in con.execute("select id, ts_utc, source, tier1_intent, tier1_confidence, escalated, action from intake_decisions order by id desc limit ?", (a.n,)):
            print(" | ".join(str(x)[:90] for x in row))
        return 0
    return route(a.text, a)


if __name__ == "__main__":
    sys.exit(main())
