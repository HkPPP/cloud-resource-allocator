"""Input validation and immutable normalized scheduling instances.

    JSON syntax errors and invalid config/server inventories abort the run with
    ValueError. Malformed job objects become per-record InvalidJob entries.
    Validation never mistakes lack of cluster capacity for malformed requirements.
"""
from collections import Counter
from dataclasses import dataclass, fields, replace
from math import isfinite
from typing import Mapping, Sequence
from .config import SchedulerConfig
from .domains import InitialDomainBuilder
from .models import DomainValue, InvalidJob, Job, RawJob, Server


_REQUIRED_JOB_FIELDS = ("job_id", "cpu", "ram_gb", "duration_minutes")
_JOB_FIELDS = {field.name for field in fields(Job)}
_RELATIONSHIP_FIELDS = ("same_server_as", "different_server_from")


def _is_id(value: object) -> bool:
    return isinstance(value, str) and bool(value)


def _is_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_resources(cpu: object, ram: object, gpu: object, storage: object) -> bool:
    return (
        _is_integer(cpu) and cpu >= 0
        and _is_integer(gpu) and gpu >= 0
        and all(
            (_is_integer(value) or isinstance(value, float) and isfinite(value))
            and value >= 0
            for value in (ram, storage)
        )
    )


@dataclass(frozen=True)
class PreparedInstance:
    """Deeply immutable benchmark input; tuples only, no mutable domain dictionaries.

    jobs have explicit deadlines and symmetric direct relationships, referencing
    only valid jobs. input_indices maps each valid unique ID to its original
    zero-based record index. Invalid-target relationships are dropped: that target
    cannot be scheduled. Each solver creates its own mutable state/domain copies.
    """
    jobs: tuple[Job, ...]
    servers: tuple[Server, ...]
    config: SchedulerConfig
    invalid_jobs: tuple[InvalidJob, ...]
    input_indices: tuple[tuple[str, int], ...]
    submitted_count: int
    domains: tuple[tuple[str, tuple[DomainValue, ...]], ...]

def validate_config(config: SchedulerConfig) -> None:
    """Delegate to config.validate(); invalid global settings raise ValueError.

    Args:
        config: Scheduling settings defining the integer-minute horizon, slot resolution
            and solver options.

    Returns:
        None: Configuration satisfies global rules; errors abort the run rather than
            classifying individual jobs.

    Raises:
        ValueError: The configuration does not satisfy SchedulerConfig rules.
    """
    config.validate()

def validate_servers(servers: Sequence[Server]) -> tuple[Server, ...]:
    """Return validated inventory in input order; allow an empty cluster.

    Raise ValueError for duplicate/empty IDs, negative/nonfinite capacity, boolean
    quantities, or noninteger CPU/GPU. No partial inventory is silently accepted.

    Args:
        servers: Server inventory in original input order; an empty inventory is
            permitted.

    Returns:
        tuple[Server, ...]: Validated inventory in original order, or an empty tuple for
            an empty cluster.

    Raises:
        ValueError: Inventory IDs or resource quantities are malformed or duplicated.
    """
    if not isinstance(servers, Sequence) or isinstance(servers, (str, bytes, bytearray)):
        raise ValueError("Server inventory must be a sequence of Server records.")

    inventory = tuple(servers)
    seen_ids = set()
    for index, server in enumerate(inventory):
        if not isinstance(server, Server) or not _is_id(server.server_id):
            raise ValueError(f"Server at index {index} must have a nonempty string ID.")
        if server.server_id in seen_ids:
            raise ValueError(f"Duplicate server ID {server.server_id!r}.")
        if not _valid_resources(
            server.cpu_capacity, server.ram_capacity_gb,
            server.gpu_capacity, server.storage_capacity_gb,
        ):
            raise ValueError(f"Invalid resource capacities for server {server.server_id!r}.")
        seen_ids.add(server.server_id)
    return inventory


def _raw_job_id(record: RawJob) -> str | None:
    if isinstance(record, Job):
        value = record.job_id
    elif isinstance(record, Mapping):
        value = record.get("job_id")
    else:
        return None
    return value if _is_id(value) else None


def _job_errors(job: Job, slot: int) -> dict[str, str]:
    errors = {}
    if not _is_id(job.job_id):
        errors["INVALID_ID"] = "job_id must be a nonempty string."
    if not _valid_resources(job.cpu, job.ram_gb, job.gpu, job.storage_gb):
        errors["INVALID_RESOURCE"] = (
            "Resources must be finite and nonnegative, with integer CPU and GPU counts."
        )

    duration = job.duration_minutes
    release = job.release_minute
    deadline = job.deadline_minute
    duration_valid = _is_integer(duration) and duration > 0
    window_valid = (
        _is_integer(release) and release >= 0
        and _is_integer(deadline) and deadline > release
    )
    if not duration_valid:
        errors["INVALID_DURATION"] = "Duration must be a positive integer."
    if not window_valid:
        errors["INVALID_TIME"] = "Release and deadline must be integers with 0 <= release < deadline."
    elif duration_valid and duration > deadline - release:
        errors["INVALID_TIME"] = "Duration exceeds the time between release and deadline."
    if any(_is_integer(value) and value % slot for value in (duration, release, deadline)):
        errors["MISALIGNED_TIME"] = "Duration, release and deadline must align to the slot grid."

    if job.required_server_id is not None and not _is_id(job.required_server_id):
        errors["INVALID_FIELD"] = "required_server_id must be a nonempty string or None."
    for name in _RELATIONSHIP_FIELDS:
        targets = getattr(job, name)
        if not isinstance(targets, (tuple, list)) or not all(map(_is_id, targets)):
            errors.setdefault("INVALID_FIELD", f"{name} must be a list or tuple of nonempty string IDs.")
    return errors

