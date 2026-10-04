# 🚀 Startup Guide — Study Planner

Hướng dẫn từng bước để khởi động dự án từ đầu. Dành cho người mới clone repo hoặc cần reset môi trường.

---

## 📋 Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu | Kiểm tra |
|---------|---------------------|----------|
| Docker Desktop | 24.x | `docker --version` |
| Docker Compose | v2.x | `docker compose version` |
| Git | 2.40+ | `git --version` |
| Node.js | 18.x hoặc 20.x | `node --version` |
| (tùy chọn) `jq` | Bất kỳ | `which jq` |

### Cài đặt nếu thiếu (macOS)

```bash
brew install --cask docker
brew install node git jq
```

Sau khi cài Docker Desktop, mở app Docker 1 lần để nó khởi động Docker daemon.

---

## ⚡ Quick Start (3 lệnh)

Nếu đã từng setup và chỉ muốn chạy lại:

```bash
docker compose up -d
docker compose ps
curl -s http://localhost:8000/health | jq
```

Kỳ vọng:
```json
{"status":"ok","service":"tier-1-web-app"}
```

Nếu thấy output này → **backend đang chạy**. Xong.

---

## 🏗️ Full Setup từ đầu (First Time)

### Bước 1: Clone repo và vào thư mục

```bash
git clone <repo-url> study-planner
cd study-planner
```

### Bước 2: Tạo file `.env` ở root

```bash
cat > .env << 'EOF'
# ===== Database =====
POSTGRES_USER=study_planner
POSTGRES_PASSWORD=dev_password_change_in_prod
POSTGRES_DB=study_planner
DATABASE_URL=postgresql+psycopg2://study_planner:dev_password_change_in_prod@postgres:5432/study_planner

# ===== JWT =====
JWT_SECRET=dev_secret_replace_with_random_64_chars_0123456789abcdefghijklmnop
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ===== Downstream services =====
RISK_API_URL=http://risk-indicator:8001
LP_SOLVER_API_URL=http://lp-solver:8002

# ===== Frontend =====
FRONTEND_URL=http://localhost:3000

# ===== Consent =====
CONSENT_VERSION=1.0
CONSENT_DURATION_DAYS=365
EOF
```

⚠️ **Lưu ý:** Không commit file `.env` — đã có trong `.gitignore`.

### Bước 3: Build Docker image

```bash
docker compose build backend
```

Lần đầu mất 2-4 phút (tải base image Python + cài dependencies). Lần sau sẽ nhanh hơn nhờ cache.

### Bước 4: Khởi động PostgreSQL

```bash
docker compose up -d postgres
```

Đợi ~10 giây cho Postgres sẵn sàng:

```bash
docker compose ps
```

Kỳ vọng:
```
NAME                STATUS
study-planner-db    Up (healthy)
```

Nếu status là `Up (health: starting)`, chờ thêm 5-10 giây và chạy lại.

### Bước 5: Chạy migration

```bash
docker compose run --rm backend alembic upgrade head
```

Kỳ vọng:
```
INFO  [alembic.runtime.migration] Running upgrade  -> ffbed559952c, initial schema
```

### Bước 6: Verify database

```bash
docker compose exec -T postgres psql -U study_planner -d study_planner -c "\dt"
```

Kỳ vọng: 10 bảng (9 bảng + `alembic_version`).

```bash
docker compose exec -T postgres psql -U study_planner -d study_planner -c "\di" | head -20
```

Kỳ vọng: thấy các index `idx_*`.

### Bước 7: Khởi động backend

```bash
docker compose up -d backend
```

### Bước 8: Verify health

```bash
curl -s http://localhost:8000/health | jq
```

Kỳ vọng:
```json
{"status":"ok","service":"tier-1-web-app"}
```

### Bước 9: Mở Swagger UI

Mở trình duyệt: **http://localhost:8000/docs**

Phải thấy 5 nhóm endpoint: `auth`, `consent`, `logs`, `subjects`, `dashboard`.

---

## 🔄 Các lệnh thường dùng

### Docker Compose

