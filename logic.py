"""
logic.py (NEW - LLM VERSION)
Chatbot logic - DATABASE-FIRST approach
- Luôn query database trước khi trả lời
- Chỉ dùng sản phẩm thực từ DB, KHÔNG hallucinate
- Giáo dục LLM với dữ liệu thực tế
"""

import re
import unicodedata
from memory import Memory
from llm_engine import LLMEngine

_engine: LLMEngine | None = None

def _get_engine() -> LLMEngine:
    global _engine
    if _engine is None:
        _engine = LLMEngine()
    return _engine

def _bo_dau(text: str) -> str:
    """Bỏ dấu tiếng Việt"""
    text = unicodedata.normalize('NFD', text)
    text = re.sub(r'[\u0300-\u036f]', '', text)
    return text.replace('\u0111', 'd').replace('\u0110', 'D').lower()


def _trich_ten(text: str) -> str | None:
    """Trích tên người dùng: 'tôi tên là Dương' -> 'Dương'"""
    nodau = _bo_dau(text)
    patterns = [
        r'(?:ten la|ten toi la|toi la|minh la|minh ten|toi ten)\s+([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]+)',
    ]
    for p in patterns:
        m = re.search(p, nodau)
        if m:
            ten = m.group(1).strip().capitalize()
            words = text.split()
            for w in words:
                if _bo_dau(w.lower()) == ten.lower():
                    return w
            return ten
    return None


def _is_count_question(text: str) -> bool:
    text = text.lower()
    # Loại trừ các câu hỏi về ship/hỗ trợ/bảo hành để không nhầm với câu hỏi đếm số
    non_count_keywords = [
        "ship", "giao hang", "giao hàng", "miễn phí", "mien phi", "phí giao hàng", "phí ship", "miễn phí ship",
        "hỗ trợ", "ho tro", "hotline", "liên hệ", "lien he", "đổi trả", "doi tra", "bảo hành", "bao hanh",
        "chăm sóc khách hàng", "cham soc khach hang", "ho tro khach hang"
    ]
    if any(kw in text for kw in non_count_keywords):
        return False
    return any(kw in text for kw in ["bao nhiêu", "có bao nhiêu", "tổng cộng", "số lượng", "database", "db", "kho hàng", "hiện tại có"])


def _is_faq_query(text: str) -> bool:
    text = text.lower()
    keywords = [
        "ship", "giao hang", "giao hàng", "mien phi", "miễn phí", "phí giao hàng", "phí ship", "miễn phí ship",
        "hỗ trợ", "ho tro", "hotline", "liên hệ", "lien he", "đổi trả", "doi tra", "bảo hành", "bao hanh",
        "chăm sóc khách hàng", "cham soc khach hang", "ho tro khach hang"
    ]
    return any(kw in text for kw in keywords)


def _is_product_query(text: str) -> bool:
    text = text.lower()
    keywords = [
        "sản phẩm", "hàng", "điện thoại", "iphone", "samsung", "xiaomi", "oppo", "vivo",
        "apple", "laptop", "máy tính", "tablet", "máy giặt", "tủ lạnh", "tivi", "tai nghe",
    ]
    return any(kw in text for kw in keywords)


def _is_out_of_scope_question(text: str) -> bool:
    """
    Nhận biết câu hỏi NGOÀI LỀ (không liên quan đến sản phẩm/FAQ của ABC)
    Ví dụ: "Giá cả ở Hà Nội?", "Thời tiết hôm nay?", "Năm nay mấy tuổi?", v.v
    """
    text_lower = text.lower()
    
    # Từ khóa liên quan đến ABC Trading - nếu có thì KHÔNG phải out-of-scope
    abc_keywords = [
        "sản phẩm", "hàng", "điện thoại", "iphone", "samsung", "xiaomi", "oppo", "vivo", "apple",
        "laptop", "máy tính", "tablet", "máy giặt", "tủ lạnh", "tivi", "tai nghe",
        "shop", "cửa hàng", "abc", "trading", "mua", "bán", "đặt hàng", "dat hang",
        "ship", "giao hang", "giao hàng", "mien phi", "miễn phí", "phí giao hàng", "phí ship",
        "hỗ trợ", "ho tro", "hotline", "liên hệ", "lien he", "đổi trả", "doi tra", "bảo hành", "bao hanh",
        "chăm sóc khách hàng", "cham soc khach hang", "ho tro khach hang", "giá", "gia", "giá cả", "gia ca",
    ]
    
    # Nếu có từ khóa ABC -> Không phải out-of-scope
    if any(kw in text_lower for kw in abc_keywords):
        return False
    
    # Câu hỏi out-of-scope: thời tiết, chính trị, lịch sử, địa lý, toán học, v.v
    out_of_scope_keywords = [
        "thời tiết", "thoi tiet", "trời hôm nay", "troi hom nay", 
        "giá cả hà nội", "gia ca ha noi", "giá hà nội", "gia ha noi",
        "giá ở", "gia o", "giá tại", "gia tai",  # Câu hỏi về giá không liên quan ABC
        "năm nay", "tuổi", "sinh nhật", "birthday",
        "chính trị", "chinh tri", "quốc tế", "quoc te", "tổng thống", "tong thong",
        "tính toán", "tinh toan", "math", "phép tính",
        "lịch sử", "lich su", "địa lý", "dia ly", 
        "khoa học", "khoa hoc", "vật lý", "vat ly",
        "ơm pa", "olympic", "thể thao", "the thao",
        "cơ thể", "co the", "sức khỏe", "suc khoe",
        "bệnh", "benh", "dịch bệnh", "dich benh", "covid",
    ]
    
    # Nếu có từ khóa out-of-scope -> Phải out-of-scope
    return any(kw in text_lower for kw in out_of_scope_keywords)


