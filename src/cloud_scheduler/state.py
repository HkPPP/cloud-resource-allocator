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
        Each state owns all its mutable arrays; do not share them between solvers.

        Args:
            prepared: Immutable normalized input containing valid jobs, servers,
                configuration, initial domains, indexed errors and original submission
                identities.

        Returns:
            None: Initializes the current state with no assignments and zero resource
                usage; does not change the prepared input.
        """
        self.prepared = prepared

        self._servers = {
            server.server_id: server for server in prepared.servers
        }

        self._assignments: dict[str, Assignment] = {}

        slot_count = (
            prepared.config.horizon_minutes // prepared.config.slot_minutes
        )

        self._usage: dict[str, list[ResourceVector]] = {
            server_id: [
                ResourceVector() for _ in range(slot_count)
            ]
            for server_id in self._servers
        }


    def can_place(self, job: Job, placement: Placement) -> bool:
        """Perform all hard checks without mutations; delegate shared checking logic.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.

        Returns:
            bool: Whether all hard constraints permit this placement without changing
                assignments, domains or usage.
        """
        # Prevent circular import 
        from .constraints import ConstraintChecker

        checker = ConstraintChecker()
        return checker.can_place(job, placement, self)


    def place(self, job: Job, placement: Placement) -> Assignment:
        """Atomically assign a feasible placement and increment every occupied slot.
        Raise ValueError on infeasibility or duplicate job; leave state unchanged.

        Args:
            job: Validated job whose resource demands, time window and placement
                relationships are being examined.
            placement: Candidate server ID and integer start minute; the job end is
                start plus its duration.

        Returns:
            Assignment: Newly committed assignment with exclusive end time and original
                input index. All occupied slots are updated atomically.

        Raises:
            ValueError: The placement is infeasible or the job already has an
                assignment; state remains unchanged.
        """
        if not self.can_place(job, placement):
            raise ValueError(
                f"Cannot place job {job.job_id} on {placement.server_id}"
            )

        slot_minutes = self.prepared.config.slot_minutes
        start = placement.start_minute
        end = start + job.duration_minutes

        first_slot = start // slot_minutes
        end_slot = end // slot_minutes

        # Calculate changes in a separate list first.
        updated_usage = self._usage[placement.server_id].copy()

        for slot in range(first_slot, end_slot):
            current = updated_usage[slot]

            updated_usage[slot] = ResourceVector(
                cpu=current.cpu + job.cpu,
                ram_gb=current.ram_gb + job.ram_gb,
                gpu=current.gpu + job.gpu,
                storage_gb=current.storage_gb + job.storage_gb,
            )

        input_indices = dict(self.prepared.input_indices)

        assignment = Assignment(
            job_id=job.job_id,
            server_id=placement.server_id,
            start_minute=start,
            end_minute=end,
            input_index=input_indices[job.job_id],
        )

        # Commit after validation and calculations have succeeded.
        self._usage[placement.server_id] = updated_usage
        self._assignments[job.job_id] = assignment

        return assignment

    def undo(self, job_id: str) -> None:
        """Remove an existing assignment and restore exact prior resource usage.
        Raise KeyError for an absent job without changing state; undo is not idempotent.

        Args:
            job_id: Unique valid job ID identifying the existing assignment to remove.

        Returns:
            None: Removes the assignment and restores exact prior occupied-slot usage
                while preserving every other assignment.

        Raises:
            KeyError: job_id is not currently assigned; state remains unchanged.
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ScheduleState.undo is not implemented.')

    def get_usage(self, server_id: str, minute: int) -> ResourceVector:
        """Return a snapshot for the slot containing minute (0 <= minute < horizon).
        Raise KeyError for unknown server, ValueError outside horizon; no mutable
        aliases.

        Args:
            server_id: ID of a server in the prepared inventory.
            minute: Integer minute in [0, horizon_minutes); non-boundary minutes select
                their containing slot.

        Returns:
            ResourceVector: Read-only value snapshot for the selected server and
                containing slot, including all concurrently assigned jobs.

        Raises:
            KeyError: server_id is absent from the inventory.
            TypeError: minute is not an int type
            ValueError: minute is outside the configured horizon.
        """
        if server_id not in self._servers:
            raise KeyError(server_id)

        if isinstance(minute, bool) or not isinstance(minute, int):
            raise TypeError(f"Minute must be an integer, not {type(minute)}")

        horizon = self.prepared.config.horizon_minutes
        if not (0 <= minute < horizon):
            raise ValueError(f"Minute is outside the scheduling horizon of 0 and {horizon}")

        slot_index = minute // self.prepared.config.slot_minutes
        return self._usage[server_id][slot_index]

    def get_usage_by_slot(self, server_id: str, slot_index: int) -> ResourceVector:
        """Return resource usage for a specific server and slot.
        Args:
            server_id: ID of a server in the prepared inventory.
            slot_index: Zero-based slot index, from 0 through slot_count - 1.

        Returns:
            ResourceVector: Immutable resource usage for the selected slot,
                including all concurrently assigned jobs.

        Raises:
            KeyError: The server ID is unknown.
            TypeError: slot_index is not an integer, or is a boolean.
            ValueError: slot_index is outside the available slots.
        """
        if server_id not in self._servers:
            raise KeyError(server_id)

        if isinstance(slot_index, bool) or not isinstance(slot_index, int):
            raise TypeError(f"Minute must be an integer, not {type(slot_index)}")

        usage = self._usage[server_id]

        if not 0 <= slot_index < len(usage):
            raise ValueError("slot_index is outside the available slots")

        return usage[slot_index]

    def get_assignments(self) -> Mapping[str, Assignment]:
        """Return an immutable view or detached snapshot keyed by unique valid job ID.

        Args:
            None. Uses the current instance only.

        Returns:
            Mapping[str, Assignment]: Read-only view or detached snapshot of assigned
                jobs. Changes through a returned object cannot alter state.
        """
        return self._assignments.copy()

    def copy(self) -> ScheduleState:
        """Return an independent mutable copy; prepared immutable input may be shared.
        Mutating or undoing either state must not affect the other.

        Args:
            None. Uses the current instance only.

        Returns:
            ScheduleState: Independent state with identical assignments and usage;
                immutable prepared data may be shared.

        Raises:
            NotImplementedError: This feature is not yet implemented.
        """
        raise NotImplementedError('ScheduleState.copy is not implemented.')
