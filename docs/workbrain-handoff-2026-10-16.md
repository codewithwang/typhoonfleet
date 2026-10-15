# WorkBrain dashboard handoff

Checked 2026-10-16, Asia/Hong_Kong. Technical status only; work-mail data stays in the private WorkBrain system.

## Verified progress

- Four dashboard views exist: Briefing, Board, Console and Process map.
- The private hosted service serves real read-only Outlook metadata snapshots. Runtime snapshots and feedback use private object storage, not source history.
- Category corrections, review marks and feedback are persisted server-side. Review marks are tied to the observed conversation timestamp.
- Sent history and later incoming replies are used as evidence. Calendar responses and automatic replies are excluded from completion evidence. Review candidates and process keywords are advisory, not verified outstanding obligations or commercial stages.
- A retrospective learning view compares earlier incoming labels with later Sent activity. Label-generation timestamps are unavailable, so this is not prospective classifier accuracy or evidence of model retraining.
- The browser checks the stored snapshot every minute while visible. This does not trigger an Outlook export.
- Command execution is not connected. The current command bar searches the board. No Outlook write handlers are implemented.
- The loaded tab remains readable after disconnection; reopening offline with real data is not supported.

## Refresh status at inspection

- The Sites source REFRESH.md documents a local Codex heartbeat intended to run every 30 minutes while the Mac is available. It requires the Mac and work laptop online.
- No cloud schedule is attached to this Site. No corresponding 30-minute task appeared in the account's ChatGPT scheduled-task list.
- Latest successful dashboard-export result found: 2026-10-16 04:07:53 HKT. The live API reports exportedAt 04:07:50 HKT and builtAt 04:09:21 HKT, matching that run.
- Recent successful export results were recorded at approximately 00:37, 01:16, 02:11, 03:11 and 04:07 HKT. These prove exports occurred, not reliable 30-minute scheduling.
- The separate work-laptop loop reported a healthy tick at 06:01:29 HKT, cockpit up, Outlook tab present, and zero pending jobs. This is a point-in-time observation, not proof of continued availability.
- Therefore the dashboard snapshot is overdue relative to the intended cadence. The local Codex heartbeat's actual configuration, last invocation and next invocation were not accessible in this cloud session. Do not label it healthy or assume it is installed/enabled from documentation alone.

## Next steps, in order

1. Inspect the Mac-side Codex heartbeat: enabled state, exact 30-minute schedule, last attempt, next attempt and failure output. Distinguish it from the work-laptop WorkBrainLoop, which was reporting healthy. Avoid creating a duplicate scheduler.
2. Resume the documented read-only refresh workflow. Check the latest export and pending queue first; if necessary request the existing dashboard-refresh job once. Wait for its result, build the metadata snapshot, upload through the private service writer, and verify API readback. Do not reset a dirty canonical checkout.
3. Add Fleet operational visibility for this pipeline: source export time, successful upload time, scheduler last/next attempt, Mac and laptop heartbeat age, pending job identity, last error, and overdue state. Represent the work dashboard as a partially integrated capability, not a live Fleet command executor.
4. Dock WorkBrain through the existing Fleet manifest contract only after defining a real callable runner, its inputs, outputs, decision log and authorization policy. A manifest or a green roster label alone is not an integration.
5. Keep classification changes measured: inspect explicit corrections, propose one evidenced improvement per run, and evaluate it on the next run. Do not infer completion from a reply, treat no reply as a negative label, or auto-deploy generalized rules.
6. A future command path requires approved plans, a durable queue, fixed laptop handlers and verified receipts. It is separate from read-only refresh restoration. Preserve the existing cockpit feature-freeze boundary unless explicitly changed.

## Runtime boundaries

Work laptop Outlook/cockpit → private Git-loop export → Mac/Codex snapshot builder and uploader → private hosted dashboard. Fleet currently supplies its own Bridge dispatcher and manifest contract; it does not yet own this refresh pipeline.

A cloud scheduler alone cannot reach the local Outlook bridge. A cloud migration needs an authenticated worker path and durable execution/status records; it must preserve private work data and the existing read-only scope.

## Evidence locations

- Private dashboard source: REFRESH.md, ui/app.js, worker/handler.js and scripts/build-snapshot.py. Inspected source commit: 6779ade521b3e2b5106b4672c21300c304a7b32f.
- Private WorkBrain repository: AGENTS.md, cockpit/loop/status.md and cockpit/loop/results/369_dashboard_refresh.*.md.
- Live private dashboard: GET /api/snapshot and GET /api/feedback checked with owner-authorized access. No payloads or credentials copied here.
- Fleet: bridge/README.md and bridge/ships/*.yaml. Pre-handoff Fleet source: c4cc18bdd1eab7e0a38569c56422f62ed3d55c35.

This handoff reconstructs progress from current source, live data and bridge receipts. It is not a full transcript of the original dashboard session. The cloud check did not change a scheduler, dispatch a laptop job, or deploy dashboard code.
