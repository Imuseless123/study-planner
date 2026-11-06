# Luồng dữ liệu End-to-End — Study Planner

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Phạm vi:** Tầng 1 (Web App) → Tầng 2 (Risk Indicator) → Tầng 3 (LP Solver)
**Ngày cập nhật:** 31/10/2026

Tài liệu này mô tả chi tiết dữ liệu đi qua hệ thống như thế nào:

1. Người dùng nhập dữ liệu ở file frontend nào.
2. Dữ liệu được gọi qua API nào của backend và lưu vào bảng database nào.
3. Tầng 2 đọc dữ liệu gì từ database, tổng hợp và xử lý ra sao.
4. Tầng 3 nhận dữ liệu gì và dùng nó để tạo lịch học như thế nào.

---

## 1. Sơ đồ tổng quát

```text
Người dùng
    │
    ▼
Frontend React (port 3000)
    │  axios + JWT
    ▼
Tầng 1 — FastAPI (port 8000)
    │  SQLAlchemy
    ▼
PostgreSQL (port 5432)
    ▲
    │  Tầng 1 đọc dữ liệu đã lưu, tổng hợp thành payload
    │
    ├── HTTP POST /api/risk/score ──────► Tầng 2 — Risk Indicator (port 8001)
    │                                          │
    │                                          └── trả risk_score, level, components
    │
    └── HTTP POST /api/schedule/generate ► Tầng 3 — LP Solver (port 8002)
                                               │
                                               └── trả schedule, explanation, warnings
    │
    ▼
Tầng 1 lưu schedule vào DB rồi trả kết quả cho Frontend
```

Điểm quan trọng: **Tầng 2 và Tầng 3 không truy cập database trực tiếp**. Tầng 1 đọc dữ liệu từ PostgreSQL, tổng hợp thành JSON rồi gọi hai service này. Tầng 2 và Tầng 3 chỉ tính toán trên payload nhận được.

---

## 2. Tầng 1 — Dữ liệu vào, API và Database

### 2.1. Đường đi chung của mọi dữ liệu nhập

```text
Component/Page (React)
    │
    │ gọi hàm trong frontend/src/api/*.ts
    ▼
axios instance (frontend/src/api/client.ts)
    │  - baseURL: VITE_API_URL hoặc http://localhost:8000
    │  - tự gắn Authorization: Bearer <access_token>
    ▼
FastAPI route (backend/app/api/*.py)
    │  - Depends(get_current_user): lấy user_id từ JWT
    │  - Pydantic schema: validate kiểu dữ liệu, giới hạn giá trị
    ▼
Repository (backend/app/repositories/*.py)
    │
    ▼
SQLAlchemy ORM model (backend/app/models/orm_models.py)
    │
    ▼
PostgreSQL
```

Các file trung tâm:

| Vai trò | File |
|---|---|
| Axios client, gắn JWT, xử lý 401 | `frontend/src/api/client.ts` |
| Xác thực user từ JWT | `backend/app/api/deps.py` |
| ORM models | `backend/app/models/orm_models.py` |
| Kết nối DB | `backend/app/core/database.py` |

### 2.2. Bảng tổng hợp dữ liệu nhập

| Dữ liệu | File frontend đọc input | Hàm gọi API frontend | Endpoint backend | Hàm xử lý backend | Bảng DB |
|---|---|---|---|---|---|
| Tài khoản | `pages/RegisterPage.tsx`, `pages/LoginPage.tsx` | `api/auth.ts` | `POST /api/auth/register`, `POST /api/auth/login` | `api/auth.py` | `users` |
| Đồng thuận | `pages/ConsentPage.tsx` | `api/consent.ts` | `POST /api/consent` | `api/consent.py` | `consents` |
| Môn học | `pages/SubjectsPage.tsx`, `components/QuickCreateButtons.tsx` | `subjectsApi.create` (`api/subjects.ts:31`) | `POST /api/subjects` | `api/subjects.py:34` → `SubjectRepository.create` | `subjects` |
| Bài tập | `pages/AssignmentsPage.tsx`, `components/QuickCreateButtons.tsx` | `assignmentsApi.create` (`api/assignments.ts:52`) | `POST /api/assignments` | `api/assignments.py:101` → `AssignmentRepository.create` | `assignments` |
| Phiên học | `components/StudyLogForm.tsx`, `components/QuickStudyBar.tsx` | `logsApi.createStudy` (`api/logs.ts:52`) | `POST /api/log/study` | `api/logs.py:22` → `LogRepository.create_study_session` | `study_sessions` |
| Giấc ngủ | `components/SleepLogForm.tsx`, `components/QuickSleepWidget.tsx` | `logsApi.createSleep` (`api/logs.ts:66`) | `POST /api/log/sleep` | `api/logs.py:61` → `LogRepository.create_sleep_log` | `sleep_logs` |
| Tâm trạng | `components/MoodLogForm.tsx`, `components/QuickMoodBar.tsx` | `logsApi.createMood` (`api/logs.ts:80`) | `POST /api/log/mood` | `api/logs.py:98` → `LogRepository.upsert_mood_log` | `mood_logs` |

