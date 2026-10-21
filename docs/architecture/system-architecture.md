# 🏛️ System Architecture — Study Planner

Tài liệu này cung cấp cái nhìn tổng quan về kiến trúc của **Hệ thống Lập kế hoạch Học tập Cá nhân**. Chi tiết kỹ thuật của từng tầng được trình bày trong các tài liệu chuyên biệt.

---

## 1. Kiến trúc 3 Tầng (Three-Tier Architecture)

Hệ thống được thiết kế theo kiến trúc **Microservices** với 3 tầng chức năng độc lập, giao tiếp với nhau qua RESTful API (JSON).

```
┌──────────────────────────────────────────────────────────────┐
│                     Frontend (React - Port 3000)             │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              Tier 1: Web Application (Port 8000)             │
│  - Xác thực (JWT)                                            │
│  - Quản lý dữ liệu (Subjects, Assignments, Logs)             │
│  - Dashboard Aggregation                                     │
└─────────┬────────────────────────────────────────┬───────────┘
          │ HTTP (Fetch Risk)                      │ HTTP (Gen Schedule)
          ▼                                        ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│ Tier 2: Risk Indicator   │         │ Tier 3: LP Solver        │
│ (Port 8001)              │         │ (Port 8002)              │
│ - Rule-based scoring     │         │ - MILP (PuLP)            │
│ - 4 behavioral components│         │ - Diminishing returns    │
└──────────────────────────┘         └──────────────────────────┘
          │
          ▼
┌──────────────────────────┐
│ PostgreSQL 15 (Port 5432)│
└──────────────────────────┘
```

---

## 2. Vai trò các Tầng

### 🔹 Tầng 1: Web Application Layer
- **Vai trò:** Giao diện người dùng và quản lý dữ liệu trung tâm.
- **Chức năng:** Thu thập dữ liệu hành vi, cung cấp CRUD cho môn học/bài tập, hiển thị dashboard và đóng vai trò proxy điều phối gọi Tầng 2 & Tầng 3.
- **Chi tiết:** Xem [tier-1-overview.md](./tier-1-overview.md)

### 🔹 Tầng 2: Workload Risk Indicator
- **Vai trò:** Đánh giá mức độ căng thẳng (không chẩn đoán y tế).
- **Chức năng:** Tính điểm rủi ro 0-100 từ 4 yếu tố (thiếu ngủ, mật độ công việc, deadline, tính nhất quán).
- **Chi tiết:** Xem [tier-2-overview.md](./tier-2-overview.md)

### 🔹 Tầng 3: LP Optimization Engine
- **Vai trò:** Lõi tối ưu hóa lịch trình.
- **Chức năng:** Sử dụng MILP để tạo lịch học tối ưu, có xét đến lợi nhuận giảm dần của việc học và các ràng buộc hành vi.
- **Chi tiết:** Xem [tier-3-overview.md](./tier-3-overview.md)

---

## 3. Luồng dữ liệu End-to-End (Data Flow)

### Luồng 1: Ghi nhật ký & Xem Dashboard
1. User nhập log (Study/Sleep/Mood) tại Frontend.
2. Frontend gọi API Tầng 1 → Lưu vào PostgreSQL.
3. Frontend gọi API Tầng 1 (`/dashboard/summary`) để lấy dữ liệu tổng hợp.
4. Frontend gọi API Tầng 1 (`/risk/score`) → Tầng 1 aggregate data → Gọi Tầng 2.
5. Tầng 2 trả về Risk Score. Tầng 1 trả về Frontend để vẽ Widget.

### Luồng 2: Tạo lịch học (Phức tạp nhất)
1. User bấm "Tạo lịch" tại Frontend.
2. Frontend gọi Tầng 1 (`POST /schedule/generate`).
3. Tầng 1 truy vấn DB lấy danh sách bài tập sắp tới.
4. Tầng 1 gọi Tầng 2 lấy Risk Score hiện tại.
5. Tầng 1 tính `W_max_effective = W_max × (1 - α × Risk/100)`.
6. Tầng 1 gọi Tầng 3 gửi kèm danh sách bài tập và `W_max_effective`.
7. Tầng 3 giải bài toán MILP, trả về lịch + giải thích.
8. Tầng 1 lưu lịch vào DB và trả về Frontend.
9. User xem lịch và gửi Feedback (1-5 sao).

---

## 4. Công nghệ sử dụng (Tech Stack)

| Component | Công nghệ | Lý do chọn |
|-----------|-----------|------------|
| **Frontend** | React 18 + TypeScript + Ant Design | Component-based, UI phong phú |
| **Backend (Tier 1)** | FastAPI + SQLAlchemy | Async, type-safe, tự động sinh Swagger |
| **Risk Indicator (Tier 2)** | FastAPI + Pydantic | Nhẹ, dễ viết unit test cho pure functions |
| **LP Solver (Tier 3)** | PuLP + CBC | Open-source, mạnh mẽ cho MILP |
| **Database** | PostgreSQL 15 | Hỗ trợ tốt JSONB, UUID, TIMESTAMPTZ |
| **Deployment** | Docker Compose | Nhất quán giữa dev và production |

---

## 5. Chất lượng & Kiểm thử (Quality Assurance)

Hệ thống được bảo vệ bởi **170 automated tests** (100% pass).

| Tầng | Tests | Coverage | Runtime |
|------|:-----:|:--------:|:-------:|
| Tier 1 (Backend) | 93 | 93.89% | 19.19s |
| Tier 2 (Risk) | 53 | 92.98% | 0.05s |
| Tier 3 (LP Solver) | 24 | 92.98% | 0.11s |
| **Total** | **170** | **>90%** | **~20s** |

- **CI/CD:** GitHub Actions chạy test tự động khi push code (Postgres container).
- **Regression Test:** Script `regression_test.sh` test toàn bộ flow E2E (Auth → CRUD → Risk → Schedule).

---

## 6. Các quyết định thiết kế quan trọng (Trade-offs)

1. **Tại sao tách Tầng 2 & 3 thành microservices?**
   - Giúp tách biệt logic tính toán phức tạp khỏi CRUD thông thường.
   - Dễ dàng thay thế/thu hồi (ví dụ: nâng cấp Tầng 3 lên dùng OR-Tools sau này) mà không ảnh hưởng đến Tầng 1.
2. **Tại sao không dùng SQLite cho testing?**
   - Vì hệ thống dùng các tính năng đặc thù của PostgreSQL (UUID, JSONB, TIMESTAMPTZ, Check Constraints). Dùng SQLite sẽ không test được logic thật.
3. **Tại sao dùng Soft Constraints trong LP Solver?**
   - Tránh việc solver báo `Infeasible` (vô nghiệm) khi user có quá nhiều bài tập. Thay vào đó, solver trả về lịch tối ưu nhất có thể kèm cảnh báo (ví dụ: thiếu 2 giờ trước deadline), cho phép user chủ động điều chỉnh.

---

**Người soạn:** Phạm Kim Long
**Ngày cập nhật:** 21/10/2026