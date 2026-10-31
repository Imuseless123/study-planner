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

- [STARTUP.md](./STARTUP.md) — Hướng dẫn khởi động chi tiết
- [docs/daily-logs/](./docs/daily-logs/) — Nhật ký công việc hàng ngày
- [docs/architecture/system-architecture.md](./docs/architecture/system-architecture.md) — **Kiến trúc tổng thể hệ thống**
  - [Tầng 1 — Web App](./docs/architecture/tier-1-overview.md)
  - [Tầng 2 — Risk Indicator](./docs/architecture/tier-2-overview.md)
  - [Tầng 3 — LP Solver](./docs/architecture/tier-3-overview.md)
  - [Luồng dữ liệu End-to-End](./docs/architecture/data-flow.md)
  - [Đánh giá lịch: lợi ích và hạn chế](./docs/architecture/schedule-benefits-limitations.md)

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
│ TẦNG 1: WEB APPLICATION                                 │
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
│                      │    │                          │
│ - Rule-based scoring │    │ - MILP với PuLP          │
│ - 4 components       │    │ - Diminishing returns    │
│ - Low/Mod/High       │    │ - Soft constraints       │
│ - Disclaimer         │    │ - Warnings               │
└──────────────────────┘    └──────────────────────────┘
```

### Trạng thái triển khai

| Tầng | Chức năng | Tech Stack | Trạng thái |
|------|-----------|------------|:----------:|
| **Tầng 1** | Web App — Thu thập dữ liệu, Dashboard | React + FastAPI + PostgreSQL | ✅ |
| **Tầng 2** | Workload Risk Indicator (rule-based) | FastAPI + Python | ✅ |
| **Tầng 3** | LP Optimization Engine | FastAPI + PuLP (MILP) | ✅ |

### Đánh giá lịch học do hệ thống tạo

Lịch được tạo bởi Tầng 3 là lịch tối ưu có ràng buộc, không phải lịch chia đều. Chi tiết xem [docs/architecture/schedule-benefits-limitations.md](./docs/architecture/schedule-benefits-limitations.md).

**Lợi ích chính:**

- Cá nhân hóa theo từng bài tập: deadline, số giờ cần học, độ khó môn, độ ưu tiên bài tập.
- Điều chỉnh theo rủi ro: trần giờ/ngày giảm khi risk score cao.
- Dùng ràng buộc mềm: luôn trả về lịch kèm cảnh báo thay vì báo vô nghiệm.
- Mô phỏng lợi nhuận giảm dần của việc học và ưu tiên khung giờ hiệu quả.
- Có giải thích theo bài tập/ngày, lưu lịch và thu feedback.

**Hạn chế chính:**

- Chưa biết lịch bận thực tế; giả định mỗi ngày có 6 giờ rảnh.
- Deadline chỉ xét theo ngày, chưa theo giờ.
- Chưa dùng dữ liệu mood/stress/energy và chưa có vòng phản hồi từ kết quả học thực tế.
- Khung giờ cố định (sáng/chiều/tối), chưa có giờ bắt đầu chính xác, nghỉ ngơi hay export calendar.
- Một số tham số mô hình còn mang tính heuristic, chưa được hiệu chỉnh bằng dữ liệu người dùng.

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

| # | Chức năng | Status |
|---|-----------|:------:|
| 1-5 | Auth, Consent, Logging (Study/Sleep/Mood) | ✅ |
| 6-7 | CRUD Subjects & Assignments | ✅ |
| 8-9 | Dashboard Heatmap & Deadline Timeline | ✅ |
| 10 | Risk Score Widget | ✅ |
| 11-12 | Schedule Generation & Constraint Explanation | ✅ |
| 13 | Feedback Rating | ✅ |
| 14 | Data Export/Delete | ✅ |

**Tổng:** 14/14 (100%)

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

