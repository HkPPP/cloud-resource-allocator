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
        """
        raise NotImplementedError('Objective evaluation is not implemented.')

class MaxJobs(Objective):
    """Maximize the number of assignments, each representing a distinct valid job."""
    name = "max_jobs"
    direction = Direction.MAXIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Return assignment count for this complete feasible schedule; empty -> 0."""
        raise NotImplementedError('Scheduled-job count is not implemented.')

class MinWait(Objective):
    """Minimize total start-release over scheduled jobs, not average waiting time."""
    name = "min_wait"
    direction = Direction.MINIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Sum nonnegative waiting minutes for assigned jobs; omitted jobs add zero."""
        raise NotImplementedError('Total waiting time is not implemented.')

class MinActiveServers(Objective):
    """Minimize distinct server IDs used anywhere in the full horizon."""
    name = "min_active_servers"
    direction = Direction.MINIMIZE

    def evaluate(self, assignments: Sequence[Assignment], jobs: Mapping[str, Job]) -> float:
        """Count servers with at least one assignment, regardless of overlap; empty -> 0."""
        raise NotImplementedError('Active server count is not implemented.')

def compare_schedules(left: Sequence[Assignment], right: Sequence[Assignment], jobs: Mapping[str, Job], objectives: Sequence[str]) -> int:
    """Return +1 if left is better, -1 if worse, 0 if tied, lexicographically.

    The first unequal objective decides using its own direction; no weighted sum.
    Reject unknown, duplicate or empty objectives with ValueError. Recommended
    max_jobs,min_wait prevents fewer jobs from winning merely through lower wait.
    Alternate min_wait/min_active_servers first may intentionally prefer empty
    schedules. Full ties do not imply identical assignments or unique optima.
    """
    raise NotImplementedError('Lexicographic comparison is not implemented.')
