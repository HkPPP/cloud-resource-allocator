"""Independent validation; must never consult ScheduleState or its resource arrays."""
from dataclasses import dataclass
from typing import Sequence
from ..config import SchedulerConfig
from ..models import RawJob, ScheduleResult, Server

@dataclass(frozen=True)
class ValidationReport:
    """valid iff both collections are empty.

    errors contain structural/status/identity errors; constraint_violations contain
    time, capacity, pinning and relationship violations, with job/server context.
    """
    valid: bool
    errors: tuple[str, ...] = ()
    constraint_violations: tuple[str, ...] = ()

class ScheduleValidator:
    """Rebuild usage from final assignments, independently of scheduler state."""

    def validate_schedule(self, result: ScheduleResult, jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> ValidationReport:
        """Combine all checks, collecting errors rather than failing at first issue.

        Independently inspect raw submissions and indexed classification. Never
        trust claimed INVALID status to excuse a valid job or misreported errors.
        Invalid global inventory/config raises ValueError; malformed output becomes
        a report. Resource reconstruction must not use the scheduler's tracker.
        """
        raise NotImplementedError('Independent schedule validation is not implemented.')

    def validate_assignments(self, result: ScheduleResult, jobs: Sequence[RawJob], servers: Sequence[Server]) -> tuple[str, ...]:
        """Find unknown IDs, duplicate assignments, mismatched input indices and
        wrong end-start durations; no assignment may refer to an invalid job.
        Return structural errors with record context; do not mutate result.
        """
        raise NotImplementedError('Assignment integrity is not implemented.')

    def validate_resource_usage(self, result: ScheduleResult, jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> tuple[str, ...]:
        """Reconstruct each resource independently from assignment intervals.
        Sweep events or fresh arrays; release before acquire at equal endpoints.
        Return every cumulative overflow with server/time/resource context.
        """
        raise NotImplementedError('Independent resource reconstruction is not implemented.')

    def validate_time_constraints(self, result: ScheduleResult, jobs: Sequence[RawJob], config: SchedulerConfig) -> tuple[str, ...]:
        """Check integer aligned starts/ends, duration, release/deadline and horizon.
        Interpret default deadlines from config and half-open intervals exactly.
        """
        raise NotImplementedError('Independent time validation is not implemented.')

    def validate_placement_constraints(self, result: ScheduleResult, jobs: Sequence[RawJob]) -> tuple[str, ...]:
        """Check pins and both directions of direct same/different-server edges.
        Check pairs only when both jobs are assigned, without transitive closure.
        """
        raise NotImplementedError('Independent placement validation is not implemented.')

    def validate_status_accounting(self, result: ScheduleResult, jobs: Sequence[RawJob]) -> tuple[str, ...]:
        """Require exactly one classification for each original zero-based index.
        Detect missing/out-of-range/repeated indices, identity mismatches, duplicate
        IDs classified as valid, and invalid entries lacking structured errors.
        """
        raise NotImplementedError('Per-submission accounting is not implemented.')