Các trang sử dụng form:

- `pages/LoggingPage.tsx` dùng `StudyLogForm`, `SleepLogForm`, `MoodLogForm` cho 3 tab nhập đầy đủ.
- `pages/DashboardPage.tsx` dùng `QuickStudyBar`, `QuickMoodBar`, `QuickSleepWidget`, `QuickCreateButtons` cho nhập nhanh.

### 2.3. Chi tiết từng loại dữ liệu

#### 2.3.1. Môn học — `subjects`

**Frontend đầy đủ:** `frontend/src/pages/SubjectsPage.tsx`
**Frontend nhập nhanh:** `frontend/src/components/QuickCreateButtons.tsx` (chỉ nhập tên, difficulty và priority mặc định = 3)

Payload gửi lên:

```json
{
  "subject_name": "Cấu trúc dữ liệu",
  "difficulty": 4,
  "priority": 5
}
```

Backend:

- `POST /api/subjects` (`backend/app/api/subjects.py:34`)
- Pydantic `SubjectCreate`: `subject_name` 1-100 ký tự, `difficulty` 1-5, `priority` 1-5.
- `SubjectRepository.create` thêm `user_id` lấy từ JWT rồi ghi vào bảng `subjects`.

Ý nghĩa dữ liệu:

- `difficulty`: độ khó môn học, dùng ở Tầng 3 để tính hệ số hiệu quả.
- `priority`: độ ưu tiên môn học, dùng ở Tầng 3 để tính hệ số hiệu quả.
- `subject_id`: UUID do database sinh, dùng làm khóa ngoại cho bài tập và phiên học.

#### 2.3.2. Bài tập — `assignments`

**Frontend đầy đủ:** `frontend/src/pages/AssignmentsPage.tsx`
**Frontend nhập nhanh:** `frontend/src/components/QuickCreateButtons.tsx`

Payload gửi lên:

```json
{
  "subject_id": "uuid-cua-mon-hoc",
  "title": "Bài tập chương 3",
  "deadline": "2026-11-05T16:59:00.000Z",
  "required_hours": 4.5,
  "priority": 5
}
```

Cách frontend tạo dữ liệu:

- `AssignmentsPage.tsx` dùng Ant Design `DatePicker`, sau đó gọi `values.deadline.toISOString()` để đổi giờ local sang chuỗi ISO UTC.
- `QuickCreateButtons.tsx` mặc định deadline = hiện tại + 7 ngày, 23:59; `required_hours` mặc định 2; `priority` mặc định 3.

Backend:

- `POST /api/assignments` (`backend/app/api/assignments.py:101`)
- Kiểm tra `subject_id` tồn tại và thuộc user hiện tại (`_get_subject_name`).
- Kiểm tra deadline phải ở tương lai (so với UTC).
- Pydantic giới hạn `required_hours` > 0 và <= 100, `priority` 1-5.
- `AssignmentRepository.create` ghi vào bảng `assignments`, `is_completed` mặc định `false`.

Ý nghĩa dữ liệu:

- `deadline`: mốc thời gian Tầng 2 dùng để tính độ gần deadline và Tầng 3 dùng để tính `deadline_day`.
- `required_hours`: số giờ cần học cho bài tập, là nhu cầu chính của bài toán Tầng 3.
- `priority`: độ ưu tiên của bài tập, dùng ở Tầng 3.
- `subject_id`: liên kết bài tập với môn học để lấy `difficulty` của môn.

#### 2.3.3. Phiên học — `study_sessions`

**Frontend đầy đủ:** `frontend/src/components/StudyLogForm.tsx`
**Frontend nhập nhanh:** `frontend/src/components/QuickStudyBar.tsx`

Payload gửi lên:

```json
{
  "subject_id": "uuid-cua-mon-hoc",
  "assignment_id": "uuid-bai-tap-hoac-bo-trong",
  "start_time": "2026-10-31T06:30:00.000Z",
  "duration": 1.5,
  "focus_level": 3
}
```

Cách frontend tạo dữ liệu:

- `StudyLogForm.tsx:23` ghép ngày + giờ người dùng chọn bằng dayjs, sau đó `toISOString()` để gửi UTC.
- `QuickStudyBar.tsx:55` lấy `start_time = hiện tại - duration` (giả định người dùng vừa học xong), `focus_level = 3`, có thể gắn `assignment_id` tùy chọn.

Backend:

- `POST /api/log/study` (`backend/app/api/logs.py:22`)
- Kiểm tra `subject_id` thuộc user (`SubjectRepository.get_by_id`).
- Pydantic `StudyLogRequest`: `duration` > 0 và <= 12, `focus_level` 1-5.
- `LogRepository.create_study_session` ghi vào bảng `study_sessions`.

