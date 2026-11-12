"""Measured metrics contracts; no fabricated values or benchmarks."""
from dataclasses import dataclass
from typing import Sequence
from ..config import SchedulerConfig
from ..models import Job, ScheduleResult, Server

@dataclass(frozen=True)
class MetricsReport:
    """Rates/utilizations are fractions in [0,1], not percentages.

    Completion denominator is valid submissions. None denotes undefined completion
    (no valid jobs), waiting (no scheduled jobs), or utilization (zero capacity).
    Per-run timed_out is a boolean; timeout_rate is aggregated by benchmarks.
    """
    completion_rate: float | None
    average_waiting_minutes: float | None
    unscheduled_count: int
    invalid_count: int
    cpu_utilization: float | None
    ram_utilization: float | None
    gpu_utilization: float | None
    storage_utilization: float | None
    runtime_ms: float
    search_nodes: int
    timed_out: bool
    optimality_proven: bool

class MetricsCalculator:
    """Calculate quality/utilization only after independent schedule validation."""

    def calculate(self, result: ScheduleResult, jobs: Sequence[Job], servers: Sequence[Server], config: SchedulerConfig) -> MetricsReport:
        """Use valid resolved jobs (excluding INVALID records) for quality metrics.

        Utilization is sum(demand * assigned duration) / sum(capacity * horizon)
        for each resource, including idle horizon minutes. Wait averages scheduled
        jobs only. Propagate runtime, nodes, timeout and proof fields unchanged.
        Empty/zero-denominator values follow MetricsReport's None convention.
        Do not round internally; report formatting may convert fractions to percent.
        """
        raise NotImplementedError('Measured metrics is not implemented.')
