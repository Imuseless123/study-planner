# Đánh giá lịch học do hệ thống tạo ra — Lợi ích và hạn chế

**Dự án:** Study Planner — Hệ thống Lập kế hoạch Học tập Cá nhân
**Phạm vi:** Lịch được tạo bởi Tầng 3 (LP Solver) và được điều phối bởi Tầng 1
**Ngày cập nhật:** 31/10/2026

Tài liệu này trả lời hai câu hỏi:

1. Lịch do dự án tạo ra có lợi gì so với cách lập lịch thủ công hoặc các cách lập lịch đơn giản?
2. Lịch đó còn hạn chế gì, khi nào không nên dùng, và có thể cải thiện theo hướng nào?

Luồng dữ liệu chi tiết từ frontend → database → Tầng 2 → Tầng 3 được mô tả trong [`data-flow.md`](./data-flow.md). Tài liệu này chỉ tập trung vào **chất lượng của lịch đầu ra**.

---

## 1. Tóm tắt cách lịch được tạo

```text
Bài tập trong DB
    │  mỗi bài tập = 1 "subject" của LP
    │  id = assignment_id
    │  required_hours, deadline_day, difficulty, priority
    ▼
Risk Score từ Tầng 2
    │  risk_score, level
    ▼
Tầng 1 tính trần giờ/ngày
    │  W_max_effective = 6.0 × (1 − 0.5 × risk_score / 100)
    ▼
Tầng 3 giải MILP
    │  biến x[i,d,t], y[i,d,t], delta[i,d,k], s[i], u[d]
    │  hàm mục tiêu có diminishing returns + phạt mềm
    ▼
Lịch + explanation + warnings
    │
    ▼
Lưu vào bảng schedules, hiển thị ở SchedulePage
```

Điểm cốt lõi: lịch không được tạo bằng cách chia đều số giờ hay xếp bài tập gần deadline trước. Nó được tạo bằng một bài toán tối ưu có ràng buộc, trong đó mục tiêu là tối đa hóa hiệu quả học tập có xét đến độ gấp, độ khó, độ ưu tiên, thời điểm học và mức rủi ro hiện tại.

---

## 2. Lợi ích của lịch do hệ thống tạo ra

### 2.1. Cá nhân hóa theo từng bài tập, không chỉ theo môn học

Mỗi bài tập được đưa vào LP như một đối tượng riêng với:

- `required_hours`: số giờ cần học.
- `deadline_day`: số ngày còn lại đến deadline.
- `difficulty`: độ khó của môn chứa bài tập.
- `priority`: độ ưu tiên của bài tập.
- `urgency`: tự tính bằng `1 / (1 + deadline_day)`.

Hệ số hiệu quả:

```text
E[i] = urgency × difficulty × priority
```

Nhờ vậy hai bài tập cùng một môn vẫn có thể được xếp khác nhau nếu deadline hoặc priority khác nhau. Cách lập lịch thủ công thường chỉ nhìn theo môn hoặc theo deadline, dễ bỏ qua bài tập khó nhưng ít gấp hoặc bài tập quan trọng nhưng còn xa.

**File liên quan:** `backend/app/services/schedule_service.py:40`, `lp-solver/app/model.py:76`

### 2.2. Có điều chỉnh theo mức rủi ro của người dùng

Trần giờ học mỗi ngày không cố định mà giảm khi risk score tăng:

```text
W_max_effective = 6.0 × (1 − 0.5 × risk_score / 100)
```

Ví dụ:

| Risk score | Trần giờ/ngày |
|---|---|
| 0 | 6.0h |
| 40 | 4.8h |
| 80 | 3.6h |
| 100 | 3.0h |

Đây là điểm khác biệt so với lịch tĩnh: khi người dùng đang thiếu ngủ, khối lượng công việc cao hoặc deadline quá gần, hệ thống không ép họ học tối đa 6 giờ/ngày mà tự giảm trần để ưu tiên tính bền vững.

**File liên quan:** `backend/app/services/schedule_service.py:143-144`

### 2.3. Dùng ràng buộc mềm, tránh trả về ngõ cụt

Bài toán không dùng deadline và trần giờ/ngày như ràng buộc cứng. Thay vào đó:

