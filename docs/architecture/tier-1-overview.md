# 🏗️ Tầng 1 — Web Application Layer

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Phiên bản:** 1.0
**Ngày hoàn thành:** 06/10/2026
**Trạng thái:** ✅ Hoàn thành (9/14 FR)

---

## 📌 Tổng quan

Tầng 1 là **giao diện duy nhất** mà người dùng tương tác trực tiếp. Đây là nơi:
- Thu thập dữ liệu hành vi học tập (study, sleep, mood)
- Quản lý môn học và bài tập
- Hiển thị dashboard với các widget trực quan
- Là cầu nối để gọi Tầng 2 (Risk Indicator) và Tầng 3 (LP Solver)

### Tech Stack

| Layer | Công nghệ | Phiên bản |
|-------|-----------|-----------|
| **Frontend** | React + TypeScript + Vite | 18.2 / 5.3 / 5.0 |
| **UI Library** | Ant Design | 5.12 |
| **Chart** | Recharts | 2.10 |
| **State** | Zustand | 4.4 |
| **HTTP Client** | Axios | 1.6 |
| **Backend** | FastAPI + Python | 0.104 / 3.11 |
| **ORM** | SQLAlchemy | 2.0 |
| **Migration** | Alembic | 1.12 |
| **Database** | PostgreSQL | 15 |
| **Auth** | JWT (python-jose) + bcrypt | — |
| **Deploy** | Docker Compose | v2 |

---

## 🗄️ Cấu trúc Database

### Sơ đồ quan hệ thực thể (ERD)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│                          ┌──────────┐                            │
│                          │  users   │                            │
│                          └────┬─────┘                            │
│                               │                                  │
│         ┌─────────────────────┼─────────────────────┐            │
│         │                     │                     │            │
│         ▼                     ▼                     ▼            │
│   ┌──────────┐          ┌──────────┐          ┌──────────┐       │
│   │ consents │          │ subjects │          │  mood_   │       │
│   └──────────┘          └────┬─────┘          │   logs   │       │
│                              │                └──────────┘       │
│                    ┌─────────┴──────────┐                        │
│                    ▼                    ▼                        │
│              ┌──────────┐        ┌────────────────┐              │
│              │  study_  │        │  assignments   │              │
│              │ sessions │        └────────────────┘              │
│              └──────────┘                                        │
│                                                                  │
│   ┌──────────┐          ┌──────────┐          ┌──────────┐       │
│   │  sleep_  │          │schedules │◄─────────┤ feedback │       │
│   │   logs   │          └──────────┘          └──────────┘       │
│   └──────────┘                                                   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Chi tiết 9 bảng

#### 1. `users` — Tài khoản người dùng

| Cột | Kiểu | Ràng buộc | Mô tả |
|-----|------|-----------|-------|
| `user_id` | UUID | PK, default `gen_random_uuid()` | Định danh |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Tên đăng nhập |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt cost 12 |
| `email` | VARCHAR(100) | UNIQUE, NOT NULL | Email |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Ngày tạo |

**Indexes:** `users_pkey`, `users_username_key`, `users_email_key`

#### 2. `consents` — Đồng thuận nghiên cứu

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `consent_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `version` | VARCHAR(20) | NOT NULL |
| `signed_at` | TIMESTAMPTZ | DEFAULT NOW() |
| `expires_at` | TIMESTAMPTZ | NOT NULL |
| `withdrawn_at` | TIMESTAMPTZ | NULLABLE |

**Indexes:** `idx_consents_user`

#### 3. `subjects` — Môn học

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `subject_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `subject_name` | VARCHAR(100) | NOT NULL |
| `difficulty` | INTEGER | CHECK (1-5) |
| `priority` | INTEGER | CHECK (1-5) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** `idx_subjects_user`

#### 4. `assignments` — Bài tập

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `assignment_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `subject_id` | UUID | FK → subjects (CASCADE) |
| `title` | VARCHAR(200) | NOT NULL |
| `deadline` | TIMESTAMPTZ | NOT NULL |
| `required_hours` | NUMERIC(4,2) | CHECK (> 0) |
| `priority` | INTEGER | CHECK (1-5) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** `idx_assignments_user_deadline (user_id, deadline)`, `idx_assignments_subject`

#### 5. `study_sessions` — Phiên học

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `session_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `subject_id` | UUID | FK → subjects (CASCADE) |
| `start_time` | TIMESTAMPTZ | NOT NULL |
| `duration` | NUMERIC(4,2) | CHECK (> 0) |
| `focus_level` | INTEGER | CHECK (1-5) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** `idx_study_sessions_user_date (user_id, start_time)`, `idx_study_sessions_subject`

