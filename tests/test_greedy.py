import pytest

import json
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.models import Server
from cloud_scheduler.schedulers.greedy import GreedyScheduler

def test_earliest_deterministic_input_order(jobs,servers,config):
    """Verify earliest deterministic input order.

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
    solver=GreedyScheduler()
    a=solver.schedule(jobs,servers,config); b=solver.schedule(jobs,servers,config)
    assert a.assignments==b.assignments
    assert [(x.job_id,x.server_id,x.start_minute) for x in a.assignments]==[('a','gpu',0),('b','gpu',0)]
    assert not a.optimality_proven
    assert solver.order_jobs(jobs)==jobs

@pytest.mark.parametrize('name',['simple','greedy_failure','gpu_scarcity','high_demand','time_constraints'])
def test_documented_scenarios(name,repo_root):
    """Verify documented scenarios.

    Args:
        name: Scenario file name, or job identifier where a local fixture requires one.
        repo_root: Absolute repository root, derived from the test location rather than
            the working directory.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    d=json.loads((repo_root/'data'/'scenarios'/f'{name}.json').read_text(encoding="utf-8"))
    cfg=SchedulerConfig(**(d['config'] | {'objectives':tuple(d['config']['objectives'])}))
    r=GreedyScheduler().schedule(d['jobs'],[Server(**s) for s in d['servers']],cfg)
    assert len(r.assignments)==d['expected']['greedy_count']
    if 'greedy_unscheduled' in d['expected']:
        assert {j.job_id for j in r.unscheduled_jobs}==set(d['expected']['greedy_unscheduled'])
    if name=='greedy_failure':
        assert next(a for a in r.assignments if a.job_id=='flex').server_id=='gpu'
    if 'invalid' in d['expected']:
        assert {j.job_id for j in r.invalid_jobs}==set(d['expected']['invalid'])

@pytest.mark.parametrize('empty_cluster',[False,True])
def test_empty_inputs_and_inventory(empty_cluster,jobs,servers,config):
    """Verify empty inputs and inventory.

    Args:
        empty_cluster: Whether to submit valid jobs to an empty inventory instead of
            testing an empty batch.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    solver=GreedyScheduler()
    submitted=jobs if empty_cluster else []
    result=solver.schedule(submitted,[] if empty_cluster else servers,config)
    assert not result.assignments and not result.invalid_jobs
    assert len(result.unscheduled_jobs) == len(submitted)
    assert result.search_nodes == 0 and not result.optimality_proven

def test_earlier_start_beats_preferred_server(jobs,servers,config):
    """Verify earlier start beats preferred server.

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
    from dataclasses import replace
    a=replace(jobs[0],cpu=4,required_server_id='gpu')
    b=replace(jobs[1],cpu=4)
    result=GreedyScheduler().schedule([a,b],servers,config)
    assert [(a.job_id,a.server_id,a.start_minute) for a in result.assignments] == [('a','gpu',0),('b','cpu',0)]

def test_job_waits_until_capacity_is_released(jobs,servers,config):
    """Verify job waits until capacity is released.

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
    from dataclasses import replace
    js=[replace(j,cpu=4,required_server_id='gpu') for j in jobs]
    result=GreedyScheduler().schedule(js,servers,config)
    assert [a.start_minute for a in result.assignments] == [0,15]

def test_malformed_job_does_not_stop_remaining_batch(servers,config):
    """Verify malformed job does not stop remaining batch.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    from cloud_scheduler.models import Job
    result=GreedyScheduler().schedule([{},Job('valid',1,1,15)],servers,config)
    assert len(result.invalid_jobs) == 1 and result.invalid_jobs[0].input_index == 0
    assert len(result.assignments) == 1 and result.assignments[0].input_index == 1
    assert result.assignments[0].job_id == 'valid'
