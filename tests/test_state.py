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
    state.undo('b')
    assert state.get_usage('gpu',0) == ResourceVector(2,4)
    assert set(state.get_assignments()) == {'a'}
    state.undo('a')
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


@pytest.mark.parametrize('start', [0, 15, 45])
def test_reverse_undo_restores_each_exact_snapshot(start, state_factory):
    """Restore each previous state exactly while unwinding fractional placements.

    Args:
        start: Aligned start time, including the last slot in the horizon.
        state_factory: Factory constructing independent state from explicit inputs.

    Returns:
        None. Every reverse-order undo recovers its exact saved state and usage.
    """
    from cloud_scheduler.models import Job, Server
    jobs = [Job(name,1,amount,15,gpu=1,storage_gb=amount,deadline_minute=60)
            for name,amount in [('a',0.1),('b',0.2),('c',0.3)]]
    state = state_factory(jobs,inventory=[Server('gpu',4,16,3,100)])
    snapshots = []
    for job in jobs:
        snapshots.append((dict(state.get_assignments()),
                          [state.get_usage('gpu',minute) for minute in (0,15,30,45)]))
        state.place(job,Placement('gpu',start))
    for job, (assignments,usage) in zip(reversed(jobs),reversed(snapshots)):
        state.undo(job.job_id)
        assert dict(state.get_assignments()) == assignments
        assert [state.get_usage('gpu',minute) for minute in (0,15,30,45)] == usage
    assert not state.get_assignments()


@pytest.mark.parametrize('second_server',['gpu','cpu'])
def test_out_of_order_undo_leaves_usage_and_history_unchanged(second_server, prepared, jobs):
    """Reject non-LIFO undo across both overlapping jobs and different servers.

    Args:
        second_server: Server for the newer job; global reverse order applies to both.
        prepared: Immutable two-job scheduling input.
        jobs: Valid jobs placed in the order a, then b.

    Returns:
        None. Rejected undo preserves state and both subsequent valid undos succeed.
    """
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0))
    state.place(jobs[1],Placement(second_server,0))
    assignments = dict(state.get_assignments())
    usage = {server:[state.get_usage(server,t) for t in (0,15,30,45)]
             for server in ('gpu','cpu')}
    with pytest.raises(ValueError,match='reverse placement order'):
        state.undo('a')
    assert dict(state.get_assignments()) == assignments
    assert {server:[state.get_usage(server,t) for t in (0,15,30,45)]
            for server in ('gpu','cpu')} == usage
    state.undo('b')
    state.undo('a')
    assert not state.get_assignments()
    assert all(state.get_usage(server,0) == ResourceVector() for server in ('gpu','cpu'))


def test_undo_restores_values_without_resource_recalculation(monkeypatch, prepared, jobs):
    """Undo from saved values without adding, subtracting or rebuilding slot ranges.

    Args:
        monkeypatch: pytest fixture making any resource recalculation fail immediately.
        prepared: Immutable input with two jobs.
        jobs: Jobs whose combined demand fits the selected server.

    Returns:
        None. Undo succeeds despite arithmetic and demand calculation being disabled.
    """
    from cloud_scheduler.models import Job
    import cloud_scheduler.state as state_module
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0))
    before = state.get_usage('gpu',0)
    state.place(jobs[1],Placement('gpu',0))

    def forbidden(*args, **kwargs):
        """Reject recalculation after placement has saved the undo values.

        Args:
            *args: Positional arguments to a disabled resource operation.
            **kwargs: Keyword arguments to a disabled resource operation.

        Returns:
            None. Every call raises an assertion failure.

        Raises:
            AssertionError: Undo tried to recompute resources or occupied slots.
        """
        raise AssertionError('Undo must restore saved values directly')

    monkeypatch.setattr(ResourceVector,'__add__',forbidden)
    monkeypatch.setattr(ResourceVector,'__sub__',forbidden)
    monkeypatch.setattr(Job,'resource_requirements',forbidden)
    monkeypatch.setattr(state_module,'occupied_slots',forbidden)
    state.undo('b')
    assert state.get_usage('gpu',0) == before
    assert set(state.get_assignments()) == {'a'}
    state.undo('a')
    assert state.get_usage('gpu',0) == ResourceVector()


def test_undo_preserves_other_intervals_and_servers(state_factory):
    """Restore only the latest placement's occupied slots on its selected server.

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
    state.place(b,Placement('gpu',0))
    state.place(c,Placement('cpu',15))
    state.place(a,Placement('gpu',15))
    other_server_before = [state.get_usage('cpu',minute) for minute in (0,15,30,45)]
    outside_before = state.get_usage('gpu',0)
    state.undo('a')
    assert state.get_usage('gpu',0) == outside_before
    assert state.get_usage('gpu',15) == ResourceVector(1,2)
    assert state.get_usage('gpu',30) == ResourceVector(1,2)
    assert state.get_usage('gpu',45) == ResourceVector()
    assert [state.get_usage('cpu',minute) for minute in (0,15,30,45)] == other_server_before


def test_copied_state_keeps_independent_undo_history(prepared, jobs):
    """Allow copied search branches to undo and place independently.

    Args:
        prepared: Immutable input shared by both state copies.
        jobs: Two valid jobs placed before the branch is copied.

    Returns:
        None. Each branch restores its own history after taking different decisions.
    """
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0))
    state.place(jobs[1],Placement('gpu',15))
    branch = state.copy()
    branch.undo('b')
    branch.place(jobs[1],Placement('cpu',30))
    state.undo('b')
    state.undo('a')
    assert not state.get_assignments()
    assert branch.get_usage('gpu',0) == ResourceVector(2,4)
    assert branch.get_usage('cpu',30) == ResourceVector(2,4)
    branch.undo('b')
    assert branch.get_usage('cpu',30) == ResourceVector()
    branch.undo('a')
    assert not branch.get_assignments()


def test_rejected_placement_preserves_undo_history(prepared, jobs):
    """Keep the last successful placement on the undo stack after a rejected attempt.

    Args:
        prepared: Immutable input containing the jobs to place.
        jobs: Valid jobs; the second is modified to exceed server capacity.

    Returns:
        None. Failed placement creates no undo entry and the prior assignment unwinds.
    """
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0))
    with pytest.raises(ValueError):
        state.place(replace(jobs[1],cpu=99),Placement('gpu',0))
    with pytest.raises(KeyError):
        state.undo('b')
    state.undo('a')
    assert state.get_usage('gpu',0) == ResourceVector()
    assert not state.get_assignments()


def test_undone_job_can_be_placed_and_undone_again(prepared, jobs):
    """Discard used history entries before the same job is placed on another branch.

    Args:
        prepared: Immutable scheduling input.
        jobs: Valid jobs, with job a reused after an undo.

    Returns:
        None. Both placements unwind without stale slot values from the earlier branch.
    """
    state = ScheduleState(prepared)
    state.place(jobs[0],Placement('gpu',0))
    state.undo('a')
    state.place(jobs[0],Placement('cpu',30))
    state.undo('a')
    assert not state.get_assignments()
    for server in ('gpu','cpu'):
        assert all(state.get_usage(server,t) == ResourceVector() for t in (0,15,30,45))
