import pytest

from dataclasses import replace
from cloud_scheduler.domains import InitialDomainBuilder
from cloud_scheduler.models import UNASSIGNED, Placement

def test_hardware_and_pin(jobs,servers,config):
    """Verify hardware and pin.

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
    b=InitialDomainBuilder()
    assert [s.server_id for s in b.get_eligible_servers(replace(jobs[0],gpu=1),servers)]==["gpu"]
    assert [s.server_id for s in b.get_eligible_servers(replace(jobs[0],required_server_id="cpu"),servers)]==["cpu"]

@pytest.mark.parametrize("slot,expected", [(15,(0,15,30,45)),(5,tuple(range(0,46,5)))])
def test_start_grid(slot,expected,jobs,config):
    """Verify start grid.

    Args:
        slot: Time resolution in integer minutes.
        expected: Expected return value for the parameterized behavior or boundary case.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    assert InitialDomainBuilder().get_valid_start_times(jobs[0],replace(config,slot_minutes=slot))==expected

def test_horizon_and_omission(jobs,servers,config):
    """Verify horizon and omission.

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
    b=InitialDomainBuilder()
    j=replace(jobs[0],release_minute=60,deadline_minute=90)
    assert b.get_valid_start_times(j,config)==()
    assert b.build_domains([j],servers,config)[j.job_id]==(UNASSIGNED,)

def test_no_hypothetical_filtering(jobs,servers,config):
    """Verify no hypothetical filtering.

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
    js=[replace(j,same_server_as=(jobs[1-i].job_id,)) for i,j in enumerate(jobs)]
    domains=InitialDomainBuilder().build_domains(js,servers,config)
    assert domains['a']==tuple(Placement(s.server_id,t) for t in (0,15,30,45) for s in servers)+(UNASSIGNED,)

def test_unary_filter_removes_invalid_placements(jobs,servers,config):
    """Verify unary filter removes invalid placements.

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
    candidates=(Placement('gpu',0),Placement('gpu',1),Placement('gpu',60),Placement('missing',0))
    assert InitialDomainBuilder().filter_unary_constraints(jobs[0],candidates,servers,config)==(Placement('gpu',0),)

@pytest.mark.parametrize('release,deadline,duration,expected',[(15,30,15,(15,)),(0,90,30,(0,15,30)),(45,90,30,()),(0,60,60,(0,))])
def test_start_times_clip_deadline_to_horizon(release,deadline,duration,expected,jobs,config):
    """Verify start times clip deadline to horizon.

    Args:
        release: Earliest permitted start minute for the job.
        deadline: Job deadline in integer minutes, including exact-boundary and
            beyond-horizon cases.
        duration: Continuous job duration in integer minutes.
        expected: Expected return value for the parameterized behavior or boundary case.
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    job=replace(jobs[0],release_minute=release,deadline_minute=deadline,duration_minutes=duration)
    assert InitialDomainBuilder().get_valid_start_times(job,config) == expected

def test_empty_jobs_and_empty_inventory(jobs,config):
    """Verify empty jobs and empty inventory.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        config: Fixture containing a 60-minute horizon and 15-minute slot resolution,
            unless overridden in this case.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    builder=InitialDomainBuilder()
    assert builder.build_domains([],[],config) == {}
    assert builder.build_domains(jobs,[],config) == {j.job_id:(UNASSIGNED,) for j in jobs}

def test_pin_does_not_override_hardware_eligibility(jobs,servers):
    """Verify pin does not override hardware eligibility.

    Args:
        jobs: Fixture containing valid jobs a and b, each requesting two CPU cores and
            four GB RAM for 15 minutes.
        servers: Fixture containing the GPU server first and CPU-only server second;
            both have four CPU cores.

    Returns:
        None. Test assertions report behavioral failures through pytest.
    """
    job=replace(jobs[0],gpu=1,required_server_id='cpu')
    assert InitialDomainBuilder().get_eligible_servers(job,servers) == ()

def test_domain_order_uses_original_server_order(jobs,servers,config):
    """Verify domain order uses original server order.

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
    result=InitialDomainBuilder().build_domains([jobs[0]],tuple(reversed(servers)),config)['a']
    assert result[:4] == (Placement('cpu',0),Placement('gpu',0),Placement('cpu',15),Placement('gpu',15))
    assert result[-1] is UNASSIGNED
    assert sum(value is UNASSIGNED for value in result) == 1


