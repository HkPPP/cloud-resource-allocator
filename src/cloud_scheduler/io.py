"""Portable UTF-8 JSON transport and semantic loading interfaces."""
import json
from dataclasses import fields
from pathlib import Path
from typing import Sequence
from .config import SchedulerConfig
from .models import RawJob, Server
from .preprocessing import validate_servers

PathLike = str | Path

def read_json(path: PathLike) -> object:
    """Read UTF-8 JSON (including Windows BOM); preserve raw per-job records.

    File errors propagate as OSError, syntax errors as JSONDecodeError. Resource
    finiteness and schema validation belong to preprocessing, not this transport.

    Args:
        path: Input or output filesystem path as str or pathlib.Path; relative paths are
            resolved from the current working directory.

    Returns:
        object: Decoded JSON root, preserving arrays, objects, scalars and null without
            schema conversion.

    Raises:
        OSError: The file cannot be opened or read.
        json.JSONDecodeError: The file does not contain syntactically valid JSON.
    """
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)

def write_json(path: PathLike, value: object) -> None:
    """Write JSON-compatible data as UTF-8 with LF; reject NaN/infinity.

    Parent directories must exist. Serialization/file errors propagate; callers
    explicitly convert dataclasses/enums, avoiding hidden lossy coercion.

    Args:
        path: Input or output filesystem path as str or pathlib.Path; relative paths are
            resolved from the current working directory.
        value: JSON-compatible value to serialize. Nonfinite floats are rejected rather
            than emitted as nonstandard JSON.

    Returns:
        None: Writes indented UTF-8 JSON with LF endings and a trailing newline; parent
            directories must already exist.

    Raises:
        OSError: The destination cannot be written.
        ValueError: A nonfinite float is present.
        TypeError: A value cannot be serialized as JSON.
    """
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")

def load_config(path: PathLike) -> SchedulerConfig:
    """Read a config object, convert objectives to tuple, reject unknown keys and
    types, then validate. Structural type errors raise TypeError; invalid keys
    and settings raise ValueError.

    Args:
        path: Input or output filesystem path as str or pathlib.Path; relative paths are
            resolved from the current working directory.

    Returns:
        SchedulerConfig: Configuration with JSON objective arrays converted to tuples
            and semantic validation completed.

    Raises:
        ValueError: Keys or values are invalid.
        TypeError: The root is not an object or objectives is not an array.
        OSError: The input cannot be read.
    """
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise TypeError("Configuration must be a JSON object.")

    unknown = payload.keys() - {item.name for item in fields(SchedulerConfig)}
    if unknown:
        raise ValueError(f"Unknown configuration fields: {', '.join(sorted(unknown))}.")

    if "objectives" in payload:
        if not isinstance(payload["objectives"], list):
            raise TypeError("Configuration objectives must be a JSON array.")
        payload["objectives"] = tuple(payload["objectives"])

    config = SchedulerConfig(**payload)
    config.validate()
    return config

def load_servers(path: PathLike) -> tuple[Server, ...]:
    """Read a JSON array of server objects, construct and validate in input order.
    Structural type errors raise TypeError. Invalid record fields, IDs and
    capacities raise ValueError; file/JSON errors propagate.

    Args:
        path: Input or output filesystem path as str or pathlib.Path; relative paths are
            resolved from the current working directory.

    Returns:
        tuple[Server, ...]: Constructed and validated inventory in original file order.

    Raises:
        TypeError: The root is not an array or a server record is not an object.
        ValueError: Server fields, IDs or resource quantities are invalid.
        OSError: The input cannot be read.
    """
    payload = read_json(path)
    if not isinstance(payload, list):
        raise TypeError("Server inventory must be a JSON array.")

    servers = []
    for index, record in enumerate(payload):
        if not isinstance(record, dict):
            raise TypeError(f"Server at index {index} must be a JSON object.")
        try:
            servers.append(Server(**record))
        except TypeError as error:
            raise ValueError(f"Invalid server fields at index {index}: {error}") from error

    return validate_servers(servers)

def load_jobs(path: PathLike) -> Sequence[RawJob]:
    """Read an array, preserving malformed entries and original indices for
    preprocessing; reject a non-array root with TypeError. Never construct Job
    eagerly in a way that aborts a batch on a missing field.

    Args:
        path: Input or output filesystem path as str or pathlib.Path; relative paths are
            resolved from the current working directory.

    Returns:
        Sequence[RawJob]: Raw JSON array elements in file order, including malformed
            individual entries for indexed preprocessing errors.

    Raises:
        TypeError: The file root is not a JSON array.
        OSError: The input cannot be read.
    """
    payload = read_json(path)
    if not isinstance(payload, list):
        raise TypeError("Job input must be a JSON array.")
    return payload
