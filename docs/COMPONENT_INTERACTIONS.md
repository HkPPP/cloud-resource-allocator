# Component interactions

![Scheduler component interaction diagram](diagrams/component-interactions.png)

Open the [PNG image](diagrams/component-interactions.png) directly, or use the
[SVG image](diagrams/component-interactions.svg) for sharper zooming and printing.
The image displays in a standard Markdown preview without a Mermaid extension.

These diagrams describe the component interfaces and planned execution flow.
Scheduling, preprocessing, constraint checking, optimization and evaluation are
not yet implemented; their interfaces raise `NotImplementedError`.

The detailed Mermaid diagrams below provide additional views and editable text
source. Rendering those blocks requires Mermaid support. Both image formats can
be opened on Windows and Ubuntu.

## From input files to an evaluated schedule

```mermaid
flowchart TB
    files["JSON inputs<br/>config/default.json<br/>data/jobs.json + data/servers.json"]
    entry["Entry points<br/>main.py / python -m cloud_scheduler<br/>cloud-scheduler"]
    io["cli.py + io.py<br/>Read UTF-8 JSON and load inputs<br/>Preserve raw job records"]

    subgraph pipeline["Shared scheduling pipeline"]
        base["BaseScheduler.schedule<br/>Common entry point for both strategies"]
        prep["preprocess_inputs<br/>Validate configuration, servers and jobs<br/>Normalize direct relationship references"]
        domains["InitialDomainBuilder<br/>Filter hardware, pins and time windows<br/>Include UNASSIGNED for every valid job"]
        prepared["PreparedInstance<br/>Immutable jobs, servers, config and domains<br/>Invalid records and original input indices"]
        strategy["Selected strategy: solve(prepared)<br/>GreedyScheduler OR CSPScheduler"]
        result["ScheduleResult<br/>Assignments + invalid + unscheduled records<br/>Runtime, nodes, timeout and proof status"]

        base --> prep
        prep --> domains
        domains --> prepared
        prepared --> strategy
        strategy --> result
    end

    subgraph evaluation["Independent evaluation"]
        validator["ScheduleValidator<br/>Reconstruct usage from final assignments<br/>Check hard constraints and every input index"]
        report["ValidationReport<br/>valid, errors, constraint_violations"]
        accepted{"Valid schedule?"}
        metrics["MetricsCalculator<br/>Completion, waiting, capacity-time utilization<br/>Runtime, nodes, timeout and optimality"]
        metricReport["MetricsReport"]
        rejected["Report validation errors<br/>Do not accept quality metrics"]

        validator --> report --> accepted
        accepted -->|yes| metrics
        accepted -->|no| rejected
        metrics --> metricReport
    end

    output["CLI / caller<br/>Present or serialize results<br/>Optional JSON artifacts in results/"]
    globalError["Abort run with a clear error<br/>Malformed JSON, configuration or inventory"]

    entry --> io
    files --> io
    io -->|raw jobs, servers, config| base
    io -.->|file or JSON error| globalError
    prep -.->|global validation error| globalError
    io -->|original submissions, servers, config| validator
    result --> validator
    result -->|assignments and performance fields| metrics
    prepared -->|valid jobs, servers, config| metrics
    result --> output
    report --> output
    metricReport --> output
```

Malformed individual jobs become indexed `InvalidJob` records and remain in the
final accounting. Valid jobs with no feasible placement become `UnscheduledJob`
records. A global configuration or inventory error aborts the run.

Evaluation is a separate step after `schedule()` returns. The current CLI
does not yet connect evaluation or output serialization; those connections above
show the intended application flow.

## Inside the selected solver

