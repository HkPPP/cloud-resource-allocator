"""One shared pipeline for raw inputs, with a prepared-input benchmark entry point."""
from abc import ABC, abstractmethod
from dataclasses import replace
from time import perf_counter
from typing import Sequence
from ..config import SchedulerConfig
from ..models import RawJob, ScheduleResult, Server
from ..preprocessing import PreparedInstance, preprocess_inputs

class BaseScheduler(ABC):
    """Validate, prepare, solve and classify consistently across all strategies."""

    def schedule(self, jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> ScheduleResult:
        """Prepare raw inputs and return the solver result with end-to-end timing.

        Args:
            jobs: Original submissions in input order, including malformed records.
                Each submission is identified by its zero-based input index.
            servers: Server inventory in original input order. It may be empty.
            config: Scheduling horizon, slot resolution and solver options.

        Returns:
            ScheduleResult: Solver classifications, original input indices and
                statistics, with runtime in milliseconds covering preprocessing
                and solving.

        Raises:
            ValueError: Configuration or server inventory is invalid. Individual
                job errors are returned in the result.
        """
        start = perf_counter()
        prepared = preprocess_inputs(jobs, servers, config)
        result = self.solve(prepared)
        return replace(result, runtime_ms=(perf_counter() - start) * 1000)

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
