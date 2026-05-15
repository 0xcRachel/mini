"""
llm_engine.py
LLM Engine - Sử dụng Groq API cho phản hồi tự nhiên như ChatGPT.
- Model: mixtral-8x7b hoặc llama2-70b
- Tư vấn linh hoạt, hiểu ngữ cảnh
- Kết hợp với database sản phẩm cho thông tin chính xác
"""

import os
import json
import mysql.connector
from groq import Groq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "abc_trading",
    "charset":  "utf8mb4",
}


class LLMEngine:
    """
    LLM Engine - Chat như ChatGPT
    - Sử dụng Groq để xử lý tự nhiên
    - Kết hợp context (sản phẩm, lịch sử) để tư vấn tốt hơn
    """
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("\n" + "="*60)
            print("❌ ERROR: GROQ_API_KEY not found!")
            print("="*60)
            print("\n📌 Steps to fix:")
            print("1. Go to: https://console.groq.com")
            print("2. Create account (free, no credit card)")
            print("3. Generate API Key")
            print("4. Create .env file with:")
            print("   GROQ_API_KEY=your_key_here")
            print("\n" + "="*60 + "\n")
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"
        self.db = None
        self._connect_db()
    
    def _connect_db(self):
        """Kết nối MySQL để lấy info sản phẩm."""
        try:
            self.db = mysql.connector.connect(**DB_CONFIG)
            print("[LLM] Database connected!")
        except Exception as e:
            print(f"[LLM] Database connection failed: {e}")
            self.db = None
    
    def _lay_danh_sach_san_pham(self, category: str = None, limit: int = 20) -> list[dict]:
        """Lấy danh sách sản phẩm từ DB."""
        if not self.db:
            return []
        
        try:
            cursor = self.db.cursor(dictionary=True)
            if category:
                cursor.execute(
                    "SELECT id, name, category, price, stock, description FROM products WHERE category = %s LIMIT %s",
                    (category, limit)
                )
            else:
                cursor.execute(
                    "SELECT id, name, category, price, stock, description FROM products LIMIT %s",
                    (limit,)
                )
            
            products = cursor.fetchall()
            cursor.close()
            return products
        except Exception as e:
            print(f"[LLM] Error fetching products: {e}")
            return []
    
    def _tim_san_pham_tuong_tu(self, keywords: str, limit: int = 15) -> list[dict]:
        """Tìm sản phẩm dựa trên keywords - LUÔN TỪ DATABASE"""
        if not self.db:
            return []
        
        try:
            cursor = self.db.cursor(dictionary=True)
            search_term = f"%{keywords}%"
            cursor.execute(
                f"""SELECT id, name, category, price, stock, description 
                   FROM products 
                   WHERE name LIKE %s OR description LIKE %s OR category LIKE %s
                   LIMIT {limit}""",
                (search_term, search_term, search_term)
            )
            products = cursor.fetchall()
            cursor.close()
            return products
        except Exception as e:
            print(f"[LLM] Error searching products: {e}")
            return []

    def search_faq(self, query: str, limit: int = 5) -> list[dict]:
        """Tìm câu trả lời FAQ trong bảng faqs dựa trên truy vấn."""
        if not self.db:
            return []
        try:
            cursor = self.db.cursor(dictionary=True)
            search_term = f"%{query}%"
            cursor.execute(
                "SELECT id, question, answer FROM faqs WHERE keywords LIKE %s OR question LIKE %s OR answer LIKE %s LIMIT %s",
                (search_term, search_term, search_term, limit)
            )
            faqs = cursor.fetchall()
            cursor.close()
            return faqs
        except Exception as e:
            print(f"[LLM] Error searching faqs: {e}")
            return []
    
    def _format_san_pham(self, products: list[dict]) -> str:
        """Format danh sách sản phẩm thành text để gửi cho LLM."""
        if not products:
            return "Không tìm thấy sản phẩm nào."
        
        lines = []
        for i, p in enumerate(products, 1):
            lines.append(f"{i}. {p['name']}")
            lines.append(f"   Giá: {p['price']:,}đ | Còn: {p['stock']} cái")
            lines.append(f"   Mô tả: {p['description'][:100]}...")
        
        return "\n".join(lines)
    
    def count_products(self) -> int:
        """Đếm tổng số sản phẩm trong database."""
        if not self.db:
            return 0
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            print(f"[LLM] Error counting products: {e}")
            return 0
    
    def find_product_by_name(self, name: str) -> dict | None:
        """Tìm sản phẩm chính xác theo tên từ DB."""
        if not self.db:
            return None
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, category, price, stock, description FROM products WHERE LOWER(name) = LOWER(%s) LIMIT 1",
                (name,)
            )
            product = cursor.fetchone()
            cursor.close()
            if product:
                return product
            # Fallback tìm tên gần đúng
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, name, category, price, stock, description FROM products WHERE name LIKE %s LIMIT 1",
                (f"%{name}%",)
            )
            product = cursor.fetchone()
            cursor.close()
            return product
        except Exception as e:
            print(f"[LLM] Error finding product: {e}")
            return None
    
    def search_product(self, query: str, limit: int = 15) -> list[dict]:
        """Tìm sản phẩm trong DB dựa trên truy vấn."""
        if not self.db:
            return []
        query = query.strip()
        if not query:
            return self._lay_danh_sach_san_pham(limit=limit)
        try:
            cursor = self.db.cursor(dictionary=True)
            search_term = f"%{query}%"
            cursor.execute(
                f"""SELECT id, name, category, price, stock, description
                   FROM products
                   WHERE name LIKE %s OR description LIKE %s OR category LIKE %s
                   LIMIT {limit}""",
                (search_term, search_term, search_term)
            )
            products = cursor.fetchall()
            cursor.close()
            return products
        except Exception as e:
            print(f"[LLM] Error searching products: {e}")
            return []
    
    @property
    def products(self) -> list[dict]:
        """Danh sách sản phẩm hiện có từ DB."""
        return self._lay_danh_sach_san_pham(limit=100)
    
    def xay_dung_system_prompt(self, context: dict, general_mode: bool = False) -> str:
        """
        Xây dựng system prompt để bot tư vấn.
        general_mode=False: Strict mode - chỉ dùng sản phẩm từ danh sách
        general_mode=True: Flexible mode - có thể trả lời tổng quát (lỏng lòng)
        """
        ten_user = context.get('ten_user', 'bạn')
        
        if general_mode:
            # MODE LỎNG LÒNG - trả lời câu hỏi tổng quát
            prompt = f"""Bạn là trợ lý ảo thân thiện của ABC Trading (Việt Nam).
Tên khách hàng: {ten_user}

HƯỚNG DẪN:
- Trả lời câu hỏi một cách tự nhiên và hữu ích
- Nếu là câu hỏi liên quan đến sản phẩm/dịch vụ ABC, hãy hướng dẫn tìm hiểu thêm
- Nếu là câu hỏi tổng quát (ngoài lề), trả lời theo kiến thức chung của bạn
- Giữ tôn trọng và lịch sự
- Trả lời NGẮN (2-3 câu), tự nhiên
"""
        else:
            # MODE STRICT - chỉ dùng sản phẩm trong danh sách
            prompt = f"""Bạn là nhân viên tư vấn bán hàng chuyên nghiệp của ABC Trading (Việt Nam).
Thông tin khách hàng: {ten_user}

⚠️ NGUYÊN TẮC QUAN TRỌNG NHẤT:
1. CHỈ recommend sản phẩm TRONG DANH SÁCH được cung cấp
2. KHÔNG TỰ TẠO hoặc CẤU ĐẠO các sản phẩm không có trong danh sách
3. Nếu không có sản phẩm phù hợp, hãy nói thẳng: "Hiện tại cửa hàng không có sản phẩm này"
4. LUÔN trích dẫn giá từ danh sách (nếu có sản phẩm)

HƯỚNG DẪN:
• Hỏi thăm nhu cầu khách
• Tư vấn từ sản phẩm CÓ TRONG KHO
• Giải đáp về giá, bảo hành, giao hàng
• Trả lời NGẮN (2-3 câu), tự nhiên

QUY TẮC BẢNG GIÁ:
- Nếu khách hỏi về sản phẩm KHÔNG trong danh sách: "Xin lỗi, cửa hàng không có sản phẩm này"
- Luôn dùng giá từ danh sách được cung cấp
- Nếu nghi ngờ, hỏi lại khách hoặc hỏi người quản lý
"""
        return prompt
    
    def chat(self, user_message: str, context: dict, product_context: str = "", history: str = "") -> str:
        """
        Chat với LLM - DATABASE FIRST APPROACH (STRICT MODE)
        user_message: Câu hỏi của user
        context: Context từ Memory
        product_context: DANH SÁCH SẢN PHẨM THỰC TỪ DB
        history: Lịch sử hội thoại
        """
        system_prompt = self.xay_dung_system_prompt(context, general_mode=False)
        
        # Xây dựng messages
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # LUÔN thêm product context - đây là nguồn dữ liệu thực
        if product_context:
            messages.append({
                "role": "user",
                "content": f"📦 DANH SÁCH SẢN PHẨM CÓ TRONG KHO (CHỈ DỰA VÀO ĐÂY ĐỂ TƯ VẤN):{product_context}\n\nBây giờ, tôi sẽ trả lời câu hỏi của khách dựa vào danh sách này. Nếu không có sản phẩm phù hợp, tôi sẽ nói rõ."
            })
            messages.append({
                "role": "assistant",
                "content": "Tôi đã ghi nhớ danh sách sản phẩm. Tôi sẽ CHỈ tư vấn những sản phẩm CÓ TRONG DANH SÁCH này. Tiếp tục!"
            })
        else:
            # Nếu không có sản phẩm - thông báo
            messages.append({
                "role": "assistant",
                "content": "⚠️  Hiện tại không có sản phẩm phù hợp trong kho. Hãy nói khách là cửa hàng đã hết hàng hoặc không có sản phẩm mà khách tìm."
            })
        
        # Thêm lịch sử hội thoại nếu có
        if history:
            messages.append({
                "role": "user",
                "content": f"Lịch sử hội thoại trước:\n{history}\n---\nTiếp tục cuộc hội thoại."
            })
        
        # Thêm câu hỏi hiện tại của user
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
            
            reply = response.choices[0].message.content.strip()
            return reply
        
        except Exception as e:
            print(f"[LLM] Error: {e}")
            return f"Xin lỗi, tôi gặp lỗi kỹ thuật: {str(e)[:50]}"

    def classify_intent(self, user_message: str, history: str = "") -> dict:
        """
        Sử dụng LLM để phân tích ý định của người dùng.
        Kết quả trả về: { "intent": "SEARCH", "entities": ["iphone", "15"], "sentiment": "neutral" }
        """
        prompt = f"""Phân tích câu nói sau của khách hàng và trả về kết quả dưới dạng JSON (CHỈ TRẢ VỀ JSON):
Câu nói: "{user_message}"
Lịch sử gần đây: {history}

Các loại Intent (ý định):
- SEARCH: Tìm kiếm sản phẩm, hỏi giá, hỏi thông số.
- FAQ: Hỏi về chính sách giao hàng, bảo hành, đổi trả, địa chỉ shop.
- ORDER_CHECK: Kiểm tra đơn hàng, hỏi về đơn đã đặt.
- GREETING: Chào hỏi.
- OUT_OF_SCOPE: Câu hỏi ngoài lề (thời tiết, toán học, kiến thức chung).
- CHITCHAT: Tán gẫu, khen ngợi, hoặc thoát/tạm biệt.

Định dạng JSON yêu cầu:
{{
  "intent": "Tên_Intent",
  "keywords": ["từ", "khóa", "tìm", "kiếm"],
  "sentiment": "tâm_trạng_khách"
}}
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": "Bạn là chuyên gia phân tích ngôn ngữ. Chỉ trả về JSON."},
                          {"role": "user", "content": prompt}],
                response_format={ "type": "json_object" },
                max_tokens=150,
                temperature=0,
            )
            return json.loads(response.choices[0].message.content.strip())
        except Exception as e:
            print(f"[LLM] Error classifying intent: {e}")
            return {"intent": "SEARCH", "keywords": [user_message], "sentiment": "neutral"}
    
    def chat_general(self, user_message: str, context: dict, history: str = "") -> str:
        """
        Chat LỎNG LÒNG - Trả lời câu hỏi tổng quát (không bị kẹp vào sản phẩm ABC)
        Được dùng cho các câu hỏi ngoài lề
        """
        system_prompt = self.xay_dung_system_prompt(context, general_mode=True)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Thêm lịch sử hội thoại nếu có
        if history:
            messages.append({
                "role": "user",
                "content": f"Lịch sử hội thoại trước:\n{history}\n---\nTiếp tục cuộc hội thoại."
            })
        
        # Thêm câu hỏi hiện tại
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=300,
                temperature=0.7,
            )
            
            reply = response.choices[0].message.content.strip()
            return reply
        
        except Exception as e:
            print(f"[LLM] Error in chat_general: {e}")
            return f"Xin lỗi, tôi gặp lỗi kỹ thuật: {str(e)[:50]}"
    
    def close(self):
        """Đóng kết nối database."""
        if self.db:
            self.db.close()


if __name__ == "__main__":
    # Test
    engine = LLMEngine()
    
    context = {
        "ten_user": "Dương",
        "buoc": "tro_chuyen"
    }
    
    reply = engine.chat(
        "Xin chào, tôi muốn mua một chiếc điện thoại",
        context
    )
    print(f"Bot: {reply}")
    
    engine.close()