Dữ liệu này được dùng ở Tầng 2 để tính độ nhất quán học tập (`study_std`).

#### 2.3.4. Giấc ngủ — `sleep_logs`

**Frontend đầy đủ:** `frontend/src/components/SleepLogForm.tsx`
**Frontend nhập nhanh:** `frontend/src/components/QuickSleepWidget.tsx`

Payload gửi lên:

```json
{
  "sleep_time": "2026-10-30T16:00:00.000Z",
  "wake_time": "2026-10-31T00:00:00.000Z",
  "quality": 4
}
```

Cách frontend tạo dữ liệu:

- `SleepLogForm.tsx:18` ghép ngày đi ngủ với giờ đi ngủ và giờ thức. Nếu giờ thức <= giờ ngủ thì tự cộng thêm 1 ngày (`SleepLogForm.tsx:32-36`).
- `QuickSleepWidget.tsx:84` tự tính:
  - `wake_time` = thời điểm hiện tại.
  - `sleep_time` = giờ đi ngủ thông thường `usual_bedtime` của user (lấy từ `users.usual_bedtime`); nếu giờ đó còn ở tương lai trong ngày thì lùi về hôm qua.
  - Người dùng chỉ chọn chất lượng giấc ngủ 1-5.

Backend:

- `POST /api/log/sleep` (`backend/app/api/logs.py:61`)
- Kiểm tra `wake_time > sleep_time`; nếu không, trả 422.
- Pydantic `SleepLogRequest`: `quality` 1-5.
- `LogRepository.create_sleep_log` ghi vào bảng `sleep_logs`.

Khi đọc danh sách, backend tự tính `hours = (wake_time - sleep_time) / 3600` (`LogRepository.list_sleep_logs`) nhưng **không lưu cột hours vào DB**.

Dữ liệu này được dùng ở Tầng 2 để tính mức thiếu ngủ trung bình 7 ngày.

#### 2.3.5. Tâm trạng — `mood_logs`

**Frontend đầy đủ:** `frontend/src/components/MoodLogForm.tsx`
**Frontend nhập nhanh:** `frontend/src/components/QuickMoodBar.tsx`

Payload gửi lên:

```json
{
  "log_date": "2026-10-31",
  "energy_level": 3,
  "stress_level": 4
}
```

Cách frontend tạo dữ liệu:

- `MoodLogForm.tsx:20` gửi ngày dạng `YYYY-MM-DD`, năng lượng và căng thẳng 1-5.
- `QuickMoodBar.tsx:48` tự gửi khi người dùng đã chọn đủ 2 emoji; ngày = hôm nay; chỉ số emoji 0-4 được đổi thành mức 1-5.

Backend:

- `POST /api/log/mood` (`backend/app/api/logs.py:98`)
- `LogRepository.upsert_mood_log` tìm bản ghi cùng `user_id` + `log_date`; nếu có thì cập nhật, nếu chưa có thì tạo mới.
- Ràng buộc `UNIQUE (user_id, log_date)` đảm bảo mỗi ngày chỉ có 1 bản ghi tâm trạng.

Hiện tại dữ liệu mood được lưu và hiển thị trên dashboard, nhưng **chưa được đưa vào công thức risk của Tầng 2**.

### 2.4. Tóm tắt bảng database liên quan

| Bảng | Cột chính | Nguồn ghi |
|---|---|---|
| `users` | `user_id`, `username`, `password_hash`, `email`, `usual_bedtime` | Register, Settings |
| `subjects` | `subject_id`, `user_id`, `subject_name`, `difficulty`, `priority` | SubjectsPage, QuickCreateButtons |
| `assignments` | `assignment_id`, `user_id`, `subject_id`, `title`, `deadline`, `required_hours`, `priority`, `is_completed` | AssignmentsPage, QuickCreateButtons |
| `study_sessions` | `session_id`, `user_id`, `subject_id`, `assignment_id`, `start_time`, `duration`, `focus_level` | StudyLogForm, QuickStudyBar |
| `sleep_logs` | `sleep_id`, `user_id`, `sleep_time`, `wake_time`, `quality` | SleepLogForm, QuickSleepWidget |
| `mood_logs` | `mood_id`, `user_id`, `log_date`, `energy_level`, `stress_level` | MoodLogForm, QuickMoodBar |
| `schedules` | `schedule_id`, `user_id`, `schedule_data` (JSONB), `feasible`, `risk_score_at_generation`, `warnings` | Tầng 1 sau khi gọi Tầng 3 |
| `feedback` | `feedback_id`, `schedule_id`, `user_id`, `rating`, `comment` | SchedulePage |

---

## 3. Tầng 2 — Đọc dữ liệu, tổng hợp và tính Risk Score

### 3.1. Ai gọi Tầng 2?

Có hai luồng gọi:

1. **Dashboard:** `frontend/src/components/RiskScoreWidget.tsx:25` gọi `riskApi.getScore()` → `GET /api/risk/score`.
2. **Tạo lịch:** `schedule_service.generate_schedule_for_user` gọi nội bộ `fetch_risk_score(user_id, db)`.