- `s[i]`: số giờ thiếu trước deadline.
- `u[d]`: số giờ vượt trần trong ngày.

Hai biến này bị phạt trong hàm mục tiêu:

```text
Maximize Z =
    Σ E[i] × f(X_eff[i,d])
  − 20 × Σ s[i]
  − 100 × Σ u[d]
```

Lợi ích:

- Nếu không thể hoàn thành mọi deadline, solver vẫn trả về lịch tốt nhất có thể kèm cảnh báo `deadline_shortfall`.
- Nếu một ngày bị quá tải, hệ thống trả về cảnh báo `daily_overload` thay vì báo lỗi.
- Người dùng biết chính xác mình thiếu bao nhiêu giờ, ở bài tập nào, ngày nào bị vượt bao nhiêu.

**File liên quan:** `lp-solver/app/model.py`, `lp-solver/app/solver.py:66`

### 2.4. Mô phỏng lợi nhuận giảm dần của việc học

Học 2 giờ đầu thường hiệu quả hơn 2 giờ sau. Hệ thống dùng xấp xỉ tuyến tính từng đoạn của `sqrt(x)` trên `[0, 4]`:

| Đoạn | Khoảng giờ | Độ dốc |
|---|---|---|
| 1 | 0.0 — 0.5 | 1.414 |
| 2 | 0.5 — 1.0 | 0.586 |
| 3 | 1.0 — 2.0 | 0.414 |
| 4 | 2.0 — 4.0 | 0.293 |

Vì độ dốc giảm dần, solver có xu hướng phân bổ giờ học cho nhiều bài tập trước khi dồn quá nhiều vào một bài. Điều này hợp lý hơn việc dùng hàm tuyến tính, nơi 10 giờ học một môn luôn được coi là hiệu quả gấp 10 lần 1 giờ.

**File liên quan:** `lp-solver/app/model.py:33-42`

### 2.5. Ưu tiên thời điểm học hiệu quả và tránh phiên học quá ngắn

Mỗi ngày có 3 khung:

| Khung | Hệ số `tod_factor` |
|---|---|
| Sáng | 1.2 |
| Chiều | 1.0 |
| Tối | 0.8 |

Giờ học hiệu dụng:

```text
X_eff = 1.2 × giờ_sáng + 1.0 × giờ_chiều + 0.8 × giờ_tối
```

Ngoài ra, ràng buộc phiên tối thiểu 0.5 giờ (`min_session_hours`) tránh tạo ra các phiên 5-10 phút khó thực hiện trong thực tế.

**File liên quan:** `backend/app/services/schedule_service.py:19`, `lp-solver/app/model.py`

### 2.6. Có giải thích, không phải hộp đen

Kết quả trả về không chỉ có lịch mà còn:

- `explanation.per_subject`: số giờ yêu cầu, số giờ đã xếp, số giờ dùng buffer, số giờ thiếu deadline.
- `explanation.per_day`: tổng giờ mỗi ngày, số giờ vượt trần.
- `warnings[]`: cảnh báo thiếu deadline, quá tải ngày, hoặc fallback do risk.
- `objective_value`: giá trị hàm mục tiêu.

Người dùng có thể thấy vì sao lịch trông như vậy. Đây là lợi thế so với các mô hình học máy chỉ trả về một lịch mà không giải thích.

**File liên quan:** `lp-solver/app/solver.py:28`, `frontend/src/pages/SchedulePage.tsx`

### 2.7. Có lưu lịch và thu feedback

- Lịch được lưu vào bảng `schedules` với `schedule_data` dạng JSONB, `feasible`, `risk_score_at_generation`, `warnings`.
- Người dùng có thể mở lại lịch gần nhất bằng `GET /api/schedule/latest`.
- Người dùng có thể đánh giá lịch 1-5 sao và để lại nhận xét; feedback được lưu vào bảng `feedback`.

Điều này tạo nền tảng để sau này đánh giá chất lượng lịch và cải thiện mô hình.

**File liên quan:** `backend/app/services/schedule_service.py:177`, `backend/app/api/feedback.py`

### 2.8. Tách biệt, dễ kiểm thử và dễ thay thế

