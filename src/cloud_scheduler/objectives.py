"""Lexicographic objectives for complete feasible schedules, including omissions."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Mapping, Sequence
from .models import Assignment, Job

class Direction(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"

class Objective(ABC):
    """Extension point: pure scalar evaluation, explicit direction, no weights."""
    name: str
    direction: Direction

    @abstractmethod
    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Evaluate a complete feasible schedule; never mutate assignments or jobs.

        Omitted jobs contribute nothing; empty schedules have value zero.
        Capacity and status validity are established independently before evaluation.

        Args:
            assignments: Complete feasible assignments, keyed by job ID when a mapping
                is required. Omitted jobs have no assignment.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            float: Objective scalar for the complete feasible schedule; omitted jobs
                contribute nothing and empty schedules evaluate to zero.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Objective evaluation is not implemented.')

class MaxJobs(Objective):
    """Maximize the number of assignments, each representing a distinct valid job."""
    name = "max_jobs"
    direction = Direction.MAXIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Return assignment count for this complete feasible schedule; empty -> 0.

        Args:
            assignments: Complete feasible assignments, keyed by job ID when a mapping
                is required. Omitted jobs have no assignment.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            float: Number of distinct assigned jobs; larger values are better.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Scheduled-job count is not implemented.')

class MinWait(Objective):
    """Minimize total start-release over scheduled jobs, not average waiting time."""
    name = "min_wait"
    direction = Direction.MINIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Sum nonnegative waiting minutes for assigned jobs; omitted jobs add zero.

        Args:
            assignments: Complete feasible assignments, keyed by job ID when a mapping
                is required. Omitted jobs have no assignment.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            float: Total start_minute - release_minute across assigned jobs, in minutes;
                smaller values are better.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Total waiting time is not implemented.')

class MinActiveServers(Objective):
    """Minimize distinct server IDs used anywhere in the full horizon."""
    name = "min_active_servers"
    direction = Direction.MINIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Count servers with at least one assignment, regardless of overlap; empty -> 0.

        Args:
            assignments: Complete feasible assignments, keyed by job ID when a mapping
                is required. Omitted jobs have no assignment.
            jobs: Mapping from unique valid job IDs to job definitions; relationships
                are direct edges and release times are measured in integer minutes.

        Returns:
            float: Number of distinct server IDs hosting assignments anywhere in the
                horizon; smaller values are better.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('Active server count is not implemented.')

def compare_schedules(left: Sequence[Assignment], right: Sequence[Assignment], jobs: Mapping[str, Job], objectives: Sequence[str]) -> int:
    """Return +1 if left is better, -1 if worse, 0 if tied, lexicographically.

    The first unequal objective decides using its own direction; no weighted sum.
    Reject unknown, duplicate or empty objectives with ValueError. Recommended
    max_jobs,min_wait prevents fewer jobs from winning merely through lower wait.
    Alternate min_wait/min_active_servers first may intentionally prefer empty
    schedules. Full ties do not imply identical assignments or unique optima.

    Args:
        left: First complete feasible schedule to compare; assignments need not be in
            job order.
        right: Second complete feasible schedule, evaluated against the same job
            definitions and objective priorities.
        jobs: Mapping from unique valid job IDs to job definitions; relationships are
            direct edges and release times are measured in integer minutes.
        objectives: Nonempty ordered sequence of unique supported objective names,
            highest priority first.

    Returns:
        int: +1 when left is preferred, -1 when right is preferred, or 0 when all
            objective values tie. The first unequal objective decides using its own
            direction.

    Raises:
        ValueError: Objective names are unknown, duplicated, or the ordering is empty.
        NotImplementedError: This feature is not yet implemented.
    """
    raise NotImplementedError('Lexicographic comparison is not implemented.')
