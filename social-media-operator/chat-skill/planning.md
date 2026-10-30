# Weekly planning rules

Use a Saturday–Friday Cairo-local week unless the operator specifies another range; show exact dates. For a partly elapsed week preserve actual publications and approved future slots, and plan only the remaining slots. The quota is 21 Stories (3 per day) and 4 Posts on four distinct days, not a promise of automatic publishing.

Read all relevant board pages and available Instagram publication history. Identify the same asset through source project/code plus confirmed file/version and post records; do not count differently named copies as new videos. Treat uncertain duplicates as review items. Exclude Published, Cancelled and confirmed already-published assets. Keep already-approved future reservations; do not allocate the same item or asset twice. Respect the recorded Post/Story format. Select Ready to Publish first; place In Progress or New content only as provisional preparation assignments, never claim it is ready. Blocked items are not committed slots.

Vary projects, client/code families and themes across each day when the inventory permits; do not invent client classifications. Show conflicts rather than silently changing formats or repeating an asset. Reusing a source as both Post and Story requires an explicit approved distinct version/use, not an assumption.

Use verified audience activity and comparable historical content performance; state account, date range, timezone and metrics actually available. Do not compare raw Story views to Post reach as if identical. Prefer the four best-supported distinct Post days and spread three Story slots over the day. Do not promise that posting at a time guarantees results.

If timing analytics are missing, propose Saturday/Monday/Wednesday/Friday at 19:00 for Posts and 12:00/17:00/21:00 for Stories, Africa/Cairo. Label these experimental defaults, not observed best times, and request operator confirmation. Re-evaluate after two weeks using available reach, engagement and Story completion/exit data; unavailable metrics remain unavailable. Do not infer a foreign audience's timezone from property addresses.

Show a table with date, Cairo-local time, format, project/code, item link, readiness and preparation required. Reconcile totals explicitly: 3 Stories on each date; 4 Posts across 4 dates; unique assets; no conflict with preserved reservations. A shortage must state exact counts and open slots. The operator can approve a feasible partial plan; leave unavailable slots unassigned.

Before writing confirmed Publish At, re-read the affected records and compare Format, Status, Code, Ready File, Caption and Publish At with the proposal snapshot. Re-propose conflicting items. Use current connector date/time semantics; convert using Africa/Cairo with the date-specific DST offset, never a fixed UTC+2/+3. Read back and show the resulting Cairo-local time. A disconnected write capability means return the approved table for manual entry and state that no write occurred.

## Optional local audit

When a Python execution tool and these package files are available, `scripts/check_plan.py` checks a full-week draft without remote writes. Otherwise perform the same checks explicitly in the proposal. It does not infer analytics, approve a plan, fetch current records or allocate times.

Input JSON contains `plan` and `current_items`. `plan` has ISO `week_start`, `published_assets` (confirmed asset keys), and `slots`. Each slot has `item_id`, confirmed `asset_id`, ISO `publish_at` with an explicit offset, and `snapshot` with `format`, `status`, `code`, `ready_file`, `caption`, `publish_at` (the old board value). `current_items` contains newly read records with `item_id` and the same six fields. Do not substitute proposal snapshots for fresh reads. The validator is for a full prospective week; midweek plans still require explicit reconciliation with actual publications.

Run `python3 scripts/check_plan.py proposal.json`. Inspect `shortages`, `errors`, and `conflicting_item_ids`; a successful result is technical validation, not permission to write.
