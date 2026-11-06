# 📋 Nhật ký công việc — Pytest Test Suite (Completed)

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Giai đoạn:** Testing & Quality (Tầng 1)
**Thời gian:** ~10:00 — 14:45
**Người thực hiện:** Phạm Kim Long

---

## 1. Mục tiêu

Setup automated test suite hoàn chỉnh cho backend Tầng 1:
- Đạt coverage ≥ 80% (tiêu chí Chương 6 luận văn)
- Test cả unit (isolated) + integration (end-to-end)
- CI/CD với GitHub Actions
- Có số liệu cụ thể cho Correctness Evaluation

---

## 2. Kết quả cuối cùng

| Metric | Kết quả | Target |
|--------|---------|--------|
| **Total tests** | 93 | — |
| **Passed** | **93 (100%)** | 100% |
| **Failed** | 0 | 0 |
| **Coverage** | **93.89%** | ≥ 80% |
| **Unit tests** | 37 | — |
| **Integration tests** | 56 | — |
| **Runtime** | 20.39s | < 60s |
| **Warnings** | 2 (non-critical) | — |

### Coverage breakdown

**100% coverage (15 files):**
- `api/auth.py`, `api/consent.py`, `api/dashboard.py`, `api/user_data.py`
- `core/config.py`, `core/security.py`
- `models/orm_models.py`
- `repositories/assignment_repo.py`, `repositories/subject_repo.py`
- Tất cả `schemas/*` và `services/*`

**90-99% coverage:**
- `api/subjects.py` (98%)
- `api/deps.py` (95%)
- `repositories/user_repo.py` (94%)
- `main.py` (90%)

**70-89% coverage:**
- `api/logs.py` (85%)
- `repositories/log_repo.py` (83%)
- `api/assignments.py` (79%)

**<70% coverage:**
- `core/database.py` (69%) — chỉ `get_db()` dependency

---

## 3. Bug phát hiện và fix

### 🐛 Bug chính: `.replace()` thay thế nhầm username

**Triệu chứng:**
```
psycopg2.OperationalError: connection to server at "postgres"
(172.19.0.2), port 5432 failed: FATAL: password authentication
failed for user "study_planner_test"
```

93 tests **ERROR** ở setup, coverage chỉ đạt 61.20%.

**Nguyên nhân:**
Trong `tests/conftest.py`:
```python
_base_url = settings.DATABASE_URL.replace("/study_planner", "/study_planner_test")
```

`DATABASE_URL` gốc:
```
postgresql+psycopg2://study_planner:password@postgres:5432/study_planner
                    ^^^^^^^^^^^^^^^                       ^^^^^^^^^^^^^^
                    username                              database name
```

`.replace()` thay thế **TẤT CẢ** occurrences, kể cả `//study_planner:` → username bị đổi thành `study_planner_test`.

**Fix:** Dùng `rsplit("/", 1)` để chỉ thay segment cuối (database name):

```python
def _build_test_db_url() -> str:
    settings = get_settings()
    main_url = settings.DATABASE_URL
    # rsplit ở "/" cuối cùng → tách biệt base URL và database name
    base, _db_name = main_url.rsplit("/", 1)
    return f"{base}/study_planner_test"
```

**Bài học:** `str.replace()` trong Python thay thế **TẤT CẢ** occurrences. Với URL, luôn dùng `rsplit()` hoặc `urlparse()` để thay thế chính xác segment.

### 🐛 Bug nhỏ: SAWarning về transaction

**Triệu chứng:**
```
SAWarning: transaction already deassociated from connection
tests/unit/test_repositories.py::test_duplicate_username_raises
```

**Nguyên nhân:** Khi `IntegrityError` xảy ra (duplicate username), SQLAlchemy tự rollback. Sau đó fixture gọi `transaction.rollback()` lần 2 → warning.

**Fix:** Kiểm tra `transaction.is_active` trước khi rollback.

---

## 4. Cấu trúc test suite

### Test files

```
backend/tests/
├── conftest.py           # Shared fixtures
├── unit/                 # 37 tests
│   ├── test_security.py      # 12 tests (bcrypt + JWT)
│   ├── test_repositories.py  # 16 tests (data access)
│   └── test_schemas.py       # 9 tests (Pydantic validation)
└── integration/          # 56 tests
    ├── test_auth.py          # 12 tests
    ├── test_consent.py       # 5 tests
    ├── test_logs.py          # 13 tests
    ├── test_subjects.py      # 11 tests
    ├── test_assignments.py   # 8 tests
    ├── test_dashboard.py     # 3 tests
    └── test_user_data.py     # 5 tests
```

### Fixtures chính

**Session-scoped:**
- `engine` — SQLAlchemy engine, dispose sau session
- `setup_test_database` — tạo/xóa tables 1 lần

**Function-scoped:**
- `db_session` — transactional session, rollback sau test
- `client` — FastAPI TestClient với DB override
- `test_user`, `second_user` — users cho isolation tests
- `auth_headers`, `second_auth_headers` — JWT headers
- `test_subject`, `second_subject` — domain fixtures
- `test_assignment`, `test_study_session`, `test_sleep_log`, `test_mood_log`
- `test_consent`

### Coverage target đạt được

