import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import replace
from cloud_scheduler.constraints import ConstraintChecker
from cloud_scheduler.models import Assignment, Job, Placement
from cloud_scheduler.state import ScheduleState

@pending
@pytest.mark.parametrize("changes",[{"cpu":3},{"ram_gb":13},{"gpu":1},{"storage_gb":91}])
def test_cumulative_resource_overflow(changes,prepared,jobs):
    prepared=replace(prepared,jobs=(replace(jobs[0],gpu=1,storage_gb=10),replace(jobs[1],**changes)))
    state=ScheduleState(prepared)
    state.place(prepared.jobs[0],Placement("gpu",0))
    assert not ConstraintChecker().check_resource_capacity(replace(jobs[1],**changes),Placement('gpu',0),state)

@pending
@pytest.mark.parametrize("start,expected",[(0,True),(45,True),(60,False),(-15,False),(1,False)])
def test_time_window(start,expected,jobs,config):
    assert ConstraintChecker().check_time_window(jobs[0],Placement('gpu',start),config) is expected

@pending
def test_pin(jobs):
    c=ConstraintChecker(); j=replace(jobs[0],required_server_id='cpu')
    assert c.check_server_pinning(j,Placement('cpu',0))
    assert not c.check_server_pinning(j,Placement('gpu',0))

@pending
@pytest.mark.parametrize("relation,method,same_ok",[("same_server_as","check_colocation",True),("different_server_from","check_anti_affinity",False)])
@pytest.mark.parametrize("declarer",[0,1])
def test_relationship_both_directions(relation,method,same_ok,declarer,jobs):
    js=list(jobs); js[declarer]=replace(js[declarer],**{relation:(js[1-declarer].job_id,)})
    check=getattr(ConstraintChecker(),method)
    mapping={j.job_id:j for j in js}
    assert check(js[1],Placement('gpu',15),{},mapping)
    assigned={'a':Assignment('a','gpu',0,15,0)}
    assert check(js[1],Placement('gpu',15),assigned,mapping) is same_ok
    assert check(js[1],Placement('cpu',15),assigned,mapping) is (not same_ok)

@pending
def test_concurrent_and_touching(prepared,jobs):
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',0))
    assert state.can_place(jobs[1],Placement('gpu',0))
    assert state.can_place(replace(jobs[1],cpu=4),Placement('gpu',15))
    assert not state.can_place(replace(jobs[1],cpu=4),Placement('gpu',0))

@pending
def test_skipped_middle_does_not_imply_transitive_colocation():
    a=Job('a',1,1,15,same_server_as=('b',),different_server_from=('c',))
    b=Job('b',1,1,15,same_server_as=('a','c'))
    c=Job('c',1,1,15,same_server_as=('b',),different_server_from=('a',))
    check=ConstraintChecker(); mapping={j.job_id:j for j in (a,b,c)}
    assigned={'a':Assignment('a','gpu',0,15,0)}
    assert check.check_colocation(c,Placement('cpu',0),assigned,mapping)
    assert check.check_anti_affinity(c,Placement('cpu',0),assigned,mapping)
