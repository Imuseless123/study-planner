# Study Planner

Hệ thống Lập kế hoạch Học tập Cá nhân — Tích hợp Chỉ báo Rủi ro Khối lượng Công việc và Tối ưu hóa Lịch trình bằng Quy hoạch Tuyến tính.

## 🚀 Quick Start

Xem [startup.md](./startup.md) để biết hướng dẫn setup chi tiết.

```bash
# Setup lần đầu
docker compose build backend
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up -d backend

# Verify
curl -s http://localhost:8000/health | jq
```

## 📖 Tài liệu

- [startup.md](./startup.md) — Hướng dẫn khởi động
- [docs/daily-logs/](./docs/daily-logs/) — Nhật ký công việc

## 🏗️ Kiến trúc

- **Tầng 1:** Web App (React + FastAPI + PostgreSQL)
- **Tầng 2:** Workload Risk Indicator (rule-based)
- **Tầng 3:** LP Optimization Engine (PuLP)

## 📝 License

Đồ án tốt nghiệp đại học — Phạm Kim Long