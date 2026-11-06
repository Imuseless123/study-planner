# ⚙️ Tầng 3 — LP Optimization Engine

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Phiên bản:** 1.0
**Ngày hoàn thành:** 19/10/2026
**Trạng thái:** ✅ Hoàn thành (2/14 FR)

---

## 📌 Tổng quan

Tầng 3 là **lõi thông minh** của hệ thống, chịu trách nhiệm tạo ra lịch học tối ưu. Đây là một microservice độc lập sử dụng kỹ thuật **MILP (Mixed-Integer Linear Programming)** — Quy hoạch tuyến tính hỗn hợp nguyên.

**Điểm khác biệt cốt lõi so với các hệ thống khác:**
- **Diminishing Returns (Lợi nhuận giảm dần):** Học 2 giờ đầu hiệu quả cao, 2 giờ sau hiệu quả thấp hơn. Hàm mục tiêu sử dụng xấp xỉ tuyến tính của `√x`.
- **Soft Constraints:** Không ép user vào ngõ cụt. Nếu không thể hoàn thành deadline, solver trả về lịch kèm cảnh báo (shortfall) thay vì báo lỗi.
- **Risk-aware:** Trần giờ học hàng ngày (`W_max_effective`) bị điều chỉnh giảm nếu điểm rủi ro từ Tầng 2 cao.

### Tech Stack

| Layer | Công nghệ | Phiên bản |
|-------|-----------|-----------|
| **Framework** | FastAPI + Python | 0.104 / 3.11 |
| **Solver** | PuLP + CBC Solver | 2.9 / coinor-cbc |
| **Data validation** | Pydantic | 2.5 |
| **Deployment** | Docker (Port 8002) | — |

---

## 🧮 Mô hình Toán học

### Biến quyết định (Decision Variables)

| Biến | Miền | Diễn giải |
|------|------|-----------|
| `x[i,d,t]` | ℝ ≥ 0 | Số giờ học môn `i` vào ngày `d`, khung giờ `t` |
| `y[i,d,t]` | {0, 1} | = 1 nếu có phiên học (dùng cho ràng buộc thời gian tối thiểu) |
| `δ[i,d,k]` | [0, width_k] | Số giờ trong đoạn thứ `k` của xấp xỉ hàm `√x` |
| `s[i]` | ℝ ≥ 0 | Slack variable: Số giờ thiếu hụt trước deadline |
| `u[d]` | ℝ ≥ 0 | Slack variable: Số giờ vượt trần cho phép trong ngày `d` |

### Hàm mục tiêu (Objective Function)

```
Maximize Z = Σ E[i] · f(X_eff[i,d]) 
           − λ₁ · Σ s[i]           (phạt thiếu deadline)
           − λ₂ · Σ u[d]           (phạt vượt trần ngày)
```
- `E[i]` = urgency × difficulty × priority (Hệ số hiệu quả của môn học).
- `f(X_eff)` = Xấp xỉ tuyến tính từng đoạn của `√X_eff`.

### Xấp xỉ tuyến tính từng đoạn (Piecewise Linear Approximation)

Hàm `f(x) = √x` được xấp xỉ bằng 4 đoạn tuyến tính trên khoảng [0, 4]:

| Đoạn | Khoảng | Độ dốc (Slope) |
|:----:|:------:|:--------------:|
| 1 | [0, 0.5] | 1.414 |
| 2 | [0.5, 1.0] | 0.586 |
| 3 | [1.0, 2.0] | 0.414 |
| 4 | [2.0, 4.0] | 0.293 |

*Do độ dốc giảm dần và bài toán là Maximize, LP solver tự nhiên lấp đầy các đoạn có slope cao trước mà không cần thêm biến nhị phân cho segment ordering.*

### Các nhóm ràng buộc (Constraints)

1. **Slot Availability:** Tổng giờ học tại một khung giờ không vượt quá thời gian rảnh thực tế.
2. **Daily Cap (Soft):** Tổng giờ học 1 ngày ≤ `W_max_effective` + `u[d]`.
3. **Deadline (Soft):** Tổng giờ học trước deadline + `s[i]` ≥ Số giờ yêu cầu.
4. **Subject Buffer:** Tổng giờ học 1 môn ≤ `Required_hours × (1 + 25%)`.
5. **Min Session:** Nếu học thì phải học ít nhất 30 phút (X_min).
6. **No Study After Deadline:** Không học sau ngày deadline.
7. **X_eff Cap:** Giới hạn giờ học hiệu dụng để đảm bảo xấp xỉ tuyến tính hợp lệ.

### Tuning Penalty Weights

- `λ_daily = 100`: Phải lớn hơn max marginal gain (E_max × slope_max ≈ 35) để solver không bao giờ tự ý phá trần giờ học.
- `λ_deadline = 20`: Đủ cao để ưu tiên deadline, nhưng thấp hơn λ_daily để solver ưu tiên cảnh báo thiếu deadline thay vì ép user học quá tải.

---

## 🔌 API Endpoints

| Method | Endpoint | Chức năng |
|--------|----------|-----------|
| **POST** | `/api/schedule/generate` | Nhận input bài tập + rủi ro, trả về lịch tối ưu |
| **GET** | `/health` | Health check |

**Request Body (Rút gọn):**
```json
{
  "subjects": [
    {"id": "math", "required_hours": 4, "deadline_day": 0, "difficulty": 4, "priority": 5}
  ],
  "time_slots": [
    {"day": 0, "slot": 0, "tod_factor": 1.2, "available_hours": 2}
  ],
  "max_daily_hours": 4.9
}
```

**Response Body (Rút gọn):**
```json
{
  "status": "optimal",
  "feasible": true,
  "schedule": [
    {"subject_id": "math", "day": 0, "slot": 0, "hours": 1.5}
  ],
  "explanation": { "per_subject": [...], "per_day": [...] },
  "warnings": [],
  "objective_value": 52.6
}
```

---

## 📈 Metrics

| Metric | Value |
|--------|-------|
| Unit + Integration tests | 24 |
| Coverage | 92.98% |
| Test runtime | 0.11s |