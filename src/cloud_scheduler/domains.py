"""Unary domain interfaces, independent of hypothetical assignments."""
from typing import Sequence
from .config import SchedulerConfig
from .models import DomainValue, Job, Placement, Server

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
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('InitialDomainBuilder.build_domains is not implemented.')

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

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('InitialDomainBuilder.get_eligible_servers is not implemented.')

    def get_valid_start_times(self, job: Job, config: SchedulerConfig) -> tuple[int, ...]:
        """Return slot-aligned starts from release through min(deadline,horizon)-duration
        inclusively. Return empty when the horizon excludes the entire window.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            config: Scheduling settings defining the integer-minute horizon, slot
                resolution and solver options.

        Returns:
            tuple[int, ...]: Ascending slot-aligned starts from release through
                min(deadline, horizon) - duration, inclusive; empty if that range is
                empty.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('InitialDomainBuilder.get_valid_start_times is not implemented.')

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

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('InitialDomainBuilder.filter_unary_constraints is not implemented.')
