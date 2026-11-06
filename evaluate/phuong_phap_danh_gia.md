# PHƯƠNG PHÁP ĐÁNH GIÁ GIẢI PHÁP (EVALUATION METHODOLOGY)

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Mô-đun đánh giá:** LP Optimization Engine (Tầng 3)
**Mục tiêu:** Đo lường tính hiệu quả, khả năng chịu tải và chất lượng lịch trình do thuật toán MILP tạo ra, so với phương pháp lập lịch thông thường (Baseline).

---

## 1. Synthetic Dataset (Tập dữ liệu giả lập)

Do việc thu thập dữ liệu thực tế từ sinh viên với đủ mọi mức độ quá tải là rất khó khăn và mất thời gian, chúng tôi xây dựng một **tập dữ liệu tổng hợp (Synthetic Dataset)** gồm **300 kịch bản** (test cases). Tập dữ liệu này được thiết kế để bao phủ toàn bộ không gian trạng thái của bài toán tối ưu hóa, từ nhẹ nhàng đến cực đoan.

### 1.1. Các trường dữ liệu (Schema)

Mỗi kịch bản (scenario) trong dataset bao gồm các trường sau, phản ánh chính xác cấu trúc đầu vào của Tầng 3:

| Tên trường | Kiểu dữ liệu | Mô tả | Ràng buộc / Khoảng giá trị |
| :--- | :--- | :--- | :--- |
| `scenario_id` | String | Mã định danh kịch bản | Duy nhất (VD: `SC_001`) |
| `scenario_type` | String | Phân loại độ khó của kịch bản | `Light`, `Normal`, `Heavy`, `Extreme` |
| `subjects` | List[Object] | Danh sách môn học | 1 - 8 môn |
| `subject_id` | String | Mã môn học | `sub_1`, `sub_2`, ... |
| `difficulty` | Integer | Độ khó môn học | 1 - 5 |
| `priority` | Integer | Độ ưu tiên môn học | 1 - 5 |
| `assignments` | List[Object] | Danh sách bài tập | 1 - 15 bài tập |
| `assignment_id` | String | Mã bài tập | `assign_1`, ... |
| `subject_id` | String | Môn học tương ứng (FK) | Phải thuộc `subjects` |
| `required_hours` | Float | Số giờ chuẩn bị yêu cầu | 0.5 - 10.0 (giờ) |
| `deadline_day` | Integer | Số ngày còn lại đến deadline | 1 - 14 (ngày) |
| `time_slots` | List[Object] | Khung thời gian rảnh trong ngày | 3 slots/ngày (Sáng, Chiều, Tối) |
| `available_hours` | Float | Số giờ rảnh trong slot | 1.0 - 3.0 (giờ) |
| `tod_factor` | Float | Hệ số hiệu quả theo giờ | Sáng: 1.2, Chiều: 1.0, Tối: 0.8 |
| `max_daily_hours` | Float | Trần giờ học tối đa/ngày | 2.0 - 8.0 (giờ) |

### 1.2. Các kịch bản kiểm thử (Test Scenarios)

Dataset được chia làm 4 nhóm chính với tỷ lệ phân bổ như sau:

1.  **Light (Nhẹ nhàng) - 30%:**
    *   *Đặc điểm:* 1-3 môn, 1-3 bài tập. Deadline xa (7-14 ngày). Tổng giờ yêu cầu << Tổng giờ rảnh.
    *   *Mục đích:* Kiểm tra xem thuật toán có tạo ra lịch tối ưu (rải đều, không dồn dập) hay không.
2.  **Normal (Bình thường) - 40%:**
    *   *Đặc điểm:* 3-5 môn, 4-8 bài tập. Deadline vừa phải (3-7 ngày). Tổng giờ yêu cầu xấp xỉ 70-80% Tổng giờ rảnh.
    *   *Mục đích:* Kịch bản thực tế nhất của sinh viên. Đánh giá khả năng cân bằng giữa các môn và tôn trọng `W_max`.
