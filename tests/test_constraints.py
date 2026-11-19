import pytest

from dataclasses import replace
from cloud_scheduler.constraints import ConstraintChecker
from cloud_scheduler.models import Assignment, Job, Placement
from cloud_scheduler.state import ScheduleState

@pytest.mark.parametrize("changes",[{"cpu":3},{"ram_gb":13},{"gpu":1},{"storage_gb":91}])
def test_cumulative_resource_overflow(changes,prepared,jobs):
    """Verify cumulative resource overflow.

    Args:
        changes: Field overrides selecting the invalid or boundary condition under test.
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    prepared=replace(prepared,jobs=(replace(jobs[0],gpu=1,storage_gb=10),replace(jobs[1],**changes)))
    state=ScheduleState(prepared)
    state.place(prepared.jobs[0],Placement("gpu",0))
    assert not ConstraintChecker().check_resource_capacity(replace(jobs[1],**changes),Placement('gpu',0),state)

@pytest.mark.parametrize("start,expected",[(0,True),(45,True),(60,False),(-15,False),(1,False)])
def test_time_window(start,expected,jobs,config):
    """Verify time window.

    Args:
        start: Candidate job start minute measured from horizon origin.
        expected: Expected return value for the parameterized behavior or boundary case.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert ConstraintChecker().check_time_window(jobs[0],Placement('gpu',start),config) is expected

def test_pin(jobs):
    """Verify pin.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    c=ConstraintChecker(); j=replace(jobs[0],required_server_id='cpu')
    assert c.check_server_pinning(j,Placement('cpu',0))
    assert not c.check_server_pinning(j,Placement('gpu',0))

@pytest.mark.parametrize("relation,method,same_ok",[("same_server_as","check_colocation",True),("different_server_from","check_anti_affinity",False)])
@pytest.mark.parametrize("declarer",[0,1])
def test_relationship_both_directions(relation,method,same_ok,declarer,jobs):
    """Verify relationship both directions.

    Args:
        relation: Job relationship field under test: same_server_as or
            different_server_from.
        method: Relationship-check method exercised by this parameterized case.
        same_ok: Expected result when related jobs share a server under the selected
            relationship.
        declarer: Index of the job declaring the relationship; verifies both declaration
            directions.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    js=list(jobs); js[declarer]=replace(js[declarer],**{relation:(js[1-declarer].job_id,)})
    check=getattr(ConstraintChecker(),method)
    mapping={j.job_id:j for j in js}
    assert check(js[1],Placement('gpu',15),{},mapping)
    assigned={'a':Assignment('a','gpu',0,15,0)}
    assert check(js[1],Placement('gpu',15),assigned,mapping) is same_ok
    assert check(js[1],Placement('cpu',15),assigned,mapping) is (not same_ok)

def test_concurrent_and_touching(prepared,jobs):
    """Verify concurrent and touching.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',0))
    assert state.can_place(jobs[1],Placement('gpu',0))
    assert state.can_place(replace(jobs[1],cpu=4),Placement('gpu',15))
    assert not state.can_place(replace(jobs[1],cpu=4),Placement('gpu',0))

def test_skipped_middle_does_not_imply_transitive_colocation():
    """Verify skipped middle does not imply transitive colocation.

    Args:
        None.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    a=Job('a',1,1,15,same_server_as=('b',),different_server_from=('c',))
    b=Job('b',1,1,15,same_server_as=('a','c'))
    c=Job('c',1,1,15,same_server_as=('b',),different_server_from=('a',))
    check=ConstraintChecker(); mapping={j.job_id:j for j in (a,b,c)}
    assigned={'a':Assignment('a','gpu',0,15,0)}
    assert check.check_colocation(c,Placement('cpu',0),assigned,mapping)
    assert check.check_anti_affinity(c,Placement('cpu',0),assigned,mapping)

@pytest.mark.parametrize(
    "release,deadline,duration,start,expected",
    [(15,45,15,0,False), (15,45,15,15,True), (15,45,15,30,True),
     (15,45,15,45,False), (0,90,15,45,True), (0,90,15,60,False),
     (0,60,60,0,True), (0,60,60,15,False)],
)
def test_time_window_checks_both_bounds(release, deadline, duration, start, expected, config):
    """Verify time window checks both bounds.

    Args:
        release: Earliest permitted start minute for the job.
        deadline: Job deadline in integer minutes, including exact-boundary and
            beyond-horizon cases.
        duration: Continuous job duration in integer minutes.
        start: Candidate job start minute measured from horizon origin.
        expected: Expected return value for the parameterized behavior or boundary case.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    job = Job('j', 1, 1, duration, release_minute=release, deadline_minute=deadline)
    assert ConstraintChecker().check_time_window(job, Placement('gpu', start), config) is expected

@pytest.mark.parametrize('field,capacity', [('cpu',4), ('ram_gb',16), ('gpu',1), ('storage_gb',100)])
@pytest.mark.parametrize('overflow', [False, True])
def test_each_resource_exact_capacity_and_overflow(field, capacity, overflow, state_factory):
    """Verify each resource exact capacity and overflow.

    Args:
        field: Resource field whose capacity, type or numerical boundary is being
            tested.
        capacity: Exact capacity of the selected server resource, in the resource's
            native units.
        overflow: Whether demand exceeds exact resource capacity by one unit.
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    job = replace(Job('j',0,0,15,deadline_minute=60), **{field:capacity + int(overflow)})
    state = state_factory([job])
    assert ConstraintChecker().check_resource_capacity(job, Placement('gpu',0),state) is (not overflow)

