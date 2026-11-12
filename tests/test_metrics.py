import pytest
pending = pytest.mark.xfail(reason="Feature not implemented", raises=NotImplementedError, strict=True)

from cloud_scheduler.models import *
from cloud_scheduler.evaluation.metrics import MetricsCalculator
from cloud_scheduler.evaluation.benchmark import BenchmarkRunner

@pending
def test_quality_and_capacity_time(config):
    jobs=(Job('a',2,4,15,gpu=1,storage_gb=10,deadline_minute=60),Job('b',1,1,15,deadline_minute=60))
    ss=(Server('s',4,16,2,100),)
    result=ScheduleResult('test',(Assignment('a','s',15,30,0),),
        (InvalidJob(2,'bad',('INVALID_RESOURCE',),('Negative CPU',)),),
        (UnscheduledJob(1,'b'),),12.5,7,True,False)
    m=MetricsCalculator().calculate(result,jobs,ss,config)
    assert m.completion_rate==0.5 and m.average_waiting_minutes==15
    assert m.unscheduled_count==1 and m.invalid_count==1
    assert m.cpu_utilization==pytest.approx(2*15/(4*60))
    assert m.ram_utilization==pytest.approx(4*15/(16*60))
    assert m.gpu_utilization==pytest.approx(1*15/(2*60))
    assert m.storage_utilization==pytest.approx(10*15/(100*60))
    assert (m.runtime_ms,m.search_nodes,m.timed_out,m.optimality_proven)==(12.5,7,True,False)

@pending
def test_empty_denominators(config):
    m=MetricsCalculator().calculate(ScheduleResult('test'),(),(Server('s',1,1),),config)
    assert m.completion_rate is None and m.average_waiting_minutes is None
    assert m.gpu_utilization is None and m.storage_utilization is None
    assert m.cpu_utilization==0 and m.ram_utilization==0

@pending
def test_benchmark_empty(prepared):
    report=BenchmarkRunner().run([],prepared)
    assert report.runs==() and report.timeout_rate is None
