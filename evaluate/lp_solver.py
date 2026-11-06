#!/usr/bin/env python3
"""
Local MILP solver — replica of Tier 3 (lp-solver/app/model.py).

Implements the exact model described in tier-3-overview.md:
  Variables: x[i,d,t] >= 0, y[i,d,t] in {0,1}, delta[i,d,k] in [0,width_k],
             s[i] >= 0 (deadline slack), u[d] >= 0 (daily-cap slack)
  Objective: Maximize Z = sum_i E[i]*f(X_eff[i,d]) - 20*sum(s) - 100*sum(u)
             E[i] = urgency * difficulty * priority, urgency = 1/(1+deadline_day)
             f = sqrt approximated with 4 linear segments on [0,4]
             slopes = 1.414, 0.586, 0.414, 0.293 (boundaries 0,.5,1,2,4)
  X_eff[i,d] = sum_t tod_factor[t] * x[i,d,t]
  Constraints C1..C7 per tier-3-overview.md; C2/C3 are soft via u[d]/s[i].

Uses PuLP + CBC (same as production). Runs locally so evaluation does not
need Docker containers.
"""
from __future__ import annotations

import pulp

# Piecewise approximation of sqrt(x) on [0,4] — tier-3-overview.md §Xấp xỉ.
BREAKPOINTS = [(0.0, 0.5, 1.414), (0.5, 1.0, 0.586),
               (1.0, 2.0, 0.414), (2.0, 4.0, 0.293)]
LAMBDA_DEADLINE = 20.0
LAMBDA_DAILY = 100.0


def _urgency(deadline_day: int) -> float:
    return 1.0 / (1.0 + deadline_day)


def solve_lp(scenario: dict) -> dict:
    """Solve one scenario. Returns {status, feasible, schedule, objective_value}."""
    subjects = list(scenario["subjects"])
    time_slots = list(scenario["time_slots"])
    max_daily = float(scenario["max_daily_hours"])
    min_session = float(scenario["min_session_hours"])
    buffer_ratio = float(scenario["buffer_ratio"])
    big_m = float(scenario["big_m"])

    if not subjects:
        return {"status": "no_assignments", "feasible": False, "schedule": [],
                "objective_value": 0.0}

    idx = {s["id"]: i for i, s in enumerate(subjects)}
    days = sorted({ts["day"] for ts in time_slots})
    slots_by_day: dict[int, list[int]] = {}
    tod: dict[tuple[int, int], float] = {}
    avail: dict[tuple[int, int], float] = {}
    for ts in time_slots:
        d, t = ts["day"], ts["slot"]
        slots_by_day.setdefault(d, []).append(t)
        tod[(d, t)] = float(ts["tod_factor"])
        avail[(d, t)] = float(ts["available_hours"])

    prob = pulp.LpProblem("schedule", pulp.LpMaximize)

    x = {}
    y = {}
    for s in subjects:
        for d in days:
            for t in slots_by_day[d]:
                if d > s["deadline_day"]:
                    continue  # C6: no study after deadline
                x[(s["id"], d, t)] = pulp.LpVariable(
                    f"x_{s['id']}_{d}_{t}", lowBound=0)
                y[(s["id"], d, t)] = pulp.LpVariable(
                    f"y_{s['id']}_{d}_{t}", cat=pulp.LpBinary)

    delta: dict[tuple[str, int, int], pulp.LpVariable] = {}
    for s in subjects:
        for d in days:
            if d > s["deadline_day"]:
                continue
            for k, (lo, hi, _) in enumerate(BREAKPOINTS):
                delta[(s["id"], d, k)] = pulp.LpVariable(
                    f"d_{s['id']}_{d}_{k}", lowBound=0,
                    upBound=hi - lo)

    s_slack = {s["id"]: pulp.LpVariable(f"s_{s['id']}", lowBound=0)
               for s in subjects}
    u_slack = {d: pulp.LpVariable(f"u_{d}", lowBound=0) for d in days}

    # --- Objective ---
    eff = {s["id"]: _urgency(s["deadline_day"]) * s["difficulty"] * s["priority"]
           for s in subjects}
    terms = []
    for s in subjects:
        for d in days:
            if d > s["deadline_day"]:
                continue
            for k, (_, _, slope) in enumerate(BREAKPOINTS):
                terms.append(eff[s["id"]] * slope * delta[(s["id"], d, k)])
    terms.append(-LAMBDA_DEADLINE * pulp.lpSum(s_slack.values()))
    terms.append(-LAMBDA_DAILY * pulp.lpSum(u_slack.values()))
    prob += pulp.lpSum(terms)

    # --- C7: link X_eff to delta, X_eff <= 4 ---
    for s in subjects:
        for d in days:
            if d > s["deadline_day"]:
                continue
            x_eff = pulp.lpSum(
                tod[(d, t)] * x[(s["id"], d, t)]
                for t in slots_by_day[d] if (s["id"], d, t) in x)
            prob += x_eff == pulp.lpSum(
                delta[(s["id"], d, k)] for k in range(len(BREAKPOINTS)))
            prob += x_eff <= 4.0

    # --- C1: slot availability ---
    for d in days:
        for t in slots_by_day[d]:
            prob += pulp.lpSum(
                x[(s["id"], d, t)] for s in subjects
                if (s["id"], d, t) in x) <= avail[(d, t)]

    # --- C2: soft daily cap ---
    for d in days:
        prob += pulp.lpSum(
            x[(s["id"], d, t)] for s in subjects for t in slots_by_day[d]
            if (s["id"], d, t) in x) - u_slack[d] <= max_daily

    # --- C3: soft deadline ---
    for s in subjects:
        before = pulp.lpSum(
            x[(s["id"], d, t)] for d in days for t in slots_by_day[d]
            if (s["id"], d, t) in x and d <= s["deadline_day"])
        prob += before + s_slack[s["id"]] >= s["required_hours"]

    # --- C4: buffer ---
    for s in subjects:
        prob += pulp.lpSum(
            x[(s["id"], d, t)] for d in days for t in slots_by_day[d]
            if (s["id"], d, t) in x) <= s["required_hours"] * (1 + buffer_ratio)

    # --- C5: min session via binary ---
    for key, var in x.items():
        prob += var >= min_session * y[key]
        prob += var <= big_m * y[key]

    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30)
    prob.solve(solver)
    status_str = pulp.LpStatus.get(prob.status, "unknown")

    schedule: list[dict] = []
    if status_str == "Optimal":
        for (sid, d, t), var in x.items():
            v = pulp.value(var) or 0.0
            if v > 1e-6:
                schedule.append({"subject_id": sid, "day": d, "slot": t,
                                 "hours": round(v, 4)})
        schedule.sort(key=lambda e: (e["day"], e["slot"], e["subject_id"]))
        return {"status": "optimal", "feasible": True, "schedule": schedule,
                "objective_value": round(pulp.value(prob.objective) or 0.0, 4)}
    return {"status": status_str.lower(), "feasible": False, "schedule": [],
            "objective_value": 0.0}
