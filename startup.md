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

Nếu thấy output này → **backend đang chạy**. Mở tiếp:

- **Backend Swagger:** http://localhost:8000/docs
- **Frontend:** http://localhost:3000

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

### Bước 3: Build Docker images

```bash
docker compose build backend frontend
```

Lần đầu mất 3-5 phút (tải base images + cài dependencies). Lần sau sẽ nhanh hơn nhờ cache.

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

### Bước 7: Khởi động backend + frontend

```bash
docker compose up -d
```

### Bước 8: Verify services

**Backend:**
```bash
curl -s http://localhost:8000/health | jq
```
Kỳ vọng: `{"status":"ok","service":"tier-1-web-app"}`

**Frontend:**
```bash
curl -s http://localhost:3000 | head -5
```
Kỳ vọng: `<!DOCTYPE html>...`

### Bước 9: Mở browser

- **Swagger UI (Backend):** http://localhost:8000/docs
- **Frontend:** http://localhost:3000

Frontend tự động redirect:
- Chưa login → `/login`
- Đã login, chưa consent → `/consent`
- Đã login + consent → `/dashboard`

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

# Chỉ xem log frontend
docker compose logs -f frontend

# Restart 1 service
docker compose restart backend
docker compose restart frontend

# Dừng tất cả (giữ data)
docker compose down

# Dừng và xóa volume (mất data)
docker compose down -v

# Vào shell của container
docker compose exec backend bash
docker compose exec frontend sh
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

## 🗄️ Visualize Database

Sau khi database đã có schema (sau Bước 5), bạn có thể xem trực quan bằng **IntelliJ IDEA** hoặc **Visual Studio Code**.

### Connection Parameters

Cả 2 IDE dùng cùng thông số kết nối:

| Field | Value |
|-------|-------|
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `study_planner` |
| **User** | `study_planner` |
| **Password** | `dev_password_change_in_prod` |
| **URL (JDBC/Postgres)** | `jdbc:postgresql://localhost:5432/study_planner` |

> **Lưu ý:** Host là `localhost` (không phải `postgres`) vì bạn kết nối từ máy host, không phải từ trong Docker network.

---

### 🎯 Cách 1: IntelliJ IDEA (Ultimate)

**Yêu cầu:** IntelliJ IDEA Ultimate (Database tools không có ở Community Edition).

#### Bước 1: Mở Database Tool Window

`View → Tool Windows → Database`

Hoặc: `⌘ ;` (macOS) / `Ctrl + Shift + ;` (Windows/Linux)

#### Bước 2: Thêm Data Source

1. Click biểu tượng **`+`** ở góc trên cùng bên trái
2. Chọn **`Data Source → PostgreSQL`**
3. Điền thông số:

   | Field | Value |
   |-------|-------|
   | Name | `Study Planner (local)` |
   | Host | `localhost` |
   | Port | `5432` |
   | Database | `study_planner` |
   | User | `study_planner` |
   | Password | `dev_password_change_in_prod` |

4. Nếu chưa có PostgreSQL JDBC driver → click **Download** ở dòng "Driver files"
5. Click **Test Connection**
   - Nếu thấy **"Succeeded"** → OK
   - Nếu lỗi `Connection refused` → Postgres chưa chạy: `docker compose up -d postgres`
6. Click **OK**

#### Bước 3: Khám phá Schema

Trong Database tool window, expand cây:

```
Study Planner (local)
└── study_planner
    └── public
        ├── tables
        │   ├── users
        │   ├── consents
        │   ├── subjects
        │   ├── assignments
        │   ├── study_sessions
        │   ├── sleep_logs
        │   ├── mood_logs
        │   ├── schedules
        │   └── feedback
        ├── views
        └── indexes
```

Double-click 1 bảng → xem data dạng bảng tính. Tab **DDL** → xem SQL CREATE TABLE.

#### Bước 4 (Bonus): ER Diagram

Chuột phải vào `public` schema → **Diagrams → Show Visualization** (hoặc `⌥⌘U`).

Kết quả: ER diagram trực quan với FK arrows.

