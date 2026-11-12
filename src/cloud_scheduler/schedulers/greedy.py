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
        Classify all records and report optimality_proven false, including empty runs."""
        raise NotImplementedError('GreedyScheduler.solve is not implemented.')

    def order_jobs(self, jobs: Sequence[Job]) -> tuple[Job, ...]:
        """Preserve original valid input order without sorting by demand or mutating input."""
        raise NotImplementedError('GreedyScheduler.order_jobs is not implemented.')

    def find_first_feasible_placement(self, job: Job, prepared: PreparedInstance, state: ScheduleState) -> Placement | None:
        """Return earliest feasible start with original server order as tiebreak.
        Return None if no real placement fits; do not mutate state while examining values."""
        raise NotImplementedError('GreedyScheduler.find_first_feasible_placement is not implemented.')