Cả hai đều đi qua:

```text
backend/app/api/risk.py:14
    └── backend/app/services/risk_service.py:14 fetch_risk_score()
            └── HTTP POST {RISK_API_URL}/api/risk/score
                    └── risk-indicator/app/api.py compute_risk_score()
```

### 3.2. Tầng 1 đọc gì từ database?

File: `backend/app/services/risk_service.py:14`

| Dữ liệu Tầng 2 cần | Nguồn DB | Hàm lấy dữ liệu | Cách tổng hợp |
|---|---|---|---|
| `sleep_hours` | `sleep_logs` | `LogRepository.get_sleep_hours_last_n_days(user_id, n=7)` | Lấy các log có `sleep_time >= now - 7 ngày`, tính từng `(wake_time - sleep_time)/3600`, rồi lấy trung bình. Nếu không có log nào thì mặc định 7.0 giờ. |
| `study_std` | `study_sessions` | `LogRepository.get_study_hours_last_n_days(user_id, n=7)` | Group theo ngày, cộng `duration`; sau đó tính độ lệch chuẩn population của các ngày có học. Nếu ít hơn 2 ngày có dữ liệu thì `study_std = 0`. |
| `required_hours` | `assignments` | `AssignmentRepository.list_upcoming(user_id, days=30)` | Lấy bài tập có deadline từ hiện tại đến +30 ngày và `is_completed = false`; cộng tổng `required_hours`. Nếu không có thì 0. |
| `days_until_deadline` | `assignments` | Cùng danh sách trên | Lấy bài tập có deadline gần nhất; tính số ngày còn lại (làm tròn xuống theo `.days`), tối thiểu 0. Nếu không có bài tập thì mặc định 30. |
| `available_hours` | Không có trong DB | Tính trong service | `max(1.0, days_until_deadline * 6.0)` — giả định mỗi ngày có 6 giờ rảnh để học. |

Payload gửi sang Tầng 2:

```json
{
  "sleep_hours": 6.5,
  "required_hours": 15.0,
  "available_hours": 30.0,
  "days_until_deadline": 5,
  "study_std": 1.2
}
```

### 3.3. Tầng 2 xử lý như thế nào?

File: `risk-indicator/app/calculator.py`

Nguyên tắc: rule-based, không ML, không chẩn đoán y tế/tâm lý, luôn kèm disclaimer.

Bốn thành phần được chuẩn hóa về `[0, 1]`:

| Thành phần | Công thức | File |
|---|---|---|
| `SD` — Sleep Deficit | `min(1, max(0, 7 - sleep_hours) / 4)` | `calculator.py:61` |
| `WD` — Workload Density | `min(1, required_hours / available_hours)` | `calculator.py:81` |
| `DP` — Deadline Proximity | `1 / (1 + days_until_deadline)` | `calculator.py:107` |
| `SI` — Study Inconsistency | `min(1, study_std / 3)` | `calculator.py:127` |

Điểm rủi ro:

```text
risk_score = 100 × (
    0.35 × SD +
    0.30 × WD +
    0.20 × DP +
    0.15 × SI
)
```

Trọng số nằm ở `calculator.py:30-33`.

Phân loại (`calculator.py:151`):

| Điểm | Mức |
|---|---|
| 0 — 30 | `low` |
| 31 — 60 | `moderate` |
| 61 — 100 | `high` |

Ví dụ:

```text
sleep_hours = 6        → SD = (7-6)/4 = 0.25
required_hours = 20    → WD = 20/30 = 0.6667
available_hours = 30
days_until_deadline = 3 → DP = 1/(1+3) = 0.25
study_std = 1.5        → SI = 1.5/3 = 0.5

risk_score = 100 × (0.35×0.25 + 0.30×0.6667 + 0.20×0.25 + 0.15×0.5)
           = 41.25  →  level = "moderate"
```

### 3.4. Tầng 2 trả về gì?

```json
{
  "risk_score": 41.25,
  "level": "moderate",
  "components": {
    "sleep_deficit": 0.25,
    "workload_density": 0.6667,
    "deadline_proximity": 0.25,
    "study_inconsistency": 0.5
  },
  "weights": {
    "sleep_deficit": 0.35,
    "workload_density": 0.30,
    "deadline_proximity": 0.20,
    "study_inconsistency": 0.15
  },
  "disclaimer": "Chỉ báo này phản ánh mức độ căng thẳng..."
}
```

Kết quả được dùng ở hai nơi:

- Frontend `RiskScoreWidget` hiển thị điểm, mức, các thành phần và disclaimer.
- `schedule_service` dùng `risk_score` để giảm trần giờ học mỗi ngày trước khi gọi Tầng 3.

---

## 4. Tầng 3 — Dùng dữ liệu để tạo lịch học

### 4.1. Luồng gọi