Tầng 3 là một service độc lập, nhận JSON và trả JSON. Lợi ích:

- Có thể thay solver (PuLP → OR-Tools) mà không sửa Tầng 1.
- Có thể unit test công thức và mô hình mà không cần database.
- Tầng 1 vẫn kiểm soát dữ liệu và quyền riêng tư; Tầng 3 không cần biết user là ai.

**File liên quan:** `lp-solver/`, `backend/app/services/schedule_service.py:23`

### 2.9. Bảng tóm tắt lợi ích

| Lợi ích | Cơ chế | Giá trị thực tế |
|---|---|---|
| Cá nhân hóa | Mỗi bài tập có deadline, độ khó, priority, urgency | Lịch sát nhu cầu từng bài tập |
| An toàn theo rủi ro | Giảm trần giờ/ngày khi risk cao | Giảm nguy cơ quá tải |
| Không bế tắc | Ràng buộc mềm + cảnh báo | Luôn có lịch gợi ý để điều chỉnh |
| Hiệu quả giảm dần | Xấp xỉ `sqrt(x)` | Phân bổ giờ hợp lý hơn |
| Ưu tiên thời điểm | `tod_factor` sáng/chiều/tối | Khuyến khích học giờ hiệu quả |
| Phiên tối thiểu | `min_session_hours = 0.5` | Lịch khả thi hơn khi thực hiện |
| Minh bạch | Explanation + warnings | Người dùng hiểu và tin tưởng hơn |
| Lưu vết | Bảng `schedules`, `feedback` | Có dữ liệu để đánh giá cải tiến |

---

## 3. Hạn chế của lịch do hệ thống tạo ra

### 3.1. Hạn chế về dữ liệu đầu vào

#### 3.1.1. Chưa có lịch bận thực tế của người dùng

Hệ thống giả định mỗi ngày luôn có:

```text
3 khung × 2 giờ = 6 giờ rảnh
```

Nó không biết người dùng có lớp học, đi làm, lịch thi, hoạt động câu lạc bộ hay ngày nghỉ. Vì vậy lịch có thể xếp phiên học vào thời gian người dùng không thực sự rảnh.

**Ảnh hưởng:** lịch đẹp trên lý thuyết nhưng khó thực hiện.

#### 3.1.2. Deadline chỉ được xét theo ngày, không theo giờ

Tầng 1 tính:

```text
deadline_day = max(0, (deadline − now).days)
```

Đây là số ngày làm tròn xuống. Nếu deadline là 23:59 ngày 5 và deadline khác là 08:00 ngày 5, cả hai đều có thể thành `deadline_day = 5`. Solver được phép xếp học trong cả ngày 5, kể cả sau 08:00.

**Ảnh hưởng:** lịch có thể xếp phiên học sau thời điểm deadline thực tế trong cùng ngày.

#### 3.1.3. Chưa dùng dữ liệu tâm trạng, năng lượng, stress

Tầng 2 chỉ dùng:

- Số giờ ngủ trung bình 7 ngày.
- Độ lệch chuẩn giờ học 7 ngày.
- Bài tập sắp tới.
- Số ngày đến deadline gần nhất.

Dữ liệu `mood_logs` (energy, stress) được lưu nhưng chưa tham gia vào risk score hay lịch. Trong khi đó, stress và năng lượng là yếu tố rất liên quan đến khả năng thực hiện lịch.

**Ảnh hưởng:** lịch có thể quá tải với người đang stress cao dù risk score chưa phản ánh hết.

#### 3.1.4. Phụ thuộc vào dữ liệu tự báo cáo

`required_hours`, `duration`, `sleep_time`, `wake_time`, `quality` đều do người dùng nhập. Nếu người dùng ước lượng sai số giờ cần học hoặc nhập thiếu log, lịch sẽ lệch theo.

**Ảnh hưởng:** chất lượng lịch phụ thuộc vào chất lượng dữ liệu nhập.

### 3.2. Hạn chế về mô hình tối ưu

#### 3.2.1. Trọng số và tham số mang tính heuristic

Các giá trị sau được chọn thủ công, chưa được hiệu chỉnh bằng dữ liệu thực tế:

