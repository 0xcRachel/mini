"""
memory.py
Quản lý bộ nhớ hội thoại -- lưu mỗi lượt hỏi/đáp vào MySQL.
Hỗ trợ: nhớ tên user, lịch sử SP đã xem, ngữ cảnh hội thoại.
"""

import mysql.connector
from datetime import datetime

DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "",
    "database": "abc_trading",
    "charset":  "utf8mb4",
}


class Memory:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context: dict = {
            "buoc"               : "chao_hoi",
            "nhanh"              : None,
            "san_pham_dang_xem"  : None,
            "danh_sach_hien_tai" : [],
            "don_hang"           : {},
            "ten_user"           : None,         # Nhớ tên người dùng
            "sp_da_xem"          : [],           # Lịch sử SP đã xem (tối đa 10)
        }
        self.history: list[dict] = []
        self._conn  = None
        self._cur   = None
        self._ket_noi()
        self._tao_bang()

    def _ket_noi(self):
        try:
            self._conn = mysql.connector.connect(**DB_CONFIG)
            self._cur  = self._conn.cursor(dictionary=True)
        except mysql.connector.Error as e:
            print(f"[Memory] Không kết nối được MySQL: {e}")
            self._conn = None

    def _tao_bang(self):
        if not self._conn:
            return
        self._cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id         INT AUTO_INCREMENT PRIMARY KEY,
                session_id VARCHAR(100),
                role       VARCHAR(20),
                content    TEXT,
                buoc       VARCHAR(100),
                nhanh      VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        self._conn.commit()

    def luu(self, role: str, content: str):
        luot = {
            "role"   : role,
            "content": content,
            "time"   : datetime.now().strftime("%H:%M:%S"),
        }
        self.history.append(luot)

        if self._conn:
            try:
                self._cur.execute(
                    """INSERT INTO conversations
                       (session_id, role, content, buoc, nhanh)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (
                        self.session_id,
                        role,
                        content,
                        self.context.get("buoc"),
                        self.context.get("nhanh"),
                    ),
                )
                self._conn.commit()
            except mysql.connector.Error:
                pass

    def cap_nhat_context(self, **kwargs):
        self.context.update(kwargs)

    def ghi_nho_sp(self, ten_sp: str):
        """Ghi nhớ SP đã xem vào lịch sử (không trùng, tối đa 10)."""
        da_xem = self.context.get("sp_da_xem", [])
        if ten_sp not in da_xem:
            da_xem.append(ten_sp)
            if len(da_xem) > 10:
                da_xem = da_xem[-10:]
            self.context["sp_da_xem"] = da_xem

    def sp_cuoi_cung(self) -> str | None:
        """Trả về SP cuối cùng đã xem."""
        da_xem = self.context.get("sp_da_xem", [])
        return da_xem[-1] if da_xem else None

    def reset_context(self):
        ten = self.context.get("ten_user")
        da_xem = self.context.get("sp_da_xem", [])
        self.context = {
            "buoc"               : "chao_hoi",
            "nhanh"              : None,
            "san_pham_dang_xem"  : None,
            "danh_sach_hien_tai" : [],
            "don_hang"           : {},
            "ten_user"           : ten,       # GIỮ LẠI tên user
            "sp_da_xem"          : da_xem,    # GIỮ LẠI lịch sử SP
        }

    def lay_lich_su_session(self) -> list[dict]:
        if not self._conn:
            return self.history
        self._cur.execute(
            "SELECT role, content, buoc, created_at FROM conversations WHERE session_id=%s ORDER BY id",
            (self.session_id,),
        )
        return self._cur.fetchall()

    def cau_hoi_truoc(self) -> str | None:
        for luot in reversed(self.history):
            if luot["role"] == "user":
                return luot["content"]
        return None

    def lay_lich_su(self, limit: int = 10) -> list[dict]:
        """Lấy lịch sử hội thoại gần nhất (mặc định 10 lần tương tác)."""
        if len(self.history) <= limit:
            return self.history
        return self.history[-limit:]

    def dong(self):
        if self._conn:
            self._cur.close()
            self._conn.close()
