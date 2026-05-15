# Hệ thống FAQ & Chatbot ABC Trading

## 1. Mục tiêu chung

Hệ thống này thiết kế để:
- Trả lời câu hỏi sản phẩm dựa trên dữ liệu thực tế từ database.
- Trả lời câu hỏi hỗ trợ/chăm sóc khách hàng (ship, bảo hành, đổi trả, hotline, thanh toán, hóa đơn) từ bảng `faqs`.
- Tránh hallucination: chỉ dùng dữ liệu có thật, không tự sáng tạo sản phẩm.
- Lưu lịch sử hội thoại để dùng lại bối cảnh và "học" từ session.
- Sinh một bộ dữ liệu FAQ lớn (khoảng 400.000 mục) với nhiều biến thể và 20% câu hỏi mở mang phong cách tư vấn LLM.

## 2. Thành phần chính của dự án

### 2.1 `chatbot.py`

Đây là entrypoint CLI của chatbot.
- Khởi tạo session mới với `Memory(session_id)`.
- Nhận input từ người dùng.
- Ghi log câu hỏi user vào memory.
- Gọi `logic.xu_ly(user_input, mem)` để xử lý.
- Ghi lại phản hồi bot và in ra màn hình.
- Kết thúc khi user nhập "thoát", "bye", "goodbye".

### 2.2 `logic.py`

Định nghĩa luồng xử lý chính và các quy tắc nghiệp vụ.
- Sử dụng `LLMEngine` để lấy sản phẩm và FAQ.
- Quyền ưu tiên:
  1. Tìm FAQ nếu câu hỏi chứa từ khóa hỗ trợ/ship/bảo hành.
  2. Nếu câu hỏi là dạng đếm số lượng sản phẩm, trả ngay từ DB.
  3. Nếu là câu hỏi sản phẩm, tìm và format sản phẩm thực từ DB rồi gọi LLM.
- Dùng `Memory` để lưu tên người dùng và dùng lịch sử hội thoại làm context.
- Đảm bảo chỉ trả lời theo dữ liệu có thật.

### 2.3 `llm_engine.py`

Quản lý kết nối database và tương tác với Groq LLM.
- Kết nối MySQL với cấu hình `DB_CONFIG`.
- Các chức năng chính:
  - `search_product(query, limit)`
  - `count_products()`
  - `search_faq(query, limit)`
  - `_lay_danh_sach_san_pham(limit)`
  - `find_product_by_name(name)`
  - `xay_dung_system_prompt(context)`
  - `chat(user_message, context, product_context, history)`
- `chat()` xây dựng system prompt theo nguyên tắc "database first" và thêm `product_context` làm nguồn dữ liệu bắt buộc.

### 2.4 `memory.py`

Quản lý lịch sử hội thoại và context session.
- Tạo bảng `conversations` nếu chưa tồn tại.
- Lưu mỗi lượt `role` + `content` vào MySQL.
- Duy trì `history` nội bộ và `context` session.
- Lưu tên user khi phát hiện.
- Trả về `lay_lich_su(limit=10)` để cung cấp cho LLM.

### 2.5 `generate_faqs_dataset.py`

Sinh bộ dữ liệu FAQ lớn.
- Mục tiêu mặc định: 400.000 mục FAQ.
- Tạo 20% câu hỏi mở (open-ended) để tạo phong cách tư vấn linh hoạt.
- Tạo 80% câu hỏi theo category cụ thể với nhiều biến thể và tham số.
- Xuất ra file SQL dạng `INSERT INTO faqs (...) VALUES ...`.

## 3. Cơ chế dữ liệu và database

### 3.1 Các bảng chính

- `products`: chứa dữ liệu sản phẩm thực tế, gồm `id`, `name`, `category`, `price`, `stock`, `description`.
- `faqs`: chứa dữ liệu câu hỏi hỗ trợ, mỗi mục có `id`, `keywords`, `question`, `answer`.
- `conversations`: lưu session chat, gồm `session_id`, `role`, `content`, `buoc`, `nhanh`, `created_at`.

### 3.2 Các nguồn dữ liệu