#### 6. `sleep_logs` — Nhật ký giấc ngủ

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `sleep_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `sleep_time` | TIMESTAMPTZ | NOT NULL |
| `wake_time` | TIMESTAMPTZ | NOT NULL |
| `quality` | INTEGER | CHECK (1-5) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**CHECK:** `wake_time > sleep_time`
**Indexes:** `idx_sleep_logs_user_time`

#### 7. `mood_logs` — Nhật ký tâm trạng

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `mood_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `log_date` | DATE | NOT NULL |
| `energy_level` | INTEGER | CHECK (1-5) |
| `stress_level` | INTEGER | CHECK (1-5) |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**UNIQUE:** `(user_id, log_date)` — 1 record/ngày
**Indexes:** `idx_mood_logs_user_date`

#### 8. `schedules` — Lịch học được tạo

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `schedule_id` | UUID | PK |
| `user_id` | UUID | FK → users (CASCADE) |
| `generated_date` | TIMESTAMPTZ | DEFAULT NOW() |
| `schedule_data` | JSONB | NOT NULL |
| `feasible` | BOOLEAN | NOT NULL |
| `risk_score_at_generation` | NUMERIC(5,2) | CHECK (0-100) |
| `warnings` | JSONB | NULLABLE |

**Indexes:** `idx_schedules_user_generated`

#### 9. `feedback` — Đánh giá lịch

| Cột | Kiểu | Ràng buộc |
|-----|------|-----------|
| `feedback_id` | UUID | PK |
| `schedule_id` | UUID | FK → schedules (CASCADE) |
| `user_id` | UUID | FK → users (CASCADE) |
| `rating` | INTEGER | CHECK (1-5) |
| `comment` | TEXT | NULLABLE |
| `created_at` | TIMESTAMPTZ | DEFAULT NOW() |

**Indexes:** `idx_feedback_schedule`, `idx_feedback_user`

### Tổng kết Database

| Metric | Số lượng |
|--------|----------|
| Bảng | 9 |
| Foreign Keys | 10 (all CASCADE) |
| Check Constraints | 11 |
| Unique Constraints | 4 |
| Indexes | 11 |

### Quan hệ cascade

Khi user bị xóa:
- ✅ Xóa hết `consents` của user
- ✅ Xóa hết `subjects` → cascade `assignments` + `study_sessions`
- ✅ Xóa hết `sleep_logs`, `mood_logs`
- ✅ Xóa hết `schedules` → cascade `feedback`

---

## 🔄 Data Flow

### Luồng dữ liệu tổng quan

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                     NGƯỜI DÙNG (Browser)                        │
│                                                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TẦNG 1: WEB APPLICATION                      │
│                                                                 │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │   Frontend       │              │    Backend       │         │
│  │  React + Vite    │◄────REST────►│   FastAPI        │         │
│  │  Port 3000       │              │   Port 8000      │         │
│  └──────────────────┘              └────────┬─────────┘         │
│                                             │                   │
└─────────────────────────────────────────────┼───────────────────┘
                                              │
                                              │ SQLAlchemy
                                              ▼
                                    ┌──────────────────┐
                                    │   PostgreSQL 15  │
                                    │   Port 5432      │
                                    └──────────────────┘

                                              ▲
                                              │ HTTP
                                              │
                                    ┌─────────┴─────────┐
                                    │  Tầng 2 & Tầng 3  │
                                    │  (Chưa triển khai)│
                                    └───────────────────┘
```

### Luồng chi tiết — Authentication

```
User                Frontend              Backend              DB
 │                     │                     │                  │
 │  1. Register        │                     │                  │
 ├────────────────────►│                     │                  │
 │                     │  2. POST /api/auth/register             │
 │                     ├────────────────────►│                  │
 │                     │                     │  3. INSERT user  │
 │                     │                     ├─────────────────►│
 │                     │                     │  4. Return OK    │
 │                     │◄────────────────────┤                  │
 │                     │                     │                  │
 │  5. Login           │                     │                  │
 ├────────────────────►│                     │                  │
 │                     │  6. POST /api/auth/login                │
 │                     ├────────────────────►│                  │
 │                     │                     │  7. SELECT user  │
 │                     │                     ├─────────────────►│
 │                     │                     │  8. Verify pwd   │
 │                     │                     │  9. Sign JWT     │
 │                     │◄────────────────────┤                  │
 │  Token stored       │                     │                  │
 │◄────────────────────┤                     │                  │
 │                     │                     │                  │
 │  10. GET /api/auth/me                     │                  │
 ├────────────────────►│────────────────────►│                  │
 │                     │  Bearer token       │  11. Verify JWT  │
 │                     │                     │  12. SELECT user │
 │                     │                     ├─────────────────►│
 │                     │◄────────────────────┤                  │
 │  User info          │                     │                  │
 │◄────────────────────┤                     │                  │
