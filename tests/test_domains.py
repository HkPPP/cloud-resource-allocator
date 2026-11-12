import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import replace
from cloud_scheduler.domains import InitialDomainBuilder
from cloud_scheduler.models import UNASSIGNED, Placement

@pending
def test_hardware_and_pin(jobs,servers,config):
    b=InitialDomainBuilder()
    assert [s.server_id for s in b.get_eligible_servers(replace(jobs[0],gpu=1),servers)]==["gpu"]
    assert [s.server_id for s in b.get_eligible_servers(replace(jobs[0],required_server_id="cpu"),servers)]==["cpu"]

@pending
@pytest.mark.parametrize("slot,expected", [(15,(0,15,30,45)),(5,tuple(range(0,46,5)))])
def test_start_grid(slot,expected,jobs,config):
    assert InitialDomainBuilder().get_valid_start_times(jobs[0],replace(config,slot_minutes=slot))==expected

@pending
def test_horizon_and_omission(jobs,servers,config):
    b=InitialDomainBuilder()
    j=replace(jobs[0],release_minute=60,deadline_minute=90)
    assert b.get_valid_start_times(j,config)==()
    assert b.build_domains([j],servers,config)[j.job_id]==(UNASSIGNED,)

@pending
def test_no_hypothetical_filtering(jobs,servers,config):
    js=[replace(j,same_server_as=(jobs[1-i].job_id,)) for i,j in enumerate(jobs)]
    domains=InitialDomainBuilder().build_domains(js,servers,config)
    assert domains['a']==tuple(Placement(s.server_id,t) for t in (0,15,30,45) for s in servers)+(UNASSIGNED,)

@pending
def test_unary_filter_removes_invalid_placements(jobs,servers,config):
    candidates=(Placement('gpu',0),Placement('gpu',1),Placement('gpu',60),Placement('missing',0))
    assert InitialDomainBuilder().filter_unary_constraints(jobs[0],candidates,servers,config)==(Placement('gpu',0),)
