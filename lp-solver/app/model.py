"""
MILP model for personal study scheduling.

Design reference: thesis §4.5 (Tầng 3 — LP Optimization Engine).

Key ideas:
- Decision variables x[i,d,t] = hours studying subject i on day d in slot t
- Binary y[i,d,t] = 1 if any session at (i,d,t), used for min session constraint
- Piecewise linear approximation of √x (diminishing returns), 4 segments
- Segment variables δ[i,d,k] ∈ [0, width_k]
- Soft constraints for deadline (s[i]) and daily cap (u[d]) via slack
- Objective: maximize Σ E[i]·f(X_eff[i,d]) − λ₁Σs − λ₂Σu

Penalty tuning:
- λ_daily MUST be > max marginal gain (E_max × slope_1 ≈ 25 × 1.414 ≈ 35)
  so that solver never overflows daily cap to gain more effectiveness.
  Chosen λ_daily = 100 (3× safety margin).
- λ_deadline (20) is high enough to prioritize meeting deadlines but
  low enough that solver prefers shortfall warning over risking overflow.
"""
import math
from typing import Final

import pulp


# ============================================================
# Piecewise-linear approximation of f(x) = √x on [0, 4]
# ============================================================
BREAKPOINTS: Final[list[float]] = [0, 0.5, 1.0, 2.0, 4.0]
X_EFF_MAX: Final[float] = 4.0

WIDTHS: Final[list[float]] = [
    BREAKPOINTS[k + 1] - BREAKPOINTS[k] for k in range(len(BREAKPOINTS) - 1)
]

SLOPES: Final[list[float]] = [
    (math.sqrt(BREAKPOINTS[k + 1]) - math.sqrt(BREAKPOINTS[k]))
    / (BREAKPOINTS[k + 1] - BREAKPOINTS[k])
    for k in range(len(BREAKPOINTS) - 1)
]
# SLOPES ≈ [1.4142, 0.5858, 0.4142, 0.2929]


# Default penalty weights (see docstring for tuning rationale)
DEFAULT_LAMBDA_DEADLINE: Final[float] = 20.0
DEFAULT_LAMBDA_DAILY: Final[float] = 100.0


