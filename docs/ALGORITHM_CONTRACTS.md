# Algorithm contracts

This document defines solver behavior and invariants. Scheduling, propagation
and optimization implementations are not yet available.

## Shared pipeline

`BaseScheduler.schedule` validates configuration and inventory, classifies
malformed jobs, normalizes relationships, constructs immutable domains and state,
invokes the selected solver, and accounts for every submission. `solve(prepared)`
supports reuse of prepared inputs across benchmark runs. All algorithms share
constraints, identity mapping and the `ScheduleResult` output structure.

## Greedy First-Fit

Jobs are processed in original valid input order. Candidate placements are ordered
by start minute, then original server order. The first feasible candidate is
selected; jobs without a feasible candidate remain unscheduled. Earlier
assignments are final. The result satisfies hard constraints without a guarantee
of objective optimality. The GPU failure fixture has an expected count of five.

## Chronological backtracking and optimization

Basic backtracking selects the next undecided job in input order, considers real
placements and `UNASSIGNED`, and restores state after each explored branch.
Complete decisions form feasible schedules; the best lexicographic result is
retained as an independent snapshot. Branch-and-bound excludes only branches
whose optimistic objective vector cannot improve the incumbent. A singleton
`UNASSIGNED` domain remains feasible.

The initial all-omitted incumbent ensures that even an immediate timeout can
return a feasible result. Interrupted searches report that optimality was not
proven. A proof requires completed search with sound pruning. Tied optimal
schedules may contain different assignments.

## Forward checking and MRV

Forward checking removes real placements that conflict with current assignments.
Omission values are retained; removed values are recorded for exact restoration.
Conflicts between hypothetical future decisions do not justify filtering.

MRV counts feasible real placements, excluding `UNASSIGNED`, and breaks ties by
input order. Zero real placements is a valid count. Basic BT, BT+FC and MRV+FC
are configurations of the same solver.

## Backjumping and MAC

Backjumping requires explicit conflict sets and restoration across skipped
levels, including omission and optimization decisions. MAC requires a cumulative
resource constraint representation; binary arc consistency alone is insufficient.
Both techniques are planned extensions. Enabled unsupported options raise
`NotImplementedError` rather than silently selecting a different technique.

## Timeouts and restoration

Search uses a monotonic deadline with checks at bounded search and propagation
intervals. Assignments, usage and domain deletions are restored on normal return,
timeout and error. Incumbents are copied rather than retained as mutable tracker
views. A timeout result accounts for every submission and passes independent
validation. Correctness tests avoid machine-dependent timing thresholds; only
forced tiny-budget cases assert interruption.