3.  **Heavy (Quá tải) - 20%:**
    *   *Đặc điểm:* 5-7 môn, 8-12 bài tập. Deadline sát nhau (1-3 ngày). Tổng giờ yêu cầu ~ 100% Tổng giờ rảnh.
    *   *Mục đích:* Đánh giá khả năng xử lý xung đột (conflict resolution) và cơ chế soft constraints (cảnh báo shortfall).
4.  **Extreme (Cực đoan) - 10%:**
    *   *Đặc điểm:* 8 môn, 15 bài tập. Deadline dồn dập trong 1-2 ngày. Tổng giờ yêu cầu > Tổng giờ rảnh (Không thể hoàn thành 100%).
    *   *Mục đích:* Đánh giá cơ chế Fallback 2 bước (chống vô nghiệm) và khả năng đưa ra cảnh báo thiếu hụt thay vì báo lỗi.

---

## 2. Baseline (Thuật toán Đối chứng)

Để chứng minh tính ưu việt của LP Solver, chúng tôi so sánh nó với một thuật toán **Tham lam (Greedy Algorithm)**. Đây là cách tiếp cận phổ biến nhất mà sinh viên thường áp dụng thủ công hoặc các app lập lịch cơ bản sử dụng.

### 2.1. Mô tả Baseline (Greedy)

Thuật toán Greedy hoạt động theo các bước sau:
1.  Sắp xếp tất cả các bài tập theo thứ tự: **Deadline gần nhất** ưu tiên trước, sau đó đến **Độ ưu tiên (Priority)** cao nhất.
2.  Duyệt qua từng ngày, từng khung giờ (Sáng, Chiều, Tối).
3.  Với mỗi khung giờ, nhét bài tập đầu tiên trong danh sách vào cho đến khi đầy quỹ thời gian `available_hours`.
4.  Nếu hết thời gian mà bài tập chưa xong, chuyển sang bài tiếp theo.
5.  Không có cơ chế điều chỉnh giờ học theo `tod_factor` (hiệu quả theo giờ).

### 2.2. Sự khác biệt cốt lõi (Greedy vs. LP Solver)

| Đặc điểm | Baseline (Greedy) | Giải pháp Đề xuất (LP Solver) |
| :--- | :--- | :--- |
| **Tầm nhìn** | Cục bộ (Local). Quyết định nhét bài nào vào giờ nào ngay lập tức. | Toàn cục (Global). Giải toàn bộ bài toán một lúc để tìm điểm tối ưu. |
| **Hàm mục tiêu** | Không có. Chỉ cố gắng nhét đầy giờ. | Tối đa hóa `Objective Z = Σ E[i]·f(X_eff)`. |
| **Diminishing Returns** | Không có. Học 4 tiếng vẫn được tính là 4. | Có. Sử dụng hàm `√x` (xấp xỉ 4 đoạn). Học 4h chỉ tính hiệu quả bằng 2h. |
| **Ràng buộc mềm (Soft)** | Không có. Dễ bị kẹt hoặc tràn giờ. | Có. Sử dụng biến `slack` và hàm phạt (`λ_daily = 100`, `λ_deadline = 20`). |
| **Rủi ro vô nghiệm** | Cao (nếu bài tập quá nhiều). | Thấp (nhờ cơ chế Fallback và soft constraints). |
| **Tính giải thích** | Không có. | Có (Breakdown, Warnings). |

---

## 3. Metrics (Các chỉ số so sánh)

Chúng tôi sử dụng 5 chỉ số đo lường để đánh giá và so sánh hai phương pháp. Các chỉ số này được tính toán trên toàn bộ 300 kịch bản của Dataset.

