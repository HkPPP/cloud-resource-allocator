"""Read-only hard-constraint checking contracts."""
from typing import Mapping
from .config import SchedulerConfig
from .models import Assignment, Job, Placement, Server
from .state import ScheduleState

class ConstraintChecker:
    """All checks are pure; direct relationships are symmetric and conditional."""

    def check_time_window(self, job: Job, placement: Placement, config: SchedulerConfig) -> bool:
        """Check aligned start and half-open end within release, deadline and horizon.
        Boundary touching is valid; the job must execute continuously for its duration."""
        raise NotImplementedError('ConstraintChecker.check_time_window is not implemented.')

    def check_resource_capacity(self, job: Job, placement: Placement, state: ScheduleState) -> bool:
        """Require usage plus demand <= all four capacities in every occupied slot.
        Overlapping jobs are allowed when their cumulative demands fit."""
        raise NotImplementedError('ConstraintChecker.check_resource_capacity is not implemented.')

    def check_server_pinning(self, job: Job, placement: Placement) -> bool:
        """Accept an unpinned job or a placement matching the required server exactly."""
        raise NotImplementedError('ConstraintChecker.check_server_pinning is not implemented.')

    def check_colocation(self, job: Job, placement: Placement, assignments: Mapping[str, Assignment], jobs: Mapping[str, Job]) -> bool:
        """Check direct same-server edges declared in either direction.
        Ignore unscheduled neighbors; time overlap is irrelevant to server affinity."""
        raise NotImplementedError('ConstraintChecker.check_colocation is not implemented.')

    def check_anti_affinity(self, job: Job, placement: Placement, assignments: Mapping[str, Assignment], jobs: Mapping[str, Job]) -> bool:
        """Check different-server edges in either direction for assigned neighbors only.
        Different intervals do not exempt jobs from this server identity restriction."""
        raise NotImplementedError('ConstraintChecker.check_anti_affinity is not implemented.')

    def can_place(self, job: Job, placement: Placement, state: ScheduleState) -> bool:
        """Conjoin all hard checks against prepared state without mutating anything.
        Return false for unknown servers or duplicate assignment of the same job."""
        raise NotImplementedError('ConstraintChecker.can_place is not implemented.')
