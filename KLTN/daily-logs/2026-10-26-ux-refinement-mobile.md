# 📋 Nhật ký công việc — Nâng cấp UX Mobile & Liên kết Dữ liệu (Quick Interactions V2)

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Giai đoạn:** UX Refinement & Data Linking
**Thời gian:** ~09:00 — 16:30
**Người thực hiện:** Phạm Kim Long

---

## 1. Bối cảnh & Mục tiêu

Tiếp thu góp ý từ GVHD và thực tế sử dụng, hệ thống cần giải quyết 2 vấn đề lớn:
1. **Giảm friction (ma sát) khi nhập liệu trên mobile:** Sinh viên thường dùng điện thoại để log dữ liệu ngay sau khi học xong. Việc phải mở menu, chuyển trang, điền form dài (5-6 bước) là rào cản lớn.
2. **Liên kết dữ liệu thông minh:** Trước đây, phiên học (Study Session) và bài tập (Assignment) là 2 thực thể rời rạc. Cần liên kết chúng lại để thuật toán LP Solver (Tầng 3) biết chính xác user đã dành bao nhiêu thời gian cho từng bài tập cụ thể, từ đó tính toán `required_hours` còn thiếu chính xác hơn.

---

## 2. Công việc đã thực hiện (Backend)

### 2.1. Cập nhật Database Schema (Migrations)
- **Migration 002:** Thêm cột `usual_bedtime` (TIME) vào bảng `users`. Mặc định là `23:00:00`. Dùng để tự động tính giờ ngủ.
- **Migration 003:** 
  - Thêm cột `is_completed` (BOOLEAN) vào bảng `assignments`. Mặc định là `false`.
  - Thêm cột `assignment_id` (UUID, FK) vào bảng `study_sessions`. Cho phép `NULL` (nếu user chỉ học chung chung mà không gắn với bài tập cụ thể).

### 2.2. Cập nhật API & Logic
- **Auth API:** Thêm endpoint `PUT /api/auth/settings` để user cập nhật `usual_bedtime`. Cập nhật `/me` để trả về field này.
- **Logs API:** `POST /api/log/study` giờ chấp nhận thêm `assignment_id` (optional).
- **Assignments API:** `PUT /api/assignments/{id}` cho phép cập nhật `is_completed`. Logic lấy `list_upcoming` tự động loại bỏ các bài tập đã completed.

---

## 3. Công việc đã thực hiện (Frontend)

Thay đổi toàn bộ Dashboard thành một "Bảng điều khiển nhập liệu nhanh" (Quick Input Hub).

### 3.1. Các Widget Tương tác nhanh (Quick Interactions)
| Component | Thay đổi | Số tap (Cũ → Mới) |
|-----------|----------|:-----------------:|
| **QuickMoodBar** | Tách thành 2 hàng (Năng lượng & Căng thẳng). Mỗi hàng 5 emoji. Auto-submit khi chọn đủ 2. | 4 → 2 |
| **QuickSleepWidget** | Chỉ cần chọn 5 emoji chất lượng giấc ngủ. Tự động tính giờ đi ngủ (dựa trên `usual_bedtime`) và giờ thức (hiện tại). | 4 → 1 |
| **QuickStudyBar** | Chọn môn (chip) → Hiện danh sách bài tập của môn đó → Chọn thời lượng (30m/1h/1.5h/2h). Auto-fill giờ bắt đầu. | 5-6 → 2 |
| **QuickCreateButtons** | Thêm nút tạo nhanh Môn học / Bài tập (Modal rút gọn). Môn học có AutoComplete gợi ý. | 6-7 → 2 |

### 3.2. Cải tiến `DeadlineTimeline`
- **Nút "Đã học ▾":** Dropdown chọn nhanh 15m / 30m / 1h. Khi bấm, hệ thống tự động tạo một Study Session gắn liền với bài tập đó.
- **Nút "Đã xong" (Check icon):** Đánh dấu bài tập hoàn thành (`is_completed = true`). Bài tập lập tức biến mất khỏi Timeline để user tập trung vào việc còn lại.

### 3.3. Trang Cài đặt (SettingsPage)
- Thêm section **"Cài đặt giấc ngủ"**.
- Dùng `TimePicker` để user chọn giờ đi ngủ thông thường.

### 3.4. Đồng bộ trạng thái
- `LoggingPage` tự động refetch dữ liệu khi tab được focus lại (`visibilitychange`), đảm bảo dữ liệu log từ Dashboard hiện ra ngay lập tức.

---

## 4. Kết quả & Đánh giá

- **Giao diện Dashboard** giờ đây đóng vai trò là một "Trung tâm điều khiển" (Command Center) thực thụ. User có thể log toàn bộ dữ liệu ngày hôm nay (Study, Mood, Sleep) chỉ trong **5 taps** ngay khi vừa mở app.
- **Dữ liệu chặt chẽ hơn:** Việc gắn `assignment_id` vào `study_session` giúp giải quyết bài toán: "Tôi đã học 2 tiếng cho môn Lập trình, nhưng cụ thể là đã làm xong bài tập nào?".
- **Thuật toán LP Solver** giờ đây có thể tính toán chính xác số giờ còn thiếu của từng assignment (thay vì chỉ tính tổng giờ của môn học).

---

## 5. Các vấn đề kỹ thuật đã xử lý

1. **Migration an toàn:** Sử dụng `server_default` cho các cột mới thêm vào (`is_completed`, `usual_bedtime`) để không làm hỏng dữ liệu cũ của user.
2. **Nullability:** `assignment_id` trong `study_sessions` cho phép `NULL` và có `ondelete='SET NULL'`. Nếu user xóa bài tập, phiên học vẫn được giữ lại (không bị xóa theo), chỉ mất liên kết.
3. **Grid Layout:** Sử dụng `alignItems: 'start'` trong Ant Design Row để các widget không bị kéo dãn chiều cao bằng nhau (khắc phục lỗi giao diện khoảng trắng thừa).

---

## 6. Công việc tiếp theo

1. **Kiểm thử toàn diện:** Chạy lại toàn bộ 170 automated tests + test tay các luồng UX mới.
2. **Chuẩn bị cho User Testing:** In bảng hỏi SUS và chuẩn bị kịch bản test 5-15 người dùng.
3. **Viết luận văn:** Đưa phần "Quick Interactions" vào Chương 4 (Thiết kế) và Chương 6 (Đánh giá tính khả dụng).

---

**Người lập log:** Phạm Kim Long
**Ngày:** 26/10/2026