def xu_ly(user_message: str, mem: Memory) -> str:
    """
    XỬ LÝ TIN NHẮN - DATABASE FIRST APPROACH
    
    1. Kiểm tra tên user
    2. LUÔN query database (không bỏ qua)
    3. Format dữ liệu thực từ DB
    4. Gửi cho LLM với constraint: "Chỉ dùng những sản phẩm được cung cấp"
    5. LLM trả lời dựa vào dữ liệu thực, KHÔNG hallucinate
    """
    
    engine = _get_engine()
    
    # Kiểm tra xem user có nhắc tên không
    ten_user = _trich_ten(user_message)
    if ten_user:
        mem.cap_nhat_context(ten_user=ten_user)
    
    # Lấy context hiện tại
    context = mem.context.copy()
    
    # ============================================================
    # STEP 1: LUÔN QUERY DATABASE (đây là chìa khóa giải quyết vấn đề)
    # ============================================================
    products = engine.search_product(user_message, limit=15)
    
    if not products and _is_product_query(user_message):
        products = engine._lay_danh_sach_san_pham(limit=15)
    
    # Nếu là câu hỏi FAQ về ship / hỗ trợ / bảo hành, trả từ bảng faqs nếu có
    if _is_faq_query(user_message):
        faqs = engine.search_faq(user_message, limit=3)
        if faqs:
            if len(faqs) == 1:
                return faqs[0]["answer"]
            faq_text = "Dưới đây là thông tin liên quan tôi tìm được:\n"
            faq_text += "\n".join(f"- {faq['question']}: {faq['answer']}" for faq in faqs)
            return faq_text

    # Nếu user hỏi tổng số sản phẩm, trả luôn dựa trên DB
    if _is_count_question(user_message):
        if products:
            matched_count = len(products)
            total_count = engine.count_products()
            return (
                f"Hiện tại có {matched_count} sản phẩm phù hợp với yêu cầu của bạn trong kho. "
                f"Tổng số sản phẩm trong kho là {total_count}."
            )
        total_count = engine.count_products()
        return f"Hiện tại cơ sở dữ liệu có {total_count} sản phẩm."
    
    if not products and _is_product_query(user_message):
        return "Xin lỗi, cửa hàng hiện không có sản phẩm phù hợp với yêu cầu của bạn."
    
    # Format sản phẩm cho LLM
    product_context = ""
    if products:
        product_context = f"""
📦 SẢN PHẨM CÓ TRONG KHO (Hiển thị tối đa {len(products)} sản phẩm):
"""
        for i, p in enumerate(products, 1):
            stock_status = "✅ Còn hàng" if p['stock'] > 0 else "❌ Hết hàng"
            product_context += f"""
{i}. {p['name']}
    Giá: {p['price']:,} VND
    {stock_status} ({p['stock']} cái)
     {p.get('description', 'N/A')[:120]}
"""
        
        product_context += f"""
  QUYẾT ĐỊNH QUAN TRỌNG:
- Chỉ dùng những sản phẩm trong danh sách trên.
- Không tự tạo hay bịa ra sản phẩm, mã, số lượng hay giá cả.
- Nếu khách hỏi sản phẩm không có, trả lời: "Xin lỗi, cửa hàng hiện không có sản phẩm phù hợp."
- Luôn sử dụng chính xác thông tin giá và tồn kho từ danh sách.
"""
    else:
        product_context = """
  Hiện tại không có sản phẩm phù hợp trong kho.
Hãy trả lời: "Xin lỗi, cửa hàng hiện không có sản phẩm mà bạn tìm kiếm."
"""
    
    # ============================================================
    # STEP 2: Lấy lịch sử hội thoại để AI học từ context
    # ============================================================
    lichsu = mem.lay_lich_su(limit=10)
    lich_su_text = ""
    if lichsu:
        for msg in lichsu[-10:]:
            lich_su_text += f"{msg['role'].upper()}: {msg['content']}\n"
    
    # ============================================================
    # STEP 3: KIỂM TRA CÓ PHẢI CÂU HỎI NGOÀI LỀ KHÔNG
    # ============================================================
    if _is_out_of_scope_question(user_message):
        # ✅ CÂU HỎI NGOÀI LỀ - Dùng CHAT GENERAL (LỎNG LÒNG)
        # Ví dụ: "Giá ở Hà Nội?", "Thời tiết hôm nay?", v.v
        try:
            tra_loi = engine.chat_general(
                user_message,
                context,
                history=lich_su_text
            )
        except Exception as e:
            tra_loi = f"Xin lỗi, tôi gặp lỗi kỹ thuật: {str(e)[:100]}"
    else:
        # ⚠️ CÂU HỎI LÀM VIỆC VỚI ABC - Dùng CHAT STRICT (KỲ CƯƠNG)
        # Chỉ trả lời dựa trên sản phẩm trong kho
        try:
            tra_loi = engine.chat(
                user_message,
                context,
                product_context=product_context,
                history=lich_su_text
            )
        except Exception as e:
            tra_loi = f"Xin lỗi, tôi gặp lỗi kỹ thuật: {str(e)[:100]}"

    if any(kw in user_message.lower() for kw in ['thoát', 'bye', 'goodbye', 'quit', 'tạm biệt']):
        tra_loi = "Cảm ơn bạn đã sử dụng dịch vụ ABC Trading! Hẹn gặp lại. 👋"
    
    return tra_loi
