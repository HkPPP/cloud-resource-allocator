# Development roadmap

Milestones are ordered by dependency. Completion requires the corresponding
behavioral tests to pass without expected-failure markers. Parameterized cases
can be split when their implementation milestones differ.

| Milestone | Scope | Acceptance criteria |
| --- | --- | --- |
| 1. Models and input validation | Resource and job helpers; configuration, inventory, job and reference validation; semantic input loading. Initial priorities: `SchedulerConfig.validate`, `validate_servers`, `validate_jobs`. | `test_models`, `test_preprocessing` validation cases and `test_io` loaders pass. Invalid submissions retain original input identity. |
| 2. Domain generation | `InitialDomainBuilder` and the complete `preprocess_inputs` pipeline. | `test_domains` and preprocessing integration tests pass, including horizon limits and omission values. |
| 3. Constraints and state | Hard constraints, cumulative resource tracking, atomic placement and reversible state. | `test_constraints` and `test_state` pass, including asymmetric relationships, skipped intermediates and copy isolation. |
| 4. Greedy baseline | Shared scheduling pipeline, deterministic First-Fit and CLI result serialization. | `test_greedy` and all documented scenarios pass. The CLI unavailable-feature test is replaced with an execution test when loading and scheduling are available. |
| 5. Independent validation | Final assignment, resource, time, placement and status checks independent of mutable solver state. | `test_validator` passes before scheduler results are accepted for evaluation. |
| 6. Basic CSP search | Chronological backtracking, omission decisions, incumbent snapshots, restoration and timeout handling. | Omission, restoration and timeout cases in `test_csp` pass. Exhaustive search provides a reference for optimization. |
| 7. Objective optimization | Objective evaluation, lexicographic comparison and admissible branch-and-bound. | `test_objectives` and small optimal-instance cases in `test_csp` pass. |
| 8. Forward checking | Reversible filtering of values conflicting with current assignments. | Forward-checking tests and scenario tests with FC enabled pass. |
| 9. MRV | Selection by feasible real-placement count, with stable input-order ties. | MRV tests and scenario tests with MRV+FC enabled pass. |
| 10. Metrics and benchmarking | Quality and capacity-time metrics, independent result validation and measured multi-run aggregation. | `test_metrics` passes; multi-run benchmark tests verify aggregation and timing scope. |
| 11. Advanced techniques | Conflict sets for backjumping and an explicit cumulative-resource representation for MAC. | Technique-specific behavior tests pass before either option is enabled. |

## Platform requirements

Every milestone targets Windows and Ubuntu. File paths use `pathlib.Path`, text
I/O uses explicit UTF-8, and subprocesses use `sys.executable`. The CI matrix
covers both operating systems. Correctness tests avoid hardware-dependent runtime
thresholds; performance measurements record their environment separately.
