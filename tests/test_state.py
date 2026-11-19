import pytest

from dataclasses import replace
from cloud_scheduler.models import Placement, ResourceVector
from cloud_scheduler.state import ScheduleState

def test_interval_usage_and_undo(prepared,jobs):
    """Verify interval usage and undo.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',15))
    assert state.get_usage('gpu',0)==ResourceVector()
    assert state.get_usage('gpu',15)==ResourceVector(2,4)
    assert state.get_usage('gpu',30)==ResourceVector()
    state.undo('a')
    assert state.get_usage('gpu',15)==ResourceVector()
    assert not state.get_assignments()

def test_failed_placement_atomic(prepared,jobs):
    """Verify failed placement atomic.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared)
    with pytest.raises(ValueError):
        state.place(replace(jobs[0],cpu=99),Placement('gpu',0))
    assert not state.get_assignments()
    assert state.get_usage('gpu',0)==ResourceVector()

def test_copy_independence(prepared,jobs):
    """Verify copy independence.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',0))
    copied=state.copy(); copied.undo('a')
    assert len(state.get_assignments())==1
    assert state.get_usage('gpu',0)==ResourceVector(2,4)
    assert copied.get_usage('gpu',0)==ResourceVector()

@pytest.mark.parametrize('minute',[15,16,29])
def test_usage_maps_minutes_to_occupied_slot(minute,state_factory):
    """Verify usage maps minutes to occupied slot.

    Args:
        minute: Minute to query, including slot interiors and invalid horizon bounds.
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    from cloud_scheduler.models import Job
    job = Job('j',1,2,15,deadline_minute=60)
    state = state_factory([job]); state.place(job,Placement('gpu',15))
    assert state.get_usage('gpu',minute) == ResourceVector(1,2)
    assert state.get_usage('cpu',minute) == ResourceVector()

@pytest.mark.parametrize('minute',[-1,60,75])
def test_usage_rejects_outside_horizon(minute,prepared):
    """Verify usage rejects outside horizon.

    Args:
        minute: Minute to query, including slot interiors and invalid horizon bounds.
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(ValueError):
        ScheduleState(prepared).get_usage('gpu',minute)

def test_usage_unknown_server(prepared):
    """Verify usage unknown server.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    with pytest.raises(KeyError):
        ScheduleState(prepared).get_usage('missing',0)

def test_duplicate_place_and_missing_undo_are_atomic(prepared,jobs):
    """Verify duplicate place and missing undo are atomic.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state = ScheduleState(prepared); original = state.place(jobs[0],Placement('gpu',0))
    with pytest.raises(ValueError): state.place(jobs[0],Placement('cpu',15))
    with pytest.raises(KeyError): state.undo('missing')
    assert state.get_assignments() == {'a':original}
    assert state.get_usage('gpu',0) == ResourceVector(2,4)
    assert state.get_usage('cpu',15) == ResourceVector()

def test_undo_preserves_other_overlapping_jobs(prepared,jobs):
    """Verify undo preserves other overlapping jobs.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0)); state.place(jobs[1],Placement('gpu',0))
    state.undo('a')
    assert state.get_usage('gpu',0) == ResourceVector(2,4)
    assert set(state.get_assignments()) == {'b'}
    state.undo('b')
    assert state.get_usage('gpu',0) == ResourceVector()
    with pytest.raises(KeyError): state.undo('b')

def test_assignment_snapshot_does_not_expose_mutable_state(prepared,jobs):
    """Verify assignment snapshot does not expose mutable state.

    Args:
        prepared: Fixture containing immutable normalized jobs, inventory, indices and
            explicitly declared candidate domains.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    state = ScheduleState(prepared); assignment = state.place(jobs[0],Placement('gpu',0))
    snapshot = state.get_assignments()
    try:
        snapshot.clear()
    except (AttributeError,TypeError):
        pass  # Both read-only views and detached copies satisfy the contract.
    assert state.get_assignments() == {'a':assignment}

def test_undo_restores_fractional_resources_exactly(state_factory):
    """Verify undo restores fractional resources exactly.

    Args:
        state_factory: Fixture callable that constructs private state from explicitly
            supplied jobs, inventory and settings.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    from cloud_scheduler.models import Job
    a,b = (Job(name,1,ram,15,storage_gb=ram,deadline_minute=60) for name,ram in [('a',0.1),('b',0.2)])
    state = state_factory([a,b]); state.place(a,Placement('gpu',0))
    before = state.get_usage('gpu',0)
    state.place(b,Placement('gpu',0)); state.undo('b')
    assert state.get_usage('gpu',0) == before


