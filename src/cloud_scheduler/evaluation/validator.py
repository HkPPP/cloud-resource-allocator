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

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.
            servers: Server inventory in original input order; an empty inventory is
                permitted.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            ValidationReport: Combined structural errors and hard-constraint violations.
                valid is True exactly when both collections are empty.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Independent schedule validation is not implemented.')

    def validate_assignments(self, result: ScheduleResult, jobs: Sequence[RawJob], servers: Sequence[Server]) -> tuple[str, ...]:
        """Find unknown IDs, duplicate assignments, mismatched input indices and
        wrong end-start durations; no assignment may refer to an invalid job.
        Return structural errors with record context; do not mutate result.

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.
            servers: Server inventory in original input order; an empty inventory is
                permitted.

        Returns:
            tuple[str, ...]: Contextual structural assignment errors; empty when IDs,
                indices, uniqueness and durations are correct.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Assignment integrity is not implemented.')

    def validate_resource_usage(self, result: ScheduleResult, jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> tuple[str, ...]:
        """Reconstruct each resource independently from assignment intervals.
        Sweep events or fresh arrays; release before acquire at equal endpoints.
        Return every cumulative overflow with server/time/resource context.

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.
            servers: Server inventory in original input order; an empty inventory is
                permitted.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            tuple[str, ...]: Independently reconstructed capacity violations with
                server, time and resource context; empty when every cumulative sum fits.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Independent resource reconstruction is not implemented.')

    def validate_time_constraints(self, result: ScheduleResult, jobs: Sequence[RawJob], config: SchedulerConfig) -> tuple[str, ...]:
        """Check integer aligned starts/ends, duration, release/deadline and horizon.
        Interpret default deadlines from config and half-open intervals exactly.

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            tuple[str, ...]: Violations of integer alignment, duration, release,
                deadline or horizon bounds; empty when all intervals are valid.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Independent time validation is not implemented.')

    def validate_placement_constraints(self, result: ScheduleResult, jobs: Sequence[RawJob]) -> tuple[str, ...]:
        """Check pins and both directions of direct same/different-server edges.
        Check pairs only when both jobs are assigned, without transitive closure.

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.

        Returns:
            tuple[str, ...]: Pinning or conditional direct relationship violations;
                empty when every scheduled pair satisfies its hard constraints.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Independent placement validation is not implemented.')

    def validate_status_accounting(self, result: ScheduleResult, jobs: Sequence[RawJob]) -> tuple[str, ...]:
        """Require exactly one classification for each original zero-based index.
        Detect missing/out-of-range/repeated indices, identity mismatches, duplicate
        IDs classified as valid, and invalid entries lacking structured errors.

        Args:
            result: Final ScheduleResult containing indexed classifications, assignments
                and performance fields. Validation methods treat it as untrusted output.
            jobs: Original submissions in input order, including raw malformed records.
                Per-record identity is the zero-based position in this sequence.

        Returns:
            tuple[str, ...]: Missing, repeated, out-of-range or mismatched original
                submission identities and malformed classifications; empty when each
                record appears exactly once.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Per-submission accounting is not implemented.')
