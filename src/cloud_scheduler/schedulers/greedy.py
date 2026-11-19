"""Deterministic first-fit baseline contract."""
from time import perf_counter
from typing import Sequence
from .base import BaseScheduler
from ..models import Job, Placement, ScheduleResult, UnscheduledJob
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
        """
        started_at = perf_counter()
        state = ScheduleState(prepared)
        for job in self.order_jobs(prepared.jobs):
            placement = self.find_first_feasible_placement(job, prepared, state)
            if placement is not None:
                state.place(job, placement)

        assignments = state.get_assignments()
        unscheduled_jobs = tuple(
            UnscheduledJob(input_index, job_id)
            for job_id, input_index in prepared.input_indices
            if job_id not in assignments
        )
        return ScheduleResult(
            algorithm="greedy",
            assignments=tuple(assignments.values()),
            invalid_jobs=prepared.invalid_jobs,
            unscheduled_jobs=unscheduled_jobs,
            runtime_ms=(perf_counter() - started_at) * 1000,
            search_nodes=0,
            optimality_proven=False,
        )

    def order_jobs(self, jobs: Sequence[Job]) -> tuple[Job, ...]:
        """Preserve original valid input order without sorting by demand or mutating input.

        Args:
            jobs: Valid jobs in original input order, with resolved deadlines and
                normalized direct relationships.

        Returns:
            tuple[Job, ...]: The jobs in exactly their supplied order, including an
                empty tuple for no jobs.
        """
        return tuple(jobs)

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
        """
        # Prepared domains are already ordered by start time and server input order.
        for candidate in dict(prepared.domains)[job.job_id]:
            if isinstance(candidate, Placement) and state.can_place(job, candidate):
                return candidate
        return None
