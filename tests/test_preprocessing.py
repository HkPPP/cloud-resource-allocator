import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import replace
from cloud_scheduler.models import Job, Server
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.preprocessing import *

@pending
def test_valid_defaults(servers,config):
    p=preprocess_inputs([{"job_id":"a","cpu":1,"ram_gb":1,"duration_minutes":15}],servers,config)
    assert p.invalid_jobs==()
    assert p.jobs[0].deadline_minute==60
    assert p.input_indices==(("a",0),)

@pending
@pytest.mark.parametrize("changes,code", [({"cpu":-1},"INVALID_RESOURCE"),({"duration_minutes":0},"INVALID_DURATION"),({"duration_minutes":75},"INVALID_TIME"),({"release_minute":1},"MISALIGNED_TIME"),({"duration_minutes":16},"MISALIGNED_TIME"),({"deadline_minute":59},"MISALIGNED_TIME"),({"cpu":True},"INVALID_RESOURCE"),({"ram_gb":float('nan')},"INVALID_RESOURCE"),({"storage_gb":float('inf')},"INVALID_RESOURCE")])
def test_invalid_fields(changes,code,jobs,config):
    valid,invalid=validate_jobs([replace(jobs[0],**changes)],config)
    assert valid==()
    assert invalid[0].input_index==0
    assert code in invalid[0].error_codes
    assert invalid[0].reasons

@pending
def test_missing_and_duplicate_id_accounting(servers,config):
    p=preprocess_inputs([{},Job("x",1,1,15),Job("x",1,1,15)],servers,config)
    assert not p.jobs
    assert {i.input_index for i in p.invalid_jobs}=={0,1,2}
    assert p.invalid_jobs[0].job_id is None
    assert all("DUPLICATE_ID" in i.error_codes for i in p.invalid_jobs[1:])

@pending
@pytest.mark.parametrize("changes", [{"required_server_id":"missing"},{"same_server_as":("unknown",)},{"different_server_from":("a",)}])
def test_bad_references(changes,jobs,servers,config):
    p=preprocess_inputs([replace(jobs[0],**changes)],servers,config)
    assert len(p.invalid_jobs)==1 and not p.jobs

@pending
def test_direct_contradiction(jobs,servers,config):
    a=replace(jobs[0],same_server_as=("b",),different_server_from=("b",))
    p=preprocess_inputs([a,jobs[1]],servers,config)
    assert {i.job_id for i in p.invalid_jobs}=={"a","b"}

@pending
def test_unavailable_gpu_is_valid(jobs,servers,config):
    p=preprocess_inputs([replace(jobs[0],gpu=4)],servers,config)
    assert len(p.jobs)==1 and not p.invalid_jobs

@pending
def test_invalid_target_does_not_cascade(jobs,servers,config):
    p=preprocess_inputs([replace(jobs[0],same_server_as=("b",)),replace(jobs[1],cpu=-1)],servers,config)
    assert [j.job_id for j in p.jobs]==["a"]
    assert p.jobs[0].same_server_as==()

@pending
@pytest.mark.parametrize("changes", [{"objectives":("unsupported",)},{"objectives":("max_jobs","max_jobs")},{"objectives":()},{"slot_minutes":0},{"slot_minutes":7},{"slot_minutes":True},{"horizon_minutes":0},{"search_timeout_seconds":-1},{"search_timeout_seconds":float('inf')}])
def test_bad_config(changes,config):
    with pytest.raises(ValueError):
        validate_config(replace(config,**changes))

@pending
@pytest.mark.parametrize("inventory", [(Server("x",-1,1),),(Server("x",1,1),Server("x",2,2))])
def test_bad_servers(inventory):
    with pytest.raises(ValueError):
        validate_servers(inventory)

@pending
def test_valid_config_and_empty_inventory(config):
    assert config.validate() is None
    assert validate_servers([])==()

@pending
def test_contrary_pins_remain_valid(jobs,servers,config):
    js=[replace(jobs[0],required_server_id='gpu',same_server_as=('b',)),replace(jobs[1],required_server_id='cpu')]
    prepared=preprocess_inputs(js,servers,config)
    assert not prepared.invalid_jobs and len(prepared.jobs)==2
    assert prepared.jobs[1].same_server_as==('a',)
