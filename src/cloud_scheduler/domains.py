"""Unary domain interfaces, independent of hypothetical assignments."""
from typing import Sequence
from .config import SchedulerConfig
from .models import DomainValue, Job, Placement, Server, UNASSIGNED

class InitialDomainBuilder:
    """Generate immutable initial candidates and include UNASSIGNED even for empty real domains."""

    def build_domains(self, jobs: Sequence[Job], servers: Sequence[Server], config: SchedulerConfig) -> dict[str, tuple[DomainValue, ...]]:
        """Return a domain per valid ID, sorted by start then original server order.
        Include exactly one UNASSIGNED last; zero servers still gives that singleton.
        Only unary filtering applies; related jobs may eventually be omitted.

        Args:
            jobs: Valid jobs in original input order, with resolved deadlines and
                normalized direct relationships.
            servers: Server inventory in original input order; an empty inventory is
                permitted.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            dict[str, tuple[DomainValue, ...]]: A domain per valid job ID, ordered by
                start then original server order, followed by exactly one UNASSIGNED. No
                real candidates yields (UNASSIGNED,); no jobs yields {}.

        Raises:
            ValueError: A job deadline has not been resolved during preprocessing.
        """
        domains = {}
        for job in jobs:
            eligible = self.get_eligible_servers(job, servers)
            candidates = tuple(
                Placement(server.server_id, start)
                for start in self.get_valid_start_times(job, config)
                for server in eligible
            )
            domains[job.job_id] = (
                *self.filter_unary_constraints(job, candidates, servers, config),
                UNASSIGNED,
            )
        return domains

    def get_eligible_servers(self, job: Job, servers: Sequence[Server]) -> tuple[Server, ...]:
        """Return individually capable servers satisfying pinning in original order.
        An empty result denotes a valid unschedulable request, not INVALID.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            servers: Server inventory in original input order; an empty inventory is
                permitted.

        Returns:
            tuple[Server, ...]: Individually capable servers satisfying the pin, in
                inventory order; empty if none qualify.

        """
        # Delay the import to avoid preprocessing -> domains -> state -> preprocessing.
        from .constraints import ConstraintChecker

        checker = ConstraintChecker()
        return tuple(
            server for server in servers
            if checker.check_server_pinning(job, Placement(server.server_id, 0))
            and server.supports(job)
        )

    def get_valid_start_times(self, job: Job, config: SchedulerConfig) -> tuple[int, ...]:
        """Return slot-aligned starts from release through min(deadline,horizon)-duration
        inclusively. Return empty when the horizon excludes the entire window.

        Args:
            job: Validated job with a resolved deadline and slot-aligned release,
                deadline and duration values.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            tuple[int, ...]: Ascending slot-aligned starts from release through
                min(deadline, horizon) - duration, inclusive; empty if that range is
                empty.

        Raises:
            ValueError: The job deadline has not been resolved during preprocessing.
        """
        if job.deadline_minute is None:
            raise ValueError("Job deadline must be resolved before domain generation.")
        latest_start = (
            min(job.deadline_minute, config.horizon_minutes) - job.duration_minutes
        )
        return tuple(range(job.release_minute, latest_start + 1, config.slot_minutes))

    def filter_unary_constraints(self, job: Job, placements: Sequence[Placement], servers: Sequence[Server], config: SchedulerConfig) -> tuple[Placement, ...]:
        """Return placements satisfying hardware, pins, grid, window and horizon.
        Preserve order and never inspect hypothetical assignments of other jobs.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placements: Candidate real placements to filter, in the order to preserve.
                Does not include UNASSIGNED.
            servers: Server inventory in original input order; an empty inventory is
                permitted.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            tuple[Placement, ...]: Placements satisfying unary hardware, pin, time-grid,
                window and horizon rules, with survivor order preserved.

        """
        from .constraints import ConstraintChecker

        eligible_ids = {
            server.server_id for server in self.get_eligible_servers(job, servers)
        }
        checker = ConstraintChecker()
        return tuple(
            placement for placement in placements
            if placement.server_id in eligible_ids
            and checker.check_time_window(job, placement, config)
        )