- Trọng số risk: `0.35 / 0.30 / 0.20 / 0.15`.
- `ALPHA = 0.5` khi giảm trần giờ theo risk.
- `λ_deadline = 20`, `λ_daily = 100`.
- `buffer_ratio = 0.25`.
- `tod_factor = 1.2 / 1.0 / 0.8`.

Chúng có cơ sở thiết kế và lý do kỹ thuật, nhưng chưa được kiểm chứng rằng là tối ưu cho mọi sinh viên.

**Ảnh hưởng:** lịch có thể tốt với nhóm này nhưng chưa chắc tốt với nhóm khác.

#### 3.2.2. Hàm hiệu quả chưa phản ánh kết quả học thật

`E[i] = urgency × difficulty × priority` giả định:

- Bài khó hơn thì học hiệu quả hơn.
- Bài ưu tiên cao hơn thì nên học nhiều hơn.
- Deadline gần hơn thì quan trọng hơn.

Đây là giả định hợp lý nhưng chưa dùng điểm số, mức độ hiểu bài, hay tiến độ thực tế của người dùng.

**Ảnh hưởng:** lịch tối ưu theo mô hình, không nhất thiết tối ưu theo kết quả học tập thực tế.

#### 3.2.3. Buffer 25% không bị phạt

Ràng buộc C4 cho phép học tối đa:

```text
required_hours × 1.25
```

Hàm mục tiêu không phạt việc dùng buffer. Vì vậy solver có thể xếp nhiều hơn số giờ cần thiết cho một bài nếu việc đó vẫn làm tăng hàm mục tiêu.

**Ảnh hưởng:** lịch có thể dư giờ cho một bài trong khi bài khác bị thiếu. UI có hiển thị `buffer_used` nhưng không cảnh báo riêng.

#### 3.2.4. Fallback có thể phá vỡ mục tiêu an toàn

Nếu lịch với `W_max_effective` không khả thi, Tầng 1 gọi lại Tầng 3 với `W_max = 6.0`. Điều này giúp người dùng có lịch, nhưng đồng nghĩa với việc **bỏ qua điều chỉnh theo risk**. Hệ thống chỉ thêm cảnh báo `risk_override`, không ngăn người dùng dùng lịch đó.

**Ảnh hưởng:** trong trường hợp xấu, người dùng rủi ro cao vẫn nhận lịch đầy 6 giờ/ngày.

#### 3.2.5. Deadline vẫn có thể bị thiếu

Vì deadline là ràng buộc mềm, solver có thể trả về lịch thiếu giờ trước deadline nếu tổng nhu cầu vượt khả năng. Đây là thiết kế có chủ đích, nhưng người dùng cần đọc cảnh báo thay vì tin rằng lịch luôn hoàn thành mọi bài.

### 3.3. Hạn chế về ràng buộc thời gian

#### 3.3.1. Khung giờ cố định, không có giờ bắt đầu chính xác

Lịch chỉ có:

- `day`: ngày thứ mấy.
- `slot`: 0, 1, 2 tương ứng sáng, chiều, tối.
- `hours`: số giờ.

Không có giờ bắt đầu cụ thể như 07:30 hay 19:15. Người dùng phải tự quyết định đặt phiên học vào thời điểm nào trong khung.

**Ảnh hưởng:** lịch mang tính gợi ý, chưa dùng trực tiếp như lịch Google Calendar.

#### 3.3.2. Không có ràng buộc nghỉ ngơi, giới hạn học liên tục

Mô hình không có:

- Số giờ học tối đa liên tục.
- Thời gian nghỉ bắt buộc giữa các phiên.
- Giới hạn số phiên mỗi ngày.
- Khung giờ ngủ cố định.

Nó chỉ giới hạn tổng giờ/ngày và giờ/khung.

**Ảnh hưởng:** lịch có thể dồn nhiều phiên vào một ngày dù tổng giờ chưa vượt trần.

#### 3.3.3. Không có tùy chọn ưu tiên của người dùng

Người dùng không thể nói:

- "Tôi chỉ học buổi sáng."
- "Thứ 4 tôi bận cả ngày."
- "Đừng xếp bài A vào cuối tuần."
- "Tôi muốn học bài B trước."

