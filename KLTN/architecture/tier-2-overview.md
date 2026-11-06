# 🧠 Tầng 2 — Workload Risk Indicator

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Phiên bản:** 1.0
**Ngày hoàn thành:** 14/10/2026
**Trạng thái:** ✅ Hoàn thành (1/14 FR)

---

## 📌 Tổng quan

Tầng 2 là một **microservice độc lập** chịu trách nhiệm đánh giá mức độ căng thẳng do khối lượng công việc dựa trên dữ liệu hành vi tự báo cáo. 

**Nguyên tắc cốt lõi:**
- **Rule-based (Không ML):** Đảm bảo tính minh bạch, dễ kiểm chứng bằng cách đọc mã nguồn. Không có "hộp đen" AI.
- **Không chẩn đoán lâm sàng:** Hệ thống từ chối sử dụng khái niệm "Burnout Detection" (kiệt sức) vì đây là khái niệm tâm lý lâm sàng, cần thang đo chuẩn và chuyên gia. Tầng 2 chỉ đưa ra **Workload Stress Indicator** (Chỉ báo căng thẳng do khối lượng công việc).
- **Disclaimer bắt buộc:** Mọi response trả về đều phải kèm theo tuyên bố miễn trừ trách nhiệm y tế/tâm lý.

### Tech Stack

| Layer | Công nghệ | Phiên bản |
|-------|-----------|-----------|
| **Framework** | FastAPI + Python | 0.104 / 3.11 |
| **Data validation** | Pydantic | 2.5 |
| **Deployment** | Docker (Port 8001) | — |
| **Testing** | Pytest | 7.4 |

---

## 🔄 Data Flow

```
Backend (Tier 1)
    │
    │  1. Aggregates behavioral data (Sleep, Study Std, Assignments)
    │  2. POST /api/risk/score {payload}
    ▼
┌───────────────────────────────┐
│  Risk Indicator (Tier 2)      │
│                               │
│  - Normalize 4 components     │
│  - Apply weights              │
│  - Classify risk (0-100)      │
│  - Attach disclaimer          │
└───────────────┬───────────────┘
                │
                │ 3. Returns {risk_score, level, components, disclaimer}
                ▼
Backend (Tier 1) ──► Dashboard (Frontend) / LP Solver (Tier 3)
```

---

## 🧮 Công thức tính điểm (Risk Score)

Điểm rủi ro được tính từ 4 thành phần, mỗi thành phần chuẩn hóa về khoảng [0, 1].

**Công thức tổng quát:**
`Risk Score = 100 × (w1·SD + w2·WD + w3·DP + w4·SI)`

### Các thành phần (Components)

| Thành phần | Định nghĩa | Công thức chuẩn hóa |
|------------|------------|---------------------|
| **SD (Sleep Deficit)** | Mức thiếu ngủ so với khuyến nghị 7-8h | `min(1, max(0, 7 - sleep_hours) / 4)` |
| **WD (Workload Density)** | Mật độ khối lượng công việc | `min(1, required_hours / available_hours)` |
| **DP (Deadline Proximity)** | Độ gần thời hạn (tính bằng ngày) | `1 / (1 + days_until_deadline)` |
| **SI (Study Inconsistency)** | Độ lệch chuẩn thời gian học hàng ngày | `min(1, std(daily_study_hours) / 3)` |

### Trọng số khởi tạo (Weights)

| Trọng số | Giá trị | Cơ sở khoa học |
|----------|:-------:|----------------|
| **w1 (Sleep)** | 0.35 | Thiếu ngủ ảnh hưởng trực tiếp đến nhận thức (trọng số cao nhất). |
| **w2 (Workload)** | 0.30 | Chỉ số trực tiếp của áp lực học tập. |
| **w3 (Deadline)** | 0.20 | Tăng căng thẳng nhưng giảm nhanh sau khi vượt qua. |
| **w4 (Inconsistency)** | 0.15 | Ảnh hưởng gián tiếp qua chất lượng học tập. |

### Phân loại đầu ra (Classification)

| Mức | Khoảng điểm | Màu UI |
|-----|:-----------:|--------|
| **Low** | 0 — 30 | Xanh lá |
| **Moderate** | 31 — 60 | Vàng / Cam |
| **High** | 61 — 100 | Đỏ |

---

## 🔌 API Endpoints

Hệ thống cung cấp 1 endpoint chính:

| Method | Endpoint | Chức năng |
|--------|----------|-----------|
| **POST** | `/api/risk/score` | Tính điểm rủi ro từ dữ liệu hành vi |
| **GET** | `/health` | Health check cho Docker orchestration |

**Request Body (Pydantic Model):**
```json
{
  "sleep_hours": 7.5,
  "required_hours": 15.0,
  "available_hours": 40.0,
  "days_until_deadline": 5,
  "study_std": 1.2
}
```

**Response Body:**
```json
{
  "risk_score": 36.6,
  "level": "moderate",
  "components": {
    "sleep_deficit": 0.0,
    "workload_density": 0.375,
    "deadline_proximity": 0.166,
    "study_inconsistency": 0.4
  },
  "weights": { "sleep_deficit": 0.35, "workload_density": 0.30, ... },
  "disclaimer": "Chỉ báo này phản ánh mức độ căng thẳng..."
}
```

---

## 🔐 Security & Privacy

- **Stateless:** Tầng 2 không lưu trữ bất kỳ dữ liệu nào của người dùng (không có Database). Nó chỉ nhận input, tính toán và trả về output.
- **No PII:** Request không chứa thông tin cá nhân (tên, email), chỉ chứa số liệu tổng hợp.
- **CORS:** Chỉ cho phép gọi từ Tier 1 Backend (`localhost:8000`) và Frontend (`localhost:3000`).

---

## 📈 Metrics

| Metric | Value |
|--------|-------|
| Unit + Integration tests | 53 |
| Coverage | 92.98% |
| Test runtime | 0.05s |