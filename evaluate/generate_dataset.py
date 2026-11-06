#!/usr/bin/env python3
"""
Synthetic dataset generator for LP Solver evaluation.

Implements phuong_phap_danh_gia.md Section 1 exactly:
  - 300 scenarios: Light 90 (30%), Normal 120 (40%), Heavy 60 (20%), Extreme 30 (10%)
  - Schema matches Tier 3 input (subjects-as-assignments, time_slots 3/day, tod_factor 1.2/1.0/0.8)
  - Deterministic: seed 42, so Thesis numbers are reproducible.

Output (JSON, ready for LP Solver POST /api/schedule/generate):
  evaluate/dataset/synthetic_dataset.json  — list of 300 scenarios
  evaluate/dataset/dataset_summary.json    — counts, coverage stats

Input shape per scenario = Tier 1 payload in data-flow.md §4.5:
  {"scenario_id", "scenario_type", "subjects", "time_slots",
   "max_daily_hours", "min_session_hours", "buffer_ratio", "big_m"}

Each "subject" is one assignment (T1 maps assignment -> LP subject):
  {"id": "assign_k", "required_hours", "deadline_day", "difficulty", "priority"}

Time slots mirror data-flow.md §4.4:
  - horizon = min(max(7, max_deadline_day + 1), 30)
  - 3 slots/day, available_hours=2.0, tod_factor 1.2 / 1.0 / 0.8
  - available_hours drawn 1.0-3.0 per phuong_phap §1.1 (varies capacity for Heavy/Extreme)

Usage:
  python evaluate/generate_dataset.py
  python evaluate/generate_dataset.py --seed 42 --output evaluate/dataset/synthetic_dataset.json --summary
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# Constants (must match Tier 1 defaults in data-flow.md / tier-3-overview.md)
# --------------------------------------------------------------------------
DEFAULT_HORIZON_DAYS = 7
MAX_HORIZON_DAYS = 30
TOD_FACTORS = (1.2, 1.0, 0.8)  # slot 0 morning, 1 afternoon, 2 evening
MIN_SESSION_HOURS = 0.5
BUFFER_RATIO = 0.25
BIG_M = 8.0
DEFAULT_W_MAX = 6.0  # used only to document capacity; scenario max_daily_hours is drawn

# phuong_phap_danh_gia.md §1.2 thresholds
SCENARIO_QUOTA = {"Light": 90, "Normal": 120, "Heavy": 60, "Extreme": 30}
TOTAL_SCENARIOS = sum(SCENARIO_QUOTA.values())  # 300


@dataclass
class ScenarioSpec:
    """Per-type shape ranges from phuong_phap_danh_gia.md §1.2."""
    n_subjects: tuple[int, int]          # inclusive
    n_assignments: tuple[int, int]       # inclusive
    deadline_day: tuple[int, int]        # inclusive
    load_ratio: tuple[float, float]      # required / capacity target (approx, used to size hours)
    max_daily_hours: tuple[float, float]


SPECS = {
    "Light":   ScenarioSpec((1, 3), (1, 3),   (7, 14), (0.15, 0.30), (4.0, 6.0)),
    "Normal":  ScenarioSpec((3, 5), (4, 8),   (3, 7),  (0.60, 0.80), (4.0, 6.0)),
    "Heavy":   ScenarioSpec((5, 7), (8, 12),  (1, 3),  (0.95, 1.05), (3.0, 5.0)),
    "Extreme": ScenarioSpec((8, 8), (15, 15), (1, 2),  (1.20, 1.60), (2.0, 4.0)),
}


def build_time_slots(horizon: int, rng: random.Random) -> list[dict]:
    """3 slots/day. available_hours in [1.0, 3.0] per §1.1 (default ~2.0 center)."""
    slots: list[dict] = []
    for day in range(horizon):
        for slot in range(3):
            # Normal-ish around 2.0, clipped to [1.0, 3.0]
            avail = round(min(3.0, max(1.0, rng.gauss(2.0, 0.35))), 2)
            slots.append({
                "day": day,
                "slot": slot,
                "tod_factor": TOD_FACTORS[slot],
                "available_hours": avail,
            })
    return slots


def capacity_of(time_slots: list[dict]) -> float:
    return sum(s["available_hours"] for s in time_slots)


def distribute_hours(n: int, total_required: float, rng: random.Random) -> list[float]:
    """Split total_required across n assignments (0.5-10.0 each per §1.1).

    Weights favour larger hours for larger n? Use uniform random then rescale,
    clipping each to [0.5, 10.0]. For Extreme, total may exceed n*10 — we cap
    and accept that the scenario is deliberately infeasible (shortfall expected).
    """
    raw = [rng.uniform(0.6, 4.5) for _ in range(n)]
    scale = sum(raw) or 1.0
    hours = [round((w / scale) * total_required, 2) for w in raw]
    # clip to §1.1 bounds
    hours = [min(10.0, max(0.5, h)) for h in hours]
    # fix rounding drift
    drift = round(total_required - sum(hours), 2)
    if hours:
        hours[-1] = round(min(10.0, max(0.5, hours[-1] + drift)), 2)
    return hours


def generate_one(scenario_id: str, scenario_type: str, rng: random.Random) -> dict:
    spec = SPECS[scenario_type]
    n_sub = rng.randint(*spec.n_subjects)
    n_assign = rng.randint(*spec.n_assignments)

    # horizon = min(max(7, max_deadline+1), 30) — need deadline first for sizing.
    # Draw deadlines in a way that produces the required load_ratio vs capacity.
    deadlines = [rng.randint(*spec.deadline_day) for _ in range(n_assign)]
    max_deadline = max(deadlines)
    horizon = min(max(DEFAULT_HORIZON_DAYS, max_deadline + 1), MAX_HORIZON_DAYS)

    time_slots = build_time_slots(horizon, rng)
    cap = capacity_of(time_slots)

    # Target total required = load_ratio * capacity, then distribute.
    ratio = rng.uniform(*spec.load_ratio)
    total_required = cap * ratio
    # For Light, keep total well below capacity even when horizon is long.
    hours = distribute_hours(n_assign, total_required, rng)

    subjects = [
        {
            "id": f"assign_{k + 1}",
            "required_hours": hours[k],
            "deadline_day": deadlines[k],
            "difficulty": rng.randint(1, 5),
            "priority": rng.randint(1, 5),
        }
        for k in range(n_assign)
    ]

    # Decorative metadata for grouping (not sent to Tier 3): map each assignment
    # to one of n_subjects logical subjects for display in thesis tables.
    subject_map = [rng.randint(1, n_sub) for _ in range(n_assign)]
    for s, m in zip(subjects, subject_map):
        s["subject_group"] = f"sub_{m}"

    max_daily = round(rng.uniform(*spec.max_daily_hours), 2)

    return {
        "scenario_id": scenario_id,
        "scenario_type": scenario_type,
        "subjects": subjects,          # NOTE: each entry is one assignment (see header)
        "time_slots": time_slots,
        "max_daily_hours": max_daily,
        "min_session_hours": MIN_SESSION_HOURS,
        "buffer_ratio": BUFFER_RATIO,
        "big_m": BIG_M,
        # ---- evaluation-only metadata (strip before POST if Tier 3 is strict) ----
        "_meta": {
            "n_subjects_logical": n_sub,
            "horizon_days": horizon,
            "total_capacity_hours": round(cap, 2),
            "total_required_hours": round(sum(hours), 2),
            "load_ratio": round(sum(hours) / cap if cap else 0.0, 3),
        },
    }


def generate_dataset(seed: int = 42) -> list[dict]:
    """Deterministic generation. Order: all Light, then Normal, Heavy, Extreme."""
    rng = random.Random(seed)
    dataset: list[dict] = []
    counter = 1
    for stype in ("Light", "Normal", "Heavy", "Extreme"):
        for _ in range(SCENARIO_QUOTA[stype]):
            dataset.append(generate_one(f"SC_{counter:03d}", stype, rng))
            counter += 1
    return dataset


def summarize(dataset: list[dict]) -> dict:
    from collections import Counter, defaultdict

    by_type = defaultdict(list)
    for sc in dataset:
        by_type[sc["scenario_type"]].append(sc)

    summary: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_scenarios": len(dataset),
        "by_type": {},
        "params": {
            "seed": 42,
            "tod_factors": list(TOD_FACTORS),
            "min_session_hours": MIN_SESSION_HOURS,
            "buffer_ratio": BUFFER_RATIO,
            "big_m": BIG_M,
            "horizon_rule": "min(max(7, max_deadline_day+1), 30)",
        },
    }
    for stype, items in by_type.items():
        ratios = [i["_meta"]["load_ratio"] for i in items]
        summary["by_type"][stype] = {
            "count": len(items),
            "avg_load_ratio": round(sum(ratios) / len(ratios), 3) if ratios else 0.0,
            "avg_assignments": round(
                sum(len(i["subjects"]) for i in items) / len(items), 2
            ) if items else 0.0,
        }
    return summary


def strip_meta(scenario: dict) -> dict:
    """Return a copy without evaluation-only fields, for direct POST to Tier 3."""
    sc = json.loads(json.dumps(scenario))
    sc.pop("_meta", None)
    for s in sc.get("subjects", []):
        s.pop("subject_group", None)
    return sc


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate 300-scenario synthetic dataset.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--output", type=str,
                    default="evaluate/dataset/synthetic_dataset.json")
    ap.add_argument("--limit", type=int, default=0,
                    help="0 = all 300 (use for quick smoke test, e.g. --limit 10)")
    args = ap.parse_args()

    dataset = generate_dataset(seed=args.seed)
    if args.limit:
        dataset = dataset[: args.limit]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Full file keeps _meta (useful for thesis tables).
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(dataset)} scenarios -> {out_path}")

    # Summary sidecar.
    summary_path = out_path.parent / "dataset_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summarize(dataset), f, ensure_ascii=False, indent=2)
    print(f"Wrote summary -> {summary_path}")

    # Print Type-3-ready sample (first scenario, no metadata).
    print("\n--- Tier-3-ready sample (SC_001, metadata stripped) ---")
    print(json.dumps(strip_meta(dataset[0]), ensure_ascii=False, indent=2)[:2000])


if __name__ == "__main__":
    main()
