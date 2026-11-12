# Architecture and input contracts

See [component interaction diagrams](COMPONENT_INTERACTIONS.md) for the input
pipeline, solver internals, independent evaluation and benchmark flow.
You can also [open the diagram as an image](diagrams/component-interactions.png).

## Modules and classes

| Module | Responsibility |
| --- | --- |
| models | ResourceVector: four resource units/arithmetic; Server: inventory/capacity; Job: demand/time/relationships; Placement: candidate; Assignment: indexed final interval; Unassigned/UNASSIGNED: omission; JobStatus: classifications; InvalidJob: indexed structured errors; UnscheduledJob: valid omission; ScheduleResult: assignments/classifications/performance. |
| config | SchedulerConfig: immutable horizon/grid/objectives/technique flags and validation; OBJECTIVE_NAMES restricts the initial objective vocabulary. |
| preprocessing | Global and per-record validation, reference normalization, original input identity, deeply immutable PreparedInstance and shared pipeline. |
| domains | InitialDomainBuilder: unary hardware, pin and time filtering; never filter against hypothetical assignments. |
| constraints | ConstraintChecker: pure checks of time, cumulative resources, pins and direct conditional relationships. |
| state | ScheduleState: private usage arrays and temporary assignments with atomic placement, exact undo and independent copies. |
| objectives | Direction and abstract Objective; MaxJobs, MinWait, MinActiveServers; compare_schedules defines the lexicographic comparison interface. |
| io | UTF-8 JSON transport via pathlib, semantic config/inventory/raw-record loaders. Only read_json/write_json work now. |
| schedulers/base | BaseScheduler: shared raw-input pipeline; solve takes an immutable prepared input for fair benchmark reuse. |
| schedulers/greedy | GreedyScheduler: input order, earliest start, server input order, irrevocable first fit. |
| schedulers/csp | CSPScheduler: configurable search/propagation hooks, incumbent snapshots, reversible domains and admissible bounds. |
| evaluation/validator | ValidationReport and ScheduleValidator reconstruct independent usage and verify constraints/classification. Never import state tracking. |
| evaluation/metrics | MetricsReport and MetricsCalculator: quality, full-horizon capacity-time utilization and per-run performance. |
| evaluation/benchmark | BenchmarkReport and BenchmarkRunner: isolate solvers, validate outputs, aggregate real measurements. |
| cli / __main__ / main.py | Portable argument parsing, explicit input paths and explicit errors for unavailable features. |

## Identity, parsing and validation

A job file is a JSON array; each element gets its original zero-based input_index,
even when not an object. Parse JSON before constructing Job. Missing fields or
malformed objects become InvalidJob entries; a syntactically invalid file aborts.
All occurrences of a duplicate job ID are invalid; duplicate server IDs invalidate
the entire inventory. Keep indexed errors when an ID is absent. Assignments and
UnscheduledJob also carry input_index, enabling exact per-submission accounting.
Collect multiple errors in one InvalidJob with parallel error_codes/reasons tuples.

Global config/inventory errors raise ValueError; file I/O errors propagate. Empty
job lists and empty inventories are allowed. No hardware fit yields a valid job
with only UNASSIGNED. Unknown fields are errors, not silently ignored.

CPU/GPU and all time values must be integers, excluding bool; RAM/storage must be
finite nonnegative numeric GB values, excluding bool. Duration is positive.
ResourceVector arithmetic may have signed intermediates; actual demands/usage may
not. Floating resource values need documented consistent numeric tolerance if
fractional GB values are supported; time is always exact integer arithmetic.

Release defaults to zero; deadline defaults to horizon during preprocessing.
Reject negative release, misaligned times, and a window shorter than duration.
A consistent aligned request extending beyond the horizon remains valid; candidate
ends are limited to min(deadline,horizon). Thus a release at/after horizon can
leave a valid job unscheduled. No pausing, migration or preemption is allowed.

## Relationships

Check original declarations for unknown targets before symmetric normalization.
Unknown job/server references invalidate the declarer. Known invalid targets are
removed without cascading. Self same-server edges are discarded; self different-
server edges are invalid. A direct pair requiring both same/different servers
invalidates both endpoints. Errors merge with existing per-record errors.
Normalize remaining direct edges symmetrically. Do not compute transitive closure.
For A=B, B=C, A!=C, skipping B permits A and C on different servers. Different
pins in a same-server pair or longer inconsistent cycles constrain feasible subsets
and do not themselves invalidate otherwise valid jobs. Relationships apply even
when assigned jobs execute at different times.

## State and timing

PreparedInstance contains only frozen dataclasses and tuples, including domains;
valid Job relationship fields and config objectives must be tuples after preparing.
Keep valid ID-to-input-index pairs so reference errors retain original identity.
Each solve copies domains and creates private state. Failed place changes nothing.
Undo restores all affected slots and assignment entries; absent undo raises KeyError.

schedule runtime includes preparation; solve runtime excludes shared preparation.
Use a monotonic clock and put timing_scope in result statistics. Count a search
node on each entered recursive search state, including the root. Greedy reports
zero search nodes. Timeout means a configured search deadline interrupted the run;
Greedy/provenance details must never falsely imply objective optimality.
