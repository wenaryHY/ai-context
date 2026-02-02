# Backend architecture review - issues (preliminary)

Context: plugin-trace backend (Halo plugin). Notes captured for later solution design.

## Key shortcomings (plain language)
1. Full scans + in-memory filtering/paging for lists/analytics/export/trash.
   - Impact: slow when data grows; memory pressure.
   - Evidence: use of client.list(...).collectList() or list+filter+skip+take in services.
   - Trade-off: likely due to extension query limits; OK for small data.

2. Counters updated by read-modify-write (votes/comments).
   - Impact: race conditions under concurrency; counts can drift.
   - Evidence: VoteServiceImpl.updateVoteCount, CommentServiceImpl.updateCommentCount.
   - Trade-off: simple implementation.

3. Endpoint layer is heavy and repetitive.
   - Impact: higher maintenance cost; inconsistent behavior risk.
   - Evidence: repeated auth, idempotency, user profile build in FeedbackConsoleEndpoint / FeedbackPublicEndpoint.

4. Blocking IO inside reactive flows.
   - Impact: blocks event loop; throughput drops.
   - Evidence: CSV parse/import/export, local file write in TrashServiceImpl.

5. Tests are missing.
   - Impact: regressions are likely when changing behavior.
   - Evidence: src/test/java is empty.

## Notes for later discussion
- Define data scale boundary (what is "small" for this plugin).
- Plan upgrades if volume grows: query filters, pre-aggregation, async jobs.
- Extract shared logic from endpoints into application/service layer.
- Add minimal test suite: workflow rules, idempotency, permissions, import/export.
