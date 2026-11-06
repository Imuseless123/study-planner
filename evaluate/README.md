# Evaluation — LP Solver vs Greedy Baseline

Implements `phuong_phap_danh_gia.md` §1–§4 end-to-end (self-contained: no Docker / no network needed).

## Files

| File | Mục đích |
|---|---|
| `generate_dataset.py` | §1 — Sinh 300 scenarios (`Light 90 / Normal 120 / Heavy 60 / Extreme 30`), seed 42 |
| `baseline_greedy.py` | §2 — Baseline Greedy (deadline → priority → nhét đầy slot) |
| `lp_solver.py` | Tầng 3 replica — MILP với PuLP+CBC, √x 4 đoạn, λ 100/20, soft constraints C1–C7 |
| `evaluate.py` | §3–§4 — Chạy replica vs Greedy, 5 metrics + objective_fair + by_type, paired T-test, biểu đồ |
| `run_real.py` | **Dự án thật** — import `lp-solver/app/solver.solve_schedule` vs Greedy, cùng dataset/metrics |
| `compare.py` | Đối chứng replica vs Tier 3 thật trên 300 scenarios (feasibility + mean/max diff) |
| `dataset/synthetic_dataset.json` | Dataset 300 kịch bản (kém `_meta` cho bảng luận văn) |
| `dataset/dataset_summary.json` | Phân bố Light/Normal/Heavy/Extreme |
| `results/per_scenario.json` | Kết quả từng kịch bản × 2 phương pháp (replica, full 300) |
| `results/metrics_summary.json` | Trung bình 5 metrics + `avg_objective_fair` + `by_type` + p-value (replica) |
| `results/table_comparison.csv` | Bảng so sánh copy-paste vào Chương 6 (replica, full 300) |
| `results/chart_comparison.png` | Bar chart 3 panel (Shortfall / Overload / Objective) (replica) |
| `results_real/` | Kết quả tương tự của `run_real.py` (Tier 3 thật, full 300) |
| `results/run_full.log` | Nhật ký lần chạy full 300 scenarios |

## Cách chạy

```bash
# 1. Sinh dataset (đã có sẵn; chạy lại nếu muốn seed khác)
python3 evaluate/generate_dataset.py

# 2. Smoke test nhanh (20 scenarios)
python3 evaluate/evaluate.py --limit 20

# 3. Chạy full 300 scenarios (~5-10 phút, MILP CBC)
python3 evaluate/evaluate.py
```

#### Chạy với dự án thật (`run_real.py`)

```bash
# Smoke test: Greedy vs Tier 3 THẬT (lp-solver/app/solver.solve_schedule)
python3 evaluate/run_real.py --limit 20

# Full 300 scenarios — chỉ khi đã fix timeLimit (xem Lưu ý) vì SC_010 có thể >5 phút
python3 evaluate/run_real.py
```

`run_real.py` ghi vào `evaluate/results_real/` (không ghi đè `results/` của replica).
Cả hai dùng chung 5 metrics và paired T-test, nên kết quả so trực tiếp được.
Chiến lược cho Chương 6:
- Dùng `evaluate.py` (replica, có `timeLimit=30`) để chạy **full 300** lấy số liệu chính.
- Dùng `run_real.py` để chạy **22–50 scenarios** kiểm chứng replica khớp Tier 3 thật (objective/shortfall/overload phải trùng tới 2 số thập phân, runtime có thể lệch).

Yêu cầu: `pulp`, `scipy`, `matplotlib` (đã cài sẵn trong môi trường kiểm thử).
Sau fix `timeLimit=30` vào `lp-solver/app/solver.py`, runtime trung bình ~5 s/scenario
(replica 5.17 s, Tier 3 thật 4.95 s) — vẫn vượt kỳ vọng `<1 giây` ở §3.5; báo đúng số
`avg_runtime_s` trong `metrics_summary.json` và giải thích bằng CBC single-thread.
Muốn chạy nhanh hơn: `CBC_TIME_LIMIT=10 python3 evaluate/run_real.py` (đánh đổi optimality gap).

## Metrics (§3)

| # | Metric | Hướng tốt | Greedy | LP |
|---|---|---|---|---|
| 1 | Feasibility Rate (%) | cao | ~100% (Light→Heavy), thấp ở Extreme nếu cần chia | 100% (soft constraints + fallback) |
| 2 | Avg Deadline Shortfall (h) | thấp | — | — |
| 3 | Avg Overload Hours (h) | thấp (expect 0) | thường > 0 | 0 (λ_daily=100) |
| 4 | Avg Objective Value (Z) | cao | raw hours | Σ E[i]·f(X_eff) − phạt |
| 5 | Avg Runtime (s) | thấp | ~0.000 s | ~0.5–3 s |

