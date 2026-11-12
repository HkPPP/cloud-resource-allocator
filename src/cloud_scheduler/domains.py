"""Unary domain interfaces, independent of hypothetical assignments."""
from typing import Sequence
from .config import SchedulerConfig
from .models import DomainValue, Job, Placement, Server

class InitialDomainBuilder:
    """Generate immutable initial candidates and include UNASSIGNED even for empty real domains."""

    def build_domains(self, jobs: Sequence[Job], servers: Sequence[Server], config: SchedulerConfig) -> dict[str, tuple[DomainValue, ...]]:
        """Return a domain per valid ID, sorted by start then original server order.
        Include exactly one UNASSIGNED last; zero servers still gives that singleton.
        Only unary filtering applies; related jobs may eventually be omitted."""
        raise NotImplementedError('InitialDomainBuilder.build_domains is not implemented.')

    def get_eligible_servers(self, job: Job, servers: Sequence[Server]) -> tuple[Server, ...]:
        """Return individually capable servers satisfying pinning in original order.
        An empty result denotes a valid unschedulable request, not INVALID."""
        raise NotImplementedError('InitialDomainBuilder.get_eligible_servers is not implemented.')

    def get_valid_start_times(self, job: Job, config: SchedulerConfig) -> tuple[int, ...]:
        """Return slot-aligned starts from release through min(deadline,horizon)-duration
        inclusively. Return empty when the horizon excludes the entire window."""
        raise NotImplementedError('InitialDomainBuilder.get_valid_start_times is not implemented.')

    def filter_unary_constraints(self, job: Job, placements: Sequence[Placement], servers: Sequence[Server], config: SchedulerConfig) -> tuple[Placement, ...]:
        """Return placements satisfying hardware, pins, grid, window and horizon.
        Preserve order and never inspect hypothetical assignments of other jobs."""
        raise NotImplementedError('InitialDomainBuilder.filter_unary_constraints is not implemented.')