def validate_jobs(jobs: Sequence[RawJob], config: SchedulerConfig) -> tuple[tuple[Job, ...], tuple[InvalidJob, ...]]:
    """Return valid normalized jobs and indexed errors, preserving submission order.

    Reject missing/unknown fields, wrong types, empty IDs, all duplicate-ID
    occurrences, nonfinite/negative resources, bool numeric values, nonpositive
    duration, noninteger/misaligned times, negative release, and duration exceeding
    deadline-release. Default release=0/deadline=horizon. Beyond-horizon release or
    deadline remains valid if internally consistent; domain generation clips to
    the horizon. Lack of suitable hardware is not an input error. Do not mutate
    raw records. Stable error codes include MISSING_FIELD, DUPLICATE_ID,
    INVALID_RESOURCE, INVALID_DURATION, INVALID_TIME, MISALIGNED_TIME.

    Args:
        jobs: Original submissions in input order, including raw malformed records.
            Per-record identity is the zero-based position in this sequence.
        config: Scheduling settings defining the integer-minute horizon, slot resolution
            and solver options.

    Returns:
        tuple[tuple[Job, ...], tuple[InvalidJob, ...]]: Normalized valid jobs and
            per-record structured errors. Each malformed or duplicate submission retains
            its original index; omitted defaults are resolved from config.
    """
    job_ids = tuple(map(_raw_job_id, jobs))
    counts = Counter(job_id for job_id in job_ids if job_id is not None)
    valid_jobs = []
    invalid_jobs = []
    for index, (record, job_id) in enumerate(zip(jobs, job_ids, strict=True)):
        errors = {}
        if counts[job_id] > 1:
            errors["DUPLICATE_ID"] = f"Job ID {job_id!r} occurs more than once."

        job = None
        if isinstance(record, Job):
            job = record
        elif isinstance(record, Mapping):
            missing = [name for name in _REQUIRED_JOB_FIELDS if name not in record]
            unknown = record.keys() - _JOB_FIELDS
            if missing:
                errors["MISSING_FIELD"] = f"Missing fields: {', '.join(missing)}."
            if unknown:
                errors["UNKNOWN_FIELD"] = f"Unknown fields: {', '.join(sorted(map(repr, unknown)))}."
            if not missing:
                job = Job(**{name: record[name] for name in record.keys() & _JOB_FIELDS})
        else:
            errors["INVALID_RECORD"] = "Job submission must be a Job or a mapping."

        if job is not None:
            if job.deadline_minute is None:
                job = replace(job, deadline_minute=config.horizon_minutes)
            errors.update(_job_errors(job, config.slot_minutes))
        if errors:
            invalid_jobs.append(InvalidJob(index, job_id, tuple(errors), tuple(errors.values())))
        else:
            valid_jobs.append(replace(
                job,
                same_server_as=tuple(job.same_server_as),
                different_server_from=tuple(job.different_server_from),
            ))
    return tuple(valid_jobs), tuple(invalid_jobs)

