"""Deterministic first-fit baseline contract."""
from typing import Sequence
from .base import BaseScheduler
from ..models import Job, Placement, ScheduleResult
from ..preprocessing import PreparedInstance
from ..state import ScheduleState

class GreedyScheduler(BaseScheduler):
    """A feasible baseline with no promise of lexicographic optimality."""

    def solve(self, prepared: PreparedInstance) -> ScheduleResult:
        """Process valid jobs in input order; try ascending starts then server input order.
        Place the first feasible candidate, never reconsider it; otherwise omit the job.
        Classify all records and report optimality_proven false, including empty runs.

        Args:
            prepared: Immutable normalized input containing valid jobs, servers,
                configuration, initial domains, indexed errors and original submission
                identities.

        Returns:
            ScheduleResult: Deterministic first-fit assignments and all invalid/omitted
                records; optimality_proven is False and search_nodes is zero.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('GreedyScheduler.solve is not implemented.')

    def order_jobs(self, jobs: Sequence[Job]) -> tuple[Job, ...]:
        """Preserve original valid input order without sorting by demand or mutating input.

        Args:
            jobs: Valid jobs in original input order, with resolved deadlines and
                normalized direct relationships.

        Returns:
            tuple[Job, ...]: The jobs in exactly their supplied order, including an
                empty tuple for no jobs.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('GreedyScheduler.order_jobs is not implemented.')

    def find_first_feasible_placement(self, job: Job, prepared: PreparedInstance, state: ScheduleState) -> Placement | None:
        """Return earliest feasible start with original server order as tiebreak.
        Return None if no real placement fits; do not mutate state while examining
        values.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            prepared: Immutable normalized input containing valid jobs, servers,
                configuration, initial domains, indexed errors and original submission
                identities.
            state: Current solver-owned assignments and per-server, per-slot resource
                usage. Read-only unless mutation is explicitly described above.

        Returns:
            Placement | None: First feasible candidate by start time then original
                server order; None if no real candidate is feasible. State is unchanged.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('GreedyScheduler.find_first_feasible_placement is not implemented.')
