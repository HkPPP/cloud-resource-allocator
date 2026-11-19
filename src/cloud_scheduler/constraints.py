"""Read-only hard-constraint checking contracts."""
from typing import Mapping
from .config import SchedulerConfig
from .models import Assignment, Job, Placement, Server, ResourceVector
from .state import ScheduleState

class ConstraintChecker:
    """All checks are pure; direct relationships are symmetric and conditional."""

    def check_time_window(self, job: Job, placement: Placement, config: SchedulerConfig) -> bool:
        """Check aligned start and half-open end within release, deadline and horizon.
        Boundary touching is valid; the job must execute continuously for its duration.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            bool: True if the aligned, continuous interval starts at or after release
                and ends at or before both deadline and horizon. The exclusive end may
                equal either bound.
        """
        return ((placement.start_minute + job.duration_minutes <= config.horizon_minutes) and
                (job.release_minute < placement.start_minute < job.deadline_minute))

    def check_resource_capacity(self, job: Job, placement: Placement, state: ScheduleState) -> bool:
        """Require usage plus demand <= all four capacities in every occupied slot.
        Overlapping jobs are allowed when their cumulative demands fit.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.
            state: Current solver-owned assignments and per-server, per-slot resource
                usage. Read-only unless mutation is explicitly described above.

        Returns:
            bool: True if current usage plus the candidate demand fits every resource in
                every occupied slot on the selected server. Other servers and
                boundary-touching intervals do not contribute.
        """
        current_usage = state.get_usage(placement.server_id, placement.start_minute)
        expected_usage = current_usage + job.resource_requirements()

        server = next(
            server for server in state.prepared.servers
                if server.server_id == placement.server_id
        )
        return expected_usage.fits_within(server.capacity())



    def check_server_pinning(self, job: Job, placement: Placement) -> bool:
        """Accept an unpinned job or a placement matching the required server exactly.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.

        Returns:
            bool: True when the job has no pin or its required server ID equals the
                candidate server ID.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ConstraintChecker.check_server_pinning is not implemented.')

    def check_colocation(self, job: Job, placement: Placement, assignments: Mapping[str, Assignment], jobs: Mapping[str, Job]) -> bool:
        """Check direct same-server edges declared in either direction.
        Ignore unscheduled neighbors; time overlap is irrelevant to server affinity.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.
            assignments: Current partial mapping of scheduled job IDs to assignments.
                Unassigned related jobs are absent and impose no relationship
                constraint.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            bool: True if every assigned direct same-server neighbor uses the candidate
                server. Unassigned neighbors and unrelated jobs impose no constraint.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ConstraintChecker.check_colocation is not implemented.')

    def check_anti_affinity(self, job: Job, placement: Placement, assignments: Mapping[str, Assignment], jobs: Mapping[str, Job]) -> bool:
        """Check different-server edges in either direction for assigned neighbors only.
        Different intervals do not exempt jobs from this server identity restriction.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.
            assignments: Current partial mapping of scheduled job IDs to assignments.
                Unassigned related jobs are absent and impose no relationship
                constraint.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            bool: True if every assigned direct different-server neighbor uses another
                server, even when execution intervals do not overlap.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ConstraintChecker.check_anti_affinity is not implemented.')

    def can_place(self, job: Job, placement: Placement, state: ScheduleState) -> bool:
        """Determine whether a new assignment satisfies every hard scheduling constraint.

        Check time alignment and bounds, cumulative resource capacity, server pinning,
        co-location and anti-affinity. Unknown servers and duplicate assignments are
        rejected. Evaluation reads the current state without changing it.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.
            state: Current solver-owned assignments and per-server, per-slot resource
                usage. Read-only unless mutation is explicitly described above.

        Returns:
            bool: True only if all hard constraints hold. Unknown servers and duplicate
                job assignments return False. No assignments or usage are changed.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ConstraintChecker.can_place is not implemented.')