```

### Luồng chi tiết — Logging (Study Session)

```
User                Frontend              Backend              DB
 │                     │                     │                  │
 │  1. Fill form       │                     │                  │
 ├────────────────────►│                     │                  │
 │                     │  2. POST /api/log/study                 │
 │                     │     {subject_id, start_time, duration, focus_level}
 │                     ├────────────────────►│                  │
 │                     │                     │  3. Validate     │
 │                     │                     │     subject_id   │
 │                     │                     ├─────────────────►│
 │                     │                     │  4. INSERT       │
 │                     │                     ├─────────────────►│
 │                     │                     │  5. Return       │
 │                     │◄────────────────────┤                  │
 │  6. Success msg     │                     │                  │
 │◄────────────────────┤                     │                  │
 │                     │                     │                  │
 │                     │  7. GET /api/log/study                  │
 │                     ├────────────────────►│                  │
 │                     │                     │  8. SELECT JOIN  │
 │                     │                     │     subjects     │
 │                     │                     ├─────────────────►│
 │                     │◄────────────────────┤                  │
 │  9. Update table    │                     │                  │
 │◄────────────────────┤                     │                  │
```

### Luồng chi tiết — Dashboard

```
User                Frontend              Backend              DB
 │                     │                     │                  │
 │  1. Load dashboard  │                     │                  │
 ├────────────────────►│                     │                  │
 │                     │  2. GET /api/dashboard/summary          │
 │                     ├────────────────────►│                  │
 │                     │                     │  3. Multiple     │
 │                     │                     │     queries:     │
 │                     │                     │  - study by date │
 │                     │                     │  - study matrix  │
 │                     │                     │  - sleep hours   │
 │                     │                     │  - assignments   │
 │                     │                     │  - subjects      │
 │                     │                     ├─────────────────►│
 │                     │                     │◄─────────────────┤
 │                     │                     │  4. Aggregate    │
 │                     │◄────────────────────┤                  │
 │  5. Render:         │                     │                  │
 │   - Statistics      │                     │                  │
 │   - Chart           │                     │                  │
 │   - Heatmap         │                     │                  │
 │   - Timeline        │                     │                  │
 │◄────────────────────┤                     │                  │
```

### Luồng tích hợp với Tầng 2 & Tầng 3 (dự kiến)

```
User → Frontend → Backend (Tầng 1)
                       │
                       ├──► Tầng 2: GET /api/risk/score
                       │    ├── Input: sleep, workload, deadline proximity
                       │    └── Output: risk_score, level, disclaimer
                       │
                       └──► Tầng 3: POST /api/schedule/generate
                            ├── Input: subjects, time_slots, risk_score
                            └── Output: schedule, explanation, warnings