```text
frontend/src/pages/SchedulePage.tsx:66
    └── scheduleApi.generate()
            └── POST /api/schedule/generate
                    └── backend/app/api/schedule.py:17
                            └── backend/app/services/schedule_service.py:110
                                    generate_schedule_for_user()
```

Ngoài ra khi mở trang, `SchedulePage.tsx:47` gọi `GET /api/schedule/latest` để lấy lịch gần nhất đã lưu.

### 4.2. Bước 1 — Tầng 1 gom bài tập thành input cho LP

File: `backend/app/services/schedule_service.py:40` — `_aggregate_subjects`

Điều kiện lấy bài tập:

- Thuộc user hiện tại.
- `deadline > now` (chưa quá hạn).

Mỗi **bài tập** trở thành một **subject đầu vào của LP** (không phải mỗi môn học). Đây là điểm dễ nhầm:

| Trường gửi sang Tầng 3 | Lấy từ đâu | Ghi chú |
|---|---|---|
| `id` | `assignment_id` | Mỗi bài tập là một "subject" riêng trong LP |
| `required_hours` | `assignments.required_hours` | Số giờ cần học |
| `deadline_day` | `max(0, (deadline - now).days)` | Số ngày tính từ hôm nay, dùng giờ UTC |
| `difficulty` | `subjects.difficulty` của môn chứa bài tập | Lấy qua `subjects_by_id` |
| `priority` | `assignments.priority` | Ưu tiên của bài tập, không phải ưu tiên môn |
| `urgency` | Không gửi | Tầng 3 tự tính `1 / (1 + deadline_day)` |

Ví dụ dữ liệu sau khi gom:

```json
{
  "subjects": [
    {
      "id": "assignment-uuid-1",
      "required_hours": 4.5,
      "deadline_day": 5,
      "difficulty": 4,
      "priority": 5
    },
    {
      "id": "assignment-uuid-2",
      "required_hours": 2.0,
      "deadline_day": 2,
      "difficulty": 3,
      "priority": 4
    }
  ]
}
```

Nếu không có bài tập nào có deadline trong tương lai, Tầng 1 trả ngay:

```json
{
  "status": "no_assignments",
  "feasible": false,
  "schedule": [],
  "warnings": [{ "type": "no_assignments", "message": "..." }]
}
```

và không gọi Tầng 3.

### 4.3. Bước 2 — Lấy Risk Score và tính trần giờ học

File: `backend/app/services/schedule_service.py:141-144`

```text
risk_score = kết quả từ Tầng 2

w_max_effective = DEFAULT_W_MAX × (1 - ALPHA × risk_score / 100)
                = 6.0 × (1 - 0.5 × risk_score / 100)

w_max_effective = max(0.5, w_max_effective)
```

Trong đó:

- `DEFAULT_W_MAX = 6.0` giờ/ngày (`schedule_service.py:16`)
- `ALPHA = 0.5` (`schedule_service.py:15`)

Ví dụ:

| Risk score | W_max_effective |
|---|---|
| 0 | 6.0 giờ/ngày |
| 40 | `6 × (1 - 0.5×0.4) = 4.8` giờ/ngày |
| 80 | `6 × (1 - 0.5×0.8) = 3.6` giờ/ngày |
| 100 | `6 × (1 - 0.5) = 3.0` giờ/ngày |

Risk càng cao thì trần giờ học mỗi ngày càng thấp.

### 4.4. Bước 3 — Tạo khung thời gian (time slots)

File: `backend/app/services/schedule_service.py:96-108`

- Mỗi ngày có 3 khung: `slot = 0` sáng, `1` chiều, `2` tối.
- Mỗi khung có `available_hours = 2.0`.
- Hệ số thời điểm trong ngày `tod_factor`:

| Slot | Thời điểm | tod_factor |
|---|---|---|
| 0 | Sáng | 1.2 |
| 1 | Chiều | 1.0 |
| 2 | Tối | 0.8 |

Tổng dung lượng tối đa là `3 × 2 = 6` giờ/ngày, khớp với `DEFAULT_W_MAX`.

Số ngày của lịch (`horizon`):

```text
horizon = min(max(DEFAULT_HORIZON_DAYS, max_deadline_day + 1), MAX_HORIZON_DAYS)
        = min(max(7, max_deadline_day + 1), 30)
```

Nghĩa là lịch tối thiểu 7 ngày, tối đa 30 ngày, và luôn phủ qua deadline xa nhất (trong giới hạn 30 ngày).

Time slots gửi sang Tầng 3:

```json
[
  { "day": 0, "slot": 0, "tod_factor": 1.2, "available_hours": 2 },
  { "day": 0, "slot": 1, "tod_factor": 1.0, "available_hours": 2 },
  { "day": 0, "slot": 2, "tod_factor": 0.8, "available_hours": 2 }
]
```

### 4.5. Bước 4 — Payload đầy đủ gửi Tầng 3

File: `backend/app/services/schedule_service.py:151-158`

