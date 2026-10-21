"""Solve the MILP and extract results."""
import pulp

from .model import (
    build_model,
    DEFAULT_LAMBDA_DEADLINE,
    DEFAULT_LAMBDA_DAILY,
)


def extract_schedule(variables: dict) -> list[dict]:
    """Extract x[i,d,t] > 0 as list of entries."""
    schedule = []
    for key, var in variables["x"].items():
        i, d, t = key
        v = var.varValue or 0.0
        if v > 1e-6:
            schedule.append({
                "subject_id": i,
                "day": d,
                "slot": t,
                "hours": round(v, 2),
            })
    schedule.sort(key=lambda e: (e["day"], e["slot"], e["subject_id"]))
    return schedule


def build_explanation(variables: dict, subjects: list[dict]) -> dict:
    """Per-subject and per-day breakdown."""
    subj_by_id = {s["id"]: s for s in subjects}

    per_subject = []
    for i in variables["subject_ids"]:
        total = sum(
            (v.varValue or 0.0)
            for (si, _, _), v in variables["x"].items()
            if si == i
        )
        R = subj_by_id[i]["required_hours"]
        shortfall = variables["s"][i].varValue or 0.0
        per_subject.append({
            "subject_id": i,
            "required_hours": round(R, 2),
            "scheduled_hours": round(total, 2),
            "buffer_used": round(max(0.0, total - R), 2),
            "deadline_shortfall": round(shortfall, 2),
        })

    per_day = []
    for d in variables["days"]:
        total = sum(
            (v.varValue or 0.0)
            for (_, di, _), v in variables["x"].items()
            if di == d
        )
        overload = variables["u"][d].varValue or 0.0
        per_day.append({
            "day": d,
            "total_hours": round(total, 2),
            "overload": round(overload, 2),
        })

    return {"per_subject": per_subject, "per_day": per_day}


def build_warnings(variables: dict) -> list[dict]:
    """Warnings for deadline shortfall / daily overload."""
    warnings = []
    for i, var in variables["s"].items():
        v = var.varValue or 0.0
        if v > 0.01:
            warnings.append({
                "type": "deadline_shortfall",
                "subject_id": i,
                "shortfall_hours": round(v, 2),
                "message": (
                    f"Subject '{i}' will be short {v:.1f}h before deadline. "
                    f"Consider reducing scope or extending deadline."
                ),
            })
    for d, var in variables["u"].items():
        v = var.varValue or 0.0
        if v > 0.01:
            warnings.append({
                "type": "daily_overload",
                "day": d,
                "overload_hours": round(v, 2),
                "message": (
                    f"Day {d} is overloaded by {v:.1f}h. "
                    f"Consider redistributing workload to other days."
                ),
            })
    return warnings


def identify_conflicts(input_data: dict) -> list[dict]:
    """When infeasible, list likely conflicts."""
    conflicts = []
    total_required = sum(s["required_hours"] for s in input_data["subjects"])
    total_available = sum(ts["available_hours"] for ts in input_data["time_slots"])

    if total_required > total_available:
        conflicts.append({
            "type": "total_hours_insufficient",
            "message": (
                f"Total required hours ({total_required:.1f}h) exceed "
                f"total available hours ({total_available:.1f}h)."
            ),
        })

    for s in input_data["subjects"]:
        slots_before = [
            ts for ts in input_data["time_slots"] if ts["day"] <= s["deadline_day"]
        ]
        available_before = sum(ts["available_hours"] for ts in slots_before)
        if s["required_hours"] > available_before:
            conflicts.append({
                "type": "deadline_infeasible",
                "subject_id": s["id"],
                "message": (
                    f"Subject '{s['id']}' requires {s['required_hours']}h before "
                    f"day {s['deadline_day']}, but only {available_before:.1f}h "
                    f"are available."
                ),
            })

    return conflicts


def solve_schedule(input_data: dict) -> dict:
    """
    Full pipeline: build model → solve → extract results.

    IMPORTANT: Fallback values MUST match DEFAULT_* constants in model.py,
    not hardcoded literals. Previous bug: fallback was 5.0 (old default)
    while model.py had 100.0 → inconsistent behavior between HTTP path
    (Pydantic fills default=100.0) and direct dict call (fallback=5.0).
    """
    prob, variables = build_model(
        subjects=input_data["subjects"],
        time_slots=input_data["time_slots"],
        max_daily_hours=input_data["max_daily_hours"],
        min_session_hours=input_data.get("min_session_hours", 0.5),
        buffer_ratio=input_data.get("buffer_ratio", 0.25),
        big_m=input_data.get("big_m", 8.0),
        lambda_deadline=input_data.get(
            "lambda_deadline", DEFAULT_LAMBDA_DEADLINE
        ),
        lambda_daily=input_data.get(
            "lambda_daily", DEFAULT_LAMBDA_DAILY
        ),
    )

    # Solve — CBC solver, quiet mode
    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    if prob.status == pulp.LpStatusOptimal:
        obj_val = pulp.value(prob.objective) or 0.0
        return {
            "status": "optimal",
            "feasible": True,
            "schedule": extract_schedule(variables),
            "explanation": build_explanation(variables, input_data["subjects"]),
            "warnings": build_warnings(variables),
            "objective_value": round(obj_val, 4),
        }

    if prob.status == pulp.LpStatusInfeasible:
        return {
            "status": "infeasible",
            "feasible": False,
            "conflicts": identify_conflicts(input_data),
        }

    if prob.status == pulp.LpStatusUnbounded:
        return {
            "status": "unbounded",
            "feasible": False,
            "error": "Objective function is unbounded (should not happen).",
        }

    return {
        "status": "unknown",
        "feasible": False,
        "error": f"Unexpected solver status: {pulp.LpStatus[prob.status]}",
    }
