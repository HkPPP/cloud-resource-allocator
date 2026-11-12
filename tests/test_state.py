import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import replace
from cloud_scheduler.models import Placement, ResourceVector
from cloud_scheduler.state import ScheduleState

@pending
def test_interval_usage_and_undo(prepared,jobs):
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',15))
    assert state.get_usage('gpu',0)==ResourceVector()
    assert state.get_usage('gpu',15)==ResourceVector(2,4)
    assert state.get_usage('gpu',30)==ResourceVector()
    state.undo('a')
    assert state.get_usage('gpu',15)==ResourceVector()
    assert not state.get_assignments()

@pending
def test_failed_placement_atomic(prepared,jobs):
    state=ScheduleState(prepared)
    with pytest.raises(ValueError):
        state.place(replace(jobs[0],cpu=99),Placement('gpu',0))
    assert not state.get_assignments()
    assert state.get_usage('gpu',0)==ResourceVector()

@pending
def test_copy_independence(prepared,jobs):
    state=ScheduleState(prepared); state.place(jobs[0],Placement('gpu',0))
    copied=state.copy(); copied.undo('a')
    assert len(state.get_assignments())==1
    assert state.get_usage('gpu',0)==ResourceVector(2,4)
    assert copied.get_usage('gpu',0)==ResourceVector()