Hệ thống tự quyết định dựa trên mô hình.

**Ảnh hưởng:** lịch có thể tối ưu theo thuật toán nhưng không khớp sở thích cá nhân.

#### 3.3.4. Horizon bị giới hạn 30 ngày

Lịch tối thiểu 7 ngày, tối đa 30 ngày. Bài tập có deadline xa hơn 30 ngày vẫn được đưa vào LP nhưng lịch chỉ kéo dài 30 ngày.

**Ảnh hưởng:** các bài tập dài hạn có thể bị xếp dồn trong 30 ngày đầu hoặc không được lên kế hoạch chi tiết cho giai đoạn sau.

#### 3.3.5. Múi giờ

Tính toán deadline dùng UTC, trong khi hiển thị lịch dùng ngày local của trình duyệt (`dayjs().add(d, 'day')`). Với người dùng ở múi giờ lệch nhiều so với UTC, ngày trên lịch có thể lệch so với kỳ vọng.

### 3.4. Hạn chế về vòng đời của lịch

#### 3.4.1. Không theo dõi tiến độ thực hiện

Hệ thống không so sánh:

- Kế hoạch đã tạo.
- Số giờ thực tế đã học.
- Bài tập đã hoàn thành.

Mỗi lần bấm "Tạo lại", một lịch mới được tạo từ dữ liệu hiện tại. Không có cơ chế đánh dấu phiên đã học xong hay tự động dời phiên bị bỏ lỡ.

**Ảnh hưởng:** lịch là ảnh chụp tại một thời điểm, không phải kế hoạch sống được cập nhật liên tục.

#### 3.4.2. Feedback chưa được dùng để cải thiện lịch

Rating và comment được lưu vào bảng `feedback`, nhưng chưa có vòng lặp nào dùng dữ liệu này để điều chỉnh trọng số, tham số hay mô hình. Đây là dữ liệu thô cho tương lai, chưa phải learning loop.

#### 3.4.3. Bài tập đã hoàn thành có thể vẫn vào lịch

`_aggregate_subjects` lọc `deadline > now` nhưng không lọc `is_completed`. Trong khi Tầng 2 lại lọc `is_completed = false`. Vì vậy bài tập đã hoàn thành nhưng chưa quá deadline vẫn có thể xuất hiện trong lịch mới.

**Ảnh hưởng:** lịch có thể chứa bài không còn cần làm, làm giảm độ chính xác của risk và lịch.

### 3.5. Hạn chế kỹ thuật và giao diện

#### 3.5.1. Giới hạn số bài tập đầu vào

Schema Tầng 3 giới hạn tối đa 20 `subjects` trong một request (`lp-solver/app/schemas.py`). Nếu người dùng có nhiều hơn 20 bài tập chưa quá hạn, request có thể bị từ chối hoặc phải xử lý theo cách khác.

#### 3.5.2. Hiển thị tên môn có thể sai

`SchedulePage.getSubjectName()` tra cứu `subjects` theo `subject_id`, nhưng dữ liệu lịch dùng `assignment_id` trong trường `subject_id`. Vì vậy UI thường hiển thị fallback `#<id rút gọn>` thay vì tên môn.

**Ảnh hưởng:** người dùng khó nhận ra phiên học thuộc bài tập/môn nào.

#### 3.5.3. Lịch chưa xuất được ra calendar

Chưa có xuất `.ics`, đồng bộ Google Calendar, hay nhắc nhở. Người dùng phải tự chép lịch sang công cụ khác.

#### 3.5.4. Chưa có giao diện điều chỉnh ràng buộc

Người dùng không thể kéo thả phiên học, khóa phiên, hay thay đổi trần giờ/ngày ngay trên UI. Muốn thay đổi phải sửa dữ liệu đầu vào (bài tập, deadline, priority) rồi tạo lại.

### 3.6. Bảng tóm tắt hạn chế

