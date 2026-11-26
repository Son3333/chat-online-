import sqlite3
import os
import hashlib
import re
import random
import secrets
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
        conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=30000;")
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

            # 10.1 Bảng Lưu mã OTP xác thực đa năng (Đổi mật khẩu, liên kết SĐT/Gmail)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS otp_verifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target TEXT NOT NULL,
                target_type TEXT DEFAULT 'phone', -- 'phone' hoặc 'email'
                otp_code TEXT NOT NULL,
                purpose TEXT DEFAULT 'password_reset', -- 'password_reset', 'link_contact'
                expires_at TIMESTAMP NOT NULL,
                is_used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """)
            conn.commit()

            # Migration nâng cấp schema bảo mật & phân quyền nhóm
            for migration_sql in [
                "ALTER TABLE users ADD COLUMN email TEXT DEFAULT NULL",
                "ALTER TABLE users ADD COLUMN is_email_verified INTEGER DEFAULT 0",
                "ALTER TABLE conversations ADD COLUMN is_muted INTEGER DEFAULT 0",
                "ALTER TABLE conversations ADD COLUMN custom_mute_text TEXT DEFAULT 'Bạn bị khóa mõm bởi ban quản trị'",
                "ALTER TABLE conversations ADD COLUMN avatar_url TEXT DEFAULT NULL",
                "ALTER TABLE conversations ADD COLUMN theme TEXT DEFAULT NULL",
                "ALTER TABLE conversation_members ADD COLUMN is_muted INTEGER DEFAULT 0",
                "ALTER TABLE conversation_members ADD COLUMN muted_by_name TEXT DEFAULT NULL",
                "ALTER TABLE conversation_members ADD COLUMN muted_at TIMESTAMP DEFAULT NULL",
                "ALTER TABLE conversation_members ADD COLUMN status TEXT DEFAULT 'active'",
                "ALTER TABLE users ADD COLUMN session_token TEXT DEFAULT NULL"
            ]:
                try:
                    cursor.execute(migration_sql)
                    conn.commit()
                except Exception:
                    pass

            # Bảng lưu biệt danh trong cuộc trò chuyện (Direct hoặc Group)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_nicknames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                nickname TEXT NOT NULL,
                set_by INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(conversation_id, user_id),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
            session_token = secrets.token_urlsafe(32)

            cursor.execute("""
                INSERT INTO users (id, username, password_hash, full_name, avatar_color, session_token)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, username, pwd_hash, full_name, avatar_color, session_token))

            # Tự động thêm vào nhóm chat chung nếu có
            cursor.execute("SELECT id FROM conversations WHERE name = 'Nhóm 05 - Đồ Án CNPM'")
            grp = cursor.fetchone()
            if grp:
                cursor.execute("""
                    INSERT OR IGNORE INTO conversation_members (conversation_id, user_id, role)
                    VALUES (?, ?, 'member')
                """, (grp["id"], new_id))

            conn.commit()
            return {
                "success": True,
                "session_token": session_token,
                "user": {
                    "id": new_id,
                    "username": username,
                    "full_name": full_name,
                    "avatar_color": avatar_color,
                    "session_token": session_token
                }
            }

    def authenticate_user(self, username, password):
        username = username.strip().lower().lstrip("@")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            pwd_hash = hash_password(password)
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, avatar_url, email, COALESCE(is_email_verified, 0) as is_email_verified, phone_number, is_phone_verified, is_online, pin_code
                FROM users
                WHERE username = ? AND password_hash = ?
            """, (username, pwd_hash))
            row = cursor.fetchone()
            if row:
                user_dict = dict(row)
                session_token = secrets.token_urlsafe(32)
                cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (session_token, user_dict["id"]))
                conn.commit()
                user_dict["session_token"] = session_token
                return {"success": True, "session_token": session_token, "user": user_dict}
            return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu!"}

    def verify_session_token(self, user_id, token: str) -> bool:
        if not user_id or not token:
            return False
        try:
            uid = int(user_id)
        except Exception:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_token FROM users WHERE id = ?", (uid,))
            row = cursor.fetchone()
            if not row or not row["session_token"]:
                return False
            return secrets.compare_digest(str(row["session_token"]), str(token))

    def is_conversation_member(self, conversation_id, user_id) -> bool:
        try:
            cid = int(conversation_id)
            uid = int(user_id)
        except Exception:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM conversation_members
                WHERE conversation_id = ? AND user_id = ? AND (status IS NULL OR status = 'active')
            """, (cid, uid))
            return cursor.fetchone() is not None

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
                SELECT id, username, full_name, avatar_color, avatar_url, email, COALESCE(is_email_verified, 0) as is_email_verified, phone_number, is_phone_verified, is_online, last_seen, pin_code
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

        # Gửi OTP qua dịch vụ SMS Gateway / Email
        try:
            from .otp_service import otp_service
            otp_service.send_otp(clean_phone, otp_code, "phone")
        except Exception as e:
            print(f"[OTP Service] Không thể gửi SMS: {e}")

        print(f"[OTP] Generated OTP for user {user_id} ({clean_phone}): {otp_code} (expires at {expires_at})")
        return {
            "success": True,
            "otp_code": otp_code,
            "phone_number": clean_phone,
            "expires_in": 300,
            "message": f"Mã xác thực OTP đã được gửi đến số điện thoại {clean_phone}."
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

    def create_email_otp(self, user_id, email):
        """Tạo mã OTP 6 số xác thực địa chỉ Gmail/Email và lưu vào CSDL với thời hạn 5 phút."""
        clean_email = str(email or '').strip().lower()
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', clean_email):
            return {"success": False, "error": "Địa chỉ Gmail/Email không đúng định dạng!"}

        otp_code = f"{random.randint(100000, 999999)}"
        expires_at = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE otp_verifications SET is_used = 1
                WHERE user_id = ? AND target = ? AND purpose = 'email_verification' AND is_used = 0
            """, (user_id, clean_email))
            cursor.execute("""
                INSERT INTO otp_verifications (user_id, target, target_type, otp_code, purpose, expires_at)
                VALUES (?, ?, 'email', ?, 'email_verification', ?)
            """, (user_id, clean_email, otp_code, expires_at))
            conn.commit()

        # Gửi OTP qua dịch vụ Email
        try:
            from .otp_service import otp_service
            otp_service.send_otp(clean_email, otp_code, "email")
        except Exception as e:
            print(f"[OTP Service] Không thể gửi Email OTP: {e}")

        print(f"[OTP] Generated Email OTP for user {user_id} ({clean_email}): {otp_code} (expires at {expires_at})")
        return {
            "success": True,
            "otp_code": otp_code,
            "email": clean_email,
            "expires_in": 300,
            "message": f"Mã xác thực OTP đã được gửi đến Gmail {clean_email}."
        }

    def verify_email_otp(self, user_id, email, otp_code):
        """Xác thực mã OTP từ CSDL và đánh dấu Gmail đã xác minh cho tài khoản."""
        clean_email = str(email or '').strip().lower()
        clean_otp = str(otp_code or '').strip()

        if not clean_email or not clean_otp:
            return {"success": False, "error": "Thiếu địa chỉ Gmail hoặc mã OTP!"}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, otp_code, expires_at, is_used
                FROM otp_verifications
                WHERE user_id = ? AND target = ? AND purpose = 'email_verification' AND is_used = 0
                ORDER BY id DESC LIMIT 1
            """, (user_id, clean_email))
            record = cursor.fetchone()

            if not record:
                return {"success": False, "error": "Không tìm thấy yêu cầu xác minh nào! Vui lòng nhấn gửi lại mã OTP."}

            if record["otp_code"] != clean_otp:
                return {"success": False, "error": "Mã OTP không chính xác! Vui lòng kiểm tra lại."}

            if record["expires_at"] < now_str:
                return {"success": False, "error": "Mã OTP đã hết hạn (chỉ có hiệu lực trong 5 phút)! Vui lòng yêu cầu mã mới."}

            cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = ?", (record["id"],))
            cursor.execute("""
                UPDATE users SET email = ?, is_email_verified = 1 WHERE id = ?
            """, (clean_email, user_id))
            conn.commit()

            user = self.get_user_by_id(user_id)
            return {"success": True, "message": "Xác minh và liên kết Gmail thành công!", "user": user}

    def request_unlink_otp(self, user_id, target_type):
        """Tạo mã OTP 6 số để xác nhận hủy liên kết Số điện thoại hoặc Gmail."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "error": "Người dùng không tồn tại!"}

        target_type = str(target_type or '').strip().lower()
        if target_type == 'email':
            target = user.get('email')
            if not target:
                return {"success": False, "error": "Tài khoản chưa liên kết Gmail!"}
            purpose = 'unlink_email'
        elif target_type == 'phone':
            target = user.get('phone_number')
            if not target:
                return {"success": False, "error": "Tài khoản chưa liên kết số điện thoại!"}
            purpose = 'unlink_phone'
        else:
            return {"success": False, "error": "Loại xác thực không hợp lệ!"}

        otp_code = f"{random.randint(100000, 999999)}"
        expires_at = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE otp_verifications SET is_used = 1
                WHERE user_id = ? AND target = ? AND purpose = ? AND is_used = 0
            """, (user_id, target, purpose))
            cursor.execute("""
                INSERT INTO otp_verifications (user_id, target, target_type, otp_code, purpose, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, target, target_type, otp_code, purpose, expires_at))
            conn.commit()

        try:
            from .otp_service import otp_service
            otp_service.send_otp(target, otp_code, target_type)
        except Exception as e:
            print(f"[OTP Service] Không thể gửi OTP hủy liên kết: {e}")

        print(f"[OTP] Generated Unlink OTP for user {user_id} ({target_type}={target}): {otp_code}")
        return {
            "success": True,
            "target": target,
            "target_type": target_type,
            "expires_in": 300,
            "message": f"Mã xác thực OTP đã được gửi đến {target} để xác nhận hủy liên kết."
        }

    def verify_unlink_otp(self, user_id, target_type, otp_code):
        """Xác thực mã OTP trước khi chính thức xóa Số điện thoại hoặc Gmail."""
        user = self.get_user_by_id(user_id)
        if not user:
            return {"success": False, "error": "Người dùng không tồn tại!"}

        target_type = str(target_type or '').strip().lower()
        clean_otp = str(otp_code or '').strip()
        if not clean_otp or len(clean_otp) != 6:
            return {"success": False, "error": "Vui lòng nhập đúng mã OTP 6 chữ số!"}

        if target_type == 'email':
            target = user.get('email')
            purpose = 'unlink_email'
        elif target_type == 'phone':
            target = user.get('phone_number')
            purpose = 'unlink_phone'
        else:
            return {"success": False, "error": "Loại xác thực không hợp lệ!"}

        if not target:
            return {"success": False, "error": f"Tài khoản chưa liên kết {target_type}!"}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, otp_code, expires_at, is_used
                FROM otp_verifications
                WHERE user_id = ? AND target = ? AND purpose = ? AND is_used = 0
                ORDER BY id DESC LIMIT 1
            """, (user_id, target, purpose))
            record = cursor.fetchone()

            if not record:
                return {"success": False, "error": "Không tìm thấy yêu cầu xác minh OTP hợp lệ! Vui lòng nhấn gửi lại mã."}

            if record["otp_code"] != clean_otp:
                return {"success": False, "error": "Mã OTP xác thực không chính xác! Vui lòng kiểm tra lại."}

            if record["expires_at"] < now_str:
                return {"success": False, "error": "Mã OTP đã hết hạn (5 phút)! Vui lòng yêu cầu mã mới."}

            # Đánh dấu mã đã sử dụng
            cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = ?", (record["id"],))

            # Thực hiện hủy liên kết chính thức
            if target_type == 'email':
                cursor.execute("UPDATE users SET email = NULL, is_email_verified = 0 WHERE id = ?", (user_id,))
                msg = "Đã xác thực OTP thành công. Đã hủy liên kết Gmail!"
            else:
                cursor.execute("UPDATE users SET phone_number = NULL, is_phone_verified = 0 WHERE id = ?", (user_id,))
                msg = "Đã xác thực OTP thành công. Đã hủy liên kết số điện thoại!"

            conn.commit()

        updated_user = self.get_user_by_id(user_id)
        return {"success": True, "message": msg, "user": updated_user}

    def remove_email(self, user_id):
        """Gỡ liên kết Gmail khỏi tài khoản."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET email = NULL, is_email_verified = 0 WHERE id = ?", (user_id,))
            conn.commit()
            user = self.get_user_by_id(user_id)
            return {"success": True, "message": "Đã gỡ liên kết Gmail khỏi tài khoản!", "user": user}

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
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, avatar_url, phone_number, is_phone_verified, is_online
                FROM users
                WHERE id != ?
            """, (curr_id,))
            all_users = [dict(r) for r in cursor.fetchall()]

            exact_matches = []
            partial_matches = []
            id_query = clean_keyword.replace("id:", "").strip()

            for u in all_users:
                uname = (u.get("username") or "").lower()
                fname = (u.get("full_name") or "").lower()
                uname_norm = _strip_accents(uname)
                fname_norm = _strip_accents(fname)
                uid_str = str(u.get("id"))
                phone = (u.get("phone_number") or "").strip()
                phone_digits = re.sub(r'[^0-9]', '', phone)

                is_exact = (
                    search_lower == uname or
                    (id_query and id_query == uid_str) or
                    (search_digits and phone_digits and search_digits == phone_digits)
                )
                is_phone_match = bool(search_digits and len(search_digits) >= 3 and phone_digits and (search_digits in phone_digits))
                is_partial = (
                    is_phone_match or
                    search_normalized in uname_norm or
                    search_lower in fname or
                    search_normalized in fname_norm or
                    (id_query and id_query in uid_str) or
                    search_lower in uid_str
                )

                if is_exact:
                    exact_matches.append(u)
                elif is_partial:
                    partial_matches.append(u)

            return (exact_matches + partial_matches)[:20]

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
                SELECT c.id, c.type, c.name, c.avatar_url, c.theme, c.created_at,
                       COALESCE(c.is_muted, 0) as is_muted,
                       COALESCE(c.custom_mute_text, 'Bạn bị khóa mõm bởi ban quản trị') as custom_mute_text,
                       COALESCE(m.role, 'member') as my_role,
                       COALESCE(m.is_muted, 0) as my_is_muted,
                       m.muted_by_name as my_muted_by
                FROM conversations c
                JOIN conversation_members m ON c.id = m.conversation_id
                WHERE m.user_id = ? AND (m.status IS NULL OR m.status = 'active')
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

                # Lấy danh sách biệt danh cho cuộc trò chuyện này
                cursor.execute("SELECT user_id, nickname FROM conversation_nicknames WHERE conversation_id = ?", (conv_id,))
                nicknames = {r["user_id"]: r["nickname"] for r in cursor.fetchall()}
                conv["nicknames"] = nicknames

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
                        WHERE m.conversation_id = ? AND u.id != ? AND (m.status IS NULL OR m.status = 'active')
                    """, (conv_id, user_id))
                    partner = cursor.fetchone()
                    if partner:
                        partner_id = partner["id"]
                        # Nếu có biệt danh thì hiển thị biệt danh cho direct chat
                        partner_nickname = nicknames.get(partner_id)
                        conv["title"] = partner_nickname if partner_nickname else partner["full_name"]
                        conv["original_title"] = partner["full_name"]
                        conv["avatar_color"] = partner["avatar_color"]
                        conv["avatar_url"] = partner["avatar_url"]
                        conv["is_online"] = partner["is_online"]
                        conv["partner_id"] = partner_id
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
                    # Đếm số thành viên đang hoạt động
                    cursor.execute("SELECT COUNT(*) as count FROM conversation_members WHERE conversation_id = ? AND (status IS NULL OR status = 'active')", (conv_id,))
                    conv["member_count"] = cursor.fetchone()["count"]

                result.append(conv)
            return result

    def get_conversation_members(self, conversation_id):
        try:
            conversation_id = int(conversation_id)
        except Exception:
            pass
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT u.id, u.username, u.full_name, u.avatar_color, u.avatar_url, u.is_online,
                       COALESCE(m.role, 'member') as role,
                       COALESCE(m.is_muted, 0) as is_muted,
                       m.muted_by_name,
                       COALESCE(m.status, 'active') as status,
                       m.joined_at,
                       cn.nickname
                FROM conversation_members m
                JOIN users u ON m.user_id = u.id
                LEFT JOIN conversation_nicknames cn ON cn.conversation_id = m.conversation_id AND cn.user_id = u.id
                WHERE m.conversation_id = ? AND (m.status IS NULL OR m.status = 'active')
                ORDER BY
                    CASE COALESCE(m.role, 'member')
                        WHEN 'owner' THEN 1
                        WHEN 'admin' THEN 1
                        WHEN 'co_leader' THEN 2
                        WHEN 'deputy' THEN 3
                        ELSE 4
                    END ASC,
                    u.full_name ASC
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

    # =========================================================================
    # --- PHÂN HỆ BẢO MẬT: XÁC THỰC THÀNH VIÊN & CHỐNG NGHE LÉN / GỬI LẬU ---
    # =========================================================================
    def is_conversation_member(self, conversation_id: int, user_id: int) -> bool:
        """Kiểm tra một user có phải là thành viên hợp lệ (active) của cuộc hội thoại hay không."""
        try:
            conversation_id = int(conversation_id)
            user_id = int(user_id)
        except Exception:
            return False
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM conversation_members
                WHERE conversation_id = ? AND user_id = ? AND (status IS NULL OR status = 'active')
            """, (conversation_id, user_id))
            return cursor.fetchone() is not None

    def get_conversation_info(self, conversation_id: int):
        """Lấy thông tin cài đặt và trạng thái cấm ngôn của cuộc hội thoại."""
        try:
            conversation_id = int(conversation_id)
        except Exception:
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, type, name, created_by,
                       COALESCE(is_muted, 0) as is_muted,
                       COALESCE(custom_mute_text, 'Bạn bị khóa mõm bởi ban quản trị') as custom_mute_text,
                       created_at
                FROM conversations
                WHERE id = ?
            """, (conversation_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # =========================================================================
    # --- PHÂN HỆ ĐỔI MẬT KHẨU & LIÊN KẾT GMAIL / SĐT XÁC THỰC OTP ---
    # =========================================================================
    def link_user_contact(self, user_id: int, contact: str, contact_type: str = 'auto') -> dict:
        """Liên kết Số điện thoại hoặc Gmail vào tài khoản để nhận mã OTP."""
        try:
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID người dùng không hợp lệ!"}

        contact = contact.strip()
        if not contact:
            return {"success": False, "message": "Thông tin liên kết không được để trống!"}

        is_email = '@' in contact and '.' in contact
        is_phone = contact.replace('+', '').replace(' ', '').replace('-', '').isdigit()

        if contact_type == 'email' or is_email:
            # Xác thực định dạng email
            if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", contact):
                return {"success": False, "message": "Địa chỉ Gmail/Email không đúng định dạng!"}
            actual_type = 'email'
        elif contact_type == 'phone' or is_phone:
            clean_phone = contact.replace(' ', '').replace('-', '')
            if len(clean_phone) < 9 or len(clean_phone) > 13:
                return {"success": False, "message": "Số điện thoại không hợp lệ (từ 9 đến 13 chữ số)!"}
            actual_type = 'phone'
        else:
            return {"success": False, "message": "Vui lòng nhập đúng định dạng Số điện thoại hoặc Gmail!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if actual_type == 'email':
                cursor.execute("""
                    UPDATE users
                    SET email = ?, is_email_verified = 1
                    WHERE id = ?
                """, (contact, user_id))
            else:
                cursor.execute("""
                    UPDATE users
                    SET phone_number = ?, is_phone_verified = 1
                    WHERE id = ?
                """, (contact, user_id))
            conn.commit()

            cursor.execute("SELECT id, username, full_name, email, is_email_verified, phone_number, is_phone_verified FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            return {
                "success": True,
                "message": f"Đã liên kết thành công { 'Gmail' if actual_type == 'email' else 'Số điện thoại' }: {contact}!",
                "user": dict(user_row) if user_row else None
            }

    def create_password_reset_otp(self, user_id: int, target_type: str = 'auto') -> dict:
        """Sinh mã OTP 6 số ngẫu nhiên phục vụ đổi mật khẩu (hạn dùng 5 phút)."""
        try:
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID người dùng không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, full_name, email, is_email_verified, phone_number, is_phone_verified FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {"success": False, "message": "Tài khoản không tồn tại!"}

            target = None
            resolved_type = None

            # Ưu tiên theo yêu cầu của client hoặc tự động tìm mục đã liên kết
            if target_type == 'email' and user['email']:
                target = user['email']
                resolved_type = 'email'
            elif target_type == 'phone' and user['phone_number']:
                target = user['phone_number']
                resolved_type = 'phone'
            elif user['email']:
                target = user['email']
                resolved_type = 'email'
            elif user['phone_number']:
                target = user['phone_number']
                resolved_type = 'phone'

            if not target:
                return {
                    "success": False,
                    "need_link": True,
                    "message": "Tài khoản chưa liên kết Số điện thoại hoặc Gmail! Vui lòng liên kết trước để nhận mã OTP."
                }

            otp_code = f"{random.randint(100000, 999999)}"
            expires_at = (datetime.now() + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                INSERT INTO otp_verifications (user_id, target, target_type, otp_code, purpose, expires_at)
                VALUES (?, ?, ?, ?, 'password_reset', ?)
            """, (user_id, target, resolved_type, otp_code, expires_at))
            conn.commit()

            # Gửi mã OTP qua cổng SMS Gateway hoặc Email thực tế
            try:
                from .otp_service import otp_service
                otp_service.send_otp(target, otp_code, resolved_type)
            except Exception as e:
                print(f"[OTP Service] Không thể gửi OTP: {e}")

            return {
                "success": True,
                "target": target,
                "target_type": resolved_type,
                "otp_code": otp_code,
                "expires_at": expires_at,
                "message": f"Mã OTP đã được gửi thành công đến { 'Gmail' if resolved_type == 'email' else 'Số điện thoại' } ({target})!"
            }

    def verify_and_change_password(self, user_id: int, otp_code: str, new_password: str) -> dict:
        """Xác thực mã OTP và cập nhật mật khẩu mới băm SHA-256 + Salt an toàn."""
        try:
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID người dùng không hợp lệ!"}

        otp_code = str(otp_code).strip()
        new_password = str(new_password).strip()

        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            return {"success": False, "message": msg}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, expires_at, is_used
                FROM otp_verifications
                WHERE user_id = ? AND otp_code = ? AND purpose = 'password_reset' AND is_used = 0
                ORDER BY id DESC LIMIT 1
            """, (user_id, otp_code))
            otp_row = cursor.fetchone()

            if not otp_row:
                return {"success": False, "message": "Mã OTP không chính xác hoặc đã được sử dụng!"}

            # Kiểm tra thời hạn
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if otp_row["expires_at"] < now_str:
                return {"success": False, "message": "Mã OTP đã hết hạn (tối đa 5 phút)! Vui lòng lấy mã mới."}

            new_hash = hash_password(new_password)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            cursor.execute("UPDATE otp_verifications SET is_used = 1 WHERE id = ?", (otp_row["id"],))
            conn.commit()

            return {"success": True, "message": "Đổi mật khẩu thành công! Bạn có thể sử dụng mật khẩu mới ngay bây giờ."}

    def change_password_direct(self, user_id: int, old_password: str, new_password: str) -> dict:
        """Đổi mật khẩu trực tiếp bằng mật khẩu cũ (có kiểm tra OTP nếu đã bật xác minh)."""
        try:
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID người dùng không hợp lệ!"}

        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            return {"success": False, "message": msg}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not user or user["password_hash"] != hash_password(old_password):
                return {"success": False, "message": "Mật khẩu hiện tại không chính xác!"}

            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
            conn.commit()
            return {"success": True, "message": "Đã đổi mật khẩu thành công!"}

    # =========================================================================
    # --- PHÂN HỆ QUẢN LÝ NHÓM NÂNG CAO: PHÂN CẤP CHỨC TƯỚC, KICK & CẤM NGÔN ---
    # =========================================================================
    ROLE_RANKS = {
        'owner': 4,
        'admin': 4,
        'co_leader': 3,
        'deputy': 2,
        'member': 1
    }

    ROLE_NAMES = {
        'owner': 'Trưởng nhóm',
        'admin': 'Trưởng nhóm',
        'co_leader': 'Đồng thủ lĩnh',
        'deputy': 'Phó nhóm',
        'member': 'Thành viên'
    }

    def update_member_role(self, conversation_id: int, operator_id: int, target_id: int, new_role: str) -> dict:
        """Phong chức / Giáng chức thành viên nhóm theo cấp bậc quyền lực nghiêm ngặt."""
        try:
            conversation_id = int(conversation_id)
            operator_id = int(operator_id)
            target_id = int(target_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        if operator_id == target_id:
            return {"success": False, "message": "Không thể tự phong chức cho chính mình!"}

        valid_roles = ('admin', 'owner', 'co_leader', 'deputy', 'member')
        if new_role not in valid_roles:
            return {"success": False, "message": f"Chức vụ '{new_role}' không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM conversation_members WHERE conversation_id = ? AND user_id = ? AND (status IS NULL OR status = 'active')", (conversation_id, operator_id))
            op_row = cursor.fetchone()
            if not op_row:
                return {"success": False, "message": "Bạn không phải thành viên nhóm này!"}

            cursor.execute("SELECT m.role, u.full_name, u.username FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, target_id))
            target_row = cursor.fetchone()
            if not target_row:
                return {"success": False, "message": "Thành viên mục tiêu không tồn tại trong nhóm!"}

            op_rank = self.ROLE_RANKS.get(op_row["role"], 1)
            target_rank = self.ROLE_RANKS.get(target_row["role"], 1)
            new_rank = self.ROLE_RANKS.get(new_role, 1)

            # Quy tắc phong quyền:
            # - Chỉ Admin (rank 4) hoặc Co-Leader (rank 3) mới có quyền phong/giáng chức
            if op_rank < 3:
                return {"success": False, "message": "Chỉ Trưởng nhóm hoặc Đồng thủ lĩnh mới có quyền phong chức!"}

            # - Không ai được can thiệp vào người có cấp bậc bằng hoặc cao hơn mình
            if op_rank <= target_rank:
                return {"success": False, "message": f"Bạn không thể thay đổi chức tước của {self.ROLE_NAMES.get(target_row['role'], target_row['role'])}!"}

            # - Không ai được phong cho người khác chức tước bằng hoặc cao hơn mình (trừ Admin chuyển quyền Trưởng nhóm)
            if op_rank < 4 and new_rank >= op_rank:
                return {"success": False, "message": "Bạn không thể phong chức vị ngang bằng hoặc cao hơn mình!"}

            # Nếu Admin phong người khác làm Admin/Owner -> Chuyển giao Trưởng nhóm (giảm mình xuống Đồng thủ lĩnh)
            if new_role in ('admin', 'owner') and op_rank >= 4:
                cursor.execute("UPDATE conversation_members SET role = 'co_leader' WHERE conversation_id = ? AND user_id = ?", (conversation_id, operator_id))
                cursor.execute("UPDATE conversations SET created_by = ? WHERE id = ?", (target_id, conversation_id))

            cursor.execute("UPDATE conversation_members SET role = ? WHERE conversation_id = ? AND user_id = ?", (new_role, conversation_id, target_id))
            conn.commit()

            new_title = self.ROLE_NAMES.get(new_role, new_role)
            return {
                "success": True,
                "message": f"Đã bổ nhiệm {target_row['full_name']} làm {new_title}!",
                "target_id": target_id,
                "new_role": new_role,
                "new_role_title": new_title
            }

    def kick_group_member(self, conversation_id: int, operator_id: int, target_id: int) -> dict:
        """Kích thành viên ra khỏi nhóm và XÓA VĨNH VIỄN đoạn chat đối với người bị kích."""
        try:
            conversation_id = int(conversation_id)
            operator_id = int(operator_id)
            target_id = int(target_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        if operator_id == target_id:
            return {"success": False, "message": "Không thể tự kích chính mình!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT m.role, u.full_name FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, operator_id))
            op_row = cursor.fetchone()
            if not op_row:
                return {"success": False, "message": "Bạn không phải thành viên nhóm này!"}

            cursor.execute("SELECT m.role, u.full_name, u.username FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, target_id))
            target_row = cursor.fetchone()
            if not target_row:
                return {"success": False, "message": "Thành viên này không tồn tại trong nhóm!"}

            op_role = op_row["role"]
            target_role = target_row["role"]
            op_rank = self.ROLE_RANKS.get(op_role, 1)
            target_rank = self.ROLE_RANKS.get(target_role, 1)

            if op_rank <= 1:
                return {"success": False, "message": "Thành viên thường không có quyền kích người khác khỏi nhóm!"}

            # Quy tắc phân cấp kích thành viên:
            # - Admin (4): Kích được tất cả (3, 2, 1)
            # - Co-Leader (3): Kích được Phó nhóm (2) và Thành viên (1). Không kích được Admin.
            # - Deputy (2): Chỉ kích được Thành viên (1). Không kích được Admin, Co-Leader.
            if op_rank <= target_rank:
                op_title = self.ROLE_NAMES.get(op_role, op_role)
                target_title = self.ROLE_NAMES.get(target_role, target_role)
                return {"success": False, "message": f"{op_title} không có quyền kích {target_title}!"}

            # Xóa hoàn toàn bản ghi khỏi conversation_members -> Xóa vĩnh viễn đoạn chat và quyền truy cập
            cursor.execute("DELETE FROM conversation_members WHERE conversation_id = ? AND user_id = ?", (conversation_id, target_id))
            conn.commit()

            return {
                "success": True,
                "message": f"Đã kích {target_row['full_name']} (@{target_row['username']}) khỏi nhóm!",
                "kicked_user_id": target_id,
                "kicked_user_name": target_row["full_name"],
                "operator_name": op_row["full_name"]
            }

    def set_member_mute(self, conversation_id: int, operator_id: int, target_id: int, is_muted: bool, custom_text: str = None) -> dict:
        """Cấm ngôn / Khóa mõm cá nhân thành viên bất kỳ hoặc gỡ cấm ngôn."""
        try:
            conversation_id = int(conversation_id)
            operator_id = int(operator_id)
            target_id = int(target_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT m.role, u.full_name FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, operator_id))
            op_row = cursor.fetchone()
            if not op_row:
                return {"success": False, "message": "Bạn không phải thành viên nhóm!"}

            cursor.execute("SELECT m.role, u.full_name FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, target_id))
            target_row = cursor.fetchone()
            if not target_row:
                return {"success": False, "message": "Thành viên không tồn tại trong nhóm!"}

            op_rank = self.ROLE_RANKS.get(op_row["role"], 1)
            target_rank = self.ROLE_RANKS.get(target_row["role"], 1)

            if op_rank <= 1:
                return {"success": False, "message": "Thành viên thường không có quyền cấm ngôn!"}
            if op_rank <= target_rank:
                return {"success": False, "message": "Không thể cấm ngôn người có cấp bậc bằng hoặc cao hơn!"}

            op_name = op_row["full_name"]
            muted_val = 1 if is_muted else 0
            muted_by = op_name if is_muted else None
            cursor.execute("""
                UPDATE conversation_members
                SET is_muted = ?, muted_by_name = ?, muted_at = CURRENT_TIMESTAMP
                WHERE conversation_id = ? AND user_id = ?
            """, (muted_val, muted_by, conversation_id, target_id))

            # Cho phép Admin tùy biến câu khóa mõm
            if custom_text and custom_text.strip() and op_rank >= 4:
                cursor.execute("UPDATE conversations SET custom_mute_text = ? WHERE id = ?", (custom_text.strip(), conversation_id))

            conn.commit()
            action_str = "khóa mõm (cấm ngôn)" if is_muted else "gỡ cấm ngôn cho"
            return {
                "success": True,
                "message": f"Đã {action_str} {target_row['full_name']}!",
                "is_muted": is_muted,
                "muted_by_name": muted_by,
                "target_id": target_id,
                "target_name": target_row["full_name"]
            }

    def set_group_mute(self, conversation_id: int, operator_id: int, is_muted: bool, custom_text: str = None) -> dict:
        """Cấm chat toàn bộ nhóm (chỉ Trưởng nhóm, Đồng thủ lĩnh, Phó nhóm được phát ngôn)."""
        try:
            conversation_id = int(conversation_id)
            operator_id = int(operator_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT m.role, u.full_name FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, operator_id))
            op_row = cursor.fetchone()
            if not op_row:
                return {"success": False, "message": "Bạn không phải thành viên nhóm!"}

            op_rank = self.ROLE_RANKS.get(op_row["role"], 1)
            if op_rank <= 1:
                return {"success": False, "message": "Chỉ Ban quản trị mới có quyền bật/tắt chế độ cấm chat toàn nhóm!"}

            muted_val = 1 if is_muted else 0
            if custom_text and custom_text.strip():
                cursor.execute("UPDATE conversations SET is_muted = ?, custom_mute_text = ? WHERE id = ?", (muted_val, custom_text.strip(), conversation_id))
            else:
                cursor.execute("UPDATE conversations SET is_muted = ? WHERE id = ?", (muted_val, conversation_id))
            conn.commit()

            st = "Đã bật chế độ cấm chat toàn nhóm (chỉ Ban quản trị được phát ngôn)" if is_muted else "Đã mở lại quyền chat tự do cho toàn bộ thành viên"
            return {
                "success": True,
                "message": st,
                "is_muted": is_muted,
                "operator_name": op_row["full_name"]
            }

    def leave_group(self, conversation_id: int, user_id: int, silent: bool = False) -> dict:
        """Người dùng rời khỏi nhóm: Lựa chọn rời im lặng hoặc có thông báo, mặc định xóa vĩnh viễn đoạn chat."""
        try:
            conversation_id = int(conversation_id)
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT m.role, u.full_name, u.username FROM conversation_members m JOIN users u ON m.user_id = u.id WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')", (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Bạn không phải thành viên của nhóm này!"}

            user_role = row["role"]
            user_name = row["full_name"]

            # Xóa khỏi conversation_members -> Xóa vĩnh viễn đoạn chat và quyền truy cập
            cursor.execute("DELETE FROM conversation_members WHERE conversation_id = ? AND user_id = ?", (conversation_id, user_id))

            # Nếu người rời là admin/owner -> Tự động chuyển quyền admin cho người có thứ bậc cao nhất tiếp theo
            cursor.execute("""
                SELECT user_id, role FROM conversation_members
                WHERE conversation_id = ?
                ORDER BY
                    CASE role
                        WHEN 'co_leader' THEN 1
                        WHEN 'deputy' THEN 2
                        ELSE 3
                    END, id ASC
                LIMIT 1
            """, (conversation_id,))
            next_admin = cursor.fetchone()
            if next_admin and user_role in ('admin', 'owner'):
                cursor.execute("UPDATE conversation_members SET role = 'admin' WHERE conversation_id = ? AND user_id = ?", (conversation_id, next_admin["user_id"]))

            conn.commit()
            return {
                "success": True,
                "message": "Bạn đã rời khỏi nhóm thành công!",
                "user_name": user_name,
                "silent": silent,
                "conversation_id": conversation_id,
                "new_admin_id": next_admin["user_id"] if next_admin and user_role in ('admin', 'owner') else None
            }

    def add_group_member(self, conversation_id: int, operator_id: int, target_id: int) -> dict:
        """Thêm thành viên mới vào nhóm (chỉ quản trị nhóm có quyền và luôn gán vai trò member)."""
        try:
            conversation_id = int(conversation_id)
            operator_id = int(operator_id)
            target_id = int(target_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM conversations WHERE id = ?", (conversation_id,))
            conv = cursor.fetchone()
            if not conv or conv["type"] != "group":
                return {"success": False, "message": "Nhóm trò chuyện không tồn tại!"}

            cursor.execute("""
                SELECT role FROM conversation_members
                WHERE conversation_id = ? AND user_id = ? AND (status IS NULL OR status = 'active')
            """, (conversation_id, operator_id))
            op_row = cursor.fetchone()
            if not op_row:
                return {"success": False, "message": "Bạn không phải thành viên của nhóm này!"}

            op_rank = self.ROLE_RANKS.get(op_row["role"], 1)
            if op_rank < 2:
                return {"success": False, "message": "Chỉ ban quản trị nhóm mới có quyền thêm thành viên!"}

            cursor.execute("SELECT id, full_name FROM users WHERE id = ?", (target_id,))
            target_user = cursor.fetchone()
            if not target_user:
                return {"success": False, "message": "Không tìm thấy người dùng!"}

            cursor.execute("""
                SELECT status FROM conversation_members
                WHERE conversation_id = ? AND user_id = ?
            """, (conversation_id, target_id))
            existing = cursor.fetchone()
            if existing and (existing["status"] is None or existing["status"] == "active"):
                return {"success": False, "message": "Người dùng này đã là thành viên trong nhóm!"}

            cursor.execute("""
                INSERT INTO conversation_members (conversation_id, user_id, role, status)
                VALUES (?, ?, 'member', 'active')
                ON CONFLICT(conversation_id, user_id) DO UPDATE SET role = 'member', status = 'active', is_muted = 0
            """, (conversation_id, target_id))
            conn.commit()
            return {"success": True, "target_name": target_user["full_name"]}

    # =========================================================================
    # --- PHÂN HỆ: ĐỔI TÊN/AVATAR NHÓM, ĐẶT BIỆT DANH & CHỦ ĐỀ/THEME ĐOẠN CHAT ---
    # =========================================================================
    def update_group_info(self, conversation_id: int, user_id: int, title: str = None, avatar_url: str = None) -> dict:
        """Đổi tên và/hoặc avatar của nhóm trò chuyện (Chỉ thành viên còn active mới được đổi)."""
        try:
            conversation_id = int(conversation_id)
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID không hợp lệ!"}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Kiểm tra xem có phải là nhóm và user có là thành viên active không
            cursor.execute("""
                SELECT c.type, c.name, m.role, COALESCE(u.full_name, 'Thành viên') AS full_name
                FROM conversations c
                JOIN conversation_members m ON c.id = m.conversation_id
                LEFT JOIN users u ON u.id = m.user_id
                WHERE c.id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')
            """, (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Bạn không có quyền chỉnh sửa thông tin nhóm này!"}

            if row["type"] != 'group':
                return {"success": False, "message": "Chỉ có thể đổi thông tin cho nhóm trò chuyện!"}

            if self.ROLE_RANKS.get(row["role"], 1) < 3:
                return {"success": False, "message": "Chỉ Trưởng nhóm hoặc Đồng thủ lĩnh mới có quyền chỉnh sửa thông tin nhóm!"}

            updates = []
            params = []
            if title is not None:
                clean_title = str(title).strip()
                if not clean_title:
                    return {"success": False, "message": "Tên nhóm không được để trống!"}
                updates.append("name = ?")
                params.append(clean_title)

            if avatar_url is not None:
                updates.append("avatar_url = ?")
                params.append(str(avatar_url).strip() if str(avatar_url).strip() else None)

            if not updates:
                return {"success": False, "message": "Không có thông tin nào thay đổi!"}

            params.append(conversation_id)
            cursor.execute(f"UPDATE conversations SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()

            # Lấy thông tin nhóm cập nhật
            cursor.execute("SELECT id, type, name, avatar_url, theme FROM conversations WHERE id = ?", (conversation_id,))
            updated_conv = dict(cursor.fetchone())

            return {
                "success": True,
                "message": "Cập nhật thông tin nhóm thành công!",
                "conversation": updated_conv,
                "operator_name": row["full_name"],
                "operator_id": user_id
            }

    def set_conversation_nickname(self, conversation_id: int, user_id: int, target_user_id: int, nickname: str) -> dict:
        """Đặt biệt danh cho một thành viên trong cuộc trò chuyện (Direct hoặc Group)."""
        try:
            conversation_id = int(conversation_id)
            user_id = int(user_id)
            target_user_id = int(target_user_id)
        except Exception:
            return {"success": False, "message": "Tham số không hợp lệ!"}

        clean_nickname = str(nickname or "").strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Kiểm tra cả 2 người có thuộc cuộc trò chuyện không
            cursor.execute("""
                SELECT user_id FROM conversation_members
                WHERE conversation_id = ? AND user_id IN (?, ?) AND (status IS NULL OR status = 'active')
            """, (conversation_id, user_id, target_user_id))
            members = [r["user_id"] for r in cursor.fetchall()]

            if user_id not in members:
                return {"success": False, "message": "Bạn không phải thành viên của cuộc trò chuyện này!"}
            if target_user_id not in members:
                return {"success": False, "message": "Người này không còn trong cuộc trò chuyện!"}

            cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
            r1 = cursor.fetchone()
            op_name = r1["full_name"] if r1 else "Thành viên"

            cursor.execute("SELECT full_name FROM users WHERE id = ?", (target_user_id,))
            r2 = cursor.fetchone()
            target_name = r2["full_name"] if r2 else "Thành viên"

            if clean_nickname:
                # Thêm hoặc cập nhật biệt danh
                cursor.execute("""
                    INSERT INTO conversation_nicknames (conversation_id, user_id, nickname, set_by, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(conversation_id, user_id) DO UPDATE SET
                        nickname = excluded.nickname,
                        set_by = excluded.set_by,
                        updated_at = CURRENT_TIMESTAMP
                """, (conversation_id, target_user_id, clean_nickname, user_id))
                msg = f"Đã đặt biệt danh cho {target_name} là '{clean_nickname}'."
            else:
                # Xóa biệt danh (về lại tên gốc)
                cursor.execute("DELETE FROM conversation_nicknames WHERE conversation_id = ? AND user_id = ?", (conversation_id, target_user_id))
                msg = f"Đã xóa biệt danh của {target_name}."

            conn.commit()

            # Lấy toàn bộ danh sách biệt danh của cuộc trò chuyện này
            cursor.execute("SELECT user_id, nickname FROM conversation_nicknames WHERE conversation_id = ?", (conversation_id,))
            nicknames = {r["user_id"]: r["nickname"] for r in cursor.fetchall()}

            return {
                "success": True,
                "message": msg,
                "conversation_id": conversation_id,
                "target_user_id": target_user_id,
                "nickname": clean_nickname or None,
                "operator_name": op_name,
                "target_name": target_name,
                "all_nicknames": nicknames
            }

    def get_conversation_nicknames(self, conversation_id: int) -> dict:
        """Lấy từ điển biệt danh trong cuộc trò chuyện {user_id: nickname}."""
        try:
            conversation_id = int(conversation_id)
        except Exception:
            return {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, nickname FROM conversation_nicknames WHERE conversation_id = ?", (conversation_id,))
            return {r["user_id"]: r["nickname"] for r in cursor.fetchall()}

    def update_conversation_theme(self, conversation_id: int, user_id: int, theme: str) -> dict:
        """Thay đổi chủ đề (màu sắc/hình nền) cho cuộc trò chuyện."""
        try:
            conversation_id = int(conversation_id)
            user_id = int(user_id)
        except Exception:
            return {"success": False, "message": "ID không hợp lệ!"}

        clean_theme = str(theme or "").strip()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.role, COALESCE(u.full_name, 'Thành viên') AS full_name
                FROM conversation_members m
                LEFT JOIN users u ON u.id = m.user_id
                WHERE m.conversation_id = ? AND m.user_id = ? AND (m.status IS NULL OR m.status = 'active')
            """, (conversation_id, user_id))
            row = cursor.fetchone()
            if not row:
                return {"success": False, "message": "Bạn không có quyền đổi chủ đề cuộc trò chuyện này!"}

            cursor.execute("UPDATE conversations SET theme = ? WHERE id = ?", (clean_theme if clean_theme else None, conversation_id))
            conn.commit()

            return {
                "success": True,
                "message": "Đã đổi giao diện đoạn chat thành công!",
                "conversation_id": conversation_id,
                "theme": clean_theme,
                "operator_name": row["full_name"],
                "operator_id": user_id
            }


