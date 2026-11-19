import pytest

from dataclasses import replace
from cloud_scheduler.models import Job, Server
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.preprocessing import *

def test_valid_defaults(servers,config):
    """Verify valid defaults.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=preprocess_inputs([{"job_id":"a","cpu":1,"ram_gb":1,"duration_minutes":15}],servers,config)
    assert p.invalid_jobs==()
    assert p.jobs[0].deadline_minute==60
    assert p.input_indices==(("a",0),)

@pytest.mark.parametrize("changes,code", [({"cpu":-1},"INVALID_RESOURCE"),({"duration_minutes":0},"INVALID_DURATION"),({"duration_minutes":75},"INVALID_TIME"),({"release_minute":1},"MISALIGNED_TIME"),({"duration_minutes":16},"MISALIGNED_TIME"),({"deadline_minute":59},"MISALIGNED_TIME"),({"cpu":True},"INVALID_RESOURCE"),({"ram_gb":float('nan')},"INVALID_RESOURCE"),({"storage_gb":float('inf')},"INVALID_RESOURCE")])
def test_invalid_fields(changes,code,jobs,config):
    """Verify invalid fields.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        code: Structured error code expected for this invalid submission.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    valid,invalid=validate_jobs([replace(jobs[0],**changes)],config)
    assert valid==()
    assert invalid[0].input_index==0
    assert code in invalid[0].error_codes
    assert invalid[0].reasons

def test_missing_and_duplicate_id_accounting(servers,config):
    """Verify missing and duplicate id accounting.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=preprocess_inputs([{},Job("x",1,1,15),Job("x",1,1,15)],servers,config)
    assert not p.jobs
    assert {i.input_index for i in p.invalid_jobs}=={0,1,2}
    assert p.invalid_jobs[0].job_id is None
    assert all("DUPLICATE_ID" in i.error_codes for i in p.invalid_jobs[1:])

@pytest.mark.parametrize("changes", [{"required_server_id":"missing"},{"same_server_as":("unknown",)},{"different_server_from":("a",)}])
def test_bad_references(changes,jobs,servers,config):
    """Verify bad references.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=preprocess_inputs([replace(jobs[0],**changes)],servers,config)
    assert len(p.invalid_jobs)==1 and not p.jobs

def test_direct_contradiction(jobs,servers,config):
    """Verify direct contradiction.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    a=replace(jobs[0],same_server_as=("b",),different_server_from=("b",))
    p=preprocess_inputs([a,jobs[1]],servers,config)
    assert {i.job_id for i in p.invalid_jobs}=={"a","b"}

def test_unavailable_gpu_is_valid(jobs,servers,config):
    """Verify unavailable gpu is valid.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=preprocess_inputs([replace(jobs[0],gpu=4)],servers,config)
    assert len(p.jobs)==1 and not p.invalid_jobs

def test_invalid_target_does_not_cascade(jobs,servers,config):
    """Verify invalid target does not cascade.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    p=preprocess_inputs([replace(jobs[0],same_server_as=("b",)),replace(jobs[1],cpu=-1)],servers,config)
    assert [j.job_id for j in p.jobs]==["a"]
    assert p.jobs[0].same_server_as==()

@pytest.mark.parametrize("changes", [{"objectives":("unsupported",)},{"objectives":("max_jobs","max_jobs")},{"objectives":()},{"slot_minutes":0},{"slot_minutes":7},{"slot_minutes":True},{"horizon_minutes":0},{"search_timeout_seconds":-1},{"search_timeout_seconds":float('inf')}])
def test_bad_config(changes,config):
    """Verify bad config.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError):
        validate_config(replace(config,**changes))

@pytest.mark.parametrize("inventory", [(Server("x",-1,1),),(Server("x",1,1),Server("x",2,2))])
def test_bad_servers(inventory):
    """Verify bad servers.

    Args:
        inventory: Explicit server inventory used to check validation or override the
            default fixture.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError):
        validate_servers(inventory)

def test_valid_config_and_empty_inventory(config):
    """Verify valid config and empty inventory.

    Args:
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert config.validate() is None
    assert validate_servers([])==()

