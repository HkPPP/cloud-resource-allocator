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

        Args:
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.
            servers: Server inventory in original input order; an empty inventory is
                permitted.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            ScheduleResult: Final indexed classifications and algorithm statistics, with
                runtime including validation and preparation.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Shared scheduling pipeline is not implemented.')

    @abstractmethod
    def solve(self, prepared: PreparedInstance) -> ScheduleResult:
        """Solve an immutable instance with private mutable state and domains.

        Runtime excludes preprocessing here. Include invalid records and original
        input indices in all outputs. A timed-out run returns its best feasible
        incumbent (possibly all valid jobs omitted), with optimality_proven false.

        Args:
            prepared: Immutable normalized input containing valid jobs, servers,
                configuration, initial domains, indexed errors and original submission
                identities.

        Returns:
            ScheduleResult: Final indexed classifications from prepared input; runtime
                excludes preprocessing and interrupted searches cannot claim proven
                optimality.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Strategy is not implemented.')