### 3.1. Tỷ lệ tìm thấy lịch (Feasibility Rate) - *Càng cao càng tốt*
*   **Định nghĩa:** Phần trăm các kịch bản mà thuật toán tìm ra được ít nhất một lịch trình hợp lệ (không bị lỗi `Infeasible`).
*   **Cách tính:** `(Số kịch bản tạo lịch thành công / Tổng số kịch bản) * 100%`.
*   **Kỳ vọng:** LP Solver đạt 100% (nhờ Fallback), Greedy có thể thất bại ở kịch bản Extreme.

### 3.2. Tổng số giờ thiếu hụt (Total Deadline Shortfall) - *Càng thấp càng tốt*
*   **Định nghĩa:** Tổng số giờ mà lịch trình tạo ra không đáp ứng đủ yêu cầu (`required_hours`) trước deadline của tất cả các bài tập.
*   **Cách tính:** `Σ (required_hours - actual_hours_before_deadline)` cho tất cả bài tập.
*   **Kỳ vọng:** LP Solver có shortfall thấp hơn vì nó biết ưu tiên các môn gấp và phân bổ hợp lý. Greedy thường bị kẹt ở việc làm các bài dễ trước hoặc tràn giờ.

### 3.3. Tổng số giờ vượt trần (Total Overload Hours) - *Càng thấp càng tốt (Kỳ vọng = 0)*
*   **Định nghĩa:** Tổng số giờ học vượt quá giới hạn `max_daily_hours` (hoặc `W_max_effective` nếu có Risk).
*   **Cách tính:** `Σ (actual_hours_per_day - max_daily_hours)` với điều kiện > 0.
*   **Kỳ vọng:** LP Solver giữ mức Overload = 0 (nhờ hàm phạt `λ_daily = 100`). Greedy thường có overload cao vì nó nhét bài liên tục.

### 3.4. Điểm hiệu quả học tập (Objective Value / Learning Effectiveness) - *Càng cao càng tốt*
*   **Định nghĩa:** Tổng giá trị của hàm mục tiêu `Z` mà thuật toán đạt được. Phản ánh mức độ tối ưu hóa việc học (tập trung vào giờ hiệu quả, môn khó, môn gấp).
*   **Cách tính:** `Σ E[i] · f(X_eff[i])` (với LP Solver). Với Greedy, tính điểm dựa trên số giờ thực tế (không có diminishing returns).
*   **Kỳ vọng:** LP Solver có điểm số cao hơn hẳn (dự kiến +30-50%) do biết tận dụng `tod_factor` và hàm lợi nhuận giảm dần.

### 3.5. Thời gian chạy (Runtime) - *Càng thấp càng tốt*
*   **Định nghĩa:** Thời gian trung bình để thuật toán giải xong một kịch bản (tính bằng giây).
*   **Cách tính:** `Tổng thời gian chạy / 300`.
*   **Kỳ vọng:** Cả hai đều chạy rất nhanh (< 1 giây). Điều này chứng minh LP Solver khả thi để chạy trong thời gian thực (Real-time) trên web app.

---

## 4. Quy trình Thực hiện Đánh giá (Evaluation Process)

1.  **Bước 1:** Sinh 300 kịch bản bằng script Python (sử dụng `random` với seed cố định để tái lập kết quả).
2.  **Bước 2:** Chạy thuật toán Baseline (Greedy) cho từng kịch bản, ghi nhận 5 metrics.
3.  **Bước 3:** Gọi API `POST /api/schedule/generate` của LP Solver cho từng kịch bản, ghi nhận 5 metrics.
4.  **Bước 4:** Tính giá trị trung bình (Average) của từng metric trên toàn bộ 300 kịch bản.
5.  **Bước 5:** Lập bảng so sánh và vẽ biểu đồ (Bar chart) để trực quan hóa kết quả (dùng cho Chương 6).
6.  **Bước 6:** Thực hiện kiểm định thống kê (Paired T-test) để chứng minh sự khác biệt giữa 2 phương pháp là có ý nghĩa thống kê (p-value < 0.05).