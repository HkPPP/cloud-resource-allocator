# Intelligent Cloud Resource Scheduler

A Python framework for offline batch scheduling across heterogeneous cloud
servers, with time-window constraints and configurable optimization objectives.
Requires **Python 3.11+** on **Ubuntu or Windows**.

The project is in active development. Data models, JSON transport, package
installation, CLI argument parsing and test infrastructure are available.
Scheduling algorithms, preprocessing, constraint checking, objective evaluation,
schedule validation and metrics are not yet implemented. Calls to unavailable
features raise `NotImplementedError`. Benchmark results are not yet available.

## Setup on Ubuntu

From the repository root, with Python 3.11 or newer installed:

```bash
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python -m cloud_scheduler --help
```

If venv is unavailable, install Ubuntu's matching `python3-venv` package using
your normal package manager. Check the interpreter version before creating venv.

## Setup on Windows (PowerShell)

Install Python 3.11+ with the Python launcher, then from the repository root:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m cloud_scheduler --help
```

If `py` is unavailable, use `python` after checking `python --version`.
No activation is required, so PowerShell execution policy need not change.
Create a separate `.venv` on each OS; virtual environments are machine-specific
and excluded from version control.
Use the environment's Python for every pip/test invocation. Shell scripts,
Unix utilities and platform-specific Python dependencies are not required.

## Architecture

`src/cloud_scheduler` contains immutable models/configuration, preprocessing,
domains, constraint checking, reversible state and lexicographic objectives.
`schedulers` provides a shared pipeline and Greedy/CSP strategies; `evaluation`
provides independent validation, metrics and benchmark contracts. `data` contains
JSON inputs, `tests` acceptance tests, and `docs` the architecture and development documentation.

See [architecture](docs/ARCHITECTURE.md),
[component interaction diagrams](docs/COMPONENT_INTERACTIONS.md),
[CSP formulation](docs/CSP_FORMULATION.md),
[algorithm contracts](docs/ALGORITHM_CONTRACTS.md),
[development roadmap](docs/IMPLEMENTATION_PLAN.md), and [testing](docs/TESTING.md).

## Configuration and invocation

```json
{
  "horizon_minutes": 1440,
  "slot_minutes": 15,
  "objectives": ["max_jobs", "min_wait"],
  "search_timeout_seconds": 30,
  "use_mrv": false,
  "use_forward_checking": false,
  "use_backjumping": false,
  "use_mac": false
}
```

Time uses integer minutes and half-open intervals. Slots divide the horizon.
Objectives are unique supported names in priority order: `max_jobs`, `min_wait`,
`min_active_servers`. Prefer `max_jobs` first: putting a minimization objective
first can intentionally favor scheduling no jobs. JSON arrays become immutable
tuples during semantic loading. Optional advanced flags remain unavailable.

The scheduling command interface is shown below. Execution becomes available
when input loading and scheduling are implemented:

```text
python -m cloud_scheduler --algorithm greedy --config config/default.json --jobs data/jobs.json --servers data/servers.json
python main.py --algorithm csp
```

Here `python` means the venv interpreter shown above. The installed
`cloud-scheduler` entry point is equivalent. Run these default relative paths from
the repository root; explicit absolute paths work from other directories. Quote
paths containing spaces. CLI execution currently exits 2 with a feature-unavailable message;
it does not produce a schedule. Scenario bundles contain config/servers/jobs and
expected outcomes for tests; the CLI accepts separate files, not bundle files.

## Scenario expectations

All bundles have three servers, 5–8 jobs, a 1440-minute horizon and 15-minute slots.
The counts below define expected test outcomes. They are not benchmark measurements.

| Scenario | Greedy scheduled | CSP maximum | Details |
| --- | ---: | ---: | --- |
| simple | 6 | 6 | All start at 0; four share gpu, two share cpu. |
| greedy_failure | 5 | 6 | Greedy puts flex on gpu at 0, omits gpu-job; CSP puts flex on cpu and gpu-job on gpu at 0. Four later jobs start at 30; total CSP wait is 0. |
| gpu_scarcity | 3 | 3 | Greedy schedules g1 at 0, g2 at 15 and cpu-job at 0; g3/g4 omitted; four-gpu valid but unschedulable. |
| high_demand | 2 | 2 | Greedy selects h1 on gpu and h2 on cpu at 0; all jobs need 4 cores and [0,15). |
| time_constraints | 3 | 3 | Greedy schedules early at 0, boundary at 15, parallel at 0; conflict/outside omitted; invalid-window INVALID. |

The GPU failure requires both competing jobs to fill the same tight [0,15)
window; later execution cannot repair Greedy's first decision. CSP optimal
assignments may differ on tied scores. See the bundle's `expected` fields.

## Development roadmap

Input validation is the next milestone: `SchedulerConfig.validate`,
`validate_servers` and `validate_jobs`. Domain generation, constraint checking,
scheduling and evaluation follow in dependency order.

See the [development roadmap](docs/IMPLEMENTATION_PLAN.md) for acceptance criteria.
Tests for unavailable functionality use strict `xfail` limited to
`NotImplementedError`; unexpected errors remain visible.
