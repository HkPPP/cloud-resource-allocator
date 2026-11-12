"""Scheduling configuration and validation contracts."""
from dataclasses import dataclass

OBJECTIVE_NAMES = frozenset({"max_jobs", "min_wait", "min_active_servers"})

@dataclass(frozen=True)
class SchedulerConfig:
    """Immutable options shared by all algorithms.

    horizon/slot are positive integers (not bool); slot evenly divides horizon.
    Objectives are a nonempty tuple of unique supported names, highest priority
    first. None timeout means unlimited; otherwise use positive finite seconds.
    All technique flags are bool. MRV, FC, backjumping and MAC default off.
    Optional unsupported techniques must raise NotImplementedError when enabled,
    never silently fall back to another solver. MAC and backjumping may not both
    be enabled until their joint semantics are designed.
    """
    horizon_minutes: int = 1440
    slot_minutes: int = 15
    objectives: tuple[str, ...] = ("max_jobs", "min_wait")
    search_timeout_seconds: float | None = None
    use_mrv: bool = False
    use_forward_checking: bool = False
    use_backjumping: bool = False
    use_mac: bool = False

    def validate(self) -> None:
        """Raise ValueError for any invalid configuration; return None otherwise.

        Validate the rules above before job validation; configuration errors abort
        a run and must not be converted to individual INVALID job records.
        """
        raise NotImplementedError('Configuration validation is not implemented.')
