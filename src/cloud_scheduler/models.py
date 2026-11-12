"""Immutable scheduling models and resource arithmetic interfaces.

CPU/GPU use integer cores/counts. RAM/storage use finite GB quantities (float
representation); reject negative or nonfinite inputs during preprocessing.
Dataclasses intentionally do not validate, so malformed inputs can be reported
as INVALID rather than causing construction to abort the entire batch.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, TypeAlias

@dataclass(frozen=True)
class ResourceVector:
    """Resource amounts: CPU cores, RAM GB, GPU devices, storage GB."""
    cpu: int = 0
    ram_gb: float = 0
    gpu: int = 0
    storage_gb: float = 0

    def __add__(self, other: ResourceVector) -> ResourceVector:
        """Return component-wise sum without mutating either operand; zero is identity."""
        raise NotImplementedError('Resource addition is not implemented.')

    def __sub__(self, other: ResourceVector) -> ResourceVector:
        """Return component-wise difference; signed intermediate vectors are permitted.

        Resource accounting callers must separately prevent negative actual usage.
        """
        raise NotImplementedError('Resource subtraction is not implemented.')

    def fits_within(self, capacity: ResourceVector) -> bool:
        """Return whether every component is <= capacity, including exact equality.

        Inputs are validated resource vectors; comparison must examine all four units.
        """
        raise NotImplementedError('Component-wise comparison is not implemented.')

@dataclass(frozen=True)
class Server:
    """Unique nonempty ID and nonnegative finite capacities; CPU/GPU are integers."""
    server_id: str
    cpu_capacity: int
    ram_capacity_gb: float
    gpu_capacity: int = 0
    storage_capacity_gb: float = 0

    def capacity(self) -> ResourceVector:
        """Return this server's four capacities in standard resource units."""
        raise NotImplementedError('Capacity vector is not implemented.')

    def supports(self, job: Job) -> bool:
        """Check individual resource fit only; ignore time, pinning and other jobs."""
        raise NotImplementedError('Individual hardware fit is not implemented.')

@dataclass(frozen=True)
class Job:
    """Immutable valid-job shape; release defaults to 0, deadline to the horizon.

    A None deadline is resolved by preprocessing using the supplied configuration.
    Relationship tuples express symmetric, conditional pairwise edges, not groups.
    """
    job_id: str
    cpu: int
    ram_gb: float
    duration_minutes: int
    gpu: int = 0
    storage_gb: float = 0
    release_minute: int = 0
    deadline_minute: int | None = None
    required_server_id: str | None = None
    same_server_as: tuple[str, ...] = ()
    different_server_from: tuple[str, ...] = ()

    def latest_start(self) -> int:
        """Return resolved deadline minus duration; require a prepared job.

        Raise ValueError if deadline is still None; horizon clipping belongs in domains.
        """
        raise NotImplementedError('Latest start is not implemented.')

    def resource_requirements(self) -> ResourceVector:
        """Return the job's four demands without considering any server or time."""
        raise NotImplementedError('Requirements vector is not implemented.')

    def execution_interval(self, start_minute: int) -> tuple[int, int]:
        """Return [start, start + duration) endpoints; feasibility is checked separately."""
        raise NotImplementedError('Interval endpoints is not implemented.')

@dataclass(frozen=True)
class Placement:
    """Real domain value; integer start minutes measured from horizon origin."""
    server_id: str
    start_minute: int

class Unassigned(Enum):
    """A real search decision to omit a valid job, consuming no resources."""
    TOKEN = "UNASSIGNED"

UNASSIGNED = Unassigned.TOKEN
DomainValue: TypeAlias = Placement | Unassigned

@dataclass(frozen=True)
class Assignment:
    """Final half-open execution interval with original zero-based input identity."""
    job_id: str
    server_id: str
    start_minute: int
    end_minute: int
    input_index: int

class JobStatus(str, Enum):
    """Exactly one classification per original submission, including malformed ones."""
    SCHEDULED = "SCHEDULED"
    INVALID = "INVALID"
    UNSCHEDULED = "UNSCHEDULED"

@dataclass(frozen=True)
class InvalidJob:
    """Per-record errors. Codes and reasons are parallel nonempty tuples.

    input_index always identifies the submission even when job_id is absent or
    duplicated; all occurrences of a duplicate ID are invalid.
    """
    input_index: int
    job_id: str | None
    error_codes: tuple[str, ...]
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class UnscheduledJob:
    """Valid omitted record; reason must not imply proven impossibility by default."""
    input_index: int
    job_id: str
    reason: str | None = None

@dataclass(frozen=True)
class ScheduleResult:
    """Algorithm output. Runtime includes preprocessing for schedule(), excludes it
    for solve(prepared). Statistics identify that timing scope explicitly.
    optimality_proven is false for Greedy and for any interrupted search.
    """
    algorithm: str
    assignments: tuple[Assignment, ...] = ()
    invalid_jobs: tuple[InvalidJob, ...] = ()
    unscheduled_jobs: tuple[UnscheduledJob, ...] = ()
    runtime_ms: float = 0
    search_nodes: int = 0
    timed_out: bool = False
    optimality_proven: bool = False
    statistics: Mapping[str, int | float | str | bool] = field(default_factory=dict)

# Raw JSON elements can be scalars/lists as well as records. Classify them before
# constructing Job so malformed entries retain their input identity.
RawJob: TypeAlias = object
