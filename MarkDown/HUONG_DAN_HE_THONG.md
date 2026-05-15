# 📚 HƯỚNG DẪN HỆ THỐNG CHATBOT ABC TRADING

## 📖 Mục lục
1. [Cách chạy hệ thống](#cách-chạy-hệ-thống)
2. [Cách xử lý dữ liệu](#cách-xử-lý-dữ-liệu)
3. [Thư viện & Hàm được sử dụng](#thư-viện--hàm-được-sử-dụng)
4. [Logic lựa chọn FAQ](#logic-lựa-chọn-faq)
5. [Luồng xử lý chi tiết](#luồng-xử-lý-chi-tiết)

---

## 🚀 Cách chạy hệ thống

### 1. **Yêu cầu trước khi chạy**

```bash
# 1. Cài đặt thư viện
pip install -r requirements.txt

# 2. Cấu hình môi trường
# - Tạo file `.env` trong thư mục chat_bot/ với nội dung:
# GROQ_API_KEY=your_api_key_here

# 3. Đảm bảo MySQL đang chạy
# - Database: abc_trading
# - Các bảng: products, faqs, conversations

# 4. (Tùy chọn) Khởi tạo dữ liệu FAQ
python generate_faqs_dataset.py
```

### 2. **Chạy ứng dụng Web**

```bash
# Chạy từ thư mục d:\BT_BOT\chat_bot
python chatbot.py

# Mở trình duyệt và truy cập:
# http://127.0.0.1:5000
```

### 3. **Cấu trúc khi chạy**

```
Flask App
├── GET / ...................... Trang chủ (index.html)
├── GET /init ................... Khởi tạo session mới
├── POST /chat .................. Gửi tin nhắn (nhận message JSON)
└── POST /reset ................. Reset tất cả sessions
```

---

## 🔄 Cách xử lý dữ liệu

### **Quy trình xử lý từ input đến output**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER NHẬP CÂU HỎI                                            │
│    Input: "Bạn có iPhone 15 không?"                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 2. LOGIC.XU_LY() - PHÂN LOẠI CÂU HỎI                            │
│    - Kiểm tra tên user                                          │
│    - Xác định loại câu hỏi:                                     │
│      • FAQ (ship, bảo hành, hỗ trợ)?                           │
│      • Sản phẩm?                                                │
│      • Đếm số?                                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴─────────────┬──────────────────┐
        │                          │                  │
        ▼                          ▼                  ▼
   ┌─────────────┐          ┌─────────────┐    ┌──────────────┐
   │ FAQ Query?  │          │Product Query?    │Count Query?  │
   └─────┬───────┘          └────────┬────┘    └──────┬───────┘
         │                           │                 │
         │ YES                       │ YES             │ YES
         ▼                           ▼                 ▼
   ┌──────────────────┐    ┌────────────────────┐  ┌──────────────┐
   │Search FAQ        │    │Search Products     │  │Count         │
   │from faqs table   │    │from products table │  │Products      │
   │(Match keywords)  │    │(Match name/desc)   │  │from DB       │
   └────────┬─────────┘    └────────┬───────────┘  └──────┬───────┘
            │                       │                     │
            ▼                       ▼                     ▼
   ┌──────────────────┐    ┌────────────────────┐  ┌──────────────┐
   │Found FAQs? (n>1)     │Format Products     │  │Return Count  │
   │- Return all FAQs │    │as product_context  │  │              │
   │- User chooses    │    │(name/price/stock)  │  │Done ✓        │
   └──────────────────┘    └────────┬───────────┘  └──────────────┘
                                    │
                                    ▼
                           ┌────────────────────┐
                           │GET CONVERSATION    │
                           │HISTORY (limit=10)  │
                           └────────┬───────────┘
                                    │
                                    ▼
                           ┌────────────────────┐
                           │CALL LLM (Groq)     │
                           │System Prompt:      │
                           │"Chỉ dùng sản phẩm  │
                           │ trong danh sách"   │
                           └────────┬───────────┘
                                    │
                                    ▼
                           ┌────────────────────┐
                           │LLM GENERATES       │
                           │RESPONSE            │
                           └────────┬───────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. MEMORY.LUU() - LƯU LỊCH SỬ                                   │
│    - Lưu response vào bộ nhớ session                            │
│    - Ghi vào database (conversations table)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────────┐
│ 4. RETURN RESPONSE TO USER                                      │
│    {"response": "Chúng tôi có iPhone 15 Pro với giá..."}        │
└─────────────────────────────────────────────────────────────────┘
```

### **Ví dụ cụ thể xử lý 3 loại câu hỏi:**

#### **A. Câu hỏi FAQ (Ship/Bảo hành)**

```python
# Input: "Bao lâu thì giao hàng?"
# ✓ Matches: _is_faq_query() = True

# Steps:
1. engine.search_faq("Bao lâu thì giao hàng?", limit=3)
   → SELECT * FROM faqs 
     WHERE keywords LIKE '%giao hang%'
     OR question LIKE '%giao hang%'
   
2. If found 1 FAQ:
   return faq['answer']
   
3. If found multiple FAQs (n > 1):
   display all FAQs as options
   
# Output: "Giao hàng miễn phí trong 2-3 ngày"
```

#### **B. Câu hỏi sản phẩm**

```python
# Input: "Có iPhone 15 không?"
# ✓ Matches: _is_product_query() = True

# Steps:
1. products = engine.search_product("iPhone 15", limit=15)
   → SELECT * FROM products
     WHERE name LIKE '%iPhone 15%'
     OR description LIKE '%iPhone 15%'
     OR category LIKE '%iPhone 15%'

2. Format products as product_context:
   📦 SẢN PHẨM CÓ TRONG KHO:
   1. iPhone 15 Pro Max
      Giá: 25,999,000 VND
      ✅ Còn hàng (5 cái)
      Màn hình OLED 6.7"...

3. Get conversation history:
   HISTORY = [
     {role: "user", content: "..."},
     {role: "bot", content: "..."}
   ]

4. Call LLM:
   messages = [
     {role: "system", content: system_prompt},
     {role: "user", content: product_context},
     {role: "assistant", content: "Tôi đã ghi nhớ danh sách..."},
     {role: "user", content: "Có iPhone 15 không?"}
   ]
   response = groq_client.chat.completions.create(messages)

5. Return response to user
```

#### **C. Câu hỏi đếm số**

```python
# Input: "Bao nhiêu sản phẩm trong kho?"
# ✓ Matches: _is_count_question() = True

# Steps:
1. if products found:
   matched_count = len(products)
   total_count = engine.count_products()
   
2. return f"Hiện tại có {matched_count} sản phẩm phù hợp. Tổng: {total_count}"
```

---

## 📦 Thư viện & Hàm được sử dụng

### **1. Thư viện chính (requirements.txt)**

| Thư viện | Phiên bản | Mục đích |
|---------|---------|---------|
| `groq` | 0.7.0 | Gọi Groq API (LLM - llama-3.1-8b-instant) |
| `mysql-connector-python` | 8.2.0 | Kết nối MySQL để truy vấn dữ liệu |
| `python-dotenv` | 1.0.0 | Load biến môi trường từ .env |
| `Flask` | (built-in) | Framework web cho API endpoints |

### **2. Các hàm quan trọng**

#### **A. `logic.py`**

| Hàm | Tác dụng | Ví dụ |
|-----|---------|-------|
| `xu_ly(user_message, mem)` | **Hàm chính** - xử lý input user | `xu_ly("Có iPhone không?", memory)` |
| `_bo_dau(text)` | Bỏ dấu tiếng Việt | `"Hỏi" → "Hoi"` |
| `_trich_ten(text)` | Trích tên người dùng | `"Tôi tên là Dương" → "Dương"` |
| `_is_faq_query(text)` | Kiểm tra câu hỏi FAQ | Trả `True` nếu chứa "ship", "bảo hành" |
| `_is_product_query(text)` | Kiểm tra câu hỏi sản phẩm | Trả `True` nếu chứa "sản phẩm", "iPhone" |
| `_is_count_question(text)` | Kiểm tra câu hỏi đếm số | Trả `True` nếu chứa "bao nhiêu" |

#### **B. `llm_engine.py`**

| Hàm | Tác dụng | Trả về |
|-----|---------|--------|
| `search_product(query, limit)` | Tìm sản phẩm từ DB | `[{id, name, price, stock, ...}]` |
| `search_faq(query, limit)` | Tìm FAQ từ DB | `[{id, question, answer, ...}]` |
| `count_products()` | Đếm tổng sản phẩm | `int` (tổng số) |
| `find_product_by_name(name)` | Tìm sản phẩm theo tên chính xác | `{id, name, price, stock}` hoặc `None` |
| `_lay_danh_sach_san_pham(category, limit)` | Lấy danh sách sản phẩm | `[{...}, {...}]` |
| `_tim_san_pham_tuong_tu(keywords, limit)` | Tìm sản phẩm tương tự | `[{...}, {...}]` |
| `xay_dung_system_prompt(context)` | Tạo system prompt cho LLM | `str` (prompt) |
| `chat(user_message, context, product_context, history)` | **Gọi LLM chính** | `str` (trả lời) |

#### **C. `memory.py`**

| Hàm | Tác dụng | Ví dụ |
|-----|---------|-------|
| `__init__(session_id)` | Khởi tạo memory cho session | `mem = Memory("abc123")` |
| `luu(role, content)` | Lưu tin nhắn vào history | `mem.luu("user", "Có iPhone không?")` |
| `cap_nhat_context(**kwargs)` | Cập nhật context session | `mem.cap_nhat_context(ten_user="Dương")` |
| `ghi_nho_sp(ten_sp)` | Lưu sản phẩm đã xem | `mem.ghi_nho_sp("iPhone 15")` |
| `lay_lich_su(limit)` | Lấy lịch sử hội thoại | `[{role, content, time}]` |

#### **D. `chatbot.py` (Flask Routes)**

| Route | Method | Tác dụng |
|-------|--------|---------|
| `/` | GET | Trả về trang chủ (index.html) |
| `/init` | GET | Khởi tạo session mới + lời chào |
| `/chat` | POST | Nhận JSON `{message}` → xử lý → trả response |
| `/reset` | POST | Xóa tất cả sessions |

### **3. Model LLM sử dụng**

```python
# Groq API Configuration
model_name = "llama-3.1-8b-instant"

# Tham số:
max_tokens = 300  # Chiều dài response
temperature = 0.7  # Độ "sáng tạo" (0=logic, 1=creative)
```

---

## 🎯 Logic lựa chọn FAQ

### **Tại sao chọn 1 FAQ thay vì n FAQ?**

Hệ thống sử dụng **chiến lược multi-level prioritization**:

#### **Level 1: Số lượng kết quả tìm được**

```python
# Trong logic.py
faqs = engine.search_faq(user_message, limit=3)

if len(faqs) == 1:
    # ✓ Chỉ có 1 FAQ → TRẢ NGAY
    return faqs[0]["answer"]
    
elif len(faqs) > 1:
    # ⚠ Nhiều FAQ → HỎI LẠI USER
    faq_text = "Dưới đây là thông tin liên quan tôi tìm được:\n"
    faq_text += "\n".join(f"- {faq['question']}: {faq['answer']}" 
                          for faq in faqs)
    return faq_text
else:
    # ✗ Không tìm được → GỌI LLM
    pass
```

#### **Level 2: Cơ chế tìm kiếm trong DB**

```sql
-- FAQ được tìm theo thứ tự ưu tiên:
SELECT id, question, answer 
FROM faqs 
WHERE 
    keywords LIKE '%user_input%'          -- 1️⃣ Keywords match (chính xác)
    OR question LIKE '%user_input%'       -- 2️⃣ Question match
    OR answer LIKE '%user_input%'         -- 3️⃣ Answer match
LIMIT 3;

-- Nếu multiple FAQs có cùng độ match:
-- MySQL trả về theo thứ tự ID (tức FAQ được thêm trước có độ ưu tiên cao hơn)
```

#### **Level 3: Khi có nhiều FAQ - Tại sao không chọn 1?**

**Lý do:**
1. **Các FAQ có thể bổ sung lẫn nhau**
   - Vd: "Giao hàng mất bao lâu?" có 3 FAQ:
     - FAQ 1: "Giao hàng miễn phí"
     - FAQ 2: "Thời gian giao là 2-3 ngày"
     - FAQ 3: "Ngoại thành mất 5-7 ngày"
   - Trả tất cả 3 để user có hình ảnh **toàn diện**

2. **Tránh thiếu thông tin quan trọng**
   - Nếu chỉ chọn FAQ 1 → user không biết thời gian
   - Nếu chỉ chọn FAQ 2 → user không biết có miễn phí không

3. **Tránh misunderstanding**
   - FAQ rankings có thể không chính xác hoàn toàn
   - Để user chọn FAQ phù hợp nhất với nhu cầu

#### **Level 4: Khi chỉ có 1 FAQ**

```python
# Điều kiện: len(faqs) == 1
# → Trả FAQ đó mà không cần hỏi lại user
# → LLM không được gọi (tiết kiệm API cost)

reason = """
Khi có 1 FAQ chính xác:
✓ User nhận được câu trả lời NHANH CHÓNG
✓ Tiết kiệm 1 lần gọi LLM API (~ 0.1 USD)
✓ Đủ thông tin để user hiểu
✓ Không cần xử lý thêm
"""
```

### **Quy tắc ưu tiên tổng quát**

```
┌─────────────────────────────────────────────────────────────┐
│ User Question: "Giao hàng miễn phí không?"                  │
└─────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
        ▼                                    ▼
   ┌─────────────┐                     ┌───────────┐
   │Is FAQ?      │                     │Is Product?│
   │Check        │                     │No here    │
   │keywords     │                     └───────────┘
   │(ship, ...)?  │
   └──────┬──────┘
          │ YES
          ▼
   ┌──────────────────┐
   │Search FAQ table  │
   │(limit=3)        │
   └────────┬─────────┘
            │
     ┌──────┴──────┬──────────┐
     │             │          │
   found 1     found >1     found 0
     │             │          │
     ▼             ▼          ▼
  RETURN        RETURN    CALL LLM
  FAQ[0]       ALL FAQs   WITH
  (answer)    (as options) DATABASE
                          CONTEXT
```

---

## 🔍 Luồng xử lý chi tiết

### **Chi tiết từng bước khi user gửi "Có iPhone 15 không?"**

```
STEP 1: User nhập tin nhắn
┌─────────────────────────────────────────┐
│ message: "Có iPhone 15 không?"          │
│ session_id: "a1b2c3d4"                  │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 2: Flask route /chat nhận request
┌─────────────────────────────────────────┐
│ @app.route('/chat', methods=['POST'])   │
│ data = request.json                     │
│ user_input = "Có iPhone 15 không?"      │
│ mem = get_session(session_id)           │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 3: Lưu tin nhắn vào memory
┌─────────────────────────────────────────┐
│ mem.luu("user", "Có iPhone 15 không?") │
│ → Lưu vào history và DB (conversations) │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4: Gọi logic.xu_ly()
┌─────────────────────────────────────────┐
│ tra_loi = xu_ly(user_input, mem)        │
└────────────┬────────────────────────────┘
             │
             ▼ (trong xu_ly)
STEP 4.1: Tạo LLMEngine
┌─────────────────────────────────────────┐
│ engine = LLMEngine()                    │
│ - Load GROQ_API_KEY từ .env             │
│ - Connect MySQL                         │
│ - Init Groq client                      │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.2: Trích tên user (nếu có)
┌─────────────────────────────────────────┐
│ _trich_ten("Có iPhone 15 không?")       │
│ → Không tìm thấy tên                    │
│ ten_user = None                         │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.3: Query Database - Search Products
┌─────────────────────────────────────────┐
│ products = engine.search_product(       │
│     "Có iPhone 15 không?",              │
│     limit=15                            │
│ )                                       │
│                                         │
│ SQL:                                    │
│ SELECT id, name, category, price,       │
│        stock, description               │
│ FROM products                           │
│ WHERE name LIKE '%Có iPhone 15%'        │
│    OR description LIKE '%Có iPhone 15%' │
│    OR category LIKE '%Có iPhone 15%'    │
│ LIMIT 15                                │
│                                         │
│ Result:                                 │
│ [                                       │
│   {                                     │
│     id: 101,                            │
│     name: "iPhone 15 Pro Max",          │
│     category: "Smartphone",             │
│     price: 25999000,                    │
│     stock: 5,                           │
│     description: "Màn hình OLED..."     │
│   },                                    │
│   {                                     │
│     id: 102,                            │
│     name: "iPhone 15",                  │
│     category: "Smartphone",             │
│     price: 19999000,                    │
│     stock: 8,                           │
│     description: "Camera 48MP..."       │
│   }                                     │
│ ]                                       │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.4: Kiểm tra loại câu hỏi
┌─────────────────────────────────────────┐
│ _is_faq_query("Có iPhone 15 không?")    │
│ → False (không chứa: ship, bảo hành, ..)│
│                                         │
│ _is_product_query("Có iPhone 15 không?"│
│ → True (chứa: iPhone)                   │
│                                         │
│ _is_count_question(...)                 │
│ → False                                 │
│                                         │
│ → ĐÂY LÀ PRODUCT QUERY                 │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.5: Format products as product_context
┌─────────────────────────────────────────┐
│ product_context = """                   │
│ 📦 SẢN PHẨM CÓ TRONG KHO (Hiển thị 2): │
│                                         │
│ 1. iPhone 15 Pro Max                    │
│     Giá: 25,999,000 VND                 │
│     ✅ Còn hàng (5 cái)                 │
│     Màn hình OLED 6.7"...               │
│                                         │
│ 2. iPhone 15                            │
│     Giá: 19,999,000 VND                 │
│     ✅ Còn hàng (8 cái)                 │
│     Camera 48MP...                      │
│                                         │
│ QUYẾT ĐỊNH QUAN TRỌNG:                  │
│ - Chỉ dùng những sản phẩm trong danh... │
│ """                                     │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.6: Lấy conversation history
┌─────────────────────────────────────────┐
│ lichsu = mem.lay_lich_su(limit=10)       │
│                                         │
│ Result:                                 │
│ [                                       │
│   {role: "bot", content: "Xin chào!..." │
│   {role: "user", content: "Có iPhone.. │
│ ]                                       │
│                                         │
│ Format as text:                         │
│ lich_su_text = """                      │
│ BOT: Xin chào! 👋 Tôi là trợ lý...     │
│ USER: Có iPhone 15 không?              │
│ """                                     │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.7: Xây dựng system_prompt
┌─────────────────────────────────────────┐
│ system_prompt = engine.xay_dung...()    │
│                                         │
│ Kết quả:                                │
│ """                                     │
│ Bạn là nhân viên tư vấn chuyên...      │
│                                         │
│ ⚠️ NGUYÊN TẮC QUAN TRỌNG NHẤT:          │
│ 1. CHỈ recommend sản phẩm TRONG LIST   │
│ 2. KHÔNG TỰ TẠO hoặc CẤU ĐẠO          │
│ 3. Nếu không có: "Xin lỗi, không có"   │
│ 4. LUÔN trích dẫn giá từ danh sách      │
│ ...                                     │
│ """                                     │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.8: Call LLM API (Groq)
┌─────────────────────────────────────────┐
│ tra_loi = engine.chat(                  │
│     user_message="Có iPhone 15 không?", │
│     context={ten_user: None, ...},      │
│     product_context=product_context,    │
│     history=lich_su_text                │
│ )                                       │
│                                         │
│ Messages sent to Groq:                  │
│ [                                       │
│   {                                     │
│     role: "system",                     │
│     content: system_prompt              │
│   },                                    │
│   {                                     │
│     role: "user",                       │
│     content: "📦 DANH SÁCH SẢN PHẨM...", │
│   },                                    │
│   {                                     │
│     role: "assistant",                  │
│     content: "Tôi đã ghi nhớ..."        │
│   },                                    │
│   {                                     │
│     role: "user",                       │
│     content: "Lịch sử:\nBOT: ..."       │
│   },                                    │
│   {                                     │
│     role: "user",                       │
│     content: "Có iPhone 15 không?"      │
│   }                                     │
│ ]                                       │
│                                         │
│ API Parameters:                         │
│ model: "llama-3.1-8b-instant"           │
│ max_tokens: 300                         │
│ temperature: 0.7                        │
│                                         │
│ Response from Groq:                     │
│ "Vâng! Chúng tôi có iPhone 15 và...    │
│  iPhone 15 Pro Max. iPhone 15 giá...    │
│  iPhone 15 Pro Max giá 25,999,000 VND" │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 4.9: Kiểm tra từ khóa tạm biệt
┌─────────────────────────────────────────┐
│ if any(kw in user_message.lower()       │
│        for kw in ['thoát', 'bye', ...]) │
│ → False (không chứa từ khóa)            │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 5: Lưu response vào memory
┌─────────────────────────────────────────┐
│ mem.luu("bot", tra_loi)                 │
│ → Lưu vào history + DB                  │
└────────────┬────────────────────────────┘
             │
             ▼
STEP 6: Return response to user
┌─────────────────────────────────────────┐
│ return jsonify({                        │
│     "response": "Vâng! Chúng tôi có..." │
│     "session_id": "a1b2c3d4"            │
│ })                                      │
│                                         │
│ JSON Response:                          │
│ {                                       │
│   "response": "Vâng! Chúng tôi có      │
│                iPhone 15 và iPhone 15... │
│   "session_id": "a1b2c3d4"              │
│ }                                       │
└─────────────────────────────────────────┘
             │
             ▼
STEP 7: Frontend hiển thị
┌─────────────────────────────────────────┐
│ Màn hình user:                          │
│                                         │
│ You: Có iPhone 15 không?                │
│                                         │
│ Bot: Vâng! Chúng tôi có iPhone 15 và   │
│      iPhone 15 Pro Max. iPhone 15 giá   │
│      19,999,000 VND. iPhone 15 Pro Max  │
│      giá 25,999,000 VND.                │
└─────────────────────────────────────────┘
```

### **Chi tiết SQL queries được sử dụng**

```sql
-- 1. Search Products
SELECT id, name, category, price, stock, description
FROM products
WHERE name LIKE '%iPhone 15%'
   OR description LIKE '%iPhone 15%'
   OR category LIKE '%iPhone 15%'
LIMIT 15;

-- 2. Search FAQ
SELECT id, question, answer
FROM faqs
WHERE keywords LIKE '%ship%'
   OR question LIKE '%ship%'
   OR answer LIKE '%ship%'
LIMIT 3;

-- 3. Count Products
SELECT COUNT(*) FROM products;

-- 4. Get Category Products
SELECT id, name, category, price, stock, description
FROM products
WHERE category = 'Smartphone'
LIMIT 20;

-- 5. Save Conversation
INSERT INTO conversations
(session_id, role, content, buoc, nhanh)
VALUES ('a1b2c3d4', 'user', 'Có iPhone 15 không?', 'tro_chuyen', NULL);

-- 6. Get Conversation History
SELECT role, content, created_at
FROM conversations
WHERE session_id = 'a1b2c3d4'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 📊 Bảng dữ liệu trong Database

### **Table: products**
```
┌──────┬──────────────────────┬────────────┬──────────┬───────┬─────────────────┐
│ id   │ name                 │ category   │ price    │ stock │ description     │
├──────┼──────────────────────┼────────────┼──────────┼───────┼─────────────────┤
│ 101  │ iPhone 15 Pro Max    │ Smartphone │ 25999000 │ 5     │ Màn hình OLED...│
│ 102  │ iPhone 15            │ Smartphone │ 19999000 │ 8     │ Camera 48MP...  │
│ 103  │ Samsung Galaxy S24   │ Smartphone │ 23999000 │ 10    │ Màn hình 6.2"..  │
│ ...  │ ...                  │ ...        │ ...      │ ...   │ ...             │
└──────┴──────────────────────┴────────────┴──────────┴───────┴─────────────────┘
```

### **Table: faqs**
```
┌─────┬────────────────────────────┬──────────────────────────────┬─────────────────┐
│ id  │ keywords                   │ question                     │ answer          │
├─────┼────────────────────────────┼──────────────────────────────┼─────────────────┤
│ 1   │ ship,giao hang,miễn phí   │ Giao hàng miễn phí không?   │ Giao hàng miễn   │
│ 2   │ ship,giao hang,thời gian  │ Bao lâu thì giao hàng?      │ Giao hàng 2-3... │
│ 3   │ bảo hành,warranty,hỗ trợ  │ Bảo hành bao lâu?           │ Bảo hành 12 tháng│
│ ... │ ...                        │ ...                         │ ...             │
└─────┴────────────────────────────┴──────────────────────────────┴─────────────────┘
```

### **Table: conversations**
```
┌────┬────────────┬────────┬──────────────────────┬─────────┬──────────┬────────────────┐
│ id │ session_id │ role   │ content              │ buoc    │ nhanh    │ created_at     │
├────┼────────────┼────────┼──────────────────────┼─────────┼──────────┼────────────────┤
│ 1  │ a1b2c3d4   │ bot    │ Xin chào! 👋 ...    │ chao_hoi│ NULL     │ 2026-05-11...  │
│ 2  │ a1b2c3d4   │ user   │ Có iPhone 15 không? │ tro_chu │ NULL     │ 2026-05-11...  │
│ 3  │ a1b2c3d4   │ bot    │ Vâng! Chúng tôi có..│ tro_chu │ NULL     │ 2026-05-11...  │
│ ...│ ...        │ ...    │ ...                  │ ...     │ ...      │ ...            │
└────┴────────────┴────────┴──────────────────────┴─────────┴──────────┴────────────────┘
```

---

## 🔐 Cấu hình môi trường (.env)

```bash
# .env file
GROQ_API_KEY=gsk_1a2b3c4d5e6f7g8h9i0j  # Lấy từ https://console.groq.com

# MySQL Configuration (trong DB_CONFIG)
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=abc_trading
```

---

## ✅ Kiểm tra hệ thống hoạt động

```bash
# 1. Kiểm tra MySQL
mysql -u root -e "SELECT * FROM abc_trading.products LIMIT 1;"

# 2. Kiểm tra GROQ_API_KEY
echo $GROQ_API_KEY  # Windows: echo %GROQ_API_KEY%

# 3. Test Flask
python -c "from flask import Flask; print('Flask OK')"

# 4. Test thư viện
python -c "
import groq
import mysql.connector
from dotenv import load_dotenv
print('✓ All libraries loaded')
"

# 5. Chạy chatbot
python chatbot.py
# Mở browser: http://127.0.0.1:5000
```

---

## 📈 Tóm tắt quy trình toàn hệ thống

```
┌────────────────────────────────────────────────────────────────────┐
│                    CHATBOT ABC TRADING FLOW                        │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  USER INPUT → LOGIC.XU_LY() → DATABASE QUERY → LLM (Groq)        │
│       │              │              │              │             │
│  "Có iPhone"     Classify      Search DB      Generate           │
│  không?          FAQ/Product   (Product/FAQ)  Response           │
│       │              │              │              │             │
│       └──────────────┼──────────────┼──────────────┘             │
│                      │              │                            │
│                      ▼              ▼                            │
│                 MEMORY.LUU() ← RESPONSE FORMATTED               │
│                      │                                           │
│                      ▼                                           │
│                  RETURN JSON                                     │
│                      │                                           │
│                      ▼                                           │
│              FRONTEND DISPLAY                                    │
│              (index.html)                                        │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Lưu ý quan trọng

1. **Database-First Approach**: Hệ thống LUÔN query database trước, không bao giờ hallucinate
2. **FAQ Logic**: Trả 1 FAQ nếu tìm được 1, trả tất cả nếu tìm được nhiều
3. **Groq API Cost**: Mỗi lần gọi LLM tốn tiền, nên tối ưu số lần gọi
4. **Session Management**: Mỗi người dùng = 1 session riêng với lịch sử riêng
5. **Error Handling**: Nếu MySQL down → không hiển thị sản phẩm, LLM vẫn trả lời ngoài xử lý

---

**Tài liệu này được tạo ngày: 2026-05-11**
