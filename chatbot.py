import uuid
import os
from flask import Flask, request, jsonify, render_template
from memory import Memory
from logic import xu_ly
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()

app = Flask(__name__)

# Lưu trữ sessions (giản lược để quản lý state)
sessions = {}

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = Memory(session_id)
    return sessions[session_id]

@app.route('/')
def home():
    # Kiểm tra GROQ_API_KEY
    if not os.getenv("GROQ_API_KEY"):
        return "⚠️  Lỗi: Chưa thiết lập GROQ_API_KEY. Vui lòng kiểm tra lại file .env hoặc biến môi trường."
    return render_template('index.html')

@app.route('/products', methods=['GET'])
def get_products():
    from logic import _get_engine
    engine = _get_engine()
    products = engine._lay_danh_sach_san_pham(limit=8)
    return jsonify(products)

@app.route('/init', methods=['GET'])
def init_chat():
    session_id = str(uuid.uuid4())[:8]
    mem = get_session(session_id)
    
    loi_chao = (
        "Xin chào! 👋 Tôi là trợ lý ảo của ABC Trading.\n"
        "Mình sẽ giúp bạn tìm kiếm sản phẩm, tư vấn, và hỗ trợ đặt hàng.\n"
        "\n"
        "Bạn cần mình giúp gì hôm nay?"
    )
    mem.luu("bot", loi_chao)
    
    return jsonify({
        "session_id": session_id,
        "response": loi_chao
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # Lấy session đầu tiên (vì test local) hoặc tạo mới
    if not sessions:
        session_id = str(uuid.uuid4())[:8]
    else:
        session_id = list(sessions.keys())[-1] # Lấy session gần nhất
        
    mem = get_session(session_id)
    
    # Lưu câu hỏi của user
    mem.luu("user", user_input)
    
    # Xử lý và lấy câu trả lời
    try:
        tra_loi = xu_ly(user_input, mem)
        # Lưu câu trả lời của bot
        mem.luu("bot", tra_loi)
        return jsonify({"response": tra_loi, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    global sessions
    # Đóng tất cả connections đang mở (nếu cần thiết) trước khi clear
    for sid, mem in sessions.items():
        try:
            mem.dong()
        except:
            pass
    sessions.clear()
    return jsonify({"status": "success"})

if __name__ == "__main__":
    print("Khoi dong may chu giao dien Web tai http://127.0.0.1:5000")
    print("Mo trinh duyet va truy cap link tren de tro chuyen voi bot.")
    app.run(debug=True, use_reloader=False, port=5000)