```bash
# Khởi động tất cả service (background)
docker compose up -d

# Xem trạng thái
docker compose ps

# Xem log (theo dõi trực tiếp)
docker compose logs -f

# Chỉ xem log backend
docker compose logs -f backend

# Restart 1 service
docker compose restart backend

# Dừng tất cả (giữ data)
docker compose down

# Dừng và xóa volume (mất data)
docker compose down -v

# Vào shell của container
docker compose exec backend bash
docker compose exec postgres psql -U study_planner -d study_planner
```

### Alembic (Database Migration)

```bash
# Xem version hiện tại
docker compose run --rm backend alembic current

# Xem lịch sử migration
docker compose run --rm backend alembic history --verbose

# Chạy migration mới nhất
docker compose run --rm backend alembic upgrade head

# Rollback 1 bước
docker compose run --rm backend alembic downgrade -1

# Rollback về đầu
docker compose run --rm backend alembic downgrade base

# Tạo migration mới sau khi sửa orm_models.py
docker compose run --rm backend alembic revision --autogenerate -m "mô tả thay đổi"

# Xem SQL mà migration sẽ chạy (không thực thi)
docker compose run --rm backend alembic upgrade head --sql
```

### Database

```bash
# Vào psql shell
docker compose exec postgres psql -U study_planner -d study_planner

# Liệt kê bảng
docker compose exec -T postgres psql -U study_planner -d study_planner -c "\dt"

# Xem cấu trúc 1 bảng
docker compose exec -T postgres psql -U study_planner -d study_planner -c "\d users"

# Đếm records
docker compose exec -T postgres psql -U study_planner -d study_planner -c "SELECT COUNT(*) FROM users;"

# Backup
docker compose exec -T postgres pg_dump -U study_planner study_planner > backup.sql

# Restore
cat backup.sql | docker compose exec -T postgres psql -U study_planner -d study_planner
```

---

## 🧪 Test E2E bằng curl

Chạy **từng lệnh, từng dòng** trong **cùng một terminal session** (biến `$TOKEN` không persist giữa các tab).

```bash
# 1. Đăng ký
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123","email":"alice@example.com"}' | jq

# 2. Login + lấy token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}' | jq -r '.token')
echo "Token length: ${#TOKEN}"

# 3. Lấy thông tin user
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Tạo subject
SUBJECT_ID=$(curl -s -X POST http://localhost:8000/api/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject_name":"Toan cao cap","difficulty":4,"priority":5}' | jq -r '.subject_id')
echo "Subject ID: $SUBJECT_ID"

# 5. Ghi sleep log
curl -s -X POST http://localhost:8000/api/log/sleep \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sleep_time":"2026-10-03T23:00:00Z","wake_time":"2026-10-04T07:00:00Z","quality":4}' | jq

# 6. Dashboard
curl -s http://localhost:8000/api/dashboard/summary \
  -H "Authorization: Bearer $TOKEN" | jq

# 7. Test validation (phải fail)
echo "No token:"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/auth/me

echo "Bad difficulty:"
curl -s -X POST http://localhost:8000/api/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"subject_name":"Bad","difficulty":10,"priority":5}' | jq '.detail[0].type'
```

---

## 🔧 Troubleshooting

### Lỗi: `docker: command not found`

**Nguyên nhân:** Docker Desktop chưa mở.

**Fix:**
```bash
open -a Docker
# Đợi 30s cho Docker daemon khởi động
docker ps
```

### Lỗi: `services.networks Additional property X is not allowed`

**Nguyên nhân:** Syntax YAML sai indent.

**Fix:**
```bash
docker compose config
```
Lệnh này sẽ chỉ ra dòng lỗi. Sửa indent (dùng spaces, không dùng tab).

### Lỗi: `port is already allocated`

**Nguyên nhân:** Port 5432/8000/3000 đã bị process khác chiếm.

**Fix:**
```bash
# Tìm process đang dùng port
lsof -i :8000
lsof -i :5432

# Kill process
kill -9 <PID>

# Hoặc đổi port trong docker-compose.yml
```

### Lỗi: `command not found: alembic`

**Nguyên nhân:** Alembic chưa cài local, hoặc chạy sai chỗ.