def validate_references(jobs: Sequence[Job], servers: Sequence[Server], invalid_jobs: Sequence[InvalidJob] = (), *, input_indices: Mapping[str, int]) -> tuple[tuple[Job, ...], tuple[InvalidJob, ...]]:
    """Normalize direct edges symmetrically; return survivors and additional errors.

    Reject unknown server/job IDs, self anti-affinity, and the same direct pair
    requesting both same and different servers (invalidate both endpoints).
    Self co-location is redundant and removed. Repeated direct edges are
    deduplicated without changing their meaning. A known invalid target is omitted,
    not cascaded into invalidity. Unknown-reference errors belong to the declarer.
    Use input_indices (valid unique ID to original index) for indexed errors.
    Never take transitive closure: A=B and B=C impose no A=C constraint if B is
    skipped. Opposite pins on a same-server pair and longer contradictory cycles
    are valid inputs restricting which subsets can be scheduled.
    Codes: UNKNOWN_SERVER, UNKNOWN_JOB, CONTRADICTORY_RELATIONSHIP.

    Args:
        jobs: Individually valid normalized jobs before reference normalization;
            original IDs and indices remain available for attribution.
        servers: Server inventory in original input order; an empty inventory is
            permitted.
        invalid_jobs: Errors already associated with original submissions; their IDs
            distinguish known invalid targets from unknown references.
        input_indices: Mapping from each valid unique job ID to its original zero-based
            submission index, before invalid records were removed.

    Returns:
        tuple[tuple[Job, ...], tuple[InvalidJob, ...]]: Surviving jobs with symmetric
            direct edges, and newly discovered indexed reference errors. Previously
            supplied errors remain the caller's responsibility to merge by index.
    """
    server_ids = {server.server_id for server in servers}
    job_ids = {job.job_id for job in jobs}
    known_ids = job_ids | {error.job_id for error in invalid_jobs}
    same = {job.job_id: set() for job in jobs}
    different = {job.job_id: set() for job in jobs}
    errors_by_id = {}

    for job in jobs:
        job_id = job.job_id
        errors = {}
        pin = job.required_server_id
        if pin is not None and pin not in server_ids:
            errors["UNKNOWN_SERVER"] = f"Unknown server ID {pin!r}."
        unknown_targets = set()
        for targets, edges in (
            (job.same_server_as, same), (job.different_server_from, different),
        ):
            for target in targets:
                if target not in known_ids:
                    unknown_targets.add(target)
                elif target in job_ids and (target != job_id or edges is different):
                    edges[job_id].add(target)
                    edges[target].add(job_id)
        if unknown_targets:
            names = ", ".join(map(repr, sorted(unknown_targets)))
            errors["UNKNOWN_JOB"] = f"Unknown job IDs: {names}."
        if errors:
            errors_by_id[job_id] = errors

    for job in jobs:
        job_id = job.job_id
        conflicts = same[job_id] & different[job_id]
        if job_id in different[job_id]:
            conflicts.add(job_id)
        if conflicts:
            names = ", ".join(map(repr, sorted(conflicts, key=input_indices.__getitem__)))
            errors_by_id.setdefault(job_id, {})["CONTRADICTORY_RELATIONSHIP"] = (
                f"Conflicting relationships with job IDs: {names}."
            )

    survivors = []
    new_errors = []
    invalid_ids = set(errors_by_id)
    original_index = input_indices.__getitem__
    for job in jobs:
        job_id = job.job_id
        if job_id in errors_by_id:
            errors = errors_by_id[job_id]
            new_errors.append(
                InvalidJob(input_indices[job_id], job_id, tuple(errors), tuple(errors.values()))
            )
        else:
            survivors.append(replace(
                job,
                same_server_as=tuple(sorted(same[job_id] - invalid_ids, key=original_index)),
                different_server_from=tuple(sorted(different[job_id] - invalid_ids, key=original_index)),
            ))
    return tuple(survivors), tuple(new_errors)

def preprocess_inputs(jobs: Sequence[RawJob], servers: Sequence[Server], config: SchedulerConfig) -> PreparedInstance:
    """Validate global inputs, classify every raw record, normalize references,
    construct initial domains and freeze the result without mutating callers.

    Every input index must occur exactly once among valid jobs and errors. Error
    records merge codes per submission. Build relationship normalization from
    original direct declarations, then remove invalid endpoints without cascading.

    Args:
        jobs: Original submissions in input order, including raw malformed records.
            Per-record identity is the zero-based position in this sequence.
        servers: Server inventory in original input order; an empty inventory is
            permitted.
        config: Scheduling settings defining the integer-minute horizon, slot resolution
            and solver options.

    Returns:
        PreparedInstance: Deeply immutable preparation with initial domains, merged
            indexed errors and one accounted identity for every original submission.

    Raises:
        ValueError: Configuration or server inventory is invalid. Individual job errors
            are returned in the prepared instance.
    """
    validate_config(config)
    inventory = validate_servers(servers)
    valid_jobs, field_errors = validate_jobs(jobs, config)
    errors_by_index = {error.input_index: error for error in field_errors}
    valid_indices = (index for index in range(len(jobs)) if index not in errors_by_index)
    input_indices = {
        job.job_id: index for job, index in zip(valid_jobs, valid_indices, strict=True)
    }
    survivors, reference_errors = validate_references(
        valid_jobs, inventory, field_errors, input_indices=input_indices,
    )
    for error in reference_errors:
        previous = errors_by_index.get(error.input_index)
        if previous is not None:
            error = replace(
                previous,
                error_codes=previous.error_codes + error.error_codes,
                reasons=previous.reasons + error.reasons,
            )
        errors_by_index[error.input_index] = error

    domains = InitialDomainBuilder().build_domains(survivors, inventory, config)
    return PreparedInstance(
        jobs=survivors,
        servers=inventory,
        config=config,
        invalid_jobs=tuple(errors_by_index[index] for index in sorted(errors_by_index)),
        input_indices=tuple((job.job_id, input_indices[job.job_id]) for job in survivors),
        submitted_count=len(jobs),
        domains=tuple((job.job_id, domains[job.job_id]) for job in survivors),
    )
