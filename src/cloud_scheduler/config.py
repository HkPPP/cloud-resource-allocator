"""Scheduling configuration and validation contracts."""
from dataclasses import dataclass
from math import isfinite

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

        Args:
            None. Uses the current instance only.

        Returns:
            None: Successful validation has no return value and does not modify the
                frozen configuration.

        Raises:
            ValueError: A type, range, resolution, objective or option-combination rule
                is violated.
        """
        for name in ("horizon_minutes", "slot_minutes"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
        if self.horizon_minutes % self.slot_minutes:
            raise ValueError("slot_minutes must evenly divide horizon_minutes.")

        if not isinstance(self.objectives, tuple) or not self.objectives:
            raise ValueError("objectives must be a nonempty tuple of supported names.")
        if any(not isinstance(name, str) or name not in OBJECTIVE_NAMES
               for name in self.objectives):
            raise ValueError("objectives contains an unsupported objective name.")
        if len(set(self.objectives)) != len(self.objectives):
            raise ValueError("objectives must not contain duplicates.")

        timeout = self.search_timeout_seconds
        if timeout is not None:
            if (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                    or timeout <= 0 or (isinstance(timeout, float) and not isfinite(timeout))):
                raise ValueError("search_timeout_seconds must be positive and finite, or None.")

        for name in ("use_mrv", "use_forward_checking", "use_backjumping", "use_mac"):
            if not isinstance(getattr(self, name), bool):
                raise ValueError(f"{name} must be a boolean.")
        if self.use_mac and self.use_backjumping:
            raise ValueError("MAC and backjumping cannot both be enabled.")
