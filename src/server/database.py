import sqlite3
import os
import hashlib
import re
import random
from datetime import datetime, timedelta
from contextlib import contextmanager

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "chat_database.db")

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with fixed salt."""
    salt = "cnpm_nhom5_chat_salt_"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Kiểm tra mật khẩu: tối thiểu 6 ký tự, gồm chữ hoa, chữ thường, số và ký tự đặc biệt."""
    if len(password) < 6:
        return False, "Mật khẩu phải có độ dài tối thiểu từ 6 ký tự trở lên!"
    if not re.search(r"[A-Z]", password):
        return False, "Mật khẩu phải chứa ít nhất 1 chữ cái in hoa (A-Z)!"
    if not re.search(r"[a-z]", password):
        return False, "Mật khẩu phải chứa ít nhất 1 chữ cái in thường (a-z)!"
    if not re.search(r"[0-9]", password):
        return False, "Mật khẩu phải chứa ít nhất 1 chữ số (0-9)!"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]", password):
        return False, "Mật khẩu phải chứa ít nhất 1 ký tự đặc biệt (!@#$%^&*...)!"
    return True, ""

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def generate_random_user_id(self, cursor) -> int:
        """Tạo mã ID ngẫu nhiên gồm 10 chữ số (từ 1,000,000,000 đến 9,999,999,999) và không trùng lặp."""
        while True:
            new_id = random.randint(1000000000, 9999999999)
            cursor.execute("SELECT id FROM users WHERE id = ?", (new_id,))
            if not cursor.fetchone():
                return new_id

    def init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Bảng Người dùng (ID là dãy số ngẫu nhiên gồm 10 chữ số bảo mật)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                avatar_color TEXT DEFAULT '#2563EB',
                is_online INTEGER DEFAULT 0,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)

            # 2. Bảng Bạn bè
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'accepted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, friend_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (friend_id) REFERENCES users(id)
            )
            """)

            # 3. Bảng Cuộc hội thoại (1-1 hoặc Nhóm)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL, -- 'direct' hoặc 'group'
                name TEXT,          -- Tên nhóm nếu là group
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
            """)

            # 4. Bảng Thành viên trong hội thoại
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member', -- 'admin', 'member'
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(conversation_id, user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)

            # 5. Bảng Tệp tin đính kèm
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_name TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT,
                uploader_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploader_id) REFERENCES users(id)
            )
            """)

            # 6. Bảng Tin nhắn
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message_type TEXT DEFAULT 'text', -- 'text', 'image', 'file'
                content TEXT,
                file_id INTEGER,
                is_deleted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
            """)

            # Tự động thêm cột is_deleted và reply_to_id vào CSDL cũ nếu chưa có
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN is_deleted INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE messages ADD COLUMN reply_to_id INTEGER DEFAULT NULL")
            except Exception:
                pass

            # 7. Bảng Chặn người dùng (Block / Unblock)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocked_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                blocked_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, blocked_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (blocked_id) REFERENCES users(id)
            )
            """)

            # 8. Bảng Cảm xúc tin nhắn (Reactions: ❤️, 👍, 😂, 😮, 😢, 😡)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, user_id),
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)

            # 9. Bảng Tin nhắn ghim (Pinned Message theo từng cuộc trò chuyện)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS pinned_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL UNIQUE,
                message_id INTEGER NOT NULL,
                pinned_by INTEGER NOT NULL,
                pinned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
                FOREIGN KEY (pinned_by) REFERENCES users(id)
            )
            """)
            conn.commit()

            # Migration: Add pin_code, avatar_url, phone_number, is_phone_verified to users table if not exists
            for col_def in [
                "pin_code TEXT",
                "avatar_url TEXT",
                "phone_number TEXT",
                "is_phone_verified INTEGER DEFAULT 0"
            ]:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_def}")
                    conn.commit()
                except Exception:
                    pass

            # 10. Bảng Lưu mã OTP xác thực số điện thoại
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS phone_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                phone_number TEXT NOT NULL,
                otp_code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                is_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            conn.commit()

            # 11. Tự động nạp tài khoản mẫu của nhóm nếu cơ sở dữ liệu mới tinh (Seed Data)
            cursor.execute("SELECT COUNT(*) as count FROM users")
            row = cursor.fetchone()
            if row and row["count"] == 0:
                seed_members = [
                    (1000000001, "sondeptrai", "Son123@", "Vũ Duy Thái Sơn", "#2563EB"),
                    (1000000002, "dcmmm", "Son123@", "Vũ Duy Thái Sơn", "#2563EB"),
                    (1000000003, "tam_123", "Tam_123", "Phạm Đức Tâm", "#7C3AED"),
                    (1000000004, "manh_vy", "Manh123@", "Vy Thế Mạnh", "#059669"),
                    (1000000005, "dan_vu", "Dan123@", "Vũ Minh Dân", "#D97706"),
                    (1000000006, "huu_long", "Huu123@", "Long Đức Hữu", "#DC2626"),
                ]
                for uid, uname, pwd, fname, color in seed_members:
                    pwd_h = hash_password(pwd)
                    cursor.execute("""
                        INSERT OR IGNORE INTO users (id, username, password_hash, full_name, avatar_color)
                        VALUES (?, ?, ?, ?, ?)
                    """, (uid, uname, pwd_h, fname, color))

                # Tạo nhóm chat chung của Nhóm 21
                cursor.execute("""
                    INSERT INTO conversations (type, name, created_by)
                    VALUES ('group', 'Nhóm 21 - Đồ Án CNPM', 1000000001)
                """)
                group_id = cursor.lastrowid
                for uid, _, _, _, _ in seed_members:
                    cursor.execute("""
                        INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, role)
                        VALUES (?, ?, 'member')
                    """, (group_id, uid))

                # Kết bạn chéo giữa tất cả các thành viên (status = 'accepted')
                member_ids = [m[0] for m in seed_members]
                for i in range(len(member_ids)):
                    for j in range(i + 1, len(member_ids)):
                        u1, u2 = member_ids[i], member_ids[j]
                        cursor.execute("""
                            INSERT OR IGNORE INTO friends (user_id, friend_id, status)
                            VALUES (?, ?, 'accepted')
                        """, (u1, u2))

                conn.commit()

    # --- User APIs ---
    def register_user(self, username, password, full_name):
        username = username.strip().lower().lstrip("@")
        full_name = full_name.strip()
        if not username or not password or not full_name:
            return {"success": False, "message": "Vui lòng nhập đầy đủ thông tin!"}

        # Kiểm tra tính hợp lệ của username (chuẩn như Telegram: a-z, 0-9, dấu gạch dưới, dài từ 3 - 20 ký tự)
        if len(username) < 3 or len(username) > 20:
            return {"success": False, "message": "Username phải có độ dài từ 3 đến 20 ký tự!"}
        if not re.match(r"^[a-z0-9_]+$", username):
            return {"success": False, "message": "Username chỉ được gồm chữ cái thường, số và dấu gạch dưới (_), không dấu, không khoảng trắng!"}

        ok, msg = validate_password_strength(password)
        if not ok:
            return {"success": False, "message": msg}

        colors = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2", "#4F46E5"]
        avatar_color = colors[len(username) % len(colors)]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "message": f"Username @{username} đã có người sử dụng! Vui lòng chọn username khác."}

            pwd_hash = hash_password(password)
            new_id = self.generate_random_user_id(cursor)

            cursor.execute("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_color)
                VALUES (?, ?, ?, ?, ?)
            """, (new_id, username, pwd_hash, full_name, avatar_color))

            # Tự động thêm vào nhóm chat chung nếu có
            cursor.execute("SELECT id FROM conversations WHERE name = 'Nhóm 05 - Đồ Án CNPM'")
            grp = cursor.fetchone()
            if grp:
                cursor.execute("""
                    INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, 'member')
                """, (grp["id"], new_id))

            conn.commit()
            return {"success": True, "user": {"id": new_id, "username": username, "full_name": full_name, "avatar_color": avatar_color}}

    def authenticate_user(self, username, password):
        username = username.strip().lower().lstrip("@")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            pwd_hash = hash_password(password)
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, avatar_url, phone_number, is_phone_verified, is_online, pin_code
                FROM users
                WHERE username = ? AND password_hash = ?
            """, (username, pwd_hash))
            row = cursor.fetchone()
            if row:
                return {"success": True, "user": dict(row)}
            return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu!"}

    def reset_all_online_status(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET is_online = 0")
            conn.commit()

    def set_online_status(self, user_id, is_online: bool):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            status_val = 1 if is_online else 0
            cursor.execute("""
                UPDATE users SET is_online = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?
            """, (status_val, user_id))
            conn.commit()

    def get_user_by_id(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, avatar_url, phone_number, is_phone_verified, is_online, last_seen, pin_code
                FROM users WHERE id = ?
            """, (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_user_profile(self, user_id, full_name=None, avatar_color=None, new_password=None, pin_code=None, avatar_url=None, phone_number=None, is_phone_verified=None):
        """Cập nhật thông tin hồ sơ cá nhân, ảnh đại diện, số điện thoại và mã PIN."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            if full_name and full_name.strip():
                updates.append("full_name = ?")
                params.append(full_name.strip())
            if avatar_color and avatar_color.strip():
                updates.append("avatar_color = ?")
                params.append(avatar_color.strip())
            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(avatar_url.strip() if avatar_url.strip() else None)
            if phone_number is not None:
                updates.append("phone_number = ?")
                params.append(phone_number.strip() if phone_number.strip() else None)
            if is_phone_verified is not None:
                updates.append("is_phone_verified = ?")
                params.append(1 if is_phone_verified else 0)
            if new_password and new_password.strip():
                is_valid, msg = validate_password_strength(new_password)
                if not is_valid:
                    return {"success": False, "error": msg}
                salt = bcrypt.gensalt()
                pw_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
                updates.append("password_hash = ?")
                params.append(pw_hash)
            if pin_code is not None:
                pin_str = str(pin_code).strip()
                if pin_str:
                    if not pin_str.isdigit() or len(pin_str) != 4:
                        return {"success": False, "error": "Mã PIN phải bao gồm đúng 4 chữ số (0-9)!"}
                    updates.append("pin_code = ?")
                    params.append(pin_str)
                else:
                    updates.append("pin_code = NULL")

            if not updates:
                return {"success": False, "error": "Không có thông tin thay đổi!"}

            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()

            user = self.get_user_by_id(user_id)
            return {"success": True, "user": user}

    def create_phone_otp(self, user_id, phone_number):
        """Tạo mã OTP 6 số xác thực số điện thoại và lưu vào CSDL với thời hạn 5 phút."""
        clean_phone = re.sub(r'[\s\-\(\)]', '', str(phone_number or '').strip())
        if not clean_phone or len(clean_phone) < 9 or len(clean_phone) > 15:
            return {"success": False, "error": "Số điện thoại không hợp lệ (từ 9 đến 15 chữ số)!"}

        # Sinh mã OTP ngẫu nhiên 6 chữ số
        otp_code = f"{random.randint(100000, 999999)}"
        # Hạn 5 phút
        expires_at = (datetime.utcnow() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Hủy các OTP chưa dùng trước đó cho user này
            cursor.execute("""
                UPDATE phone_verifications SET is_used = 1
                WHERE user_id = ? AND is_used = 0
            """, (user_id,))
            cursor.execute("""
                INSERT INTO phone_verifications (user_id, phone_number, otp_code, expires_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, clean_phone, otp_code, expires_at))
            conn.commit()

        print(f"[OTP] Generated OTP for user {user_id} ({clean_phone}): {otp_code} (expires at {expires_at})")
        return {
            "success": True,
            "otp_code": otp_code,
            "phone_number": clean_phone,
            "expires_in": 300,
            "message": f"Mã OTP đã được tạo thành công cho {clean_phone}."
        }

    def verify_phone_otp(self, user_id, phone_number, otp_code):
        """Xác thực mã OTP từ CSDL và đánh dấu số điện thoại đã xác minh."""
        clean_phone = re.sub(r'[\s\-\(\)]', '', str(phone_number or '').strip())
        clean_otp = str(otp_code or '').strip()

        if not clean_phone or not clean_otp:
            return {"success": False, "error": "Thiếu số điện thoại hoặc mã OTP!"}

        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, otp_code, expires_at, is_used
                FROM phone_verifications
                WHERE user_id = ? AND phone_number = ? AND is_used = 0
                ORDER BY id DESC LIMIT 1
            """, (user_id, clean_phone))
            record = cursor.fetchone()

            if not record:
                return {"success": False, "error": "Không tìm thấy yêu cầu xác minh nào! Vui lòng nhấn gửi lại mã OTP."}

            if record["otp_code"] != clean_otp:
                return {"success": False, "error": "Mã OTP không chính xác! Vui lòng kiểm tra lại."}

            if record["expires_at"] < now_str:
                return {"success": False, "error": "Mã OTP đã hết hạn (chỉ có hiệu lực trong 5 phút)! Vui lòng yêu cầu mã mới."}

            # Đánh dấu mã đã dùng
            cursor.execute("UPDATE phone_verifications SET is_used = 1 WHERE id = ?", (record["id"],))

            # Cập nhật số điện thoại và trạng thái đã xác minh cho user
            cursor.execute("""
                UPDATE users SET phone_number = ?, is_phone_verified = 1 WHERE id = ?
            """, (clean_phone, user_id))
            conn.commit()

            user = self.get_user_by_id(user_id)
            return {"success": True, "message": "Xác minh số điện thoại thành công!", "user": user}

    def search_users(self, keyword, current_user_id=None):
        keyword = (keyword or "").strip()
        if not keyword:
            return []  # Bảo mật: Không bao giờ trả về danh sách nếu để trống từ khóa!

        curr_id = current_user_id if current_user_id is not None else 0

        # Tự động loại bỏ ký tự @ hoặc # ở đầu (hỗ trợ người dùng gõ @username hoặc #id)
        clean_keyword = keyword.lstrip("@#").strip()
        if not clean_keyword:
            return []

        import unicodedata
        def _strip_accents(s: str) -> str:
            if not s:
                return ""
            s = s.replace("đ", "d").replace("Đ", "D")
            return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

        search_normalized = _strip_accents(clean_keyword)
        search_lower = clean_keyword.lower()
        search_digits = re.sub(r'[^0-9]', '', clean_keyword)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Tìm theo ID cụ thể nếu là số ngắn (ví dụ: "#5", "id:5")
            id_query = clean_keyword.replace("id:", "").strip()
            if id_query.isdigit() and len(id_query) <= 6:
                cursor.execute("""
                    SELECT id, username, full_name, avatar_color, avatar_url, phone_number, is_phone_verified, is_online
                    FROM users
                    WHERE (id = ? OR CAST(id AS TEXT) LIKE ?) AND id != ?
                """, (int(id_query), f"{id_query}%", curr_id))
                res = [dict(r) for r in cursor.fetchall()]
                if res:
                    return res

            # 2. Tìm kiếm thông minh hỗ trợ cả số điện thoại, tiếng Việt có dấu, không dấu, username và họ tên
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, avatar_url, phone_number, is_phone_verified, is_online
                FROM users
                WHERE id != ?
            """, (curr_id,))
            all_users = [dict(r) for r in cursor.fetchall()]

            matched = []
            for u in all_users:
                uname = (u.get("username") or "").lower()
                fname = (u.get("full_name") or "").lower()
                uname_norm = _strip_accents(uname)
                fname_norm = _strip_accents(fname)
                uid_str = str(u.get("id"))
                phone = (u.get("phone_number") or "").strip()
                phone_digits = re.sub(r'[^0-9]', '', phone)

                # Kiểm tra khớp:
                # - Số điện thoại chứa dãy số tìm kiếm (nếu tìm kiếm có ít nhất 3 chữ số)
                # - ID chứa từ khóa
                # - Username khớp hoàn toàn hoặc chứa từ khóa (cả có dấu và không dấu)
                # - Họ tên chứa từ khóa (cả có dấu và không dấu)
                is_phone_match = bool(search_digits and len(search_digits) >= 3 and phone_digits and (search_digits in phone_digits))
                if (is_phone_match or
                    search_lower == uname or
                    search_normalized in uname_norm or
                    search_lower in fname or
                    search_normalized in fname_norm or
                    search_lower in uid_str):
                    matched.append(u)
                    if len(matched) >= 15:
                        break

            return matched

    # --- Danh bạ bạn bè & Lời mời kết bạn (Friend Request & Approval APIs) ---
    def send_friend_request(self, user_id, friend_id):
        try:
            user_id = int(user_id)
            friend_id = int(friend_id)
        except Exception:
            pass
        if user_id == friend_id:
            return {"success": False, "message": "Không thể kết bạn với chính mình!"}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name, avatar_color, is_online FROM users WHERE id = ?", (friend_id,))
            target = cursor.fetchone()
            if not target:
                return {"success": False, "message": "Người dùng không tồn tại!"}

            # Kiểm tra xem đã là bạn bè chưa (cả 2 chiều)
            cursor.execute("SELECT status FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)", (user_id, friend_id, friend_id, user_id))
            existing_rows = cursor.fetchall()
            for r in existing_rows:
                if r["status"] == "accepted":
                    # Đảm bảo đồng bộ cả 2 chiều thành accepted
                    cursor.execute("""
                        INSERT INTO friends (user_id, friend_id, status)
                        VALUES (?, ?, 'accepted')
                        ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
                    """, (user_id, friend_id))
                    cursor.execute("""
                        INSERT INTO friends (user_id, friend_id, status)
                        VALUES (?, ?, 'accepted')
                        ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
                    """, (friend_id, user_id))
                    conn.commit()
                    return {"success": False, "message": f"Bạn và @{target['username']} đã là bạn bè của nhau rồi!"}

            # Kiểm tra xem đối phương có đang gửi lời mời chờ mình duyệt không
            cursor.execute("SELECT status FROM friends WHERE user_id = ? AND friend_id = ?", (friend_id, user_id))
            row2 = cursor.fetchone()
            if row2 and row2["status"] == "pending":
                # Đối phương đã mời trước -> Tự động chấp nhận luôn cả 2 chiều!
                cursor.execute("""
                    INSERT INTO friends (user_id, friend_id, status)
                    VALUES (?, ?, 'accepted')
                    ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
                """, (friend_id, user_id))
                cursor.execute("""
                    INSERT INTO friends (user_id, friend_id, status)
                    VALUES (?, ?, 'accepted')
                    ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
                """, (user_id, friend_id))
                conn.commit()
                return {
                    "success": True,
                    "accepted": True,
                    "message": f"Đã chấp nhận lời mời từ @{target['username']}! Hai bạn đã trở thành bạn bè.",
                    "friend": dict(target)
                }

            # Nếu chưa có -> Tạo lời mời kết bạn mới với trạng thái 'pending'
            cursor.execute("""
                INSERT INTO friends (user_id, friend_id, status)
                VALUES (?, ?, 'pending')
                ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'pending'
            """, (user_id, friend_id))
            conn.commit()
            return {
                "success": True,
                "accepted": False,
                "message": f"Đã gửi lời mời kết bạn tới @{target['username']}! Đang chờ đối phương đồng ý.",
                "target": dict(target)
            }

    def accept_friend_request(self, user_id, requester_id):
        """Chấp nhận lời mời kết bạn từ requester_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                user_id = int(user_id)
                requester_id = int(requester_id)
            except Exception:
                pass
            cursor.execute("SELECT id, username, full_name, avatar_color, is_online FROM users WHERE id = ?", (requester_id,))
            requester = cursor.fetchone()
            if not requester:
                return {"success": False, "message": "Người dùng không tồn tại!"}

            # Đồng bộ cả 2 chiều thành accepted
            cursor.execute("""
                INSERT INTO friends (user_id, friend_id, status)
                VALUES (?, ?, 'accepted')
                ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
            """, (requester_id, user_id))

            cursor.execute("""
                INSERT INTO friends (user_id, friend_id, status)
                VALUES (?, ?, 'accepted')
                ON CONFLICT(user_id, friend_id) DO UPDATE SET status = 'accepted'
            """, (user_id, requester_id))
            conn.commit()
            return {"success": True, "message": f"Đã đồng ý kết bạn với @{requester['username']}!", "friend": dict(requester)}

    def reject_friend_request(self, user_id, requester_id):
        """Từ chối lời mời kết bạn từ requester_id."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM friends WHERE user_id = ? AND friend_id = ? AND status = 'pending'", (requester_id, user_id))
            conn.commit()
            return {"success": True, "message": "Đã từ chối lời mời kết bạn."}

    def remove_friend(self, user_id, friend_id):
        """Hủy kết bạn (xóa cả 2 chiều)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                           (user_id, friend_id, friend_id, user_id))
            conn.commit()
            return {"success": True, "message": "Đã xóa người này khỏi Danh bạ bạn bè."}

    def get_friendship_status(self, user_id, other_id):
        """Kiểm tra trạng thái quan hệ bạn bè giữa 2 user: 'friends', 'sent_pending', 'received_pending', 'none'"""
        if user_id == other_id:
            return "self"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 1. Nếu bất kỳ chiều nào đã accepted -> đã là bạn bè
            cursor.execute("SELECT status FROM friends WHERE (user_id = ? AND friend_id = ?) OR (user_id = ? AND friend_id = ?)",
                           (user_id, other_id, other_id, user_id))
            rows = cursor.fetchall()
            for r in rows:
                if r["status"] == "accepted":
                    return "friends"

            # 2. Chiều mình gửi đang pending
            cursor.execute("SELECT status FROM friends WHERE user_id = ? AND friend_id = ?", (user_id, other_id))
            my_rel = cursor.fetchone()
            if my_rel and my_rel["status"] == "pending":
                return "sent_pending"

            # 3. Chiều đối phương gửi đang pending chờ mình duyệt
            cursor.execute("SELECT status FROM friends WHERE user_id = ? AND friend_id = ?", (other_id, user_id))
            other_rel = cursor.fetchone()
            if other_rel and other_rel["status"] == "pending":
                return "received_pending"

            return "none"

    def is_friend(self, user_id, friend_id):
        return self.get_friendship_status(user_id, friend_id) == "friends"

    def get_friends(self, user_id):
        """Lấy danh sách bạn bè chính thức (status = 'accepted') hai chiều."""
        try:
            user_id = int(user_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.full_name, u.avatar_color, u.avatar_url, u.phone_number, u.is_phone_verified, u.is_online, u.last_seen
                FROM users u
                JOIN friends f ON (
                    (f.user_id = ? AND f.friend_id = u.id AND f.status = 'accepted')
                    OR
                    (f.friend_id = ? AND f.user_id = u.id AND f.status = 'accepted')
                )
                WHERE u.id != ?
                ORDER BY u.full_name ASC
            """, (user_id, user_id, user_id))
            return [dict(r) for r in cursor.fetchall()]

    def get_pending_requests(self, user_id):
        """Lấy danh sách các lời mời kết bạn mà người khác gửi đến cho user này chờ duyệt."""
        try:
            user_id = int(user_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.avatar_color, u.avatar_url, u.phone_number, u.is_phone_verified, u.is_online, f.created_at
                FROM friends f
                JOIN users u ON f.user_id = u.id
                WHERE f.friend_id = ? AND f.status = 'pending'
                ORDER BY f.created_at DESC
            """, (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_sent_requests(self, user_id):
        """Lấy danh sách ID người dùng mà user này đã gửi lời mời kết bạn đi và đang chờ duyệt."""
        try:
            user_id = int(user_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.friend_id as id
                FROM friends f
                WHERE f.user_id = ? AND f.status = 'pending'
            """, (user_id,))
            return [r["id"] for r in cursor.fetchall()]

    # --- Conversations APIs ---
    def get_direct_conversation(self, user1_id, user2_id):
        """Lấy hoặc tạo cuộc trò chuyện 1-1 giữa 2 người dùng."""
        try:
            user1_id = int(user1_id)
            user2_id = int(user2_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id FROM conversations c
                JOIN conversation_members m1 ON c.id = m1.conversation_id AND m1.user_id = ?
                JOIN conversation_members m2 ON c.id = m2.conversation_id AND m2.user_id = ?
                WHERE c.type = 'direct'
            """, (user1_id, user2_id))
            row = cursor.fetchone()
            if row:
                return row["id"]

            # Tạo mới
            cursor.execute("""
                INSERT INTO conversations (type, created_by) VALUES ('direct', ?)
            """, (user1_id,))
            conv_id = cursor.lastrowid
            cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user1_id))
            cursor.execute("INSERT INTO conversation_members (conversation_id, user_id) VALUES (?, ?)", (conv_id, user2_id))
            conn.commit()
            return conv_id

    def create_group_conversation(self, name, creator_id, member_ids):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (type, name, created_by)
                VALUES ('group', ?, ?)
            """, (name, creator_id))
            conv_id = cursor.lastrowid

            all_members = set([creator_id] + member_ids)
            for uid in all_members:
                role = 'admin' if uid == creator_id else 'member'
                cursor.execute("""
                    INSERT INTO conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, ?)
                """, (conv_id, uid, role))
            conn.commit()
            return conv_id

    def get_user_conversations(self, user_id):
        """Lấy danh sách các cuộc hội thoại (1-1 và Nhóm) của người dùng."""
        try:
            user_id = int(user_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.type, c.name, c.created_at
                FROM conversations c
                JOIN conversation_members m ON c.id = m.conversation_id
                WHERE m.user_id = ?
                ORDER BY c.created_at DESC
            """, (user_id,))
            conversations = [dict(r) for r in cursor.fetchall()]

            result = []
            for conv in conversations:
                conv_id = conv["id"]
                # Lấy tin nhắn cuối cùng
                cursor.execute("""
                    SELECT m.content, m.message_type, m.created_at, u.full_name as sender_name
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    WHERE m.conversation_id = ?
                    ORDER BY m.id DESC LIMIT 1
                """, (conv_id,))
                last_msg = cursor.fetchone()
                conv["last_message"] = dict(last_msg) if last_msg else None

                if conv["type"] == 'saved':
                    conv["title"] = "Cloud của tôi (Saved Messages)"
                    conv["avatar_color"] = "#8B5CF6"
                    conv["is_online"] = 1
                    conv["partner_id"] = user_id
                elif conv["type"] == 'direct':
                    # Tìm đối phương
                    cursor.execute("""
                        SELECT u.id, u.username, u.full_name, u.avatar_color, u.avatar_url, u.phone_number, u.is_phone_verified, u.is_online
                        FROM users u
                        JOIN conversation_members m ON u.id = m.user_id
                        WHERE m.conversation_id = ? AND u.id != ?
                    """, (conv_id, user_id))
                    partner = cursor.fetchone()
                    if partner:
                        conv["title"] = partner["full_name"]
                        conv["avatar_color"] = partner["avatar_color"]
                        conv["avatar_url"] = partner["avatar_url"]
                        conv["is_online"] = partner["is_online"]
                        conv["partner_id"] = partner["id"]
                        conv["partner_username"] = partner["username"]
                        conv["phone_number"] = partner["phone_number"]
                        conv["is_phone_verified"] = partner["is_phone_verified"]
                    else:
                        conv["title"] = "Người dùng"
                        conv["avatar_color"] = "#64748B"
                        conv["is_online"] = 0
                else:
                    conv["title"] = conv["name"] or "Nhóm trò chuyện"
                    conv["avatar_color"] = "#0EA5E9"
                    # Đếm số thành viên
                    cursor.execute("SELECT COUNT(*) as count FROM conversation_members WHERE conversation_id = ?", (conv_id,))
                    conv["member_count"] = cursor.fetchone()["count"]

                result.append(conv)
            return result

    def get_conversation_members(self, conversation_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.avatar_color, u.avatar_url, u.is_online, m.role
                FROM conversation_members m
                JOIN users u ON m.user_id = u.id
                WHERE m.conversation_id = ?
            """, (conversation_id,))
            return [dict(r) for r in cursor.fetchall()]

    # --- Message & File APIs ---
    def save_message(self, conversation_id, sender_id, message_type, content, file_id=None, reply_to_id=None):
        try:
            conversation_id = int(conversation_id)
            sender_id = int(sender_id)
            if reply_to_id is not None:
                reply_to_id = int(reply_to_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (conversation_id, sender_id, message_type, content, file_id, reply_to_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (conversation_id, sender_id, message_type, content, file_id, reply_to_id))
            msg_id = cursor.lastrowid
            conn.commit()

            # Lấy thông tin tin nhắn vừa lưu kèm thông tin người gửi & thông tin trích dẫn reply
            cursor.execute("""
                SELECT m.id, m.conversation_id, m.sender_id, m.message_type, m.message_type as msg_type, m.content,
                       m.file_id, m.is_deleted, m.created_at, m.reply_to_id,
                       u.full_name as sender_name, u.avatar_color, u.avatar_url,
                       f.original_name, f.original_name as file_name, f.file_size, f.file_type,
                       parent.content as reply_content, parent_user.full_name as reply_sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                LEFT JOIN files f ON m.file_id = f.id
                LEFT JOIN messages parent ON m.reply_to_id = parent.id
                LEFT JOIN users parent_user ON parent.sender_id = parent_user.id
                WHERE m.id = ?
            """, (msg_id,))
            row = cursor.fetchone()
            d = dict(row) if row else None
            if d:
                d["reactions"] = []
            return d

    def get_messages(self, conversation_id, limit=200):
        try:
            conversation_id = int(conversation_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM (
                    SELECT m.id, m.conversation_id, m.sender_id, m.message_type, m.message_type as msg_type, m.content,
                           m.file_id, m.is_deleted, m.created_at, m.reply_to_id,
                           u.full_name as sender_name, u.avatar_color, u.avatar_url,
                           f.original_name, f.original_name as file_name, f.file_size, f.file_type,
                           parent.content as reply_content, parent_user.full_name as reply_sender_name
                    FROM messages m
                    JOIN users u ON m.sender_id = u.id
                    LEFT JOIN files f ON m.file_id = f.id
                    LEFT JOIN messages parent ON m.reply_to_id = parent.id
                    LEFT JOIN users parent_user ON parent.sender_id = parent_user.id
                    WHERE m.conversation_id = ?
                    ORDER BY m.id DESC
                    LIMIT ?
                ) sub
                ORDER BY sub.id ASC
            """, (conversation_id, limit))
            messages = [dict(r) for r in cursor.fetchall()]

            # Nạp danh sách cảm xúc (reactions) cho từng tin nhắn
            if messages:
                msg_ids = [m["id"] for m in messages]
                placeholders = ",".join("?" * len(msg_ids))
                sql = (
                    "SELECT mr.message_id, mr.reaction, mr.user_id, u.full_name "
                    "FROM message_reactions mr "
                    "JOIN users u ON mr.user_id = u.id "
                    "WHERE mr.message_id IN (" + placeholders + ")"  # nosec B608
                )
                cursor.execute(sql, msg_ids)
                all_rx = cursor.fetchall()
                rx_map = {}
                for r in all_rx:
                    mid = r["message_id"]
                    rx = r["reaction"]
                    if mid not in rx_map:
                        rx_map[mid] = {}
                    if rx not in rx_map[mid]:
                        rx_map[mid][rx] = {"reaction": rx, "count": 0, "users": []}
                    rx_map[mid][rx]["count"] += 1
                    rx_map[mid][rx]["users"].append({"id": r["user_id"], "name": r["full_name"]})

                for m in messages:
                    mid = m["id"]
                    m["reactions"] = list(rx_map.get(mid, {}).values())
            return messages

    def recall_message(self, message_id: int, user_id: int):
        """Thu hồi tin nhắn ở cả 2 phía (người gửi và người nhận)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT conversation_id, sender_id FROM messages WHERE id = ?", (message_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Tin nhắn không tồn tại!", None
            if row["sender_id"] != user_id:
                return False, "Bạn chỉ có thể thu hồi tin nhắn do chính mình gửi!", None

            cursor.execute("""
                UPDATE messages
                SET is_deleted = 1, content = 'Tin nhắn đã được thu hồi'
                WHERE id = ?
            """, (message_id,))
            conn.commit()
            return True, "Đã thu hồi tin nhắn thành công!", row["conversation_id"]

    def delete_conversation(self, conversation_id: int, user_id: int):
        """Xóa toàn bộ cuộc trò chuyện và lịch sử tin nhắn."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Xóa các cảm xúc liên kết với tin nhắn trong hội thoại
            cursor.execute("""
                DELETE FROM message_reactions
                WHERE message_id IN (SELECT id FROM messages WHERE conversation_id = ?)
            """, (conversation_id,))
            # Xóa các tin nhắn trong hội thoại
            cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
            # Xóa các thành viên
            cursor.execute("DELETE FROM conversation_members WHERE conversation_id = ?", (conversation_id,))
            # Xóa cuộc trò chuyện
            cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            conn.commit()
            return True

    # --- Block / Unblock User APIs ---
    def block_user(self, user_id: int, blocked_id: int):
        """Chặn một người dùng (không cho gửi tin nhắn hoặc kết bạn)."""
        if user_id == blocked_id:
            return False, "Không thể chặn chính mình!"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO blocked_users (user_id, blocked_id)
                VALUES (?, ?)
            """, (user_id, blocked_id))
            conn.commit()
            return True, "Đã chặn người dùng thành công!"

    def unblock_user(self, user_id: int, blocked_id: int):
        """Bỏ chặn người dùng."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM blocked_users
                WHERE user_id = ? AND blocked_id = ?
            """, (user_id, blocked_id))
            conn.commit()
            return True, "Đã bỏ chặn người dùng thành công!"

    def is_blocked(self, user_a: int, user_b: int) -> bool:
        """Kiểm tra xem giữa 2 user có ai đang chặn người kia không."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM blocked_users
                WHERE (user_id = ? AND blocked_id = ?) OR (user_id = ? AND blocked_id = ?)
            """, (user_a, user_b, user_b, user_a))
            return cursor.fetchone() is not None

    def is_user_blocked_by_me(self, user_id: int, target_id: int) -> bool:
        """Kiểm tra xem user_id có đang chặn target_id không."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM blocked_users
                WHERE user_id = ? AND blocked_id = ?
            """, (user_id, target_id))
            return cursor.fetchone() is not None

    def get_blocked_users(self, user_id: int):
        """Lấy danh sách các tài khoản mà user_id đã chặn."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT b.blocked_id, u.username, u.full_name, u.avatar_color, b.created_at
                FROM blocked_users b
                JOIN users u ON b.blocked_id = u.id
                WHERE b.user_id = ?
            """, (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def save_file_record(self, original_name, stored_path, file_size, file_type, uploader_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO files (original_name, stored_path, file_size, file_type, uploader_id)
                VALUES (?, ?, ?, ?, ?)
            """, (original_name, stored_path, file_size, file_type, uploader_id))
            file_id = cursor.lastrowid
            conn.commit()
            return file_id

    def get_file_record(self, file_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Reaction APIs ---
    def toggle_reaction(self, message_id: int, user_id: int, reaction: str):
        """Thêm, thay đổi hoặc gỡ cảm xúc (Reactions: ❤️, 👍, 😂, 😮, 😢, 😡) của tin nhắn."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reaction FROM message_reactions WHERE message_id = ? AND user_id = ?", (message_id, user_id))
            row = cursor.fetchone()
            if row:
                if row["reaction"] == reaction:
                    cursor.execute("DELETE FROM message_reactions WHERE message_id = ? AND user_id = ?", (message_id, user_id))
                else:
                    cursor.execute("UPDATE message_reactions SET reaction = ? WHERE message_id = ? AND user_id = ?", (reaction, message_id, user_id))
            else:
                cursor.execute("INSERT INTO message_reactions (message_id, user_id, reaction) VALUES (?, ?, ?)", (message_id, user_id, reaction))
            conn.commit()

            # Lấy conversation_id của tin nhắn này
            cursor.execute("SELECT conversation_id FROM messages WHERE id = ?", (message_id,))
            m_row = cursor.fetchone()
            conv_id = m_row["conversation_id"] if m_row else None

            return self.get_message_reactions(message_id), conv_id

    def get_message_reactions(self, message_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT mr.reaction, mr.user_id, u.full_name
                FROM message_reactions mr
                JOIN users u ON mr.user_id = u.id
                WHERE mr.message_id = ?
            """, (message_id,))
            rows = cursor.fetchall()
            grouped = {}
            for r in rows:
                rx = r["reaction"]
                if rx not in grouped:
                    grouped[rx] = {"reaction": rx, "count": 0, "users": []}
                grouped[rx]["count"] += 1
                grouped[rx]["users"].append({"id": r["user_id"], "name": r["full_name"]})
            return list(grouped.values())

    # --- Pinned Messages APIs ---
    def pin_message(self, conversation_id: int, message_id: int, user_id: int):
        """Ghim một tin nhắn trong cuộc hội thoại."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pinned_messages (conversation_id, message_id, pinned_by)
                VALUES (?, ?, ?)
                ON CONFLICT(conversation_id) DO UPDATE SET
                    message_id = excluded.message_id,
                    pinned_by = excluded.pinned_by,
                    pinned_at = CURRENT_TIMESTAMP
            """, (conversation_id, message_id, user_id))
            conn.commit()
            return self.get_pinned_message(conversation_id)

    def unpin_message(self, conversation_id: int):
        """Bỏ ghim tin nhắn của cuộc hội thoại."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pinned_messages WHERE conversation_id = ?", (conversation_id,))
            conn.commit()
            return True

    def get_pinned_message(self, conversation_id: int):
        """Lấy thông tin tin nhắn đang được ghim trong cuộc hội thoại."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.conversation_id, p.message_id as id, p.message_id, p.pinned_by, p.pinned_at,
                       m.content, m.message_type, u.full_name as sender_name
                FROM pinned_messages p
                JOIN messages m ON p.message_id = m.id
                JOIN users u ON m.sender_id = u.id
                WHERE p.conversation_id = ?
            """, (conversation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # --- Saved Messages (Cloud của tôi) ---
    def get_or_create_saved_conversation(self, user_id: int) -> int:
        """Lấy hoặc tự động tạo không gian 'Cloud của tôi (Saved Messages)' cho người dùng."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM conversations WHERE type = 'saved' AND created_by = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return row["id"]
            cursor.execute("""
                INSERT INTO conversations (type, name, created_by)
                VALUES ('saved', 'Cloud của tôi (Saved Messages)', ?)
            """, (user_id,))
            conv_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO conversation_members (conversation_id, user_id, role)
                VALUES (?, ?, 'admin')
            """, (conv_id, user_id))
            conn.commit()
            return conv_id