def test_capacity_uses_sum_of_three_overlapping_jobs(state_factory):
    """Verify capacity uses sum of three overlapping jobs.

    Args:
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    jobs = [Job(str(i), 2, 1, 30, deadline_minute=60) for i in range(3)]
    state = state_factory(jobs)
    state.place(jobs[0], Placement('gpu',0))
    state.place(jobs[1], Placement('gpu',15))
    assert not ConstraintChecker().check_resource_capacity(jobs[2],Placement('gpu',15),state)
    assert ConstraintChecker().check_resource_capacity(jobs[2],Placement('cpu',15),state)

def test_capacity_checks_last_occupied_slot(state_factory):
    """Verify capacity checks last occupied slot.

    Args:
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    blocker = Job('blocker',4,1,15,release_minute=30,deadline_minute=45)
    candidate = Job('candidate',1,1,45,deadline_minute=60)
    state = state_factory([blocker,candidate])
    state.place(blocker,Placement('gpu',30))
    assert not ConstraintChecker().check_resource_capacity(candidate,Placement('gpu',0),state)

@pytest.mark.parametrize('checker_method', ['can_place','state_can_place'])
@pytest.mark.parametrize('kind', ['unknown_server','duplicate','window','pin','capacity','colocation','anti_affinity'])
def test_can_place_rejects_every_hard_violation_without_mutation(checker_method,kind,state_factory):
    """Verify can place rejects every hard violation without mutation.

    Args:
        checker_method: Whether feasibility is exercised through ConstraintChecker or
            ScheduleState.
        kind: Named hard-constraint or output-accounting violation introduced by this
            case.
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    a = Job('a',4,1,15,deadline_minute=60)
    b = Job('b',1,1,15,deadline_minute=60)
    candidate = Placement('gpu',0)
    if kind == 'window': candidate = Placement('gpu',60)
    if kind == 'unknown_server': candidate = Placement('missing',0)
    if kind == 'pin': b = replace(b,required_server_id='cpu')
    if kind == 'colocation':
        b = replace(b,same_server_as=('a',)); candidate = Placement('cpu',15)
    if kind == 'anti_affinity':
        b = replace(b,different_server_from=('a',)); candidate = Placement('gpu',15)
    state = state_factory([a,b]); state.place(a,Placement('gpu',0))
    job = a if kind == 'duplicate' else b
    before = dict(state.get_assignments())
    usage = state.get_usage('gpu',0)
    allowed = (state.can_place(job,candidate) if checker_method == 'state_can_place'
               else ConstraintChecker().can_place(job,candidate,state))
    assert allowed is False
    assert dict(state.get_assignments()) == before
    assert state.get_usage('gpu',0) == usage

@pytest.mark.parametrize('method,relation', [('check_colocation','same_server_as'),('check_anti_affinity','different_server_from')])
def test_all_assigned_relationship_neighbors_are_checked(method,relation):
    """Verify all assigned relationship neighbors are checked.

    Args:
        method: Relationship-check method exercised by this parameterized case.
        relation: Job relationship field under test: same_server_as or
            different_server_from.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    candidate = Job('candidate',1,1,15,deadline_minute=60,**{relation:('a','b','omitted')})
    neighbors = [Job(name,1,1,15,deadline_minute=60) for name in ('a','b','omitted')]
    mapping = {job.job_id:job for job in [candidate,*neighbors]}
    assignments = {'a':Assignment('a','gpu',0,15,1), 'b':Assignment('b','cpu',15,30,2)}
    # One neighbor violates each relation, even though the first may satisfy it.
    assert not getattr(ConstraintChecker(),method)(candidate,Placement('gpu',30),assignments,mapping)

def test_unrelated_assigned_jobs_do_not_create_affinity_constraints(jobs):
    """Verify unrelated assigned jobs do not create affinity constraints.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    mapping = {job.job_id:job for job in jobs}
    assigned = {'a':Assignment('a','gpu',0,15,0)}
    checker = ConstraintChecker()
    for server in ('gpu','cpu'):
        assert checker.check_colocation(jobs[1],Placement(server,0),assigned,mapping)
        assert checker.check_anti_affinity(jobs[1],Placement(server,0),assigned,mapping)

@pytest.mark.parametrize('checker_method', ['can_place','state_can_place'])
def test_can_place_accepts_feasible_candidate_without_mutation(checker_method,state_factory,jobs):
    """Accept a valid overlapping candidate while keeping the tracker unchanged.

    Args:
        checker_method: Feasibility entry point, through the checker or state wrapper.
        state_factory: Factory creating isolated state for the provided valid jobs.
        jobs: Two jobs whose combined demand exactly fits the GPU server's CPU.

    Returns:
        None. Assertions verify acceptance and unchanged assignments and usage.
    """
    state = state_factory(jobs)
    state.place(jobs[0],Placement('gpu',0))
    before = dict(state.get_assignments())
    usage = state.get_usage('gpu',0)
    candidate = Placement('gpu',0)
    allowed = (state.can_place(jobs[1],candidate) if checker_method == 'state_can_place'
               else ConstraintChecker().can_place(jobs[1],candidate,state))
    assert allowed is True
    assert dict(state.get_assignments()) == before
    assert state.get_usage('gpu',0) == usage
