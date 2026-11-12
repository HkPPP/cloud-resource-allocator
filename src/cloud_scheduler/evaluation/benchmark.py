"""Benchmark execution and performance aggregation contracts."""
from dataclasses import dataclass
from typing import Sequence
from ..preprocessing import PreparedInstance
from ..schedulers.base import BaseScheduler
from .metrics import MetricsReport

@dataclass(frozen=True)
class BenchmarkReport:
    """Per-run reports and aggregate timed-out-runs / total-runs; None if empty."""
    runs: tuple[MetricsReport, ...]
    timeout_rate: float | None

class BenchmarkRunner:
    """Share immutable preparation and isolate all mutable state between runs."""

    def run(self, schedulers: Sequence[BaseScheduler], prepared: PreparedInstance, repetitions: int = 1) -> BenchmarkReport:
        """Measure each solve with a monotonic clock; exclude shared preparation.

        Reject repetitions < 1; independently validate each result before metrics.
        Preserve solver configuration fairness, report actual observations only,
        and aggregate boolean timeouts over all completed benchmark attempts.
        Correctness tests must not assert machine-specific timing thresholds.
        """
        raise NotImplementedError('Benchmark orchestration is not implemented.')