```json
{
  "subjects": [ ... ],
  "time_slots": [ ... ],
  "max_daily_hours": 4.8,
  "min_session_hours": 0.5,
  "buffer_ratio": 0.25,
  "big_m": 8.0
}
```

Endpoint Tầng 3:

```text
POST {LP_SOLVER_API_URL}/api/schedule/generate
```

Mặc định `LP_SOLVER_API_URL = http://localhost:8002` (`backend/app/core/config.py`).

### 4.6. Bước 5 — Tầng 3 xây mô hình MILP

File: `lp-solver/app/model.py:50` — `build_model`

#### Biến quyết định

| Biến | Ý nghĩa | Miền |
|---|---|---|
| `x[i,d,t]` | Số giờ học bài tập `i` vào ngày `d`, khung `t` | Liên tục >= 0 |
| `y[i,d,t]` | Có phiên học hay không | Nhị phân 0/1 |
| `delta[i,d,k]` | Số giờ nằm trong đoạn thứ `k` của xấp xỉ `sqrt(x)` | `[0, width_k]` |
| `s[i]` | Số giờ thiếu trước deadline | Liên tục >= 0 |
| `u[d]` | Số giờ vượt trần trong ngày `d` | Liên tục >= 0 |

#### Hàm mục tiêu

```text
Maximize Z =
    Σ E[i] × f(X_eff[i,d])
  − λ_deadline × Σ s[i]
  − λ_daily    × Σ u[d]
```

Trong đó:

- `E[i] = urgency × difficulty × priority`
- `urgency = 1 / (1 + deadline_day)` nếu Tier 1 không gửi (Tầng 3 tự tính ở `model.py:76-78`).
- `f(x) = sqrt(x)` được xấp xỉ tuyến tính từng đoạn trên `[0, 4]` với 4 đoạn (`model.py:33-42`).
- `λ_deadline = 20`, `λ_daily = 100` (`model.py:46-47`).

`X_eff[i,d]` là số giờ học **hiệu dụng**, có nhân `tod_factor`:

```text
X_eff[i,d] = Σ_t tod_factor[t] × x[i,d,t]
```

Vì vậy học buổi sáng (1.2) có hiệu quả cao hơn buổi tối (0.8).

#### Các ràng buộc chính

| Mã | Ràng buộc | Diễn giải |
|---|---|---|
| C1 | `Σ_i x[i,d,t] <= available_hours[d,t]` | Không vượt quá 2 giờ/khung |
| C2 | `Σ_i Σ_t x[i,d,t] − u[d] <= max_daily_hours` | Trần giờ/ngày là mềm; vượt thì bị phạt qua `u[d]` |
| C3 | `Σ_{d <= deadline_day} x[i,d,t] + s[i] >= required_hours[i]` | Deadline là mềm; thiếu thì bị phạt qua `s[i]` |
| C4 | `Σ x[i,·] <= required_hours[i] × (1 + buffer_ratio)` | Học tối đa 125% yêu cầu để tránh dồn quá nhiều |
| C5 | `min_session × y <= x <= big_m × y` | Nếu đã học thì ít nhất 0.5 giờ |
| C6 | `x[i,d,t] = 0` nếu `d > deadline_day` | Không học sau deadline |
| C7 | `X_eff[i,d] = Σ_k delta[i,d,k]` và `X_eff <= 4` | Liên kết xấp xỉ `sqrt`, giới hạn hiệu dụng |

#### Giải

File: `lp-solver/app/solver.py:130` — `solve_schedule`

- Dùng PuLP + CBC (`PULP_CBC_CMD`).
- Nếu tối ưu: trả `status = "optimal"`, `feasible = true`, danh sách lịch, giải thích, cảnh báo, `objective_value`.
- Nếu vô nghiệm: trả `status = "infeasible"`, `feasible = false`, danh sách `conflicts`.
- Nếu vô biên hoặc trạng thái khác: trả lỗi tương ứng.

Kết quả mỗi phiên học:

```json
{ "subject_id": "assignment-uuid-1", "day": 0, "slot": 0, "hours": 1.5 }
```

Lưu ý: `subject_id` ở đây thực chất là **assignment_id** do Tầng 1 gán khi gom dữ liệu.

### 4.7. Bước 6 — Fallback khi Tầng 3 báo infeasible

File: `backend/app/services/schedule_service.py:161-173`

Nếu kết quả không khả thi, Tầng 1 gọi lại Tầng 3 một lần với trần giờ gốc:

```text
max_daily_hours = DEFAULT_W_MAX = 6.0
```

Nếu lần hai khả thi, dùng kết quả đó và thêm cảnh báo:

```json
{
  "type": "risk_override",
  "message": "Lịch được tạo vượt mức giờ khuyến nghị do rủi ro cao ..."
}
```

Mục đích: không trả về ngõ cụt cho người dùng, nhưng vẫn cảnh báo rằng lịch vượt trần an toàn.

