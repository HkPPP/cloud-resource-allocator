import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

import json
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.models import Server
from cloud_scheduler.schedulers.greedy import GreedyScheduler

@pending
def test_earliest_deterministic_input_order(jobs,servers,config):
    solver=GreedyScheduler()
    a=solver.schedule(jobs,servers,config); b=solver.schedule(jobs,servers,config)
    assert a.assignments==b.assignments
    assert [(x.job_id,x.server_id,x.start_minute) for x in a.assignments]==[('a','gpu',0),('b','gpu',0)]
    assert not a.optimality_proven
    assert solver.order_jobs(jobs)==jobs

@pending
@pytest.mark.parametrize('name',['simple','greedy_failure','gpu_scarcity','high_demand','time_constraints'])
def test_documented_scenarios(name,repo_root):
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