```

---

## 🔌 API Endpoints

### Tổng quan 6 nhóm chính

| Nhóm | Số endpoints | Mô tả |
|------|:------------:|-------|
| **auth** | 4 | Đăng ký, đăng nhập, đăng xuất, lấy info |
| **consent** | 3 | Ký, xem, rút lui đồng thuận |
| **logs** | 9 | Study, Sleep, Mood (POST/GET/DELETE mỗi loại) |
| **subjects** | 5 | CRUD môn học |
| **assignments** | 6 | CRUD + stats bài tập |
| **dashboard** | 1 | Summary cho dashboard |
| **Total** | **28** | |

### Chi tiết endpoints

#### Authentication (`/api/auth`)

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `/register` | `{username, password, email}` | `{status, user_id}` |
| POST | `/login` | `{username, password}` | `{status, token, refresh_token}` |
| POST | `/logout` | — | `{status}` |
| GET | `/me` | — | `{user_id, username, email, created_at}` |

#### Consent (`/api/consent`)

| Method | Endpoint | Body | Response |
|--------|----------|------|----------|
| POST | `` | `{version}` | `{consent_id, version, signed_at, expires_at}` |
| GET | `` | — | `{consent_id, ...}` hoặc `null` |
| POST | `/withdraw` | — | `{status}` |

#### Logs (`/api/log`)

| Method | Endpoint | Chức năng |
|--------|----------|-----------|
| POST | `/study` | Tạo phiên học |
| GET | `/study?limit=50` | List phiên học |
| DELETE | `/study/{session_id}` | Xóa phiên học |
| POST | `/sleep` | Tạo nhật ký giấc ngủ |
| GET | `/sleep?limit=50` | List giấc ngủ |
| DELETE | `/sleep/{sleep_id}` | Xóa nhật ký |
| POST | `/mood` | Tạo/cập nhật tâm trạng |
| GET | `/mood?limit=50` | List tâm trạng |
| DELETE | `/mood/{mood_id}` | Xóa nhật ký |

#### Subjects (`/api/subjects`)

| Method | Endpoint | Chức năng |
|--------|----------|-----------|
| GET | `` | List môn học |
| POST | `` | Tạo môn học (201) |
| GET | `/{subject_id}` | Lấy 1 môn |
| PUT | `/{subject_id}` | Partial update |
| DELETE | `/{subject_id}` | Xóa môn (cascade) |

#### Assignments (`/api/assignments`)

| Method | Endpoint | Chức năng |
|--------|----------|-----------|
| GET | `` | List bài tập |
| GET | `/stats` | Statistics (đặt trước `/{id}`) |
| POST | `` | Tạo bài tập |
| GET | `/{assignment_id}` | Lấy 1 bài tập |
| PUT | `/{assignment_id}` | Partial update |
| DELETE | `/{assignment_id}` | Xóa bài tập |

#### Dashboard (`/api/dashboard`)

| Method | Endpoint | Response |
|--------|----------|----------|
| GET | `/summary` | `{study_hours_by_date, study_hours_matrix, sleep_hours_recent, upcoming_assignments, subjects}` |

---

## 🎨 Frontend Pages

| Route | Page | Chức năng |
|-------|------|-----------|
| `/login` | LoginPage | Đăng nhập |
| `/register` | RegisterPage | Đăng ký |
| `/consent` | ConsentPage | Ký đồng thuận |
| `/dashboard` | DashboardPage | Trang chủ với widgets |
| `/logging` | LoggingPage | 3 tabs: Study/Sleep/Mood |
| `/subjects` | SubjectsPage | CRUD môn học |
| `/assignments` | AssignmentsPage | CRUD bài tập |
| `/schedule` | Placeholder | Chờ Tầng 3 |
| `/settings` | Placeholder | Chờ FR #14 |

### Components tái sử dụng

| Component | Dùng ở | Chức năng |
|-----------|--------|-----------|
| `ProtectedRoute` | App.tsx | Auth + Consent guard |
| `AuthLayout` | Login, Register | Card centered layout |
| `AppLayout` | Tất cả app pages | Sidebar + Header |
| `StatisticsCards` | Dashboard | 4 metric cards |
| `WeeklyStudyChart` | Dashboard | Recharts bar chart |
| `WorkloadHeatmap` | Dashboard | Subjects × days grid |
| `DeadlineTimeline` | Dashboard | Upcoming assignments |
| `SleepQualityCard` | Dashboard | Circular progress |
| `RiskScoreWidget` | Dashboard | Placeholder Tầng 2 |
| `StudyLogForm` | Logging | Form phiên học |
| `SleepLogForm` | Logging | Form giấc ngủ |
| `MoodLogForm` | Logging | Form tâm trạng |

---

## 🔐 Security & Privacy

### Authentication
- **Password hashing:** bcrypt cost factor 12
- **JWT:** access token 30 phút, refresh token 7 ngày
- **Token storage:** access token trong memory (không localStorage), refresh trong HTTP-only cookie
- **Auto-logout:** response interceptor bắt 401 → clear auth + redirect

### Authorization
- **Access control:** mọi query lọc theo `user_id` từ JWT
- **Ownership check:** DELETE endpoints verify user sở hữu record
- **CORS:** chỉ allow `http://localhost:3000`

### Privacy
- **Consent:** version + signed_at + expires_at + withdrawn_at
- **Export:** `GET /api/user/data` (chưa làm)
- **Delete:** `DELETE /api/user/data` (chưa làm)
- **Disclaimer:** hiển thị cùng mọi risk output (sẵn sàng cho Tầng 2)

---

## 📊 Trạng thái 14 FR

