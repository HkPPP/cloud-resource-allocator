"""One shared pipeline for raw inputs, with a prepared-input benchmark entry point."""
from abc import ABC, abstractmethod
from typing import Sequence
from ..config import SchedulerConfig
from ..models import RawJob, ScheduleResult, Server
from ..preprocessing import PreparedInstance

class BaseScheduler(ABC):
    """Validate, prepare, solve and classify consistently across all strategies."""

    def schedule(self, jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> ScheduleResult:
        """Time validation, separate invalid records, build domains, initialize state,
        invoke solve, classify each record once, and return statistics.

        Share preprocess_inputs; subclasses must not duplicate validation. Use a
        monotonic clock. Config/server errors abort with ValueError. Per-job errors
        are retained in results. Unavailable functionality raises NotImplementedError.
        """
        raise NotImplementedError('Shared scheduling pipeline is not implemented.')

    @abstractmethod
    def solve(self, prepared: PreparedInstance) -> ScheduleResult:
        """Solve an immutable instance with private mutable state and domains.

        Runtime excludes preprocessing here. Include invalid records and original
        input indices in all outputs. A timed-out run returns its best feasible
        incumbent (possibly all valid jobs omitted), with optimality_proven false.
        """
        raise NotImplementedError('Strategy is not implemented.')