- **Overall: 93.89%** (target 80%) → vượt 13.89 điểm
- **Business logic (services, repos):** ≥ 83%
- **API endpoints:** ≥ 79%
- **Schemas (Pydantic):** 100%
- **Security:** 100%

---

## 5. Test isolation strategy

### Transactional rollback

Mỗi test function chạy trên 1 transaction riêng, rollback sau khi xong:

```python
@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
```

**Ưu điểm:**
- Không cần clean DB thủ công
- Tests hoàn toàn độc lập
- Nhanh (không recreate DB)

### Cross-user isolation tests

Test kỹ security: mỗi resource đều có test cho:
- User A thấy data của mình ✅
- User A KHÔNG thấy data của User B ✅
- User A KHÔNG GET được resource của User B (404) ✅
- User A KHÔNG DELETE được resource của User B (404) ✅

Áp dụng cho: subjects, assignments, logs, dashboard.

---

## 6. CI/CD setup

### GitHub Actions workflow

File `.github/workflows/test.yml`:
- Trigger: push + PR to main/master/develop
- PostgreSQL service container (15-alpine)
- Python 3.11 với cache pip
- Chạy pytest với coverage
- Upload coverage report (artifact + Codecov)

### Makefile targets

```makefile
make test              # Full suite với coverage
make test-unit         # Chỉ unit tests
make test-integration  # Chỉ integration tests
make coverage          # Mở HTML report
```

---

## 7. Số liệu cho Chương 6 luận văn

### Correctness Evaluation

| Chỉ số | Giá trị |
|--------|---------|
| Total test cases | 93 |
| Pass rate | **100%** |
| Unit test ratio | 39.8% |
| Integration test ratio | 60.2% |
| Line coverage | **93.89%** |
| Branch coverage | ~90% |
| Total runtime | 20.39s |
| Avg per test | 0.22s |

### Cross-user isolation coverage

| Resource | List | Get | Delete |
|----------|:----:|:---:|:------:|
| Subjects | ✅ | ✅ | ✅ |
| Assignments | ✅ | ✅ | ✅ |
| Logs (study) | ✅ | — | ✅ |
| Dashboard | ✅ | — | — |

### Error case coverage

| Status code | Số test cases |
|-------------|:-------------:|
| 400 (Bad Request) | 2 |
| 401 (Unauthorized) | 4 |
| 403 (Forbidden) | 1 |
| 404 (Not Found) | 5 |
| 409 (Conflict) | 2 |
| 422 (Validation) | 8 |
| **Total error cases** | **22** |

→ **23.6% tests là error cases** — coverage đầy đủ cho correctness.

---

## 8. Bài học kinh nghiệm

### 8.1. Về string manipulation trong Python

- **KHÔNG** dùng `str.replace()` cho URL segments — nó thay TẤT CẢ
- Dùng `rsplit("/", 1)` để thay segment cuối
- Hoặc dùng `urlparse` + `urlunparse` cho URL chuẩn

### 8.2. Về test DB strategy

- **Không dùng SQLite** vì Postgres-specific features (JSONB, UUID, TIMESTAMPTZ)
- **Cùng Postgres instance, DB khác** — đơn giản, đủ tốt cho scope này
- **testcontainers** là alternative mạnh hơn nhưng overkill ở giai đoạn prototype

### 8.3. Về pytest-cov behavior

- `pytest --collect-only` **không tăng coverage** vì không chạy tests
- `--no-cov` để tắt coverage khi muốn chạy nhanh
- HTML report hữu ích để review từng dòng chưa test

### 8.4. Về warnings

- Không phải warning nào cũng cần fix
- Passlib deprecation là vấn đề của library, không phải code mình
- SAWarning về transaction là minor — fix bằng `is_active` check

---

## 9. Công việc tiếp theo

### Ưu tiên cao

1. **Tầng 2 — Risk Indicator** (FR #10)
   - Rule-based scoring service độc lập
   - Test suite cho Tầng 2
   - Tích hợp vào Dashboard widget (đã có placeholder)

### Ưu tiên trung bình

2. **Tầng 3 — LP Solver** (FR #11, #12)
3. **Feature Feedback** (FR #13)

### Ưu tiên sau

4. Deploy lên Railway/Render
5. User testing (SUS 5-15 users)

---

## 10. Thống kê công việc

| Metric | Số lượng |
|--------|----------|
| Test files | 10 |
| Fixtures | 14 |
| Total tests | 93 |
| Coverage | 93.89% |
| Warnings | 2 (non-critical) |
| Test runtime | 20.39s |
| CI workflows | 1 |
| Makefile targets thêm | 4 |

---

## 11. Kết luận

**Pytest test suite đã hoàn thành xuất sắc:**

1. **93 automated tests** — 100% pass
2. **93.89% coverage** — vượt target 80%
3. **CI/CD với GitHub Actions** — auto run on push/PR
4. **Makefile targets** — dev-friendly commands
5. **2 warnings non-critical** — có thể fix nếu muốn

**Đây là dữ liệu thực tế vững chắc cho Chương 6 — Correctness Evaluation của luận văn.**

**Tiếp theo:** Tầng 2 — Risk Indicator (rule-based scoring service).

---

**Người lập log:** Phạm Kim Long
**Ngày:** 12/10/2026