**Fix:** Luôn chạy Alembic **trong Docker**:
```bash
docker compose run --rm backend alembic upgrade head
```

### Lỗi: `the input device is not a TTY`

**Nguyên nhân:** Pipe heredoc vào `docker compose exec` không có terminal.

**Fix:** Thêm flag `-T`:
```bash
docker compose exec -T postgres psql -U study_planner -d study_planner << 'EOF'
SELECT 1;
EOF
```

### Lỗi: Backend container không start

**Chẩn đoán:**
```bash
# 1. Xem log
docker compose logs backend

# 2. Chạy foreground để thấy lỗi
docker compose up backend

# 3. Test import module
docker compose run --rm backend python -c "from app.main import app; print('OK')"
```

### Lỗi: `relation "users" does not exist`

**Nguyên nhân:** Chưa chạy migration.

**Fix:**
```bash
docker compose run --rm backend alembic upgrade head
```

### Lỗi: Curl trả về rỗng, `$TOKEN` length = 0

**Nguyên nhân:** Backend chưa chạy hoặc restart sai cách.

**Fix:**
```bash
docker compose up -d backend
docker compose ps
curl -s http://localhost:8000/health
```

⚠️ **Lưu ý:** Dùng `up -d` (tạo mới), KHÔNG dùng `restart` nếu container chưa tồn tại.

---

## 🔄 Reset toàn bộ (Clean slate)

Khi cần xóa hết và làm lại từ đầu:

```bash
# 1. Dừng tất cả và xóa volume
docker compose down -v

# 2. Xóa image cũ (tuỳ chọn)
docker compose down --rmi local

# 3. Khởi động lại từ đầu
docker compose build backend
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up -d backend

# 4. Verify
curl -s http://localhost:8000/health | jq
```

---

## 📁 Cấu trúc project

```
study-planner/
├── STARTUP.md              # File này
├── README.md               # Tổng quan dự án
├── docker-compose.yml      # Orchestration
├── .env                    # Secrets (KHÔNG commit)
├── .env.example            # Template
├── .gitignore
├── Makefile                # Shortcut commands
├── backend/                # FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/            # Migrations
│   ├── app/                # Source code
│   └── db/                 # Scripts (verify, seed)
├── frontend/               # React frontend
│   ├── Dockerfile
│   ├── package.json
│   └── src/
├── docs/                   # Documentation
│   └── daily-logs/         # Work logs
└── shared/
    └── scripts/            # Shared utility scripts
```

---

## 🎯 Ports sử dụng

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | `localhost:5432` |
| Backend API | 8000 | http://localhost:8000 |
| Swagger UI | 8000 | http://localhost:8000/docs |
| ReDoc | 8000 | http://localhost:8000/redoc |
| Frontend | 3000 | http://localhost:3000 (chưa có) |

---

## 🔑 Credentials mặc định (dev)

| Field | Value |
|-------|-------|
| Postgres user | `study_planner` |
| Postgres password | `dev_password_change_in_prod` |
| Postgres database | `study_planner` |
| Test user (sau khi register) | `alice` / `password123` |

⚠️ **Trong production:** Đổi hết password, dùng strong JWT_SECRET (64+ chars random).

---

## ✅ Checklist sau khi setup

- [ ] `docker compose ps` → 2 container healthy
- [ ] `curl /health` → `{"status":"ok"}`
- [ ] Swagger UI hiển thị 5 nhóm endpoint
- [ ] `\dt` trong psql → 10 bảng
- [ ] `\di` trong psql → có `idx_*` indexes
- [ ] E2E test pass (register → login → me → subject → log → dashboard)
- [ ] Validation test fail đúng (no token → 403, bad difficulty → 422)

---

## 📚 Tài liệu liên quan

- `docs/daily-logs/` — Nhật ký công việc hàng ngày
- `docs/architecture/` — Kiến trúc hệ thống (sẽ bổ sung)
- `plan.docx` — Kế hoạch tổng thể 12 tuần
- `README.md` — Tổng quan dự án

---

**Cập nhật lần cuối:** 2026-10-04
**Phiên bản:** Tầng 1 (Web Application Layer)
STARTUPEOF