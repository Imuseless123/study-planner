# 📋 Nhật ký công việc — Full System Regression Test

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Giai đoạn:** Testing & Integration (Tier 1 + Tier 2)
**Thời gian:** ~13:45 — 14:00
**Người thực hiện:** Phạm Kim Long

---

## 1. Mục tiêu

Verify toàn bộ hệ thống sau khi hoàn thành Tầng 2:
- Tier 1 test suite pass (không regression sau khi thêm Tier 2)
- Tier 2 test suite pass
- Integration Tier 1 ↔ Tier 2 hoạt động (không có interaction bug)
- Boundary cases: empty user, Tier 2 down, cross-tier error handling
- Database consistency: không có orphan records

---

## 2. Kết quả

### Automated test suites

| Suite | Tests | Runtime | Status |
|-------|------:|--------:|:------:|
| Tier 1 (backend) | 93 | 19.43s | ✅ 100% |
| Tier 2 (risk-indicator) | 53 | 0.05s | ✅ 100% |
| **Total** | **146** | ~20s | ✅ |

### Docker services

```
study-planner-backend           Up (healthy)   port 8000
study-planner-risk-indicator    Up (healthy)   port 8001
study-planner-db                Up (healthy)   port 5432
study-planner-frontend          Up             port 3000
```

→ Tất cả 4 container healthy.

### Health checks

| Service | Status | Response |
|---------|:------:|----------|
| Tier 1 | ✅ | `{"status":"ok","service":"tier-1-web-app"}` |
| Tier 2 | ✅ | `{"status":"ok","service":"risk-indicator","version":"1.0.0"}` |
| Frontend | ✅ | HTTP 200 |

### E2E Integration Test (15 cases)

| Nhóm | Tests | Status |
|------|------:|:------:|
| Health checks | 2 | ✅ |
| Auth flow | 2 | ✅ |
| Consent | 1 | ✅ |
| Risk score (empty) | 1 | ✅ |
| Subjects CRUD | 1 | ✅ |
| Assignments CRUD | 1 | ✅ |
| Logs (study/sleep/mood) | 3 | ✅ |
| Risk score (with data) | 1 | ✅ |
| Dashboard | 1 | ✅ |
| Data export | 1 | ✅ |
| Cleanup (delete account) | 1 | ✅ |
| **Total** | **15** | **✅** |

**Điểm quan trọng:** Risk score với data thật của user = **8.33** → tích hợp Tier 1 ↔ Tier 2 hoạt động end-to-end.

### Boundary tests

| Test | Kết quả | Status |
|------|---------|:------:|
| User không có data → risk score | score=0.65, level=low | ✅ |
| Tier 2 down → Tier 1 proxy | HTTP 502 (graceful degradation) | ✅ |
| Tier 2 up lại → Tier 1 proxy | HTTP 200 | ✅ |

→ **Graceful degradation:** khi Tier 2 chết, Tier 1 không crash mà trả về 502 với error message rõ ràng.

### Database consistency

| Metric | Value | Status |
|--------|------:|:------:|
| Users | 2 | ✅ |
| Consents | 1 | ✅ |
| Subjects | 2 | ✅ |
| Assignments | 4 | ✅ |
| Sleep logs | 2 | ✅ |
| Mood logs | 1 | ✅ |
| Study sessions | 0 | ✅ |
| **Orphan records** | **0** | **✅** |

→ Foreign key CASCADE hoạt động đúng, không có dangling references.

---

## 3. So sánh với kỳ vọng

| Kỳ vọng | Thực tế | Status |
|---------|---------|:------:|
| Tier 1: 93 tests pass | 93 passed | ✅ |
| Tier 2: 53 tests pass | 53 passed | ✅ |
| 4 containers healthy | 4 healthy | ✅ |
| E2E 15 cases pass | 15 passed | ✅ |
| Empty user → low risk | 0.65 / low | ✅ |
| Tier 2 down → 502 | HTTP 502 | ✅ |
| 0 orphans | 0 | ✅ |

**Không có bất kỳ test case nào fail.** 

---

## 4. Issue phát hiện (cosmetic, không phải bug)

### 4.1. Terminal encoding

Output hiển thị mojibake:
- `‚úÖ` thay vì `✅`
- `‚ÄĒ` thay vì `—`
- `√ī` thay vì `ô`

**Nguyên nhân:** Container dùng UTF-8, shell của macOS không match locale khi pipe output.

