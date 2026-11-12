"""Small declarative fixtures; no scheduling/reference oracle implementation."""
from pathlib import Path
import pytest
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.models import Assignment, Job, Placement, Server, UNASSIGNED
from cloud_scheduler.preprocessing import PreparedInstance

@pytest.fixture
def config():
    return SchedulerConfig(horizon_minutes=60)

@pytest.fixture
def servers():
    return (Server("gpu", 4, 16, 1, 100), Server("cpu", 4, 16, 0, 100))

@pytest.fixture
def jobs():
    return (Job("a", 2, 4, 15, deadline_minute=60), Job("b", 2, 4, 15, deadline_minute=60))

@pytest.fixture
def prepared(jobs, servers, config):
    return PreparedInstance(jobs, servers, config, (), (("a",0),("b",1)), 2,
        tuple((j.job_id, tuple(Placement(s.server_id,t) for t in (0,15,30,45) for s in servers)+(UNASSIGNED,)) for j in jobs))

@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parents[1]