@pytest.mark.parametrize('changes', [
    {'cpu': 5}, {'ram_gb': 17}, {'gpu': 2}, {'storage_gb': 101},
])
def test_hardware_filter_checks_each_resource(changes, jobs, servers):
    """Exclude every server when any single demand exceeds its capacity.

    Args:
        changes: Resource override exceeding both servers' available hardware.
        jobs: Valid base job definitions.
        servers: Inventory with four cores, 16 GB RAM, at most one GPU and 100 GB storage.

    Returns:
        None. No server is eligible for the excessive demand.
    """
    job = replace(jobs[0], **changes)
    assert InitialDomainBuilder().get_eligible_servers(job, servers) == ()


def test_unary_filter_preserves_input_order_and_removes_bad_values(jobs, servers, config):
    """Filter pins, unknown servers and malformed starts without sorting survivors.

    Args:
        jobs: Valid job definitions used to construct a GPU-pinned candidate.
        servers: GPU and CPU-only inventory.
        config: Valid horizon and time resolution.

    Returns:
        None. Surviving candidates keep their input order and the source is unchanged.
    """
    job = replace(jobs[0], required_server_id='gpu')
    candidates = [Placement('gpu',30), Placement('cpu',0), Placement('missing',0),
                  Placement('gpu',True), Placement('gpu',15.0), Placement('gpu',-15),
                  Placement('gpu',1), Placement('gpu',60), Placement('gpu',0)]
    before = candidates.copy()
    result = InitialDomainBuilder().filter_unary_constraints(job,candidates,servers,config)
    assert result == (Placement('gpu',30), Placement('gpu',0))
    assert candidates == before


def test_opposite_pins_on_related_jobs_do_not_erase_real_domains(jobs, servers, config):
    """Keep unary-feasible placements when related jobs cannot both be scheduled.

    Args:
        jobs: Jobs whose direct same-server relationship is conditional on scheduling.
        servers: Two eligible servers to pin the jobs to independently.
        config: Valid horizon and resolution.

    Returns:
        None. Each job retains its pinned placements and omission decision.
    """
    a = replace(jobs[0], required_server_id='gpu', same_server_as=('b',))
    b = replace(jobs[1], required_server_id='cpu', same_server_as=('a',))
    result = InitialDomainBuilder().build_domains([a,b],servers,config)
    assert result['a'] == tuple(Placement('gpu',t) for t in (0,15,30,45))+(UNASSIGNED,)
    assert result['b'] == tuple(Placement('cpu',t) for t in (0,15,30,45))+(UNASSIGNED,)


def test_unavailable_hardware_leaves_only_omission(jobs, servers, config):
    """Represent excessive hardware demand as valid omission rather than an error.

    Args:
        jobs: Base jobs used to construct an unavailable four-GPU demand.
        servers: Inventory with at most one GPU per server.
        config: Valid horizon and resolution.

    Returns:
        None. The valid job has exactly the UNASSIGNED domain value.
    """
    job = replace(jobs[0], gpu=4)
    assert InitialDomainBuilder().build_domains([job],servers,config) == {'a':(UNASSIGNED,)}


def test_start_generation_requires_resolved_deadline(jobs, config):
    """Reject unresolved optional deadlines at the normalized-input boundary.

    Args:
        jobs: Valid base jobs from which an unresolved deadline is constructed.
        config: Horizon used by preprocessing to resolve omitted deadlines.

    Returns:
        None. A clear ValueError identifies the missing preparation step.
    """
    with pytest.raises(ValueError, match='deadline must be resolved'):
        InitialDomainBuilder().get_valid_start_times(replace(jobs[0],deadline_minute=None),config)
