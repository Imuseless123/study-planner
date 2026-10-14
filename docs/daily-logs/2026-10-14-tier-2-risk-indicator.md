# 📋 Nhật ký công việc — Tầng 2: Workload Risk Indicator

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Giai đoạn:** Tầng 2 — Risk Indicator (FR #10)
**Thời gian:** ~09:00 — 12:30
**Người thực hiện:** Phạm Kim Long

---

## 1. Mục tiêu

Xây dựng **Mô-đun 2 — Workload Risk Indicator** như một service độc lập:
- Rule-based scoring (không ML — minh bạch, kiểm chứng được)
- Không dùng "burnout detection" (lý do đạo đức)
- 4 thành phần: Sleep Deficit, Workload Density, Deadline Proximity, Study Inconsistency
- Disclaimer bắt buộc trong mọi response
- Test suite với coverage ≥ 90%
- Tích hợp với Tầng 1 (Backend proxy + Frontend widget)

**Định vị:** Đây KHÔNG phải là "novel AI framework". Đây là rule-based scoring service sử dụng công thức từ tài liệu tâm lý học giáo dục.

---

## 2. Kiến trúc Tầng 2

### Service độc lập, port 8001

```
┌─────────────────┐         ┌──────────────────────┐
│   Frontend      │         │   Backend (Tier 1)   │
│  (port 3000)    │────────►│   (port 8000)        │
└─────────────────┘         └──────────┬───────────┘
                                       │ HTTP
                                       ▼
                            ┌──────────────────────┐
                            │  Risk Indicator      │
                            │  (port 8001)         │
                            │  - Rule-based        │
                            │  - Pure functions    │
                            └──────────────────────┘
```

**Lý do tách riêng service:**
1. **Separation of concerns** — Risk calculation độc lập với business logic
2. **Scalability** — Có thể scale riêng nếu cần
3. **Testability** — Pure functions, không phụ thuộc DB
4. **Replaceability** — Có thể thay bằng implementation khác qua API

### Công thức (từ thesis §3.6.2)

```
Risk Score = 100 × (0.35·SD + 0.30·WD + 0.20·DP + 0.15·SI)

Where:
  SD = min(1, max(0, 7 - sleep_hours) / 4)       [sleep deficit]
  WD = min(1, required_hours / available_hours)  [workload density]
  DP = 1 / (1 + days_until_deadline)             [deadline proximity]
  SI = min(1, study_std / 3)                     [study inconsistency]
```

**Phân loại:** Low (0-30), Moderate (31-60), High (61-100).

---

## 3. Công việc đã thực hiện

### 3.1. Cấu trúc module

```
risk-indicator/
├── app/
│   ├── calculator.py   # Pure functions (không side effect)
│   ├── schemas.py      # Pydantic v2
│   ├── api.py          # FastAPI router
│   └── main.py         # App entry
├── tests/
│   ├── conftest.py     # Fixtures
│   ├── test_calculator.py  # Unit tests
│   └── test_api.py         # Integration tests
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

### 3.2. Calculator — Pure functions

File `app/calculator.py` (kernel của service):

**Constants:**
- `W_SLEEP_DEFICIT = 0.35`
- `W_WORKLOAD_DENSITY = 0.30`
- `W_DEADLINE_PROXIMITY = 0.20`
- `W_STUDY_INCONSISTENCY = 0.15`
- `DISCLAIMER` — chuỗi tiếng Việt đầy đủ

**Functions:**
- `normalize_sleep_deficit(sleep_hours)` → [0, 1]
- `normalize_workload_density(required, available)` → [0, 1]
- `normalize_deadline_proximity(days)` → (0, 1]
- `normalize_study_inconsistency(std)` → [0, 1]
- `classify_risk(score)` → 'low' | 'moderate' | 'high'
- `calculate_risk_score(sd, wd, dp, si)` → [0, 100]
- `compute_risk(...)` → full pipeline, returns `RiskResult` dataclass

Tất cả functions:
- Pure (không side effect)
- Validate inputs (raise `ValueError` nếu negative)
- Có docstring + examples

### 3.3. Schemas — Pydantic v2

File `app/schemas.py`:
- `RiskRequest` — validate inputs với `Field(ge=, le=, gt=)`
- `RiskResponse` — bao gồm score, level, components, weights, disclaimer
- `RiskComponents` + `RiskWeights` — breakdown chi tiết
- `HealthResponse` — cho `/health`

### 3.4. API endpoints

File `app/api.py`:
- `POST /api/risk/score` — tính risk score từ behavioral inputs
- Error handling: `ValueError` → HTTP 422

File `app/main.py`:
- CORS cho localhost:3000 (frontend) và localhost:8000 (tier-1 backend)
- `GET /health` + `GET /`

### 3.5. Docker Compose

Thêm service `risk-indicator`:
- Build từ `./risk-indicator/Dockerfile`
- Port 8001
- Volume mount để hot-reload code

### 3.6. Tích hợp Tầng 1 → Tầng 2

**Backend (Tier 1):**

File `backend/app/services/risk_service.py`:
- Aggregate dữ liệu từ DB:
  - Sleep hours (avg 7 ngày từ `log_repo.get_sleep_hours_last_n_days`)
  - Study std (population std từ `study_by_date`)
  - Required/available hours từ assignments
  - Days until nearest deadline
- Gọi Tier 2 qua httpx: `POST {RISK_API_URL}/api/risk/score`
- Handle error → 502 Bad Gateway

File `backend/app/api/risk.py`:
- Endpoint `GET /api/risk/score` (proxy tới Tier 2)

### 3.7. Frontend Widget

File `frontend/src/api/risk.ts`:
- Type `RiskScore`
- Method `riskApi.getScore()`

File `frontend/src/components/RiskScoreWidget.tsx` (rewrite):
- Circular progress với score
- Tag màu theo level (low/moderate/high)
- Component breakdown (4 Statistic + weight)
- Disclaimer đầy đủ
- Nút refresh + CTA "Ghi thêm nhật ký"
- Loading + Error states

### 3.8. Test Suite

File `pytest.ini`:
- Coverage target: **90%** (cao hơn Tầng 1 vì code đơn giản hơn)
- Report HTML + term-missing

File `tests/conftest.py`:
- `client` fixture — FastAPI TestClient
- `good_habits_payload`, `high_risk_payload`, `boundary_payload`

File `tests/test_calculator.py` (~35 tests):
- Weight invariants (sum = 1)
- Normalize functions: boundary + error cases
- Classify risk: 6 boundary tests
- Calculate: all-zero, all-one, only-one-component
- Compute risk: good/high/boundary scenarios từ thesis

File `tests/test_api.py` (~9 tests):
- Health + root
- Risk endpoint: good/high/boundary
- Response structure: disclaimer, components, weights
- Validation: sleep>24, negative, required=0, missing field

---

## 4. Test Scenarios (từ thesis §3.6.2)

### Scenario 1: Good habits (low risk)

**Input:**
```
sleep_hours=8, required=10, available=40, days=14, std=0.49
```

**Components:**
- SD = max(0, 7-8)/4 = 0
- WD = 10/40 = 0.25
- DP = 1/(1+14) = 0.0667
- SI = min(1, 0.49/3) = 0.1633

**Score:**
```
100 × (0.35×0 + 0.30×0.25 + 0.20×0.0667 + 0.15×0.1633)
= 100 × (0 + 0.075 + 0.0133 + 0.0245)
= 11.28 ≈ 11.3
```

**Expected:** ~11.3, level = "low" ✓

### Scenario 2: High risk

**Input:**
```
sleep_hours=5, required=30, available=40, days=2, std=3.06
```

**Components:**
- SD = max(0, 7-5)/4 = 0.5
- WD = 30/40 = 0.75
- DP = 1/(1+2) = 0.3333
- SI = min(1, 3.06/3) = 1.0

**Score:**
```
100 × (0.35×0.5 + 0.30×0.75 + 0.20×0.3333 + 0.15×1.0)
= 100 × (0.175 + 0.225 + 0.0667 + 0.15)
= 61.67 ≈ 61.7
```

**Expected:** ~61.7, level = "high" ✓

### Scenario 3: Boundary (all max)

**Input:**
```
sleep_hours=3, required=40, available=40, days=0, std=3.0
```

**Components:** All = 1.0

**Score:** 100 × (0.35 + 0.30 + 0.20 + 0.15) = **100.0** ✓

→ Cả 3 scenarios khớp với giá trị kỳ vọng trong luận văn.

---

## 5. Nguyên tắc đạo đức (ethics)

### 5.1. Không dùng "Burnout Detection"

**Lý do:**
- Burnout là khái niệm tâm lý lâm sàng (clinical psychological concept)
- Cần thang đo chuẩn (Maslach Burnout Inventory) + chuyên gia
- Không thể suy ra từ self-reported data (sleep + mood)
- Có rủi ro gây lo lắng không cần thiết nếu user hiểu nhầm là chẩn đoán y tế

**Thay thế:**
- Chỉ cung cấp **workload stress indicator** (chỉ báo căng thẳng do khối lượng công việc)
- Dựa trên 4 yếu tố behavioral observable
- Có disclaimer rõ ràng: "KHÔNG phải chẩn đoán y tế/tâm lý"

### 5.2. Disclaimer bắt buộc

Mọi response từ `/api/risk/score` đều chứa `disclaimer` (chuỗi >100 ký tự) với:
- Nêu rõ đây là behavioral indicator, không phải medical diagnosis
- Khuyến nghị tìm chuyên gia nếu kiệt sức kéo dài
- Không thay thế tư vấn chuyên nghiệp

### 5.3. Transparent formula

- Công thức public, có thể audit
- Weights và normalizations giải thích bằng comments
- Pure functions → dễ verify bằng đọc code
- Không có hidden ML model

---

## 6. Điểm kỹ thuật đáng chú ý

### 6.1. Pure functions testability

Tất cả logic calculation là pure functions (không side effect):
- `normalize_sleep_deficit(8)` luôn trả về `0.0`
- Dễ test, không cần mock DB
- Có thể verify bằng mental math

### 6.2. Pydantic v2 Field validation

Request schema dùng Field validators:
- `ge=0, le=24` cho sleep_hours
- `gt=0` cho required/available_hours
- `ge=0, le=365` cho days_until_deadline

FastAPI tự return 422 khi input invalid — không cần custom validation.

### 6.3. Error handling tại Service boundary

Backend Tier 1 bọc Tier 2 call trong try/except:
```python
try:
    r = await http.post(...)
    r.raise_for_status()
    return r.json()
except httpx.HTTPError as e:
    raise HTTPException(502, f"Risk service unavailable: {e}")
```

Tránh leak internal error của Tier 2 ra client.

### 6.4. Data aggregation logic

Backend Tier 1 aggregate data trước khi call Tier 2:
- Sleep: average of last 7 days
- Study std: population std (matching thesis §3.6.2)
- Required hours: sum of all upcoming assignments
- Available hours: naive estimate 6h/day
- Days until deadline: from nearest assignment

**Future improvement:** available_hours nên tính từ user's actual calendar (chưa có feature này).

---

## 7. Trạng thái 14 FR

| # | Chức năng | Trước | Sau |
|---|-----------|:-----:|:---:|
| 1-9 | (như trước) | ✅ | ✅ |
| **10** | **Risk widget** | ❌ | ✅ **Done** |
| 11-14 | Schedule, Feedback, Data | ❌ | ❌ |

**10/14 FR hoàn thành** — vượt 70%.

---

## 8. Bài học kinh nghiệm

### 8.1. Về microservice design

- **Service độc lập** đơn giản hơn monolith cho module có thể tách biệt
- **Container hóa** → dev/prod parity dễ dàng
- **Healthcheck** giúp orchestration reliable
- **CORS** phải config đúng cho các origin

### 8.2. Về rule-based system

- **Pure functions** = dễ test, không cần mock
- **Constants at top** = dễ điều chỉnh weights
- **Docstring + examples** = code tự document
- **Type hints** = catch bugs sớm

### 8.3. Về ethics trong ML/AI systems

- **Không phải cứ có dữ liệu là được phép kết luận**
- Self-reported behavioral data → behavioral indicator, không phải diagnosis
- **Disclaimer không phải "cover ass"** mà là responsible design
- **Formula transparent** > black-box ML cho sensitive domains

### 8.4. Về integration testing

- Test Tier 2 độc lập trước khi tích hợp
- Boundary scenarios (0, 100) quan trọng hơn happy path
- Verify số cụ thể khớp với thesis (11.3, 61.7, 100)

---

## 9. Công việc tiếp theo

### Ưu tiên cao

1. **Tầng 3 — LP Optimization Engine** (FR #11, #12)
   - MILP với PuLP
   - Diminishing returns function (√x)
   - 7 nhóm ràng buộc
   - Tích hợp risk score vào W_max_effective

### Ưu tiên trung bình

2. **Feature Feedback** (FR #13) — sau khi có Tầng 3
3. **Sensitivity analysis** của weights (cho Chương 6)

### Ưu tiên sau

4. Deploy lên Railway/Render
5. User testing (SUS 5-15 users)

---

## 10. Thống kê công việc

| Metric | Số lượng |
|--------|----------|
| Files tạo mới | 12 |
| Lines of code (backend) | ~400 LOC |
| Lines of code (tests) | ~350 LOC |
| Lines of code (frontend) | ~250 LOC |
| Endpoints mới | 2 |
| Test cases | ~44 |
| Test coverage target | ≥90% |

---

## 11. Bug fix — required_hours=0 validation

### Triệu chứng

Khi gọi `GET /api/risk/score` từ Tier 1 (user bob **không có assignment nào**):
```
502 Bad Gateway
Detail: Risk Indicator service unavailable: Client error
'422 Unprocessable Entity' for url 'http://risk-indicator:8001/api/risk/score'
```

### Nguyên nhân

Trong `risk_service.py`:
```python
if not upcoming:
    required_hours = 0.0    # gửi 0 khi không có bài tập
```

Nhưng schema Tier 2 ban đầu:
```python
required_hours: float = Field(gt=0, ...)   # bắt buộc > 0
```

→ Pydantic reject `required_hours=0` → 422 → backend bọc thành 502.

### Fix

Đổi `gt=0` → `ge=0` trong `risk-indicator/app/schemas.py`:
```python
required_hours: float = Field(
    ge=0, le=100,
    description="Total hours needed... (0 if no upcoming assignments)",
)
```

**Cơ sở logic:**
- `required_hours = 0` là **state hợp lệ về mặt nghiệp vụ** (user chưa có assignment)
- `available_hours` vẫn giữ `gt=0` vì chia cho 0 là vô nghĩa
- Validate theo **domain semantics**, không theo "số học có ý nghĩa"

### Tests updated

- `test_required_hours_zero_is_valid` → expect 200 (thay vì 422)
- `test_validation_negative_required` → vẫn expect 422 (âm không hợp lệ)
- `test_validation_available_zero` → vẫn expect 422 (chia 0)

### Verification

| Test | Kết quả |
|------|---------|
| Health check Tier 2 | ✅ 200 |
| Direct Tier 2 với required_hours=0 | ✅ 200, score=3.15 |
| Tier 1 proxy (bob không có assignment) | ✅ 200, score=0.65 |
| Test suite | ✅ 53 passed |

**Sự khác biệt 3.15 vs 0.65 là hành vi đúng:**
- Direct test dùng input cố định (`study_std=0.5`)
- Tier 1 aggregate từ DB thật (bob không có study session → `study_std=0`)

---

## Tiến độ tổng thể

| # | Feature | Backend | Frontend | Tests | Status |
|---|---------|:-------:|:--------:|:-----:|:------:|
| 1 | Authentication | ✅ | ✅ | ✅ | ✅ |
| 2 | Consent | ✅ | ✅ | ✅ | ✅ |
| 3 | Log study | ✅ | ✅ | ✅ | ✅ |
| 4 | Log sleep | ✅ | ✅ | ✅ | ✅ |
| 5 | Log mood | ✅ | ✅ | ✅ | ✅ |
| 6 | CRUD Subjects | ✅ | ✅ | ✅ | ✅ |
| 7 | CRUD Assignments | ✅ | ✅ | ✅ | ✅ |
| 8 | Dashboard Heatmap | ✅ | ✅ | ✅ | ✅ |
| 9 | Dashboard Timeline | ✅ | ✅ | ✅ | ✅ |
| **10** | **Risk Widget** | ✅ | ✅ | ✅ | ✅ |
| 11 | Schedule Generation | ❌ | ❌ | ❌ | ⏳ Tầng 3 |
| 12 | Constraint Explanation | ❌ | ❌ | ❌ | ⏳ Tầng 3 |
| 13 | Feedback | ❌ | ❌ | ❌ | ❌ |
| 14 | Data Export/Delete | ✅ | ✅ | ✅ | ✅ |

**10/14 FR hoàn thành (71%)**

**Test suite hiện tại:**
- Tier 1: **93 tests** (coverage 93.89%)
- Tier 2: **53 tests** (coverage > 90%)
- **Total: 146 automated tests**

---

## 🎯 Tiếp theo: Tầng 3 — LP Optimization Engine

Đây là **phần phức tạp nhất** trong 3 tầng. Cần:

### Các khái niệm toán học

1. **MILP (Mixed-Integer Linear Programming)** với PuLP
2. **Diminishing returns** function `f(x) = √x`, xấp xỉ 4 đoạn tuyến tính
3. **7 nhóm ràng buộc:**
   - Không âm
   - Giới hạn khung giờ: `Σx[i,t] ≤ H[t]`
   - Giới hạn ngày: `Σx[i,t] ≤ W_max`
   - Hoàn thành deadline: `Σx[i,t] ≥ R[i]`
   - Giới hạn tổng giờ theo môn: `Σx[i,t] ≤ R[i] × (1+buffer)`
   - Thời gian tối thiểu phiên: `X_min ≤ x[i,t] ≤ M × y[i,t]`
   - Không học sau deadline: `x[i,t] = 0` nếu ngày > d[i]

4. **Soft constraints** cho deadline và daily limit (qua slack variables `s[i]` và `u[d]`)
5. **Tích hợp risk** qua `W_max_effective = W_max × (1 - α × Risk/100)` với α=0.5

### Công việc chính

| Task | Mô tả |
|------|-------|
| **Service** | MILP service độc lập trên port 8002 |
| **Model** | `build_model()` với biến x, y, δ, s, u |
| **Objective** | `Maximize Z = Σ E[i,d] × Σ slope[k] × δ[i,d,k] − λ₁Σs − λ₂Σu` |
| **Solver** | PuLP 2.9.x với CBC |
| **Endpoints** | `POST /api/schedule/generate`, `GET /api/schedule/latest` |
| **Test suite** | 8-10 ca: feasible, infeasible, boundary, tight |
| **Backend integration** | `schedule_service.py` gọi Tier 3 |
| **Frontend** | Trang `/schedule` với calendar view + feedback |
| **Fallback** | Cơ chế 2 bước khi solver báo Infeasible |

## 12. Kết luận

**Tầng 2 — Workload Risk Indicator đã hoàn thành:**

1. **Service độc lập** trên port 8001, build + run qua Docker
2. **Rule-based scoring** với 4 thành phần từ thesis
3. **Pure functions** với ~35 unit tests + 9 integration tests
4. **Disclaimer bắt buộc** trong mọi response
5. **Tích hợp Tier 1** qua HTTP proxy
6. **Frontend widget** hiển thị risk score thực tế (thay placeholder)
7. **Ethics-first design** — không claim diagnosis

**Verification:**
- Scenario 1 (good habits): score ~11.3, level = low ✓
- Scenario 2 (high risk): score ~61.7, level = high ✓
- Scenario 3 (boundary): score = 100, level = high ✓

**Đây là Tầng 2 hoàn chỉnh, sẵn sàng làm input cho Tầng 3 (LP Solver) — nơi risk score sẽ điều chỉnh W_max_effective.**

**Tiếp theo:** Tầng 3 — LP Optimization Engine.

---

**Người lập log:** Phạm Kim Long
**Ngày:** 14/10/2026