| Nhóm | Hạn chế chính | Ảnh hưởng |
|---|---|---|
| Dữ liệu đầu vào | Không có lịch bận thực tế | Lịch khó thực hiện |
| Dữ liệu đầu vào | Deadline chỉ theo ngày | Có thể xếp sau giờ deadline |
| Dữ liệu đầu vào | Chưa dùng mood/stress/energy | Chưa phản ánh trạng thái tinh thần |
| Mô hình | Trọng số heuristic | Chưa tối ưu cho mọi người |
| Mô hình | Buffer không bị phạt | Có thể dư giờ một bài |
| Mô hình | Fallback bỏ qua risk | Có thể vượt trần an toàn |
| Thời gian | Khung giờ cố định | Không có giờ bắt đầu chính xác |
| Thời gian | Không có nghỉ/giới hạn liên tục | Lịch có thể dồn phiên |
| Thời gian | Horizon tối đa 30 ngày | Kế hoạch dài hạn bị cắt |
| Vòng đời | Không theo dõi tiến độ | Không tự điều chỉnh khi trễ |
| Vòng đời | Feedback chưa được dùng | Chưa có vòng học cải tiến |
| Kỹ thuật | Bài đã xong vẫn có thể vào lịch | Lịch chứa việc không cần làm |
| Kỹ thuật | Map tên môn sai | UI khó đọc |
| Kỹ thuật | Chưa export calendar | Chưa dùng trực tiếp hằng ngày |

---

## 4. Khi nào lịch phát huy lợi ích tốt nhất?

Lịch do hệ thống tạo ra phù hợp nhất khi:

- Người dùng có nhiều bài tập với deadline trong vòng 1-30 ngày.
- Người dùng nhập tương đối đầy đủ giờ học, giấc ngủ và bài tập.
- Lịch sinh hoạt tương đối ổn định, ít thay đổi đột xuất.
- Người dùng cần một gợi ý phân bổ thời gian, không cần lịch chính xác đến từng phút.
- Ưu tiên là cân bằng giữa hoàn thành deadline và tránh quá tải.

Lịch ít phù hợp khi:

- Người dùng có thời khóa biểu cố định, nhiều lớp học và hoạt động bắt buộc.
- Deadline cần chính xác đến giờ.
- Bài tập có phụ thuộc lẫn nhau hoặc cần chia giai đoạn phức tạp.
- Người dùng muốn tự kiểm soát hoàn toàn thời gian học.
- Dữ liệu nhập vào quá ít hoặc không chính xác.

---

## 5. Đề xuất cải thiện

### Ưu tiên cao

1. **Thêm lịch bận và khung giờ ưa thích của người dùng.**
   - Cho phép chọn ngày bận, giờ bận, khung giờ muốn học.
   - Thay `time_slots` cố định bằng dữ liệu thực tế.

2. **Đồng bộ bộ lọc bài tập giữa Tầng 2 và Tầng 3.**
   - Lọc `is_completed = false` trong `_aggregate_subjects`.
   - Đảm bảo risk và lịch dùng cùng tập bài tập.

3. **Xử lý deadline theo giờ, không chỉ theo ngày.**
   - Thêm ràng buộc không học sau thời điểm deadline thực tế.
   - Hoặc đổi `deadline_day` thành `deadline_datetime` trong LP.

4. **Sửa map tên môn/bài tập trên UI.**
   - Trả kèm `assignment_title` và `subject_name` trong response lịch.
   - Hoặc join dữ liệu ở frontend trước khi hiển thị.

### Ưu tiên trung bình

5. **Thêm ràng buộc nghỉ ngơi và giới hạn phiên liên tiếp.**
   - Tối đa số giờ liên tục.
   - Nghỉ tối thiểu giữa các phiên.
   - Giới hạn số phiên/ngày.

6. **Đưa mood/stress/energy vào risk hoặc lịch.**
   - Có thể dùng như hệ số điều chỉnh trần giờ/ngày.
   - Hoặc dùng để ưu tiên ngày học nhẹ hơn.

7. **Phạt việc dùng buffer quá mức.**
   - Thêm penalty nhỏ cho `buffer_used`.
   - Hoặc giảm `buffer_ratio` khi tổng nhu cầu đã cao.

8. **Cho người dùng điều chỉnh ràng buộc trên UI.**
   - Chọn trần giờ/ngày.
   - Khóa phiên học.
   - Ưu tiên bài tập.
   - Kéo thả phiên học.