| # | Chức năng | Backend | Frontend | Status |
|---|-----------|:-------:|:--------:|:------:|
| 1 | Authentication | ✅ | ✅ | ✅ |
| 2 | Consent | ✅ | ✅ | ✅ |
| 3 | Log study | ✅ | ✅ | ✅ |
| 4 | Log sleep | ✅ | ✅ | ✅ |
| 5 | Log mood | ✅ | ✅ | ✅ |
| 6 | CRUD subjects | ✅ | ✅ | ✅ |
| 7 | CRUD assignments | ✅ | ✅ | ✅ |
| 8 | Dashboard heatmap | ✅ | ✅ | ✅ |
| 9 | Deadline timeline | ✅ | ✅ | ✅ |
| 10 | Risk widget | ⏳ | ⏳ | Tầng 2 |
| 11 | Schedule generation | ❌ | ❌ | Tầng 3 |
| 12 | Constraint explanation | ❌ | ❌ | Tầng 3 |
| 13 | Feedback | ❌ | ❌ | Cần Tầng 3 |
| 14 | Data export/delete | ❌ | ❌ | Chưa |

**Tiến độ:** 9/14 FR (64%)

---

## 🚀 Deployment

### Docker Compose

```yaml
services:
  postgres:    # postgres:15-alpine, port 5432
  backend:     # FastAPI, port 8000
  frontend:    # Vite, port 3000
```

### Ports

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | localhost:5432 |
| Backend | 8000 | http://localhost:8000 |
| Swagger UI | 8000 | http://localhost:8000/docs |
| Frontend | 3000 | http://localhost:3000 |

### Environment Variables

```bash
# Database
POSTGRES_USER=study_planner
POSTGRES_PASSWORD=...
POSTGRES_DB=study_planner
DATABASE_URL=postgresql+psycopg2://...

# JWT
JWT_SECRET=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Downstream
RISK_API_URL=http://risk-indicator:8001
LP_SOLVER_API_URL=http://lp-solver:8002

# Frontend
FRONTEND_URL=http://localhost:3000
```

---

## 📈 Metrics

### Codebase

| Component | Files | LOC |
|-----------|:-----:|:---:|
| Backend Python | ~25 | ~2,500 |
| Frontend TSX/TS | ~25 | ~3,500 |
| **Total** | **~50** | **~6,000** |

### Database

| Metric | Count |
|--------|-------|
| Tables | 9 |
| Columns | 58 |
| Foreign Keys | 10 |
| Check Constraints | 11 |
| Indexes | 11 |

### API

| Metric | Count |
|--------|-------|
| Endpoints | 28 |
| Routers | 6 |
| Schemas (Pydantic) | ~25 |

---

## 🎯 Điểm mạnh

1. **Kiến trúc modular rõ ràng** — 3 tier tách biệt, giao tiếp qua API
2. **Security first** — JWT + bcrypt + ownership check + consent
3. **Type safety** — TypeScript frontend + Pydantic backend
4. **Database integrity** — 11 check constraints + 10 FK CASCADE
5. **UX tốt** — responsive, empty states, onboarding, disclaimer
6. **Ethics-aware** — consent flow + không chẩn đoán y tế
7. **Testability** — repositories + services tách biệt cho unit test

## ⚠️ Hạn chế hiện tại

1. **Chưa có test suite** — chỉ manual test
2. **Chưa deploy** — chỉ chạy local
3. **Chưa tích hợp Tầng 2/3** — placeholder trong dashboard
4. **Thiếu FR #13, #14** — feedback + data export/delete
5. **Chưa có user testing** — SUS survey pending
6. **Timezone** — chưa có test cross-timezone

---

## 🔗 Tài liệu liên quan

- [`STARTUP.md`](../../STARTUP.md) — Hướng dẫn cài đặt
- [`docs/daily-logs/`](../daily-logs/) — Nhật ký hàng ngày
- [`docs/architecture/tier-2-overview.md`](./tier-2-overview.md) — (Chưa làm)
- [`docs/architecture/tier-3-overview.md`](./tier-3-overview.md) — (Chưa làm)

---

## 📅 Lịch sử thay đổi

| Ngày | Phiên bản | Thay đổi |
|------|-----------|----------|
| 04/10/2026 | 0.1 | Backend Tầng 1 hoàn thành: DB + 14 endpoints |
| 05/10/2026 | 0.2 | Frontend Auth + Consent |
| 05/10/2026 | 0.3 | Logging feature (Study/Sleep/Mood) |
| 06/10/2026 | 0.4 | CRUD Subjects |
| 06/10/2026 | 0.5 | CRUD Assignments |
| 06/10/2026 | 1.0 | Dashboard Widgets — Tầng 1 hoàn thành |

---

**Người soạn:** Phạm Kim Long
**Ngày cập nhật:** 06/10/2026
**Phiên bản:** 1.0