#!/usr/bin/env python3
"""
Baseline greedy scheduler — phuong_phap_danh_gia.md §2.1.

Spec (§2.1):
  1. Sort assignments by deadline_day asc, then priority desc.
  2. Iterate day 0..horizon-1, slot 0..2 (Morning, Afternoon, Evening).
  3. Fill each slot from the head of the list until available_hours is full.
  4. If an assignment is unfinished, move to the next.
  5. No tod_factor awareness (by design — the difference vs LP).

Output schedule: [{subject_id, day, slot, hours}]  (same shape as LP solver)

Feasibility: Greedy fails if it cannot schedule anything before deadline,
or if an assignment is left with 0 hours planned (treated as infeasible so
Feasibility Rate reflects the doc's expectation: Greedy fails on Extreme).
"""
from __future__ import annotations

MIN_SESSION_HOURS = 0.5


def solve_greedy(scenario: dict) -> dict:
    """Greedy per §2.1. Returns {status, feasible, schedule, objective_value...}.

    objective_value for Greedy is computed as raw hours (no diminishing
    returns) so it is comparable to LP's Z only qualitatively — the thesis
    chart uses LP's own Z for LP and raw hours for Greedy (§3.4).
    """
    subjects = list(scenario["subjects"])
    time_slots = sorted(scenario["time_slots"], key=lambda s: (s["day"], s["slot"]))
    # §2.1 step 1: deadline nearest first, priority desc.
    ordered = sorted(subjects, key=lambda s: (s["deadline_day"], -s["priority"]))

    # Track remaining hours per assignment.
    remaining = {s["id"]: float(s["required_hours"]) for s in subjects}
    schedule: list[dict] = []

    for ts in time_slots:
        day, slot, avail = ts["day"], ts["slot"], float(ts["available_hours"])
        for s in ordered:
            if avail <= 1e-9:
                break
            sid = s["id"]
            if remaining[sid] <= 1e-9:
                continue
            if day > s["deadline_day"]:
                continue  # C6 hard rule — even Greedy never studies after deadline
            hours = min(avail, remaining[sid])
            if hours < MIN_SESSION_HOURS:
                # Either take it as a tiny tail (if it finishes the assignment)
                # or skip to avoid fragment < min session.
                if remaining[sid] - hours > 1e-9:
                    continue
                hours = remaining[sid]  # finish it
            schedule.append({"subject_id": sid, "day": day, "slot": slot,
                             "hours": round(hours, 4)})
            remaining[sid] -= hours
            avail -= hours

    planned = {s["id"]: 0.0 for s in subjects}
    for e in schedule:
        planned[e["subject_id"]] += e["hours"]

    # Feasible iff every assignment got at least some hours before deadline.
    # (If total_required >> capacity, Greedy will still return a schedule but
    # with shortfall — we count feasible=True but shortfall>0, matching §3.1.)
    feasible = all(v > 1e-9 for v in planned.values())
    status = "optimal" if feasible else "infeasible"
    return {
        "status": status,
        "feasible": feasible,
        "schedule": schedule,
        "objective_value": round(sum(planned.values()), 4),  # raw hours, no f()
        "planned_hours": planned,
    }