### Kết quả full 300 (replica — đã kiểm chứng trên Tier 3 thật)

| Metric | Greedy | LP | p-value |
|---|---|---|---|
| Feasibility Rate (%) | 70.0 | 100.0 | — |
| Avg Shortfall (h) | 7.88 | 10.58 | <0.001 |
| Avg Overload (h) | 5.04 | 0.00 | <0.001 |
| Avg Objective Fair (cùng Z) | -633.87 | -163.46 | <0.001 |
| Avg Runtime (s) | 0.00 | 5.17 | <0.001 |

Tier 3 thật (`results_real/`): feasibility 70.0/100.0, shortfall 7.88/10.58, overload 5.04/0.00,
objective_fair -633.87/-163.55, runtime 0.00/4.95 — khớp replica tới 0.1.
Đối chứng: `python3 evaluate/compare.py` → mean diff objective_fair 0.099, max 2.23,
feasibility mismatch 0/300.

**Nhắc khi viết Chương 6:**
- Shortfall của LP *cao hơn* Greedy (10.58 vs 7.88) không phải lỗi: LP tôn trọng `max_daily_hours`
  (overload=0) nên chấp nhận thiếu giờ ở deadline, Greedy vi phạm trần ngày (overload 5.04 h)
  để giảm shortfall. Đây là tradeoff của λ_daily=100.
- `avg_objective` gốc (LP Z vs Greedy raw hours) chỉ so định tính; số chính để so là
  `avg_objective_fair` — cùng công thức Z = ΣE·f(X_eff)−20s−100u cho cả hai (mới thêm vào `evaluate.py`/`run_real.py`).
- Breakdown theo type trong `metrics_summary.json` (`by_type`): Light (90), Normal (120),
  Heavy (60), Extreme (30) — Heavy/Extreme Greedy feasibility 0% (có assignment 0 giờ trước deadline).

## Đọc kết quả vào luận văn (Chương 6)

1. Lấy `table_comparison.csv` → dán vào Bảng 6.x.
2. Lấy `chart_comparison.png` → Hình 6.x.
3. Trích p-value từ `metrics_summary.json` (`paired_ttest_pvalues`): shortfall/overload/objective_fair đều <0.001 trên 300 scenarios.
4. Nhắc threats: dataset synthetic, N=300, runtime ~5s/scenario vượt kỳ vọng §3.5 vì CBC single-thread + timeLimit 30s.

## Lưu ý kỹ thuật

- `lp_solver.py` xấp xỉ đúng `tier-3-overview.md`. Nếu chạy số liệu khác với backend Docker (mã `lp-solver/` không nằm trong workspace), chênh lệch chỉ do CBC version/timeLimit — pivot: tăng `timeLimit=30` trong `solve_lp` nếu muốn tối ưu hơn.
- `evaluate.py --limit 20` chỉ lấy 20 scenario đầu (toàn Light). Muốn kiểm tra Extreme cần chạy full hoặc lọc theo type.
- **Runtime Tier 3 thật:** `lp-solver/app/solver.py` gọi `PULP_CBC_CMD(msg=False)` **không có `timeLimit`**, trong khi replica có `timeLimit=30`. Đo thực tế 20 scenarios đầu: replica `avg_runtime_s=2.6s`, Tier 3 thật `avg_runtime_s=23.5s` (riêng `SC_010` mất **449s**). Đây là điểm khác biệt đã đo, không phải đoán. Fix: `prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=30))` trong `lp-solver/app/solver.py` rồi mới chạy full 300, nếu không `run_real.py` sẽ tốn hàng giờ và có thể bị timeout.
- `run_real.py` **không đi qua Tier 1**: gửi thẳng `subjects/time_slots/max_daily_hours` của dataset tới Tier 3. Đây là lựa chọn công bằng nhất (Greedy và LP thấy cùng `available_hours`/`max_daily_hours`). Qua Tier 1 (`schedule_service._build_time_slots`) sẽ bị ghi đè thành 2h/slot cố định và `W_max_effective` từ Risk Score — mất độ đa dạng Light/Normal/Heavy của dataset.