**Ảnh hưởng:** Chỉ là hiển thị. Tests pass 100%.

**Fix (tùy chọn):**
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### 4.2. zsh `#` warnings

Trong boundary test output:
```
zsh: command not found: #
```

**Nguyên nhân:** Paste multi-line comment `# Test 1: ...` vào zsh non-interactive.

**Ảnh hưởng:** Cosmetic. Các lệnh thực tế vẫn chạy.

**Fix:** Bỏ dấu `#` khi paste vào terminal, hoặc dùng `#!/bin/bash` script file.

---

## 5. Điểm kỹ thuật quan trọng

### 5.1. Graceful degradation giữa các Tier

Test Tier 2 down cho thấy Tier 1 không crash:
```python
try:
    r = await http.post(f"{settings.RISK_API_URL}/api/risk/score", json=payload)
    r.raise_for_status()
    return r.json()
except httpx.HTTPError as e:
    raise HTTPException(502, f"Risk service unavailable: {e}")
```

**Best practice:** Microservice calls luôn phải có error handling ở caller. Nếu không, 1 service down sẽ cascade failure toàn hệ thống.

### 5.2. Empty user edge case

User mới chưa có dữ liệu:
- Sleep hours = default 7.0 (khuyến nghị)
- Study std = 0.0 (không có sessions)
- Required hours = 0 (không có assignments)
- Days until deadline = 30 (fallback)

→ Score = 0.65 (rất thấp). Hợp lý về mặt nghiệp vụ.

### 5.3. Foreign key CASCADE verification

Orphan check với LEFT JOIN:
```sql
SELECT COUNT(*) FROM subjects s
LEFT JOIN users u ON u.user_id = s.user_id
WHERE u.user_id IS NULL
```

→ 0 kết quả = không có orphan.

Điều này quan trọng vì:
- Sau khi test E2E xóa account → 4 assignments + 2 subjects + logs liên quan bị xóa theo
- Verify FK CASCADE hoạt động đúng

---

## 6. Milestone đạt được

Sau regression test này, chúng ta có:

| Milestone | Status |
|-----------|:------:|
| Tier 1 hoàn thành (10/14 FR backend + frontend) | ✅ |
| Tier 2 hoàn thành (Risk Indicator service) | ✅ |
| 146 automated tests (93 + 53) | ✅ |
| Coverage: Tier 1 93.89%, Tier 2 >90% | ✅ |
| Integration E2E 15 cases | ✅ |
| Graceful degradation verified | ✅ |
| 0 orphan records | ✅ |
| Docker 4 containers healthy | ✅ |
| CI/CD với GitHub Actions | ✅ |

**Hệ thống ổn định end-to-end, sẵn sàng cho Tầng 3.**

---

## 7. Công việc tiếp theo

### Bước tiếp theo: Tầng 3 — LP Optimization Engine

Complexity **cao hơn Tier 1 + Tier 2 cộng lại**:

1. **MILP model** với PuLP (Mixed-Integer Linear Programming)
2. **Diminishing returns** function `f(x) = √x`, xấp xỉ 4 đoạn tuyến tính
3. **7 nhóm ràng buộc** cứng + **soft constraints** cho deadline và daily limit
4. **Tích hợp risk** qua `W_max_effective = W_max × (1 - 0.5 × Risk/100)`
5. **Test suite** với feasible/infeasible/boundary cases
6. **Cơ chế dự phòng 2 bước** khi solver Infeasible
7. **Frontend** trang `/schedule` với calendar view + feedback

**Ước lượng:** 2-3 buổi làm việc.

---

## 8. Thống kê

| Metric | Value |
|--------|------:|
| Total test cases | 146 |
| Total runtime | ~20s |
| Passing rate | 100% |
| Services | 4 |
| Containers healthy | 4/4 |
| Orphan records | 0 |
| Docker images | 4 |

---

## 9. Kết luận

**Regression test PASS toàn bộ.** Không có bug nào phát hiện sau khi thêm Tier 2.

**Điểm sáng:**
- 146 automated tests (100% pass)
- Coverage Tier 1 = 93.89%, Tier 2 > 90%
- Graceful degradation khi Tier 2 down
- Foreign key CASCADE hoạt động đúng (0 orphans)
- 15 E2E integration cases pass

**Sẵn sàng bắt đầu Tầng 3 — phần phức tạp nhất của luận văn.**

---

**Người lập log:** Phạm Kim Long
**Ngày:** 15/10/2026