# The Bridge (v0)

Fleet-level dispatcher for Typhoon Fleet (target-state-v3 §3.1). Routes a request to one ship,
checks the ship's guardrails, dispatches, records. Never scans, writes or files anything itself.

- `ships/*.yaml` — one manifest per ship (dock protocol item 1). **New ship = new manifest.** No code here changes.
- `bridge route "<request>" --authorization F --profile F [--ship id] [--dry-run] [--yes]`
- `bridge ships` · `bridge log`
- `dock.py record --ship <id> --summary "..."` — one decision-log row for a scheduled ship (CVE Intel uses it from `run-refresh.sh`).
- Decision log: `state/intake.sqlite` (botlib `IntakeLog`; gitignored). Ships keep their own log at the path their manifest names.
- Runtime: `.venv` (uv, pyyaml) + `botlib` symlink, like every bot in the fleet. `/opt/homebrew/bin/python3` has no pyyaml, hence the venv.

Tiers: L0/L1 dispatch; L2 needs `--yes`; L3 refused. RULE 0 ships need a signed, unexpired authorization file
(the ship's own gate re-checks every target exactly). Telegram surface: Harry's call (v3 §10 item 1); `route()` is the function a bot would call.