### 4.8. Bước 7 — Tầng 1 lưu lịch vào database

File: `backend/app/services/schedule_service.py:177-188`

Bảng `schedules`:

| Cột | Giá trị |
|---|---|
| `user_id` | User hiện tại |
| `schedule_data` | Toàn bộ JSON kết quả Tầng 3 (JSONB) |
| `feasible` | `result["feasible"]` |
| `risk_score_at_generation` | Risk score tại thời điểm tạo lịch |
| `warnings` | Mảng cảnh báo (JSONB) hoặc `null` |

Sau khi lưu, Tầng 1 bổ sung metadata vào response:

```json
{
  "schedule_id": "uuid-cua-schedule",
  "risk_score_at_generation": 41.25,
  "risk_level": "moderate",
  "w_max_effective": 4.8,
  "w_max": 6.0,
  "horizon_days": 7
}
```

### 4.9. Bước 8 — Frontend hiển thị lịch

File: `frontend/src/pages/SchedulePage.tsx`

Dữ liệu trả về được dùng như sau:

| Dữ liệu | Cách dùng trên UI |
|---|---|
| `schedule[]` | Nhóm theo `(day, slot)` để vẽ bảng lịch: hàng = 3 khung Sáng/Chiều/Tối, cột = `horizon_days` ngày |
| `day` | Quy đổi thành ngày thực tế bằng `dayjs().add(day, 'day')` |
| `hours` | Hiển thị số giờ trong tag của phiên học |
| `w_max_effective`, `risk_score_at_generation`, `risk_level` | Hiển thị trong card thống kê phía trên |
| `warnings[]` | Hiển thị các `Alert` cảnh báo |
| `explanation.per_subject` | Hiển thị số giờ đã xếp / yêu cầu, số giờ thiếu deadline |
| `explanation.per_day` | Hiển thị tổng giờ mỗi ngày và số giờ vượt trần |
| `objective_value` | Hiển thị giá trị mục tiêu của LP |
| `schedule_id` | Dùng để gửi feedback |

Feedback:

- `SchedulePage.tsx` gửi `POST /api/feedback` với `{ schedule_id, rating, comment }`.
- Backend `api/feedback.py` kiểm tra schedule thuộc user rồi ghi vào bảng `feedback`.

---

## 5. Bảng chuyển đổi dữ liệu qua các tầng

| Giai đoạn | Dữ liệu chính | Ví dụ |
|---|---|---|
| Người dùng nhập | Form React | Chọn môn "CTDL", difficulty 4, priority 5 |
| Frontend gửi | JSON payload | `{ "subject_name": "CTDL", "difficulty": 4, "priority": 5 }` |
| Tầng 1 lưu | Row trong PostgreSQL | `subjects(subject_id, user_id, subject_name, difficulty, priority)` |
| Tạo bài tập | Form + API | `{ "subject_id": "...", "title": "Bài 3", "deadline": "...", "required_hours": 4.5, "priority": 5 }` |
| Tầng 2 tổng hợp | Payload 5 trường | `{ sleep_hours, required_hours, available_hours, days_until_deadline, study_std }` |
| Tầng 2 trả về | Risk object | `{ risk_score: 41.25, level: "moderate", components: {...} }` |
| Tầng 1 gom cho LP | Mỗi bài tập = 1 subject | `{ id: assignment_id, required_hours: 4.5, deadline_day: 5, difficulty: 4, priority: 5 }` |
| Tầng 3 trả về | Schedule entries | `{ subject_id: assignment_id, day: 0, slot: 0, hours: 1.5 }` |
| Tầng 1 lưu lịch | Row trong `schedules` | `schedule_data = { status, feasible, schedule, explanation, warnings, ... }` |
| Frontend hiển thị | Bảng lịch + giải thích | Ngày 0 / Sáng: 1.5h bài tập X |

---

## 6. Các lưu ý kỹ thuật quan trọng

### 6.1. Đơn vị và múi giờ

- Mọi thời điểm gửi lên backend đều là chuỗi ISO UTC (`toISOString()` ở frontend).
- `deadline_day` ở Tầng 3 là số ngày làm tròn xuống: `(deadline - now).days` theo UTC.
- `duration`, `required_hours`, `available_hours`, `max_daily_hours` đều tính bằng giờ.
- `sleep hours` được suy ra từ chênh lệch `wake_time - sleep_time`, không lưu cột riêng.

### 6.2. `subject_id` khác `assignment_id`

Đây là điểm dễ nhầm nhất khi đọc code:

- Ở database: bài tập có `assignment_id`, thuộc một `subject_id`.
- Ở Tầng 2: chỉ dùng `assignments` và `subjects` để lấy số liệu tổng hợp.
- Ở Tầng 3: mỗi bài tập được gán `id = assignment_id`, và trường này được đặt tên là `subject_id` trong kết quả lịch.
- Vì vậy trong response lịch, `subject_id` thực chất là **assignment_id**.