- Với câu hỏi sản phẩm: dữ liệu lấy từ `products`.
- Với câu hỏi hỗ trợ/ship/bảo hành: ưu tiên tìm mục phù hợp trong `faqs`.
- Với câu hỏi đếm tổng số sản phẩm: dùng `count_products()` để trả số lượng.
- Lịch sử chat được lấy từ `Memory.lay_lich_su()` để làm context cho LLM.

## 4. Luồng xử lý chính trong `logic.xu_ly()`

1. Tạo `engine = LLMEngine()`.
2. Phát hiện tên người dùng bằng `_trich_ten()` và cập nhật `mem.context['ten_user']`.
3. `products = engine.search_product(user_message, limit=15)`.
4. Nếu không tìm được product nhưng user có key sản phẩm, lấy danh sách chung với `_lay_danh_sach_san_pham(limit=15)`.
5. Nếu câu hỏi là FAQ support/ship/bảo hành (`_is_faq_query()`):
   - Tìm FAQ bằng `engine.search_faq(user_message, limit=3)`.
   - Nếu tìm ra, trả luôn nội dung FAQ.
6. Nếu câu hỏi là đếm số (`_is_count_question()`):
   - Trả số lượng sản phẩm phù hợp và tổng số sản phẩm.
7. Nếu không có product và user hỏi sản phẩm, trả lời "Xin lỗi, cửa hàng hiện không có sản phẩm phù hợp".
8. Nếu có sản phẩm, format `product_context` theo cấu trúc:
   - Danh sách sản phẩm
   - Giá, trạng thái tồn kho, mô tả
   - Quy tắc quan trọng: chỉ dùng sản phẩm trong danh sách
9. Lấy lịch sử chat gần nhất `history = mem.lay_lich_su(limit=10)`.
10. Gọi `engine.chat(user_message, context, product_context, history)`.
11. Kiểm tra từ khóa tạm biệt để gửi câu kết thúc thân thiện.

## 5. Quy tắc phân luồng FAQ vs sản phẩm

### 5.1 Khi nào dùng FAQ?

Các câu hỏi chứa keyword về:
- ship / giao hàng / miễn phí / phí ship / phí giao hàng
- hỗ trợ / hotline / liên hệ / đổi trả / bảo hành
- chăm sóc khách hàng

Khi phát hiện các keyword này, bot sẽ tìm trong bảng `faqs` trước.

### 5.2 Khi nào dùng tính năng đếm số?

Nếu câu hỏi chứa từ khóa:
- "bao nhiêu", "có bao nhiêu", "tổng cộng", "số lượng", "database", "db", "kho hàng", "hiện tại có"

và không chứa keyword hỗ trợ/ship, bot sẽ trả kết quả đếm sản phẩm.

### 5.3 Khi nào gọi LLM?

- Nếu không phải FAQ support.
- Và nếu có sản phẩm phù hợp từ DB.
- LLM nhận context sản phẩm thật và lịch sử chat.

## 6. Cơ chế tìm FAQ trong `LLMEngine.search_faq()`

- Dùng `keywords LIKE %query%` hoặc `question LIKE %query%` hoặc `answer LIKE %query%`.
- Trả tối đa 5 kết quả.
- Câu FAQ được dùng trực tiếp, không cần qua LLM nếu đã tìm ra.

## 7. Cơ chế tìm sản phẩm trong `LLMEngine` 

- `search_product(query, limit)` tìm `name`, `description`, `category` với `%query%`.
- `_lay_danh_sach_san_pham(limit)` lấy danh sách sản phẩm chung.
- `find_product_by_name(name)` tìm chính xác theo tên, fallback tìm LIKE.
- `count_products()` trả tổng số sản phẩm.

## 8. `xay_dung_system_prompt()` và quy tắc LLM

System prompt đặt ra những nguyên tắc sau:
- Bot là nhân viên tư vấn ABC Trading.
- BẮT BUỘC: chỉ dùng sản phẩm trong danh sách được cung cấp.
- KHÔNG được tạo sản phẩm mới.
- Nếu không có sản phẩm phù hợp, phải nói thẳng.
- Luôn trích dẫn giá và dữ liệu đúng.
- Hỏi thăm nhu cầu, tư vấn, giải đáp giá/bảo hành/giao hàng.
- Trả lời ngắn gọn, tự nhiên.