### Ưu tiên dài hạn

9. **Theo dõi kế hoạch và thực tế.**
   - Đánh dấu phiên đã học.
   - So sánh planned vs actual.
   - Tự động tạo lại lịch khi người dùng trễ.

10. **Dùng feedback để hiệu chỉnh mô hình.**
    - Học trọng số từ rating.
    - Điều chỉnh `E[i]`, `λ`, `buffer_ratio` theo phản hồi.

11. **Xuất lịch ra `.ics` và nhắc nhở.**
    - Tích hợp Google Calendar.
    - Thông báo trước phiên học.

12. **Đánh giá bằng người dùng thật.**
    - Đo tỷ lệ hoàn thành phiên.
    - Đo số giờ thiếu deadline.
    - Đo số ngày quá tải.
    - Đo mức hài lòng (rating/SUS).

---

## 6. Cách đo lường lợi ích một cách khách quan

Để chứng minh lịch có lợi, nên so sánh với một baseline đơn giản, ví dụ:

- **Baseline 1:** xếp bài tập theo deadline gần nhất trước (Earliest Deadline First).
- **Baseline 2:** chia đều số giờ cần học cho các ngày còn lại.
- **Baseline 3:** lịch thủ công của người dùng.

Các chỉ số nên đo:

| Chỉ số | Ý nghĩa | Cách đo |
|---|---|---|
| Deadline shortfall | Tổng giờ thiếu trước deadline | Từ `explanation.per_subject` |
| Daily overload | Tổng giờ vượt trần | Từ `explanation.per_day` |
| Số ngày quá tải | Số ngày có `overload > 0` | Đếm từ kết quả |
| Số bài thiếu giờ | Số bài có `deadline_shortfall > 0` | Đếm từ kết quả |
| Mức sử dụng buffer | Tổng `buffer_used` | Từ kết quả |
| Thời gian giải | Thời gian solver chạy | Đo runtime |
| Mức hài lòng | Rating 1-5 | Bảng `feedback` |
| Tỷ lệ thực hiện | Số phiên thực tế / số phiên kế hoạch | Cần thêm tính năng theo dõi |

Lưu ý: nếu chỉ so sánh trên dữ liệu mô phỏng, kết quả chỉ chứng minh mô hình hoạt động đúng, chưa chứng minh người dùng thực sự học tốt hơn. Cần thêm nghiên cứu người dùng để kết luận về hiệu quả thực tế.

---

## 7. Kết luận

Lịch do dự án tạo ra có lợi thế rõ ràng ở ba điểm:

1. **Cá nhân hóa theo bài tập và theo rủi ro** thay vì chia đều hoặc chỉ nhìn deadline.
2. **Có thể giải thích và có cảnh báo** thay vì trả về một lịch hộp đen.
3. **Không bế tắc** nhờ ràng buộc mềm và fallback, phù hợp với bối cảnh sinh viên có khối lượng công việc thay đổi.

Tuy nhiên, lịch vẫn là **gợi ý**, chưa phải lịch thực thi chính xác:

- Chưa biết lịch bận thực tế.
- Chưa xử lý deadline theo giờ.
- Chưa có vòng phản hồi học tập từ dữ liệu thực tế.
- Các tham số mô hình còn mang tính heuristic.

Vì vậy, cách sử dụng phù hợp nhất là xem lịch như một **bản nháp tối ưu có giải thích**, sau đó người dùng điều chỉnh theo thực tế. Các cải tiến ở mục 5 sẽ giúp lịch tiến gần hơn đến một công cụ lập kế hoạch cá nhân dùng được hằng ngày.

---

## 8. Tài liệu liên quan

- [`data-flow.md`](./data-flow.md) — Luồng dữ liệu chi tiết từ Tầng 1 đến Tầng 3.
- [`tier-2-overview.md`](./tier-2-overview.md) — Công thức và API của Risk Indicator.
- [`tier-3-overview.md`](./tier-3-overview.md) — Mô hình MILP và API của LP Solver.
- [`system-architecture.md`](./system-architecture.md) — Kiến trúc tổng thể hệ thống.