### 6.3. Bộ lọc bài tập giữa Tầng 2 và Tầng 3 chưa hoàn toàn giống nhau

- Tầng 2 (`AssignmentRepository.list_upcoming`): lọc deadline trong 30 ngày và `is_completed = false`.
- Tầng 3 (`_aggregate_subjects`): lọc `deadline > now`, **không lọc** `is_completed`, và không giới hạn 30 ngày (nhưng horizon tối đa 30 ngày).

Điều này có nghĩa bài tập đã hoàn thành vẫn có thể được đưa vào lịch nếu chưa quá deadline. Đây là hành vi hiện tại của code, cần cân nhắc nếu muốn đồng bộ logic.

### 6.4. Hiển thị tên môn trong SchedulePage

`SchedulePage.getSubjectName()` tra cứu `subjects` theo `subject_id`, nhưng dữ liệu lịch chứa `assignment_id`. Do đó UI thường hiển thị fallback `#<6 ký tự đầu của id>` thay vì tên môn. Muốn hiển thị đúng cần map `assignment_id → assignment.subject_id → subject_name` hoặc trả kèm tên bài tập/tên môn từ backend.

### 6.5. Tầng 2 và Tầng 3 là stateless

- Không có database riêng.
- Không lưu dữ liệu người dùng.
- Tầng 1 là nơi duy nhất đọc/ghi PostgreSQL.

---

## 7. Danh mục file tham chiếu

### Frontend

| File | Vai trò |
|---|---|
| `frontend/src/api/client.ts` | Axios client, gắn JWT, xử lý 401 |
| `frontend/src/api/subjects.ts` | Gọi API môn học |
| `frontend/src/api/assignments.ts` | Gọi API bài tập |
| `frontend/src/api/logs.ts` | Gọi API study/sleep/mood |
| `frontend/src/api/risk.ts` | Gọi API risk score |
| `frontend/src/api/schedule.ts` | Gọi API tạo/lấy lịch |
| `frontend/src/components/StudyLogForm.tsx` | Form nhập phiên học đầy đủ |
| `frontend/src/components/SleepLogForm.tsx` | Form nhập giấc ngủ đầy đủ |
| `frontend/src/components/MoodLogForm.tsx` | Form nhập tâm trạng đầy đủ |
| `frontend/src/components/QuickStudyBar.tsx` | Nhập nhanh phiên học |
| `frontend/src/components/QuickSleepWidget.tsx` | Nhập nhanh giấc ngủ |
| `frontend/src/components/QuickMoodBar.tsx` | Nhập nhanh tâm trạng |
| `frontend/src/components/QuickCreateButtons.tsx` | Tạo nhanh môn/bài tập |
| `frontend/src/pages/AssignmentsPage.tsx` | CRUD bài tập |
| `frontend/src/pages/SubjectsPage.tsx` | CRUD môn học |
| `frontend/src/pages/LoggingPage.tsx` | Trang nhập nhật ký |
| `frontend/src/pages/SchedulePage.tsx` | Hiển thị lịch và feedback |

### Backend Tầng 1

| File | Vai trò |
|---|---|
| `backend/app/api/logs.py` | API study/sleep/mood |
| `backend/app/api/subjects.py` | API môn học |
| `backend/app/api/assignments.py` | API bài tập |
| `backend/app/api/risk.py` | Proxy gọi Tầng 2 |
| `backend/app/api/schedule.py` | Proxy gọi Tầng 3 |
| `backend/app/services/risk_service.py` | Tổng hợp dữ liệu và gọi Tầng 2 |
| `backend/app/services/schedule_service.py` | Gom bài tập, tính W_max, gọi Tầng 3, lưu lịch |
| `backend/app/repositories/log_repo.py` | Truy vấn study/sleep/mood |
| `backend/app/repositories/assignment_repo.py` | Truy vấn bài tập |
| `backend/app/repositories/subject_repo.py` | Truy vấn môn học |
| `backend/app/models/orm_models.py` | Định nghĩa 9 bảng |
| `backend/app/schemas/logs.py` | Validate payload study/sleep/mood |
| `backend/app/schemas/assignments.py` | Validate payload bài tập |
| `backend/app/schemas/subjects.py` | Validate payload môn học |

### Tầng 2

| File | Vai trò |
|---|---|
| `risk-indicator/app/api.py` | Endpoint `POST /api/risk/score` |
| `risk-indicator/app/schemas.py` | Validate input/output risk |
| `risk-indicator/app/calculator.py` | Chuẩn hóa 4 thành phần, tính điểm, phân loại |

### Tầng 3

| File | Vai trò |
|---|---|
| `lp-solver/app/api.py` | Endpoint `POST /api/schedule/generate` |
| `lp-solver/app/schemas.py` | Validate input/output LP |
| `lp-solver/app/model.py` | Xây biến, hàm mục tiêu, ràng buộc |
| `lp-solver/app/solver.py` | Giải MILP, trích lịch, giải thích, cảnh báo |