## 9. Cách `generate_faqs_dataset.py` hoạt động

### 9.1 Mục tiêu

- Sinh ra file SQL lớn với các câu hỏi và câu trả lời đa dạng.
- Mặc định tạo `400000` mục.
- Khoảng 20% câu hỏi mở (`OPEN_ENDED_TEMPLATES`) mang tính tư vấn.
- 80% còn lại tạo theo danh mục hỗ trợ cố định.

### 9.2 Dữ liệu đầu vào

- `GLOBAL_VALUES`: chứa danh sách giá, địa điểm, loại sản phẩm, phương thức ship, loại hỗ trợ, vấn đề, phương thức thanh toán, hóa đơn, mã đơn, giọng bán hàng.
- `CATEGORY_TEMPLATES`: mỗi category gồm `topic`, `keywords`, `question_templates`, `answer_templates`, `params`.
- `OPEN_ENDED_TEMPLATES` và `OPEN_ENDED_ANSWERS`: tạo câu hỏi/tư vấn theo phong cách LLM.

### 9.3 Luồng sinh dữ liệu

1. Sinh trước `open_ended_target = int(limit * 0.2)` mục mở rộng.
2. Sinh các câu FAQ theo từng `CATEGORY_TEMPLATES`.
3. Kết hợp `itertools.product` để tạo nhiều biến thể tham số.
4. Loại trùng lặp câu hỏi bằng `questions` set.
5. Ghi file SQL cuối cùng với định dạng `INSERT INTO faqs (id, keywords, question, answer) VALUES ...`.

### 9.4 Chú ý quan trọng

- Hàm `normalize_text()` chuẩn hóa Unicode, escape apostrophe và loại newline.
- Tên file đầu ra mặc định: `faqs_400k.sql`.
- Có thể thay đổi tham số với `--limit` và `--output`.

## 10. Tóm tắt nghiệp vụ

### 10.1 Luôn ưu tiên dữ liệu thật
- Sản phẩm: chỉ dùng từ `products` DB.
- FAQ: chỉ dùng từ `faqs` DB.
- Session: dùng lịch sử chat để giữ context.

### 10.2 Không để LLM tự do hoàn toàn
- LLM chỉ là lớp trả lời sau khi dữ liệu đã được sắp xếp.
- Nếu đã có FAQ chính xác, bot trả luôn FAQ mà không hỏi LLM.
- Nếu hỏi về sản phẩm, LLM chỉ được phép dùng danh sách `product_context`.

### 10.3 Hỗ trợ ship/hỗ trợ/bảo hành
- Các câu hỏi có keyword support sẽ đi vào đường FAQ.
- Điều này giúp tránh lỗi trước đây khi câu ship/hỗ trợ lại bị hiểu thành câu hỏi đếm số.

## 11. Hướng dẫn dùng nhanh

### Chạy chatbot
```powershell
cd d:\BT_BOT\chat_bot
python chatbot.py
```

### Chạy generator bộ FAQ 400k
```powershell
cd d:\BT_BOT\chat_bot
python generate_faqs_dataset.py --limit 400000 --output faqs_400k.sql
```

### Ghi chú cấu hình
- Cần có biến môi trường `GROQ_API_KEY`.
- MySQL phải chạy và database `abc_trading` phải có quyền truy cập.
- Bảng `faqs` và `products` cần được tạo trước khi dùng.

## 12. Kết luận

Tài liệu này mô tả toàn bộ cách hoạt động hiện tại của hệ thống:
- `chatbot.py` là vòng lặp user -> logic -> trả lời.
- `logic.py` điều phối dữ liệu sản phẩm, FAQ, đếm số, và gọi LLM.
- `llm_engine.py` cung cấp kết nối DB, tìm sản phẩm/FAQ và xây prompt.
- `memory.py` quản lý lịch sử chat, nhớ tên user, và dùng lại context.
- `generate_faqs_dataset.py` sinh bộ dữ liệu FAQ lớn, đa dạng, phù hợp với kịch bản hỗ trợ và tư vấn.

Nếu cần, tôi có thể mở rộng tài liệu này bằng sơ đồ luồng hoặc phần giải thích chi tiết các query SQL.