```mermaid
flowchart TB
    prepared["PreparedInstance<br/>Shared immutable input"]

    subgraph greedyPath["GreedyScheduler"]
        greedy["order_jobs<br/>Original valid input order"]
        first["find_first_feasible_placement<br/>Earliest start, then server input order"]
        greedy --> first
    end

    subgraph cspPath["CSPScheduler"]
        privateDomains["Private mutable domain copy<br/>Placements plus UNASSIGNED"]
        search["backtrack<br/>select_next_job + order_domain_values<br/>Consider placement and omission branches"]
        propagation["Optional forward_check / propagate_constraints<br/>Remove conflicts with current assignments<br/>Retain UNASSIGNED and restoration data"]
        objective["Objective framework<br/>MaxJobs / MinWait / MinActiveServers<br/>compare_schedules: lexicographic priority"]
        best["Best feasible incumbent + admissible bounds<br/>update_best_solution / should_prune<br/>Timeout returns incumbent without proof"]
        privateDomains --> search
        search --> propagation
        propagation -->|filtered domains for next decision| search
        search -->|complete feasible schedule| objective
        objective --> best
        best -->|bound or continue search| search
    end

    state["ScheduleState: one private instance per solve<br/>Assignments and per-server, per-slot usage<br/>place / undo / copy / get_usage"]
    checker["ConstraintChecker<br/>Time windows, cumulative resource capacity<br/>Server pins, co-location and anti-affinity"]
    models["Shared models<br/>Job / Server / ResourceVector<br/>Placement / Assignment / UNASSIGNED"]
    result["ScheduleResult<br/>Exactly one status per original submission"]

    prepared --> greedy
    prepared --> privateDomains
    prepared -->|initialize private state| state
    first -->|can_place; place first fit| state
    search -->|can_place; place; undo; restore_state| state
    propagation -->|inspect current assignments and usage| state
    state -->|delegate feasibility checks| checker
    checker -->|read usage and assigned neighbors| state
    models -.->|common types and resource units| state
    models -.->|candidate and constraint data| checker
    first -->|final assignments and omissions| result
    best -->|incumbent snapshot and search statistics| result
```

The Greedy and CSP paths are alternatives. Each run creates its own mutable state;
they share interfaces and input contracts, rather than a live resource tracker.
Greedy never undoes earlier decisions. CSP must restore assignments, resource
usage and domain removals exactly when leaving a branch.

`ConstraintChecker` reads state without changing it. `ScheduleState.place()` checks
feasibility before changing usage; failed placement is atomic. Relationships apply
only when both directly related jobs are scheduled. An omission consumes no
resources and remains a valid decision even when no real placements survive.

`ScheduleValidator` deliberately sits outside this interaction: it rebuilds usage
from final assignments and never reads the solver's resource tracker. Optional
backjumping and MAC remain unavailable until their representations are designed.

## Benchmark reuse and test coverage

```mermaid
flowchart LR
    scenario["Scenario inputs<br/>data/scenarios/*.json<br/>Expected test outcomes"]
    prepare["Preprocess once"]
    prepared["Immutable PreparedInstance"]
    runner["BenchmarkRunner.run<br/>Repeat each selected solve<br/>Exclude preparation from solve timing"]
    solvers["Greedy / BT / BT+FC / MRV+FC<br/>Fresh state and domain copies per run"]
    validate["Independent validation<br/>Then MetricsCalculator"]
    report["BenchmarkReport<br/>Per-run MetricsReport values<br/>Aggregate timeout rate"]
    tests["pytest behavioral specifications<br/>Models, preprocessing, domains, constraints,<br/>state, schedulers, objectives, validation,<br/>metrics and portable I/O"]

    scenario --> prepare --> prepared --> runner
    runner --> solvers --> validate --> report
    scenario -.->|expected behavior| tests
    tests -.->|exercise shared preparation| prepare
    tests -.->|exercise each technique| solvers
    tests -.->|verify correctness and metrics| validate
```

The benchmark path calls `solve(prepared)` directly rather than repeating
`schedule()` and preprocessing. The benchmark implementation must retain original
submission context for independent validation, including malformed records;
`PreparedInstance` currently contains normalized jobs and errors rather than all
original raw payloads, so that context must be passed or retained when wiring the
runner. Only independently validated runs contribute accepted metrics. Expected
scenario counts define expected behavior; performance results require measured runs.

Tests for unavailable features use strict `xfail` limited to
`NotImplementedError`. See [the development roadmap](IMPLEMENTATION_PLAN.md) for
implementation dependencies and acceptance criteria.
