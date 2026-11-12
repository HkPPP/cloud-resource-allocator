"""Mutable scheduling state and reversible resource accounting interfaces."""
from __future__ import annotations
from typing import Mapping
from .models import Assignment, Job, Placement, ResourceVector
from .preprocessing import PreparedInstance

class ScheduleState:
    """Track server/slot usage with exact reversible updates.

    Invariants: no negative/over-capacity usage, each job assigned once, intervals
    occupy start//slot through end//slot exclusively, and failed operations are atomic."""

    def __init__(self, prepared: PreparedInstance) -> None:
        """Initialize empty assignments and zero usage using immutable prepared inputs.
        Each state owns all its mutable arrays; do not share them between solvers."""
        raise NotImplementedError('ScheduleState.__init__ is not implemented.')

    def can_place(self, job: Job, placement: Placement) -> bool:
        """Perform all hard checks without mutations; delegate shared checking logic."""
        raise NotImplementedError('ScheduleState.can_place is not implemented.')

    def place(self, job: Job, placement: Placement) -> Assignment:
        """Atomically assign a feasible placement and increment every occupied slot.
        Raise ValueError on infeasibility or duplicate job; leave state unchanged."""
        raise NotImplementedError('ScheduleState.place is not implemented.')

    def undo(self, job_id: str) -> None:
        """Remove an existing assignment and restore exact prior resource usage.
        Raise KeyError for an absent job without changing state; undo is not idempotent."""
        raise NotImplementedError('ScheduleState.undo is not implemented.')

    def get_usage(self, server_id: str, minute: int) -> ResourceVector:
        """Return a snapshot for the slot containing minute (0 <= minute < horizon).
        Raise KeyError for unknown server, ValueError outside horizon; no mutable aliases."""
        raise NotImplementedError('ScheduleState.get_usage is not implemented.')

    def get_assignments(self) -> Mapping[str, Assignment]:
        """Return an immutable view or detached snapshot keyed by unique valid job ID."""
        raise NotImplementedError('ScheduleState.get_assignments is not implemented.')

    def copy(self) -> ScheduleState:
        """Return an independent mutable copy; prepared immutable input may be shared.
        Mutating or undoing either state must not affect the other."""
        raise NotImplementedError('ScheduleState.copy is not implemented.')
