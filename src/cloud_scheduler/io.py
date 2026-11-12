"""Portable UTF-8 JSON transport and semantic loading interfaces."""
import json
from pathlib import Path
from typing import Sequence
from .config import SchedulerConfig
from .models import RawJob, Server

PathLike = str | Path

def read_json(path: PathLike) -> object:
    """Read UTF-8 JSON (including Windows BOM); preserve raw per-job records.

    File errors propagate as OSError, syntax errors as JSONDecodeError. Resource
    finiteness and schema validation belong to preprocessing, not this transport.
    """
    with Path(path).open(encoding="utf-8-sig") as stream:
        return json.load(stream)

def write_json(path: PathLike, value: object) -> None:
    """Write JSON-compatible data as UTF-8 with LF; reject NaN/infinity.

    Parent directories must exist. Serialization/file errors propagate; callers
    explicitly convert dataclasses/enums, avoiding hidden lossy coercion.
    """
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")

def load_config(path: PathLike) -> SchedulerConfig:
    """Read a config object, convert objectives to tuple, reject unknown keys and
    types, then validate. Raise ValueError for malformed semantic configuration.
    """
    raise NotImplementedError('Configuration loading is not implemented.')

def load_servers(path: PathLike) -> tuple[Server, ...]:
    """Read a JSON array of server objects, construct and validate in input order.
    Raise ValueError for invalid inventory; file/JSON errors propagate.
    """
    raise NotImplementedError('Inventory loading is not implemented.')

def load_jobs(path: PathLike) -> Sequence[RawJob]:
    """Read an array, preserving malformed entries and original indices for
    preprocessing; reject a non-array root with ValueError. Never construct Job
    eagerly in a way that aborts a batch on a missing field.
    """
    raise NotImplementedError('Raw job loading is not implemented.')