def test_contrary_pins_remain_valid(jobs,servers,config):
    """Verify contrary pins remain valid.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    js=[replace(jobs[0],required_server_id='gpu',same_server_as=('b',)),replace(jobs[1],required_server_id='cpu')]
    prepared=preprocess_inputs(js,servers,config)
    assert not prepared.invalid_jobs and len(prepared.jobs)==2
    assert prepared.jobs[1].same_server_as==('a',)

@pytest.mark.parametrize('raw',[None,42,True,'job',[],{'cpu':1,'ram_gb':1,'duration_minutes':15}])
def test_malformed_records_keep_original_identity(raw,config):
    """Verify malformed records keep original identity.

    Args:
        raw: Raw submission element, possibly malformed or missing its job ID.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    valid,invalid=validate_jobs([raw],config)
    assert not valid and len(invalid) == 1
    assert invalid[0].input_index == 0 and invalid[0].job_id is None
    assert invalid[0].error_codes and len(invalid[0].error_codes) == len(invalid[0].reasons)

@pytest.mark.parametrize('field',['cpu','ram_gb','gpu','storage_gb'])
@pytest.mark.parametrize('value',[-1,True,float('nan'),float('inf')])
def test_all_resource_fields_reject_invalid_quantities(field,value,jobs,config):
    """Verify all resource fields reject invalid quantities.

    Args:
        field: Resource field whose capacity, type or numerical boundary is being
            tested.
        value: Resource quantity or JSON value chosen for this parameterized type or
            boundary case.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    valid,invalid=validate_jobs([replace(jobs[0],**{field:value})],config)
    assert not valid and 'INVALID_RESOURCE' in invalid[0].error_codes

@pytest.mark.parametrize('field',['cpu','gpu'])
def test_discrete_resources_reject_fractional_values(field,jobs,config):
    """Verify discrete resources reject fractional values.

    Args:
        field: Resource field whose capacity, type or numerical boundary is being
            tested.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    valid,invalid=validate_jobs([replace(jobs[0],**{field:0.5})],config)
    assert not valid and 'INVALID_RESOURCE' in invalid[0].error_codes

@pytest.mark.parametrize('changes',[{'release_minute':-15},{'duration_minutes':True},{'release_minute':0.5},{'deadline_minute':True},{'deadline_minute':0}])
def test_malformed_times_are_invalid(changes,jobs,config):
    """Verify malformed times are invalid.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    valid,invalid=validate_jobs([replace(jobs[0],**changes)],config)
    assert not valid and invalid[0].error_codes

@pytest.mark.parametrize('changes',[{'horizon_minutes':True},{'slot_minutes':1.5},{'objectives':'max_jobs'},{'search_timeout_seconds':0},{'search_timeout_seconds':True},{'use_mrv':1},{'use_mac':True,'use_backjumping':True}])
def test_config_type_and_combination_errors(changes,config):
    """Verify config type and combination errors.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError): replace(config,**changes).validate()

def test_preprocessing_preserves_callers_and_valid_order(servers,config):
    """Verify preprocessing preserves callers and valid order.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    import copy
    raw=[{'job_id':'second','cpu':1,'ram_gb':1,'duration_minutes':15}, {},
         {'job_id':'first','cpu':1,'ram_gb':1,'duration_minutes':15}]
    before=copy.deepcopy(raw)
    p=preprocess_inputs(raw,servers,config)
    assert raw == before
    assert tuple(j.job_id for j in p.jobs) == ('second','first')
    assert p.input_indices == (('second',0),('first',2))
    assert p.invalid_jobs[0].input_index == 1 and p.submitted_count == 3

def test_self_colocation_removed_and_duplicate_edges_normalized(jobs,servers,config):
    """Verify self colocation removed and duplicate edges normalized.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    a=replace(jobs[0],same_server_as=('a','b','b'))
    p=preprocess_inputs([a,jobs[1]],servers,config)
    assert not p.invalid_jobs
    assert p.jobs[0].same_server_as == ('b',)
    assert p.jobs[1].same_server_as == ('a',)
