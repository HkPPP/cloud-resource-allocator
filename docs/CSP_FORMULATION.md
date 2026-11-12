# CSP formulation

For each valid job j, define X_j in D_j = {(server,start)} union {UNASSIGNED}.
Slots are integer minutes t=k*slot, 0<=k<horizon/slot. Candidate intervals are
[start,start+duration); end is excluded. Durations/releases/deadlines align with
slots. Filter individual hardware, pin, release, deadline and horizon constraints.
Do not initially remove candidates based on assignments that have not happened.

For each server s, occupied slot k and resource r:

sum(demand[j,r] for assigned j on s covering k) <= capacity[s,r].

CPU/RAM/GPU/storage are cumulative; concurrent jobs are allowed. Boundary-touching
intervals share no slots. Each scheduled job has exactly one continuous interval.
Pins select one server. Direct same/different-server edges compare server identity
only when both endpoints are scheduled, regardless of temporal overlap. They are
symmetric but are not transitively closed across omitted intermediates.

UNASSIGNED consumes nothing, has no placement relationship obligations and is
always retained. A domain containing only UNASSIGNED is feasible. Invalid jobs
are excluded before defining variables; unschedulable hardware requests are valid
variables with no real placements. An all-omitted schedule is feasible.

Compare complete feasible schedules lexicographically with each objective's
explicit direction. max_jobs maximizes scheduled count; min_wait minimizes total
start-release for assigned jobs; min_active_servers minimizes distinct used IDs.
All three evaluate empty schedules to zero. The first unequal objective decides;
full ties return equality. Recommended max_jobs,min_wait prevents lower count
from winning through omission. Alternative priorities can favor empty schedules.
Branch-and-bound requires sound optimistic bounds for the full ordered vector;
partial-schedule objective values alone are not valid general pruning bounds.

Binary arc consistency does not express cumulative resource feasibility when
three or more jobs share capacity. MAC remains optional and unimplemented until
its global constraints or equivalent representation are explicitly designed.