@pytest.mark.parametrize('removed,expected_ram', [
    ('a', 0.2 + 0.3), ('b', 0.1 + 0.3), ('c', 0.1 + 0.2),
])
def test_undo_fractional_overlap_in_any_order(removed, expected_ram, state_factory):
    """Rebuild all resource totals exactly after removing any overlapping job.

    Args:
        removed: Job ID to remove, including jobs placed before retained assignments.
        expected_ram: Exact floating-point sum of the two remaining RAM quantities.
        state_factory: Factory constructing independent state from explicit inputs.

    Returns:
        None. Remaining usage equals a fresh ordered sum without subtraction residue.
    """
    from cloud_scheduler.models import Job, Server
    jobs = [Job(name,1,amount,15,gpu=1,storage_gb=amount,deadline_minute=60)
            for name,amount in [('a',0.1),('b',0.2),('c',0.3)]]
    state = state_factory(jobs,inventory=[Server('gpu',4,16,3,100)])
    for job in jobs:
        state.place(job,Placement('gpu',15))
    state.undo(removed)
    assert state.get_usage('gpu',15) == ResourceVector(2,expected_ram,2,expected_ram)
    assert state.get_usage('gpu',0) == ResourceVector()
    assert state.get_usage('gpu',30) == ResourceVector()
    assert set(state.get_assignments()) == {'a','b','c'} - {removed}
    for job_id in tuple(state.get_assignments()):
        state.undo(job_id)
    assert state.get_usage('gpu',15) == ResourceVector()
    assert not state.get_assignments()


def test_failed_undo_reconstruction_leaves_state_unchanged(monkeypatch, prepared, jobs):
    """Keep assignments and usage intact when rebuilding remaining demand fails.

    Args:
        monkeypatch: pytest fixture injecting an arithmetic failure during undo.
        prepared: Immutable test instance containing two jobs and server capacities.
        jobs: Jobs whose combined demand fits the selected server.

    Returns:
        None. A raised reconstruction error cannot partially commit an undo.
    """
    state = ScheduleState(prepared)
    for job in jobs:
        state.place(job,Placement('gpu',0))
    assignments_before = dict(state.get_assignments())
    usage_before = state.get_usage('gpu',0)

    def fail_add(self, other):
        """Simulate an arithmetic failure before an undo commits its changes.

        Args:
            other: Resource demand that would be accumulated into the rebuilt slot.

        Returns:
            None. This injected failure never produces a resource vector.

        Raises:
            ArithmeticError: Intentional test failure during resource reconstruction.
        """
        raise ArithmeticError('Resource reconstruction failed')

    monkeypatch.setattr(ResourceVector,'__add__',fail_add)
    with pytest.raises(ArithmeticError,match='Resource reconstruction failed'):
        state.undo('b')
    assert dict(state.get_assignments()) == assignments_before
    assert state.get_usage('gpu',0) == usage_before


def test_undo_preserves_other_intervals_and_servers(state_factory):
    """Limit reconstruction to the removed job's server and occupied interval.

    Args:
        state_factory: Factory constructing isolated state from explicit jobs.

    Returns:
        None. Remaining jobs retain their demand, including outside the removed range.
    """
    from cloud_scheduler.models import Job
    a = Job('a',1,1,30,deadline_minute=60)
    b = Job('b',1,2,45,deadline_minute=60)
    c = Job('c',1,3,30,deadline_minute=60)
    state = state_factory([a,b,c])
    state.place(a,Placement('gpu',15))
    state.place(b,Placement('gpu',0))
    state.place(c,Placement('cpu',15))
    other_server_before = [state.get_usage('cpu',minute) for minute in (0,15,30,45)]
    outside_before = state.get_usage('gpu',0)
    state.undo('a')
    assert state.get_usage('gpu',0) == outside_before
    assert state.get_usage('gpu',15) == ResourceVector(1,2)
    assert state.get_usage('gpu',30) == ResourceVector(1,2)
    assert state.get_usage('gpu',45) == ResourceVector()
    assert [state.get_usage('cpu',minute) for minute in (0,15,30,45)] == other_server_before