---

### 🎯 Cách 2: Visual Studio Code

**Yêu cầu:** Extension **Database Client** hoặc **PostgreSQL** (chọn 1).

#### Option A: Extension "Database Client" (khuyến nghị)

**Cài đặt:**
1. Mở VS Code
2. `⌘ Shift X` (Extensions)
3. Search **`Database Client`** (author: cweijan)
4. Click **Install**

**Thêm Connection:**

1. Click icon **Database** ở Sidebar (góc trái, icon hình đĩa)
2. Click **`+`** → chọn **PostgreSQL**
3. Điền:

   | Field | Value |
   |-------|-------|
   | Name | `Study Planner` |
   | Host | `localhost` |
   | Port | `5432` |
   | User | `study_planner` |
   | Password | `dev_password_change_in_prod` |
   | Database | `study_planner` |

4. Click **Connect**

**Sử dụng:**

- Expand connection → thấy list tables
- Click 1 bảng → data hiện dạng bảng tính
- Chuột phải → **Show Table DDL** để xem CREATE TABLE
- Toolbar trên cùng: **Run SQL** (icon ▶) để chạy query

**Export/Import:**

- Chuột phải bảng → **Export Data** → chọn JSON/CSV/SQL
- Chuột phải database → **Import Data** để restore

---

#### Option B: Extension "PostgreSQL" (chính chủ Microsoft)

**Cài đặt:**
1. Search **`PostgreSQL`** (author: Microsoft)
2. Install

**Thêm Connection:**
1. `⌘ Shift P` → `PostgreSQL: Add Connection`
2. Điền host/port/user/password/database như trên
3. Connection xuất hiện ở panel **PostgreSQL** (icon voi)

**Hạn chế:** Chỉ query, không có GUI table viewer đẹp bằng Database Client.

---

### 🎯 Cách 3: Extension "SQLTools" (alternative)

**Cài đặt:**
1. Search **`SQLTools`** (author: Matheus Teixeira)
2. Install **SQLTools** + **SQLTools PostgreSQL/Cockroach Driver**

**Thêm Connection:**
1. Click icon SQLTools ở sidebar
2. Click **Add New Connection** → PostgreSQL
3. Điền thông số → **Save Connection** → **Connect**

**Ưu điểm:** Hỗ trợ nhiều DB (MySQL, SQLite, MongoDB...), có query history.

---

### 🎯 Cách 4: DBeaver (standalone, đầy đủ nhất)

Nếu muốn GUI chuyên nghiệp hơn IDE:

```bash
brew install --cask dbeaver-community
```

**Setup:**
1. Mở DBeaver → **New Database Connection**
2. Chọn **PostgreSQL** → Next
3. Điền host/port/database/user/password
4. **Test Connection** → **Finish**

**Tính năng mạnh:**
- ER Diagram tự động (chuột phải database → **View Diagram**)
- Data export/import nhiều format
- Query builder trực quan
- So sánh schema giữa 2 database

---

### 🎯 Cách 5: pgAdmin (web UI, chạy trong Docker)

Nếu muốn web UI, thêm service vào `docker-compose.yml`:

```yaml
services:
  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: study-planner-pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres
```

Sau đó:
```bash
docker compose up -d pgadmin
open http://localhost:5050
```

Login: `admin@example.com` / `admin`. Thêm server với host = `postgres` (không phải localhost, vì pgAdmin chạy trong Docker network).

---

### So sánh các công cụ

| Tool | Type | Ưu điểm | Nhược điểm |
|------|------|---------|------------|
| **IntelliJ IDEA Ultimate** | IDE integrated | Tích hợp sẵn, ER diagram, refactor | Cần Ultimate license |
| **VS Code + Database Client** | Extension | Nhẹ, nhanh, GUI đẹp | Ít tính năng hơn DBeaver |
| **VS Code + PostgreSQL** | Extension | Chính chủ Microsoft | Không có GUI table viewer |
| **DBeaver** | Standalone | Nhiều tính năng nhất, miễn phí | Nặng hơn, cần cài thêm |
| **pgAdmin** | Web UI | Không cần cài, truy cập từ xa | Cần chạy thêm container |

