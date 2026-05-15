"""
logic.py (NEW - AI-INTENT VERSION)
Chatbot logic - AI-driven routing and Database-first approach
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
    """Trích tên người dùng"""
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

def xu_ly(user_message: str, mem: Memory) -> str:
    """
    XỬ LÝ TIN NHẮN NÂNG CAO - AI INTENT ROUTING
    """
    engine = _get_engine()
    
    # Lấy lịch sử hội thoại
    lichsu = mem.lay_lich_su(limit=5)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in lichsu])
    
    # 1. PHÂN LOẠI Ý ĐỊNH BẰNG AI
    analysis = engine.classify_intent(user_message, history=history_text)
    intent = analysis.get("intent", "SEARCH")
    keywords_list = analysis.get("keywords", [])
    keywords = " ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)
    
    # Cập nhật tên user nếu có
    ten_user = _trich_ten(user_message)
    if ten_user:
        mem.cap_nhat_context(ten_user=ten_user)
    context = mem.context.copy()

    # 2. XỬ LÝ THEO Ý ĐỊNH (INTENT ROUTING)
    
    # A. CHÀO HỎI & TÁN GẪU
    if intent == "GREETING" or intent == "CHITCHAT":
        return engine.chat_general(user_message, context, history=history_text)

    # B. CÂU HỎI NGOÀI LỀ (Thời tiết, kiến thức chung...)
    if intent == "OUT_OF_SCOPE":
        return engine.chat_general(user_message, context, history=history_text)

    # C. HỎI ĐÁP FAQ (Bảo hành, Ship, Địa chỉ...)
    if intent == "FAQ":
        search_query = keywords if keywords else user_message
        faqs = engine.search_faq(search_query, limit=3)
        if faqs:
            faq_text = "\n".join([f"Q: {f['question']}\nA: {f['answer']}" for f in faqs])
            prompt_faq = f"Dựa trên thông tin FAQ này: {faq_text}, hãy trả lời câu hỏi của khách: {user_message}"
            return engine.chat_general(prompt_faq, context, history=history_text)
        return engine.chat_general(user_message, context, history=history_text)

    # D. KIỂM TRA ĐƠN HÀNG (MOCK)
    if intent == "ORDER_CHECK":
        return "Dạ, mình có thể giúp bạn kiểm tra đơn hàng. Bạn vui lòng cung cấp **Mã đơn hàng** (ví dụ: ABC-12345) để mình tra cứu trên hệ thống nhé!"

    # E. TÌM KIẾM SẢN PHẨM (MẶC ĐỊNH & SEARCH INTENT)
    search_term = keywords if keywords else user_message
    products = engine.search_product(search_term, limit=10)
    
    # Fallback nếu không thấy sản phẩm bằng từ khóa AI
    if not products:
        products = engine.search_product(user_message, limit=5)

    # Ghi nhớ sản phẩm vào memory nếu có
    if products:
        mem.ghi_nho_sp(products[0]['name'])

    # Format context sản phẩm cho LLM
    product_context = ""
    if products:
        product_context = "\n📦 DANH SÁCH SẢN PHẨM PHÙ HỢP:\n"
        for i, p in enumerate(products, 1):
            product_context += f"{i}. {p['name']} - Giá: {p['price']:,}đ - {'Còn hàng' if p['stock']>0 else 'Hết hàng'} ({p['stock']} cái)\n"
            product_context += f"   Mô tả: {p['description'][:120]}...\n"
    else:
        product_context = "Hiện tại cửa hàng không có sản phẩm nào phù hợp với yêu cầu này."

    # Trả lời bằng Strict Chat (Chỉ tư vấn sản phẩm thực)
    return engine.chat(user_message, context, product_context=product_context, history=history_text)
