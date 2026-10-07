# Study Planner

Hệ thống Lập kế hoạch Học tập Cá nhân — Tích hợp Chỉ báo Rủi ro Khối lượng Công việc và Tối ưu hóa Lịch trình bằng Quy hoạch Tuyến tính.

**Đồ án tốt nghiệp đại học — Phạm Kim Long**

---

## 🚀 Quick Start

Xem [STARTUP.md](./STARTUP.md) để biết hướng dẫn setup chi tiết.

```bash
# Setup lần đầu
docker compose build backend
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up -d backend frontend

# Verify
curl -s http://localhost:8000/health | jq
```

### 🌐 URLs sau khi chạy

| Service | URL | Mô tả |
|---------|-----|-------|
| **Backend API** | http://localhost:8000 | FastAPI server |
| **Swagger UI** | http://localhost:8000/docs | API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API docs |
| **Frontend** | http://localhost:3000 | React web app |

---

## 📖 Tài liệu

### Kiến trúc

- [Tầng 1 — Web Application Layer](./docs/architecture/tier-1-overview.md) — Database schema, dataflow, API endpoints, security
- *(Sắp có)* Tầng 2 — Workload Risk Indicator
- *(Sắp có)* Tầng 3 — LP Optimization Engine

### Hướng dẫn

- [STARTUP.md](./STARTUP.md) — Setup môi trường từ đầu, troubleshooting, các lệnh thường dùng
- [docs/daily-logs/](./docs/daily-logs/) — Nhật ký công việc hàng ngày

### Kế hoạch

- `plan.docx` — Kế hoạch tổng thể 12 tuần

---

## 🏗️ Kiến trúc

Hệ thống gồm **3 tầng chức năng**, giao tiếp qua RESTful API:

```
┌─────────────────────────────────────────────────────────┐
│ NGƯỜI DÙNG                                              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS
                       ▼
┌─────────────────────────────────────────────────────────┐
│ TẦNG 1: WEB APPLICATION                          ✅ Done │
│ - Auth (register/login/logout)                          │
│ - Consent (sign/withdraw)                               │
│ - Logging (study/sleep/mood)                            │
│ - CRUD (subjects/assignments)                           │
│ - Dashboard (heatmap/timeline/stats)                    │
│ - Frontend: React 18 + Vite + Ant Design                │
│ - Backend:  FastAPI + SQLAlchemy + PostgreSQL 15        │
└──────────┬──────────────────────────┬───────────────────┘
           │ gọi API                  │ gọi API
           ▼                          ▼
┌──────────────────────┐    ┌──────────────────────────┐
│ TẦNG 2:              │    │ TẦNG 3:                  │
│ RISK INDICATOR       │───▶│ LP OPTIMIZATION          │
│ ⏳ Chưa triển khai    │    │ ⏳ Chưa triển khai        │
│                      │    │                          │
│ - Rule-based scoring │    │ - MILP với PuLP          │
│ - 4 components       │    │ - Diminishing returns    │
│ - Low/Mod/High       │    │ - Soft constraints       │
│ - Disclaimer         │    │ - Warnings               │
└──────────────────────┘    └──────────────────────────┘
```

### Trạng thái triển khai

| Tầng | Trạng thái | Tiến độ |
|------|-----------|---------|
| **Tầng 1** — Web App | ✅ Hoàn thành | 9/14 FR |
| **Tầng 2** — Risk Indicator | ⏳ Chưa làm | — |
| **Tầng 3** — LP Solver | ⏳ Chưa làm | — |

---

## 🛠️ Tech Stack

| Component | Công nghệ | Phiên bản |
|-----------|-----------|-----------|
| **Frontend** | React + TypeScript + Vite | 18.2 / 5.3 / 5.0 |
| **UI Library** | Ant Design | 5.12 |
| **Chart** | Recharts | 2.10 |
| **State** | Zustand | 4.4 |
| **Backend** | FastAPI + Python | 0.104 / 3.11 |
| **ORM** | SQLAlchemy | 2.0 |
| **Migration** | Alembic | 1.12 |
| **Database** | PostgreSQL | 15 |
| **Auth** | JWT + bcrypt | — |
| **Deploy** | Docker Compose | v2 |

---

## 📊 Tiến độ 14 Functional Requirements

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
| 10 | Risk widget | — | — | Tầng 2 |
| 11 | Schedule generation | — | — | Tầng 3 |
| 12 | Constraint explanation | — | — | Tầng 3 |
| 13 | Feedback | — | — | Pending |
| 14 | Data export/delete | — | — | Pending |

**Tiến độ Tầng 1:** 9/14 FR (64%)

---

## 🔑 Credentials mặc định (dev)

| Field | Value |
|-------|-------|
| Postgres user | `study_planner` |
| Postgres password | `dev_password_change_in_prod` |
| Postgres database | `study_planner` |
| Test user | Register qua `/register` |

⚠️ **Production:** Đổi hết password + dùng strong JWT_SECRET (64+ chars random).

---

## 📝 License

Đồ án tốt nghiệp đại học — Phạm Kim Long