**Khuyến nghị:**
- Dev hàng ngày: **VS Code + Database Client**
- Xem ER diagram đẹp: **IntelliJ IDEA Ultimate** hoặc **DBeaver**
- Debug production: **pgAdmin** (chạy trên server)

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
lsof -i :3000

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

### Lỗi: Frontend báo `Failed to resolve import "X"`

**Nguyên nhân:** Package chưa được cài (thiếu trong `package.json`).

**Fix:**
```bash
# Cách 1: Cài trực tiếp trong container
docker compose exec frontend npm install <package-name>

# Cách 2: Sửa package.json + rebuild
docker compose up -d --build --force-recreate frontend
```

### Lỗi: Frontend hiển thị trang trắng

**Chẩn đoán:**
```bash
# 1. Xem log frontend
docker compose logs frontend

# 2. Mở DevTools (F12) → Console tab → xem lỗi
# 3. Kiểm tra VITE_API_URL trong docker-compose.yml
```

---

## 🔄 Reset toàn bộ (Clean slate)

Khi cần xóa hết và làm lại từ đầu:

```bash
# 1. Dừng tất cả và xóa volume
docker compose down -v

# 2. Xóa image cũ (tuỳ chọn)
docker compose down --rmi local

# 3. Khởi động lại từ đầu
docker compose build backend frontend
docker compose up -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up -d

# 4. Verify
curl -s http://localhost:8000/health | jq
curl -s http://localhost:3000 | head -3
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
│   ├── architecture/       # Kiến trúc hệ thống
│   │   └── tier-1-overview.md
│   └── daily-logs/         # Work logs
└── shared/
    └── scripts/            # Shared utility scripts
```

---

## 🎯 Ports sử dụng

| Service | Port | URL | Trạng thái |
|---------|------|-----|:----------:|
| PostgreSQL | 5432 | `localhost:5432` | ✅ |
| **Backend API** | 8000 | http://localhost:8000 | ✅ |
| Swagger UI | 8000 | http://localhost:8000/docs | ✅ |
| ReDoc | 8000 | http://localhost:8000/redoc | ✅ |
| **Frontend** | 3000 | http://localhost:3000 | ✅ |

**Routes của Frontend:**

| Route | Chức năng |
|-------|-----------|
| `/login` | Đăng nhập |
| `/register` | Đăng ký |
| `/consent` | Ký đồng thuận |
| `/dashboard` | Trang chủ |
| `/logging` | Ghi nhật ký (3 tabs) |
| `/subjects` | Quản lý môn học |
| `/assignments` | Quản lý bài tập |
| `/schedule` | Lịch học (chờ Tầng 3) |
| `/settings` | Cài đặt (chờ FR #14) |

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

- [ ] `docker compose ps` → 3 container healthy (postgres, backend, frontend)
- [ ] `curl /health` → `{"status":"ok"}`
- [ ] `curl http://localhost:3000` → có HTML
- [ ] Swagger UI hiển thị 6 nhóm endpoint (auth, consent, logs, subjects, assignments, dashboard)
- [ ] `\dt` trong psql → 10 bảng
- [ ] `\di` trong psql → có `idx_*` indexes
- [ ] Database visualized thành công qua IDE (IntelliJ/VS Code)
- [ ] E2E test pass (register → login → consent → subject → log → dashboard)
- [ ] Validation test fail đúng (no token → 403, bad difficulty → 422)

---

## 📚 Tài liệu liên quan

- [`README.md`](./README.md) — Tổng quan dự án
- [`docs/architecture/tier-1-overview.md`](./docs/architecture/tier-1-overview.md) — Kiến trúc Tầng 1 (database + dataflow)
- [`docs/daily-logs/`](./docs/daily-logs/) — Nhật ký công việc hàng ngày
- `plan.docx` — Kế hoạch tổng thể 12 tuần

---

**Cập nhật lần cuối:** 2026-10-06
**Phiên bản:** Tầng 1 (Web Application Layer) — 9/14 FR