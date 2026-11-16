"""Small declarative fixtures; no scheduling/reference oracle implementation."""
from pathlib import Path
import pytest
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.models import Assignment, Job, Placement, Server, UNASSIGNED
from cloud_scheduler.preprocessing import PreparedInstance

@pytest.fixture
def config():
    """Create config for isolated behavioral tests.

    Args:
        None.

    Returns:
        SchedulerConfig: Frozen default test configuration.
    """
    return SchedulerConfig(horizon_minutes=60)

@pytest.fixture
def servers():
    """Create servers for isolated behavioral tests.

    Args:
        None.

    Returns:
        tuple[Server, ...]: GPU-capable and CPU-only test inventory, in that order.
    """
    return (Server("gpu", 4, 16, 1, 100), Server("cpu", 4, 16, 0, 100))

@pytest.fixture
def jobs():
    """Create jobs for isolated behavioral tests.

    Args:
        None.

    Returns:
        tuple[Job, ...]: Two valid test jobs with explicit 60-minute deadlines.
    """
    return (Job("a", 2, 4, 15, deadline_minute=60), Job("b", 2, 4, 15, deadline_minute=60))

@pytest.fixture
def prepared(jobs, servers, config):
    """Provide immutable prepared input with explicitly declared candidate domains.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        PreparedInstance: Immutable fixture with original record indices and explicit
            domains.
    """
    return PreparedInstance(jobs, servers, config, (), (("a",0),("b",1)), 2,
        tuple((j.job_id, tuple(Placement(s.server_id,t) for t in (0,15,30,45) for s in servers)+(UNASSIGNED,)) for j in jobs))

@pytest.fixture
def repo_root():
    """Create repo root for isolated behavioral tests.

    Args:
        None.

    Returns:
        Path: Absolute root of the checked-out repository.
    """
    return Path(__file__).resolve().parents[1]

@pytest.fixture
def state_factory(servers, config):
    """Create state factory for isolated behavioral tests.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        Callable: Factory accepting jobs and optional inventory/settings to create an
            independent ScheduleState.
    """
    def create(job_list, *, inventory=None, settings=None):
        """Construct empty state from explicit jobs without invoking domain generation.

        Args:
            job_list: Validated job definitions to include in a manually prepared state
                fixture.
            inventory: Explicit server inventory used to check validation or override
                the default fixture.
            settings: Optional configuration override; None uses the default
                configuration fixture.

        Returns:
            ScheduleState: Fresh empty state for the supplied immutable preparation.
                Domains are unused in state-only tests.
        """
        selected_servers = tuple(servers if inventory is None else inventory)
        selected_config = config if settings is None else settings
        prepared = PreparedInstance(
            jobs=tuple(job_list), servers=selected_servers, config=selected_config,
            invalid_jobs=(),
            input_indices=tuple((job.job_id, index) for index, job in enumerate(job_list)),
            submitted_count=len(job_list), domains=(),
        )
        from cloud_scheduler.state import ScheduleState
        return ScheduleState(prepared)
    return create
