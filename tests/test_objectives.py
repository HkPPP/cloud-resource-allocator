import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from cloud_scheduler.models import Assignment, Job
from cloud_scheduler.objectives import *

@pending
@pytest.mark.parametrize('objectives,expected',[(('max_jobs','min_wait'),1),(('min_wait','max_jobs'),-1)])
def test_priority(objectives,expected):
    jobs={j.job_id:j for j in (Job('a',1,1,15),Job('b',1,1,15))}
    more=(Assignment('a','s',15,30,0),Assignment('b','s',15,30,1))
    fewer=(Assignment('a','s',0,15,0),)
    assert compare_schedules(more,fewer,jobs,objectives)==expected

@pending
def test_equal_count_lower_wait_wins(jobs):
    mapping={j.job_id:j for j in jobs}
    early=(Assignment('a','s',0,15,0),); late=(Assignment('a','s',15,30,0),)
    assert compare_schedules(early,late,mapping,('max_jobs','min_wait'))==1
    assert compare_schedules(early,early,mapping,('max_jobs','min_wait'))==0

@pending
def test_active_servers_and_empty(jobs):
    mapping={j.job_id:j for j in jobs}
    one=(Assignment('a','s',0,15,0),Assignment('b','s',0,15,1))
    two=(one[0],Assignment('b','t',0,15,1))
    assert compare_schedules(one,two,mapping,('max_jobs','min_active_servers'))==1
    assert MaxJobs().evaluate(one,mapping)==2
    assert MinWait().evaluate(one,mapping)==0
    assert MinActiveServers().evaluate(one,mapping)==1
    assert compare_schedules((),one,mapping,('min_active_servers','max_jobs'))==1
