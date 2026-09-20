"""dock.py: one decision-log row for any docked ship (dock protocol item 3).

    dock.py record --ship cve-intel --summary "refresh ok; 1234 records" [--tools a,b] [--capture-id X] [--source launchd]

Reads the ship's manifest for its decision_log path. Best-effort: never fails the caller.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import yaml  # noqa: E402
from botlib.intake_log import IntakeLog  # noqa: E402


def manifest(ship: str) -> dict:
    return yaml.safe_load(open(HERE / "ships" / f"{ship}.yaml"))


def record(ship: str, summary: str, tools=None, capture_id=None, source="launchd", text=None):
    m = manifest(ship)
    ilog = IntakeLog(m["decision_log"])
    return ilog.record(chat_id=None, source=source, text=text or f"{ship} scheduled run ({m.get('registry', '')})",
                       intent=ship, confidence=1.0, action=summary, tools=tools or [ship], capture_id=capture_id)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--ship", required=True)
    r.add_argument("--summary", required=True)
    r.add_argument("--tools", default="")
    r.add_argument("--capture-id")
    r.add_argument("--source", default="launchd")
    a = p.parse_args()
    try:
        rid = record(a.ship, a.summary[:400], [t for t in a.tools.split(",") if t], a.capture_id, a.source)
        print(f"decision-log row {rid} ({a.ship})")
    except Exception as e:  # noqa: BLE001
        print(f"dock record failed (non-fatal): {e}")
