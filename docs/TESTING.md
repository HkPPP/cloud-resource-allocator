# Testing

Use the OS-specific virtual environment setup in the README, then run tests with
that environment's interpreter:

```text
python -m pytest
python -m pytest -q
python -m pytest tests/test_domains.py -v
```

## Feature coverage and expected failures

Data model declarations, JSON transport, CLI help and input fixture structure
have passing tests. Behavioral tests for unavailable features use:

```python
@pytest.mark.xfail(
    reason="Feature not implemented",
    raises=NotImplementedError,
    strict=True,
)
```

Only `NotImplementedError` is an expected failure. Assertion errors and other
unexpected exceptions remain test failures. Strict mode reports an unexpected
pass as a failure until its marker is removed. Each completed feature requires
its behavioral assertions to pass without that marker.

An unavailable pipeline dependency can prevent downstream assertions from being
reached. Expected-failure counts therefore describe implementation coverage,
rather than establishing correctness. The [development roadmap](IMPLEMENTATION_PLAN.md)
tracks these dependencies. The CLI unavailable-feature test is replaced by an
execution test when the input-loading and scheduling pipeline is available.

## Correctness tests

Tests verify observable outcomes rather than private array or trail layouts.
Small prepared-input fixtures declare candidate domains explicitly. Scenario
expected values define acceptance criteria, separate from benchmark measurements.
The GPU fixture's shared [0,15) deadline ensures that sequential execution cannot
hide the Greedy baseline's suboptimal placement. CSP tests allow different
assignments when objective scores tie.

Coverage includes capacity boundaries, half-open intervals, conditional
relationships, record identity, objective ordering, timeout validity and
capacity-time metrics. Empty valid inputs have `completion_rate=None`; no
scheduled jobs have `average_waiting_minutes=None`. Resource utilization is
`None` when total capacity is zero; otherwise its denominator includes the full
horizon. Internal rates are fractions, with percentages reserved for presentation.

## Performance evaluation

Benchmark tests verify aggregation and data integrity. A single-run `timed_out`
boolean becomes `timeout_rate = timed_out_runs / total_runs`; an empty benchmark
has `None`. Performance experiments use measured runs and record the interpreter,
OS, hardware and configuration. They run separately from correctness tests.

## Platform coverage

CI performs fresh editable installations on Ubuntu and Windows for Python 3.11
and 3.13. Local execution verifies only the operating system used for that run.
Tests cover Unicode paths, spaces, UTF-8 BOMs and LF output on both systems.