def build_model(
    subjects: list[dict],
    time_slots: list[dict],
    max_daily_hours: float,
    min_session_hours: float = 0.5,
    buffer_ratio: float = 0.25,
    big_m: float = 8.0,
    lambda_deadline: float = DEFAULT_LAMBDA_DEADLINE,
    lambda_daily: float = DEFAULT_LAMBDA_DAILY,
) -> tuple[pulp.LpProblem, dict]:
    """
    Build MILP for study scheduling.

    Args:
        subjects: list of dicts with id, required_hours, deadline_day,
                  difficulty, priority, urgency (optional — auto-computed if absent)
        time_slots: list of dicts with day, slot, tod_factor, available_hours
        max_daily_hours: W_max_effective (already adjusted by risk on caller side)
        min_session_hours: X_min
        buffer_ratio: ratio of R[i] allowed over-cap
        big_m: big-M constant
        lambda_deadline: penalty for deadline shortfall
        lambda_daily: penalty for daily overload (default 100 — see module docstring)

    Returns:
        (problem, variables_dict)
    """
    prob = pulp.LpProblem("study_schedule", pulp.LpMaximize)

    # ----- Index sets -----
    subject_ids = [s["id"] for s in subjects]
    days = sorted({t["day"] for t in time_slots})

    # Fill in urgency if missing (compute before using in objective)
    for s in subjects:
        if s.get("urgency") is None:
            s["urgency"] = 1.0 / (1.0 + s["deadline_day"])

    # ----- Decision variables -----
    x: dict = {}  # x[i, d, t] ≥ 0
    y: dict = {}  # y[i, d, t] ∈ {0, 1}
    for i in subject_ids:
        for d in days:
            for t in [ts["slot"] for ts in time_slots if ts["day"] == d]:
                key = (i, d, t)
                x[key] = pulp.LpVariable(
                    f"x_{i}_{d}_{t}", lowBound=0, cat="Continuous"
                )
                y[key] = pulp.LpVariable(f"y_{i}_{d}_{t}", cat="Binary")

    # ----- Segment variables δ[i, d, k] ∈ [0, width_k] -----
    delta: dict = {}
    for i in subject_ids:
        for d in days:
            for k in range(4):
                delta[(i, d, k)] = pulp.LpVariable(
                    f"delta_{i}_{d}_{k}",
                    lowBound=0,
                    upBound=WIDTHS[k],
                    cat="Continuous",
                )

    # ----- Slack variables -----
    s: dict = {}
    for subj in subjects:
        s[subj["id"]] = pulp.LpVariable(
            f"s_{subj['id']}",
            lowBound=0,
            upBound=subj["required_hours"],
            cat="Continuous",
        )
    u: dict = {}
    for d in days:
        u[d] = pulp.LpVariable(
            f"u_{d}",
            lowBound=0,
            upBound=max_daily_hours,
            cat="Continuous",
        )

    # ============================================================
    # Objective: Maximize Σ E[i]·Σ slope·δ − λ₁Σs − λ₂Σu
    # ============================================================
    obj = pulp.LpAffineExpression()
    for subj in subjects:
        i = subj["id"]
        E_i = subj["urgency"] * subj["difficulty"] * subj["priority"]
        for d in days:
            for k in range(4):
                obj += E_i * SLOPES[k] * delta[(i, d, k)]

    obj -= lambda_deadline * pulp.lpSum(s[i] for i in subject_ids)
    obj -= lambda_daily * pulp.lpSum(u[d] for d in days)
    prob += obj

    # ============================================================
    # Constraints
    # ============================================================

    # C1: Slot availability — Σ_i x[i,d,t] ≤ H[d,t]
    for ts in time_slots:
        d, t = ts["day"], ts["slot"]
        prob += (
            pulp.lpSum(x[(i, d, t)] for i in subject_ids) <= ts["available_hours"],
            f"slot_avail_{d}_{t}",
        )

    # C2: Daily cap (soft) — Σ_i Σ_t x[i,d,t] − u[d] ≤ W_max
    for d in days:
        slots_of_d = [ts["slot"] for ts in time_slots if ts["day"] == d]
        prob += (
            pulp.lpSum(
                x[(i, d, t)] for i in subject_ids for t in slots_of_d
            )
            - u[d]
            <= max_daily_hours,
            f"daily_cap_{d}",
        )

    # C3: Deadline (soft) — Σ_{d ≤ d_i} x[i,d,t] + s[i] ≥ R[i]
    for subj in subjects:
        i = subj["id"]
        d_i = subj["deadline_day"]
        R_i = subj["required_hours"]
        slots_before = [ts for ts in time_slots if ts["day"] <= d_i]
        prob += (
            pulp.lpSum(
                x[(i, ts["day"], ts["slot"])] for ts in slots_before
            )
            + s[i]
            >= R_i,
            f"deadline_{i}",
        )

    # C4: Subject total cap — Σ x[i,·] ≤ R[i] × (1 + buffer)
    for subj in subjects:
        i = subj["id"]
        R_i = subj["required_hours"]
        prob += (
            pulp.lpSum(
                x[(i, ts["day"], ts["slot"])] for ts in time_slots
            )
            <= R_i * (1 + buffer_ratio),
            f"total_cap_{i}",
        )

    # C5: Min session — X_min·y ≤ x ≤ M·y
    for (i, d, t) in x.keys():
        prob += (
            x[(i, d, t)] >= min_session_hours * y[(i, d, t)],
            f"min_lb_{i}_{d}_{t}",
        )
        prob += (
            x[(i, d, t)] <= big_m * y[(i, d, t)],
            f"min_ub_{i}_{d}_{t}",
        )

    # C6: No study after deadline — x[i,d,t] = 0 if d > d_i
    for subj in subjects:
        i = subj["id"]
        d_i = subj["deadline_day"]
        for (si, d, t) in x.keys():
            if si == i and d > d_i:
                prob += (
                    x[(si, d, t)] == 0,
                    f"no_after_deadline_{i}_{d}_{t}",
                )

    # C7: Segment linkage + X_eff cap
    for subj in subjects:
        i = subj["id"]
        for d in days:
            slots_of_d = [ts for ts in time_slots if ts["day"] == d]
            x_eff_expr = pulp.lpSum(
                ts["tod_factor"] * x[(i, d, ts["slot"])] for ts in slots_of_d
            )
            delta_sum = pulp.lpSum(delta[(i, d, k)] for k in range(4))
            prob += x_eff_expr == delta_sum, f"x_eff_link_{i}_{d}"
            prob += x_eff_expr <= X_EFF_MAX, f"x_eff_max_{i}_{d}"

    variables = {
        "x": x,
        "y": y,
        "delta": delta,
        "s": s,
        "u": u,
        "subject_ids": subject_ids,
        "days": days,
        "time_slots": time_slots,
    }

    return prob, variables
