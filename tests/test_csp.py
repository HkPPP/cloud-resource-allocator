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
    """Verify small optimal scenarios.

    Args:
        name: Scenario file name, or job identifier where a local fixture requires one.
        mrv: Whether minimum-remaining-values selection is enabled for this solver
            configuration.
        fc: Whether forward checking is enabled for this solver configuration.
        repo_root: Absolute repository root, derived from the test location rather than
            the working directory.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
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
    """Verify only unassigned is feasible.

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
    r=CSPScheduler().schedule([replace(jobs[0],gpu=99)],servers,config)
    assert not r.assignments and len(r.unscheduled_jobs)==1
    assert not r.invalid_jobs and r.optimality_proven

@pending
def test_mrv_counts_real_placements(prepared,jobs):
    """Verify mrv counts real placements.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    domains={'a':(Placement('gpu',0),Placement('cpu',0),UNASSIGNED),'b':(UNASSIGNED,)}
    assert CSPScheduler().select_next_job(jobs,domains,ScheduleState(prepared),True).job_id=='b'

@pending
def test_forward_check_retains_omission(prepared,jobs):
    """Verify forward check retains omission.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    prepared=replace(prepared,jobs=(replace(jobs[0],cpu=4),jobs[1]))
    state=ScheduleState(prepared); state.place(prepared.jobs[0],Placement('gpu',0))
    domains={'b':(Placement('gpu',0),Placement('cpu',0),UNASSIGNED)}
    filtered=CSPScheduler().forward_check([jobs[1]],domains,state)
    assert filtered['b']==(Placement('cpu',0),UNASSIGNED)
    assert Placement('gpu',0) in domains['b']

@pending
def test_restore_state(prepared,jobs):
    """Verify restore state.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared); snapshot=state.copy()
    domains=dict(prepared.domains)
    state.place(jobs[0],Placement('gpu',0))
    restored,restored_domains=CSPScheduler().restore_state(snapshot,domains)
    assert not restored.get_assignments()
    assert restored_domains==domains

@pending
def test_timeout_returns_valid_incumbent(servers,config):
    """Verify timeout returns valid incumbent.

    Args:
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    cfg=replace(config,search_timeout_seconds=1e-12)
    js=[Job(str(i),1,1,15,deadline_minute=60) for i in range(50)]
    r=CSPScheduler().schedule(js,servers,cfg)
    assert r.timed_out and not r.optimality_proven
    assert ScheduleValidator().validate_schedule(r,js,servers,cfg).valid
    assert len(r.assignments)+len(r.unscheduled_jobs)==50

@pending
@pytest.mark.parametrize("objectives,count",[(('max_jobs','min_wait'),2),(('min_wait','max_jobs'),1)])
def test_solver_respects_objective_priority(objectives,count,config):
    """Verify solver respects objective priority.

    Args:
        objectives: Ordered objective names defining the optimization priority in this
            case.
        count: Expected number of scheduled jobs for the selected objective order.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    cfg=replace(config,horizon_minutes=30,objectives=objectives)
    js=[Job('a',1,1,15,deadline_minute=30),Job('b',1,1,15,deadline_minute=30)]
    result=CSPScheduler().schedule(js,[Server('s',1,2)],cfg)
    assert len(result.assignments)==count
    expected_wait=15 if count==2 else 0
    assert sum(a.start_minute for a in result.assignments)==expected_wait
    assert result.optimality_proven

@pending
@pytest.mark.parametrize('use_mrv',[False,True])
def test_variable_selection_stable_ties(use_mrv,prepared,jobs):
    """Verify variable selection stable ties.

    Args:
        use_mrv: Whether selection uses real-placement counts instead of original input
            order.
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared)
    domains={'a':(Placement('gpu',0),UNASSIGNED),'b':(Placement('cpu',0),UNASSIGNED)}
    assert CSPScheduler().select_next_job(jobs,domains,state,use_mrv) == jobs[0]

@pending
def test_variable_selection_rejects_empty_remaining(prepared):
    """Verify variable selection rejects empty remaining.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared)
    with pytest.raises(ValueError): CSPScheduler().select_next_job([],{},state,True)

@pending
def test_value_order_preserves_omission_and_server_order(prepared,jobs):
    """Verify value order preserves omission and server order.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    domains={'a':(UNASSIGNED,Placement('cpu',15),Placement('cpu',0),Placement('gpu',0))}
    ordered=CSPScheduler().order_domain_values(jobs[0],domains,prepared)
    assert ordered == (Placement('gpu',0),Placement('cpu',0),Placement('cpu',15),UNASSIGNED)
    assert domains['a'][0] is UNASSIGNED

@pending
def test_forward_check_singleton_omission_is_valid(prepared,jobs):
    """Verify forward check singleton omission is valid.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    prepared=replace(prepared,jobs=(replace(jobs[0],cpu=4),jobs[1]))
    state=ScheduleState(prepared); state.place(prepared.jobs[0],Placement('gpu',0))
    domains={'b':(Placement('gpu',0),UNASSIGNED)}
    assert CSPScheduler().forward_check([jobs[1]],domains,state) == {'b':(UNASSIGNED,)}
