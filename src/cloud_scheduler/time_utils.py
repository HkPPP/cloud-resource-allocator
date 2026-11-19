"""Shared time-slot calculations."""

from .config import SchedulerConfig
from .models import Job, Placement


def occupied_slots(
    job: Job,
    placement: Placement,
    config: SchedulerConfig,
) -> range:
    """Calculate the slot indices occupied by a validated placement.

    Args:
        job: Validated job providing the duration in minutes.
        placement: Candidate placement providing the start minute.
        config: Configuration providing the slot length in minutes.

    Returns:
        range: Occupied slot indices, excluding the slot at the interval's end.
            Assumes aligned times and an interval within the horizon.
    """
    start_slot = placement.start_minute // config.slot_minutes
    end_slot = (placement.start_minute + job.duration_minutes) // config.slot_minutes

    return range(start_slot, end_slot)