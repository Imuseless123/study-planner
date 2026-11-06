#!/usr/bin/env python3
"""
Evaluation runner — phuong_phap_danh_gia.md §3-§4.

Runs Greedy (baseline_greedy) and LP (lp_solver) on the same 300 scenarios,
computes the 5 metrics (§3), averages them, runs paired T-test (§4 step 6),
and writes thesis-ready outputs:

  evaluate/results/per_scenario.json  cross-table per scenario (both methods)
  evaluate/results/metrics_summary.json  averages per method + T-test p-values
  evaluate/results/table_comparison.csv  LaTeX/Word-ready comparison table
  evaluate/results/chart_comparison.png  bar charts (5 metrics, log-safe)

Metrics (§3):
  1. Feasibility Rate (%)        higher better
  2. Total Deadline Shortfall (h) lower better
  3. Total Overload Hours (h)     lower better (expect 0 for LP)
  4. Objective Value (Z)          higher better
  5. Runtime (s)                  lower better

Usage:
  python evaluate/evaluate.py [--limit 20]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

from baseline_greedy import solve_greedy
from lp_solver import solve_lp

try:
    from scipy.stats import ttest_rel
except ImportError:  # graceful fallback if scipy missing
    ttest_rel = None


# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------
def planned_before_deadline(scenario: dict, schedule: list[dict]) -> dict[str, float]:
    deadline = {s["id"]: s["deadline_day"] for s in scenario["subjects"]}
    planned = {s["id"]: 0.0 for s in scenario["subjects"]}
    for e in schedule:
        if e["day"] <= deadline[e["subject_id"]]:
            planned[e["subject_id"]] += e["hours"]
    return planned


def shortfall(scenario: dict, schedule: list[dict]) -> float:
    """§3.2: sum(max(0, required - planned_before_deadline))."""
    planned = planned_before_deadline(scenario, schedule)
    total = 0.0
    for s in scenario["subjects"]:
        total += max(0.0, s["required_hours"] - planned[s["id"]])
    return round(total, 4)


def overload(scenario: dict, schedule: list[dict]) -> float:
    """§3.3: sum(max(0, hours_per_day - max_daily_hours))."""
    per_day: dict[int, float] = defaultdict(float)
    for e in schedule:
        per_day[e["day"]] += e["hours"]
    cap = float(scenario["max_daily_hours"])
    return round(sum(max(0.0, v - cap) for v in per_day.values()), 4)


BREAKPOINTS = [(0.0, 0.5, 1.414), (0.5, 1.0, 0.586), (1.0, 2.0, 0.414), (2.0, 4.0, 0.293)]
LAMBDA_DEADLINE = 20.0
LAMBDA_DAILY = 100.0

def _f_sqrt(x_eff: float) -> float:
    """Piecewise-linear sqrt on [0,4] (same as LP model)."""
    x_eff = min(max(x_eff, 0.0), 4.0)
    return sum(slope * (min(x_eff, hi) - lo) for lo, hi, slope in BREAKPOINTS if x_eff > lo)

def fair_objective(scenario: dict, schedule: list[dict]) -> float:
    """Z theo cùng công thức của LP, áp cho bất kỳ schedule nào (kể cả Greedy).

    E[i]=urgency*difficulty*priority, urgency=1/(1+deadline_day)
    X_eff = Σ tod_factor * hours per (subject, day), f = _f_sqrt capped 0-4
    Z = Σ E[i]*f(X_eff) − 20*Σs − 100*Σu
    s[i]=max(0, required − planned_before_deadline), u[d]=max(0, per_day − cap)
    Dùng để so sánh công bằng; objective gốc của Greedy (raw hours) chỉ mang tính định tính.
    """
    tod = {(ts["day"], ts["slot"]): float(ts["tod_factor"]) for ts in scenario["time_slots"]}
    eff = {s["id"]: (1.0/(1.0+s["deadline_day"])) * s["difficulty"] * s["priority"] for s in scenario["subjects"]}
    # X_eff per (subject, day)
    x_eff: dict[tuple[str,int], float] = defaultdict(float)
    per_day: dict[int, float] = defaultdict(float)
    for e in schedule:
        per_day[e["day"]] += e["hours"]
        x_eff[(e["subject_id"], e["day"])] += tod.get((e["day"], e["slot"]), 1.0) * e["hours"]
    z = sum(eff[sid] * _f_sqrt(xe) for (sid, _d), xe in x_eff.items())
    # penalties
    planned = planned_before_deadline(scenario, schedule)
    s_sum = sum(max(0.0, s["required_hours"] - planned[s["id"]]) for s in scenario["subjects"])
    cap = float(scenario["max_daily_hours"])
    u_sum = sum(max(0.0, v - cap) for v in per_day.values())
    return round(z - LAMBDA_DEADLINE*s_sum - LAMBDA_DAILY*u_sum, 4)

def run_one(solver_fn, scenario: dict) -> dict:
    t0 = time.perf_counter()
    res = solver_fn(scenario)
    runtime = round(time.perf_counter() - t0, 4)
    sched = res["schedule"]
    return {
        "feasible": bool(res["feasible"]),
        "objective_value": float(res["objective_value"]),
        "objective_fair": fair_objective(scenario, sched),
        "shortfall": shortfall(scenario, sched),
        "overload": overload(scenario, sched),
        "runtime_s": runtime,
    }


def paired_ttest(a: list[float], b: list[float]) -> float | None:
    """Two-sided paired T-test; returns p-value or None."""
    if ttest_rel is None or len(a) != len(b) or len(a) < 2:
        return None
    # If all differences are identical, scipy returns nan — guard that.
    if all(x == y for x, y in zip(a, b)):
        return 1.0
    try:
        return float(ttest_rel(a, b).pvalue)
    except (ValueError, FloatingPointError):
        return None


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="evaluate/dataset/synthetic_dataset.json")
    ap.add_argument("--limit", type=int, default=0, help="0 = all scenarios")
    args = ap.parse_args()

    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    if args.limit:
        dataset = dataset[: args.limit]
    print(f"Loaded {len(dataset)} scenarios from {args.dataset}")

    per_scenario: list[dict] = []
    for i, sc in enumerate(dataset, 1):
        g = run_one(solve_greedy, sc)
        lp = run_one(solve_lp, sc)
        per_scenario.append({
            "scenario_id": sc["scenario_id"],
            "scenario_type": sc["scenario_type"],
            "greedy": g,
            "lp": lp,
        })
        if i % 50 == 0:
            print(f"  ...{i}/{len(dataset)}")

    # ---- Aggregate (§4 step 4: average over 300) ----
    N = len(per_scenario)
    agg = {}
    for method in ("greedy", "lp"):
        feas = sum(1 for r in per_scenario if r[method]["feasible"])
        agg[method] = {
            "feasibility_rate_pct": round(100.0 * feas / N, 2),
            "avg_shortfall_h": round(mean([r[method]["shortfall"] for r in per_scenario]), 4),
            "avg_overload_h": round(mean([r[method]["overload"] for r in per_scenario]), 4),
            "avg_objective": round(mean([r[method]["objective_value"] for r in per_scenario]), 4),
            "avg_objective_fair": round(mean([r[method]["objective_fair"] for r in per_scenario]), 4),
            "avg_runtime_s": round(mean([r[method]["runtime_s"] for r in per_scenario]), 4),
        }

    # ---- Paired T-test (§4 step 6) on shortfall, overload, objective ----
    pvals = {}
    for metric in ("shortfall", "overload", "objective_value", "objective_fair", "runtime_s"):
        a = [r["lp"][metric] for r in per_scenario]
        b = [r["greedy"][metric] for r in per_scenario]
        pvals[metric] = paired_ttest(a, b)

    # ---- Breakdown theo Light/Normal/Heavy/Extreme ----
    by_type = {}
    for stype in ("Light", "Normal", "Heavy", "Extreme"):
        subset = [r for r in per_scenario if r["scenario_type"] == stype]
        if not subset:
            continue
        t_agg = {}
        for method in ("greedy", "lp"):
            feas = sum(1 for r in subset if r[method]["feasible"])
            t_agg[method] = {
                "n": len(subset),
                "feasibility_rate_pct": round(100.0 * feas / len(subset), 2),
                "avg_shortfall_h": round(mean([r[method]["shortfall"] for r in subset]), 4),
                "avg_overload_h": round(mean([r[method]["overload"] for r in subset]), 4),
                "avg_objective_fair": round(mean([r[method]["objective_fair"] for r in subset]), 4),
                "avg_runtime_s": round(mean([r[method]["runtime_s"] for r in subset]), 4),
            }
        by_type[stype] = t_agg

    summary = {"n_scenarios": N, "methods": agg, "by_type": by_type, "paired_ttest_pvalues": pvals}

    results_dir = Path("evaluate/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "per_scenario.json").write_text(
        json.dumps(per_scenario, ensure_ascii=False, indent=2), encoding="utf-8")
    (results_dir / "metrics_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV comparison table (thesis copy-paste friendly)
    csv_path = results_dir / "table_comparison.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Metric", "Greedy (Baseline)", "LP Solver (Proposed)",
                    "Paired T-test p-value"])
        rows = [
            ("Feasibility Rate (%)", agg["greedy"]["feasibility_rate_pct"],
             agg["lp"]["feasibility_rate_pct"], "—"),
            ("Avg Deadline Shortfall (h)", agg["greedy"]["avg_shortfall_h"],
             agg["lp"]["avg_shortfall_h"], _fmt(pvals["shortfall"])),
            ("Avg Overload Hours (h)", agg["greedy"]["avg_overload_h"],
             agg["lp"]["avg_overload_h"], _fmt(pvals["overload"])),
            ("Avg Objective Value (raw: LP Z, Greedy raw hours — chỉ định tính)", agg["greedy"]["avg_objective"],
             agg["lp"]["avg_objective"], _fmt(pvals["objective_value"])),
            ("Avg Objective Fair (cùng công thức Z — so sánh chính)", agg["greedy"]["avg_objective_fair"],
             agg["lp"]["avg_objective_fair"], _fmt(pvals["objective_fair"])),
            ("Avg Runtime (s)", agg["greedy"]["avg_runtime_s"],
             agg["lp"]["avg_runtime_s"], _fmt(pvals["runtime_s"])),
        ]
        for r in rows:
            w.writerow(r)

    print("\n=== Metrics summary (avg over {} scenarios) ===".format(N))
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    # ---- Charts (§4 step 5) ----
    _make_charts(results_dir, agg, per_scenario)
    print(f"\nWrote: {results_dir}/per_scenario.json")
    print(f"Wrote: {results_dir}/metrics_summary.json")
    print(f"Wrote: {results_dir}/table_comparison.csv")


def _fmt(p: float | None) -> str:
    if p is None:
        return "n/a"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def _make_charts(results_dir: Path, agg: dict, per_scenario: list[dict]) -> None:
    """3-panel bar charts (metric scale differs too much for one axis)."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed — skipping charts.")
        return

    metrics = [
        ("Avg Deadline Shortfall (h)", "avg_shortfall_h"),
        ("Avg Overload Hours (h)", "avg_overload_h"),
        ("Avg Objective Value", "avg_objective"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (title, key) in zip(axes, metrics):
        bars = ax.bar(["Greedy", "LP Solver"],
                      [agg["greedy"][key], agg["lp"][key]],
                      color=["#b0bec5", "#1565c0"])
        ax.set_title(title)
        ax.set_ylabel("value")
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                    f"{b.get_height():.2f}", ha="center", va="bottom", fontsize=9)
        ax.grid(axis="y", alpha=0.3)
    fig.suptitle(f"Greedy vs LP Solver — {len(per_scenario)} scenarios")
    fig.tight_layout()
    fig.savefig(results_dir / "chart_comparison.png", dpi=150)
    plt.close(fig)
    print("Wrote: chart_comparison.png")


if __name__ == "__main__":
    main()
