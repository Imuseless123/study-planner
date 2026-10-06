# 📋 Nhật ký công việc — Dashboard Widgets

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Giai đoạn:** Frontend Dashboard (Tầng 1)
**Thời gian:** ~15:30 — 17:30
**Người thực hiện:** Phạm Kim Long

---

## 1. Mục tiêu

Triển khai feature **Dashboard Widgets** (FR #8, #9) — biến Dashboard từ placeholder thành trung tâm thông tin thực sự.

**Điều kiện trước:**
- Backend `/api/dashboard/summary` đã có: `study_hours_by_date`, `study_hours_matrix`, `sleep_hours_recent`, `upcoming_assignments`, `subjects`
- Frontend: DashboardPage chỉ là placeholder với greeting

**Mục tiêu:**
- Statistics cards (4 metrics: giờ học, giấc ngủ, deadline, streak)
- Weekly Study Chart (bar chart 7 ngày với reference line)
- Workload Heatmap (day × subject)
- Deadline Timeline với urgency indicator
- Sleep Quality Card
- Risk Score Widget placeholder (sẵn sàng Tầng 2)

---

## 2. Công việc đã thực hiện

### 2.1. API client

File `frontend/src/api/dashboard.ts`:
- Types: `DashboardSummary`, `UpcomingAssignment`
- Method `summary()` gọi `GET /api/dashboard/summary`

### 2.2. Components

**`StatisticsCards.tsx`** — 4 cards responsive:
- Giờ học 7 ngày (sum từ `study_hours_by_date`)
- TB giấc ngủ (average từ `sleep_hours_recent`), màu theo ngưỡng (xanh ≥7h, vàng ≥6h, đỏ <6h)
- Bài tập sắp tới hạn (≤3 ngày)
- Streak — số ngày liên tiếp có ghi log
- Hàm `calculateStreak()` xử lý logic: streak = 0 nếu ngày gần nhất không phải hôm nay/hôm qua (tránh user thấy streak cũ)

**`WeeklyStudyChart.tsx`** — Recharts BarChart:
- Tạo 7 ngày gần nhất
- ReferenceLine y=3 (mục tiêu 3h/ngày)
- Tooltip custom với ngày đầy đủ
- Empty state nếu chưa có data

**`WorkloadHeatmap.tsx`** — HTML table:
- Rows = subjects, Columns = 7 ngày gần nhất
- 7 mức màu cường độ từ `#f5f5f5` (0h) đến `#003eb3` (>6h)
- Auto contrast text (đen nền sáng, trắng nền đậm)
- Column "Tổng" + Row "Tổng ngày"
- Tooltip mỗi cell: subj + date + hours
- Legend 7 mức cường độ
- Scroll ngang trên mobile

**`DeadlineTimeline.tsx`** — Ant Design Timeline:
- Sort theo deadline, lấy 10 bài sắp tới
- Dot icon + màu theo urgency:
  - Đỏ: <24h hoặc hôm nay
  - Cam: ≤3 ngày
  - Xanh: ≤7 ngày
  - Xanh lá: >7 ngày
- Nút "Xem tất cả" navigate đến `/assignments`

**`SleepQualityCard.tsx`**:
- Circular dashboard progress
- Status: Tốt (≥7h), Chưa đủ (6-7h), Thiếu ngủ (<6h)
- Hiển thị TB giờ, khuyến nghị, thiếu hụt (nếu có), số ngày ghi log

**`RiskScoreWidget.tsx`** — Placeholder:
- Circular progress score=0, level="low"
- Tag "Sắp ra mắt"
- Disclaimer đầy đủ: "Không phải chẩn đoán y tế/tâm lý"
- Alert info: "Chỉ báo rủi ro sẽ có sẵn khi Tầng 2 hoàn thành"
- CTA "Ghi thêm nhật ký" navigate đến `/logging`

### 2.3. DashboardPage rewrite

File `frontend/src/pages/DashboardPage.tsx`:
- Header: greeting + ngày tháng + nút "Làm mới"
- **Onboarding Alert** cho user mới (detect all data empty)
- Layout responsive:
  - Row 1: Statistics (4 cards)
  - Row 2: WeeklyChart (lg=16) + SleepQuality (lg=8)
  - Row 3: Heatmap (lg=16) + RiskWidget (lg=8)
  - Row 4: Timeline full-width
- Loading state với Spin
- Empty state nếu không load được

---

## 3. Bug phát hiện và fix

### 🐛 Bug: `Failed to resolve import "recharts"`

**Triệu chứng:** Vite error overlay hiển thị:
```
[plugin:vite:import-analysis] Failed to resolve import "recharts" from "src/components/WeeklyStudyChart.tsx". Does the file exist?
```

**Nguyên nhân:** Khi setup `package.json` lần đầu ở phần Frontend Auth, tôi quên thêm `recharts` vào dependencies. Khi thêm Dashboard Widgets, tôi import từ `recharts` nhưng không cập nhật `package.json`.

**Fix:**
1. Thêm `"recharts": "^2.10.3"` vào `frontend/package.json`
2. Rebuild container: `docker compose up -d --build frontend`
3. Verify: `docker compose exec frontend ls node_modules/recharts` → OK

**Bài học:** Khi import từ package mới, **luôn** cập nhật `package.json`. Nếu làm việc trong container, dùng `npm install <pkg>` để auto-update.

---

## 4. Kết quả kiểm thử

### 4.1. Seed data

Đã seed cho bob:
- 1 subject ("Lập trình Web")
- 2 assignments (deadline 6 giờ + 2 ngày tới)
- 1 sleep log (8h)

### 4.2. Screenshot verify

**Screenshot 1 — Tổng quan dashboard:**
- ✅ 4 Statistics cards hiển thị: `0.0h` học, `8.0h` ngủ (xanh), `2` bài tập sắp hạn, `0` ngày streak
- ✅ Weekly Chart hiển thị Empty state "Chưa có dữ liệu" (đúng vì chưa có study session)
- ✅ Sleep quality card: circular progress 8.0h màu xanh, status "Tốt", khuyến nghị 7-8h, số ngày ghi = 1
- ✅ Heatmap: 1 row "Lập trình Web" × 7 columns, tất cả trống, tổng = 0.0h
- ✅ Risk widget: 0/100, "Mức: Thấp" (tag xanh), disclaimer + alert "Đang phát triển" + CTA
- ✅ Header "Xin chào, bob 👋" với ngày hôm nay

**Screenshot 2 — Chi tiết heatmap + timeline:**
- ✅ Heatmap legend đủ 7 mức cường độ
- ✅ Row "Tổng ngày" hiển thị `—` cho ngày không có data
- ✅ Deadline Timeline có 3 items:
  - "bài 1.5" — tag đỏ "Còn 6 giờ"
  - "bài 1.8" — tag cam "Còn 2 ngày"
  - "bài tập 1" — tag xanh "Còn 7 ngày"
- ✅ Mỗi item hiển thị: subject tag, deadline đầy đủ, số giờ chuẩn bị, priority

### 4.3. Test UI

| # | Test | Kết quả |
|---|------|---------|
| 1 | 4 Statistics cards | ✅ |
| 2 | Weekly chart empty state | ✅ |
| 3 | Sleep circular progress | ✅ |
| 4 | Sleep status màu theo ngưỡng | ✅ |
| 5 | Heatmap grid (subjects × 7 days) | ✅ |
| 6 | Heatmap legend 7 mức | ✅ |
| 7 | Timeline sort theo deadline | ✅ |
| 8 | Timeline dot màu theo urgency | ✅ |
| 9 | Risk widget placeholder | ✅ |
| 10 | Header greeting + ngày | ✅ |
| 11 | Nút "Làm mới" | ✅ |
| 12 | Responsive layout | ✅ |

---

## 5. Điểm kỹ thuật đáng chú ý

### 5.1. Streak algorithm

```typescript
function calculateStreak(studyHours: Record<string, number>): number {
  const days = Object.keys(studyHours).filter((d) => studyHours[d] > 0).sort().reverse();
  if (days.length === 0) return 0;

  const today = dayjs().startOf('day');
  const mostRecent = dayjs(days[0]).startOf('day');
  if (today.diff(mostRecent, 'day') > 1) return 0;  // streak đứt

  let streak = 1;
  for (let i = 1; i < days.length; i++) {
    if (dayjs(days[i-1]).diff(dayjs(days[i]), 'day') === 1) streak++;
    else break;
  }
  return streak;
}
```

Chỉ tính streak nếu ngày gần nhất là hôm nay hoặc hôm qua → tránh user thấy streak cũ đã đứt.

### 5.2. Heatmap color palette

7 mức cường độ dùng Ant Design Blue scale:
- `0h` → `#f5f5f5` (xám nhạt)
- `<1h` → `#e6f4ff`
- `1-2h` → `#91caff`
- `2-3h` → `#4096ff`
- `3-4h` → `#1677ff`
- `4-6h` → `#0958d9`
- `>6h` → `#003eb3`

Text auto-contrast: đen cho nền sáng, trắng cho nền đậm (hours ≥ 2).

### 5.3. Responsive breakpoints

- Statistics: `xs=12 sm=12 md=6` → 2 cards/hàng mobile, 4 cards/hàng desktop
- Chart + Sleep: `xs=24 lg=16/8` → stack mobile, side-by-side desktop
- Heatmap + Risk: `xs=24 lg=16/8`
- Timeline: `xs=24` full-width

### 5.4. Risk Widget design

Thiết kế để trông "sẵn sàng" chứ không "bỏ trống":
- Circular progress với score=0 (không phải "N/A")
- Tag "Sắp ra mắt"
- Disclaimer đầy đủ (giống thiết kế thật)
- CTA có ích: "Ghi thêm nhật ký" → user có thể làm gì đó ngay

### 5.5. Onboarding cho user mới

Detect all data empty → hiển thị Alert hướng dẫn 3 bước:
1. Tạo môn học
2. Thêm bài tập
3. Ghi nhật ký

Tránh user mới bị "bơ vơ" với dashboard trống.

---

## 6. Trạng thái 14 FR

| # | Chức năng | Backend | Frontend | Status |
|---|-----------|:-------:|:--------:|:------:|
| 1 | Authentication | ✅ | ✅ | ✅ |
| 2 | Consent | ✅ | ✅ | ✅ |
| 3 | Log study | ✅ | ✅ | ✅ |
| 4 | Log sleep | ✅ | ✅ | ✅ |
| 5 | Log mood | ✅ | ✅ | ✅ |
| 6 | CRUD subjects | ✅ | ✅ | ✅ |
| 7 | CRUD assignments | ✅ | ✅ | ✅ |
| 8 | **Dashboard heatmap** | ✅ | ✅ | ✅ **Done** |
| 9 | **Deadline timeline** | ✅ | ✅ | ✅ **Done** |
| 10 | Risk widget | ⏳ | ⏳ | Tầng 2 |
| 11 | Schedule generation | ❌ | ❌ | Tầng 3 |
| 12 | Constraint explanation | ❌ | ❌ | Tầng 3 |
| 13 | Feedback | ❌ | ❌ | Chưa |
| 14 | Data export/delete | ❌ | ❌ | Chưa |

**9/14 FR hoàn thành** — vượt nửa đường!

---

## 7. Bài học kinh nghiệm

### 7.1. Về dependency management

- **Luôn cập nhật `package.json` khi thêm import mới.** Nếu quên → Vite error khi build.
- Trong Docker container, `docker compose exec frontend npm install <pkg>` để cài nhanh, sau đó sync về `package.json`.
- Verify import: `docker compose exec frontend ls node_modules/<pkg>`.

### 7.2. Về data visualization

- **Recharts** đủ mạnh cho bar chart cơ bản, không cần D3.
- **HTML table** linh hoạt hơn library chart cho heatmap dạng grid.
- **ReferenceLine** rất tiện để show target/goal.
- **Tooltip custom** cải thiện UX đáng kể.

### 7.3. Về UX dashboard

- **Statistics first** — user thấy số liệu ngay khi vào.
- **Progressive disclosure:** chart → heatmap → timeline (tổng quan → chi tiết).
- **Empty states everywhere** — mỗi widget tự xử lý khi không có data.
- **Onboarding Alert** cho user mới — giảm "cold start" problem.

### 7.4. Về placeholder design

- **Đừng để widget trống hoàn toàn** — thiết kế skeleton với disclaimer + CTA.
- Tag "Sắp ra mắt" thay vì ẩn widget → user biết sẽ có gì.
- Risk Widget có CTA có ích ngay cả khi chưa hoạt động.

---

## 8. Thống kê công việc

| Metric | Số lượng |
|--------|----------|
| Files frontend tạo mới | 7 (dashboard.ts + 6 components) |
| Files frontend cập nhật | 2 (DashboardPage, package.json) |
| Lines of code | ~1,000 LOC |
| Components | 6 |
| Bug phát hiện + fix | 1 (recharts missing) |
| Test cases (UI) | 12 (100% pass) |

---

## 9. Kết luận

**Dashboard Widgets feature đã hoàn thành** — Dashboard giờ là **trung tâm thông tin** thực sự.

User có thể:
1. Xem 4 statistics ngay khi vào (giờ học, giấc ngủ, deadline, streak)
2. Xem biểu đồ 7 ngày với mục tiêu 3h
3. Xem heatmap khối lượng theo môn × ngày
4. Xem timeline deadline với urgency color
5. Xem chất lượng giấc ngủ qua circular progress
6. Thấy placeholder Risk Score (sẵn sàng Tầng 2)

**Điểm nổi bật:** Dashboard **responsive**, có **empty state** cho mọi widget, và **onboarding flow** cho user mới.

**Tiếp theo:** Feature Data export/delete (FR #14) — quan trọng cho ethics.

---

**Người lập log:** Phạm Kim Long
**Ngày:** 06/10/2026