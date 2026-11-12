import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import FrozenInstanceError
from cloud_scheduler.models import *
from cloud_scheduler.config import SchedulerConfig

def test_declarative_defaults_and_immutability():
    j=Job("j",1,2,15)
    assert (j.gpu,j.storage_gb,j.release_minute,j.deadline_minute)==(0,0,0,None)
    assert j.same_server_as==()
    with pytest.raises(FrozenInstanceError):
        j.cpu=9
    assert {s.value for s in JobStatus}=={"SCHEDULED","INVALID","UNSCHEDULED"}
    assert SchedulerConfig().objectives==("max_jobs","min_wait")
    assert UNASSIGNED is not None

@pending
def test_resource_arithmetic():
    a,b=ResourceVector(2,4,1,10),ResourceVector(1,2,0,5)
    assert a+b==ResourceVector(3,6,1,15)
    assert a-b==ResourceVector(1,2,1,5)
    assert b-a==ResourceVector(-1,-2,-1,-5)

@pending
@pytest.mark.parametrize("demand, expected", [(ResourceVector(4,16,1,100),True),(ResourceVector(5,1),False),(ResourceVector(1,17),False),(ResourceVector(1,1,2),False),(ResourceVector(1,1,0,101),False)])
def test_capacity_comparison(demand,expected):
    assert demand.fits_within(ResourceVector(4,16,1,100)) is expected

@pending
def test_job_and_server_helpers(jobs,servers):
    assert servers[0].capacity()==ResourceVector(4,16,1,100)
    assert servers[0].supports(jobs[0])
    assert jobs[0].resource_requirements()==ResourceVector(2,4)
    assert jobs[0].latest_start()==45
    assert jobs[0].execution_interval(15)==(15,30)

@pending
def test_unresolved_deadline():
    with pytest.raises(ValueError):
        Job("x",1,1,15).latest_start()
