import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from cloud_scheduler.models import Assignment, Job
from cloud_scheduler.objectives import *

@pending
@pytest.mark.parametrize('objectives,expected',[(('max_jobs','min_wait'),1),(('min_wait','max_jobs'),-1)])
def test_priority(objectives,expected):
    """Verify priority.

    Args:
        objectives: Ordered objective names defining the optimization priority in this
            case.
        expected: Expected return value for the parameterized behavior or boundary case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    jobs={j.job_id:j for j in (Job('a',1,1,15),Job('b',1,1,15))}
    more=(Assignment('a','s',15,30,0),Assignment('b','s',15,30,1))
    fewer=(Assignment('a','s',0,15,0),)
    assert compare_schedules(more,fewer,jobs,objectives)==expected

@pending
def test_equal_count_lower_wait_wins(jobs):
    """Verify equal count lower wait wins.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    mapping={j.job_id:j for j in jobs}
    early=(Assignment('a','s',0,15,0),); late=(Assignment('a','s',15,30,0),)
    assert compare_schedules(early,late,mapping,('max_jobs','min_wait'))==1
    assert compare_schedules(early,early,mapping,('max_jobs','min_wait'))==0

@pending
def test_active_servers_and_empty(jobs):
    """Verify active servers and empty.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    mapping={j.job_id:j for j in jobs}
    one=(Assignment('a','s',0,15,0),Assignment('b','s',0,15,1))
    two=(one[0],Assignment('b','t',0,15,1))
    assert compare_schedules(one,two,mapping,('max_jobs','min_active_servers'))==1
    assert MaxJobs().evaluate(one,mapping)==2
    assert MinWait().evaluate(one,mapping)==0
    assert MinActiveServers().evaluate(one,mapping)==1
    assert compare_schedules((),one,mapping,('min_active_servers','max_jobs'))==1

@pending
@pytest.mark.parametrize('order',[(),('unknown',),('max_jobs','max_jobs')])
def test_invalid_objective_order_rejected(order):
    """Verify invalid objective order rejected.

    Args:
        order: Objective-name sequence used to test valid comparison or invalid
            ordering.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError): compare_schedules((),(),{},order)

@pending
@pytest.mark.parametrize('objective',[MaxJobs,MinWait,MinActiveServers])
def test_empty_objective_values(objective):
    """Verify empty objective values.

    Args:
        objective: Objective class whose empty-schedule evaluation is tested.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert objective().evaluate((),{}) == 0

@pending
def test_wait_uses_release_and_omits_unscheduled_jobs():
    """Verify wait uses release and omits unscheduled jobs.

    Args:
        None.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    jobs={'a':Job('a',1,1,15,release_minute=15,deadline_minute=60),
          'b':Job('b',1,1,15,deadline_minute=60)}
    assert MinWait().evaluate((Assignment('a','s',30,45,0),),jobs) == 15

@pending
def test_comparison_reverses_sign_and_ignores_assignment_order(jobs):
    """Verify comparison reverses sign and ignores assignment order.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    mapping={j.job_id:j for j in jobs}
    early=(Assignment('a','s',0,15,0),Assignment('b','s',0,15,1))
    late=(Assignment('a','s',15,30,0),Assignment('b','s',15,30,1))
    order=('max_jobs','min_wait')
    assert compare_schedules(early,late,mapping,order) == 1
    assert compare_schedules(late,early,mapping,order) == -1
    assert compare_schedules(early,tuple(reversed(early)),mapping,order) == 0
