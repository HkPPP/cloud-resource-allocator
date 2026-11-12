import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

import json
from dataclasses import replace
from cloud_scheduler.config import SchedulerConfig
from cloud_scheduler.models import Job, Placement, Server, UNASSIGNED
from cloud_scheduler.preprocessing import preprocess_inputs
from cloud_scheduler.schedulers.csp import CSPScheduler
from cloud_scheduler.evaluation.validator import ScheduleValidator
from cloud_scheduler.state import ScheduleState

@pending
@pytest.mark.parametrize('name',['simple','greedy_failure','gpu_scarcity','high_demand','time_constraints'])
@pytest.mark.parametrize('mrv,fc',[(False,False),(False,True),(True,True)])
def test_small_optimal_scenarios(name,mrv,fc,repo_root):
    d=json.loads((repo_root/'data'/'scenarios'/f'{name}.json').read_text(encoding="utf-8"))
    cfg=SchedulerConfig(**(d['config']|{'objectives':tuple(d['config']['objectives'])}))
    cfg=replace(cfg,use_mrv=mrv,use_forward_checking=fc)
    ss=[Server(**s) for s in d['servers']]
    r=CSPScheduler().schedule(d['jobs'],ss,cfg)
    assert len(r.assignments)==d['expected']['csp_max_count']
    assert r.optimality_proven and not r.timed_out
    assert ScheduleValidator().validate_schedule(r,d['jobs'],ss,cfg).valid
    if name=='greedy_failure':
        assert next(a for a in r.assignments if a.job_id=='flex').server_id!='gpu'
        assert sum(a.start_minute-next(j['release_minute'] for j in d['jobs'] if j['job_id']==a.job_id) for a in r.assignments)==0

@pending
def test_only_unassigned_is_feasible(jobs,servers,config):
    r=CSPScheduler().schedule([replace(jobs[0],gpu=99)],servers,config)
    assert not r.assignments and len(r.unscheduled_jobs)==1
    assert not r.invalid_jobs and r.optimality_proven

@pending
def test_mrv_counts_real_placements(prepared,jobs):
    domains={'a':(Placement('gpu',0),Placement('cpu',0),UNASSIGNED),'b':(UNASSIGNED,)}
    assert CSPScheduler().select_next_job(jobs,domains,ScheduleState(prepared),True).job_id=='b'

@pending
def test_forward_check_retains_omission(prepared,jobs):
    prepared=replace(prepared,jobs=(replace(jobs[0],cpu=4),jobs[1]))
    state=ScheduleState(prepared); state.place(prepared.jobs[0],Placement('gpu',0))
    domains={'b':(Placement('gpu',0),Placement('cpu',0),UNASSIGNED)}
    filtered=CSPScheduler().forward_check([jobs[1]],domains,state)
    assert filtered['b']==(Placement('cpu',0),UNASSIGNED)
    assert Placement('gpu',0) in domains['b']

@pending
def test_restore_state(prepared,jobs):
    state=ScheduleState(prepared); snapshot=state.copy()
    domains=dict(prepared.domains)
    state.place(jobs[0],Placement('gpu',0))
    restored,restored_domains=CSPScheduler().restore_state(snapshot,domains)
    assert not restored.get_assignments()
    assert restored_domains==domains

@pending
def test_timeout_returns_valid_incumbent(servers,config):
    cfg=replace(config,search_timeout_seconds=1e-12)
    js=[Job(str(i),1,1,15,deadline_minute=60) for i in range(50)]
    r=CSPScheduler().schedule(js,servers,cfg)
    assert r.timed_out and not r.optimality_proven
    assert ScheduleValidator().validate_schedule(r,js,servers,cfg).valid
    assert len(r.assignments)+len(r.unscheduled_jobs)==50

@pending
@pytest.mark.parametrize("objectives,count",[(('max_jobs','min_wait'),2),(('min_wait','max_jobs'),1)])
def test_solver_respects_objective_priority(objectives,count,config):
    cfg=replace(config,horizon_minutes=30,objectives=objectives)
    js=[Job('a',1,1,15,deadline_minute=30),Job('b',1,1,15,deadline_minute=30)]
    result=CSPScheduler().schedule(js,[Server('s',1,2)],cfg)
    assert len(result.assignments)==count
    expected_wait=15 if count==2 else 0
    assert sum(a.start_minute for a in result.assignments)==expected_wait
    assert result.optimality_proven
