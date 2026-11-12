import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from dataclasses import replace
from cloud_scheduler.models import Assignment, ScheduleResult, UnscheduledJob, Job
from cloud_scheduler.evaluation.validator import ScheduleValidator

@pending
def test_valid_and_boundary(jobs,servers,config):
    r=ScheduleResult('test',(Assignment('a','gpu',0,15,0),Assignment('b','gpu',15,30,1)))
    assert ScheduleValidator().validate_schedule(r,jobs,servers,config).valid

@pending
@pytest.mark.parametrize('kind',['overflow','time','duplicate','missing','status_overlap','unknown_server','wrong_duration','wrong_index','pin','affinity'])
def test_invalid_output(kind,jobs,servers,config):
    js=list(jobs); assignments=[Assignment('a','gpu',0,15,0),Assignment('b','gpu',0,15,1)]; unscheduled=()
    if kind=='overflow': js=[replace(j,cpu=3) for j in js]
    if kind=='time': assignments[0]=replace(assignments[0],start_minute=60,end_minute=75)
    if kind=='duplicate': assignments.append(assignments[0])
    if kind=='missing': assignments.pop()
    if kind=='status_overlap': unscheduled=(UnscheduledJob(0,'a'),)
    if kind=='unknown_server': assignments[0]=replace(assignments[0],server_id='absent')
    if kind=='wrong_duration': assignments[0]=replace(assignments[0],end_minute=30)
    if kind=='wrong_index': assignments[0]=replace(assignments[0],input_index=99)
    if kind=='pin': js[0]=replace(js[0],required_server_id='cpu')
    if kind=='affinity': js[0]=replace(js[0],different_server_from=('b',))
    report=ScheduleValidator().validate_schedule(ScheduleResult('test',tuple(assignments),unscheduled_jobs=unscheduled),js,servers,config)
    assert not report.valid
    assert report.errors or report.constraint_violations

@pending
def test_relationship_conflict_with_nonoverlapping_times(jobs,servers,config):
    js=[replace(jobs[0],same_server_as=('b',)),jobs[1]]
    r=ScheduleResult('test',(Assignment('a','gpu',0,15,0),Assignment('b','cpu',15,30,1)))
    assert not ScheduleValidator().validate_schedule(r,js,servers,config).valid
