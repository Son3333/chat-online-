import sqlite3
import os
import hashlib
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "chat_database.db")

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with fixed salt."""
    salt = "cnpm_nhom5_chat_salt_"
    return hashlib.sha256((salt + password).encode('utf-8')).hexdigest()

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_tables()
        self.seed_default_users()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Bảng Người dùng
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (file_id) REFERENCES files(id)
            )
            """)
            conn.commit()

    def seed_default_users(self):
        """Khởi tạo 5 thành viên của nhóm 5 đồ án nếu chưa có."""
        initial_members = [
            ("son", "123", "Vũ Duy Thái Sơn (Nhóm trưởng)", "#2563EB"),
            ("manh", "123", "Vy Thế Mạnh", "#7C3AED"),
            ("dan", "123", "Vũ Minh Dân", "#059669"),
            ("tam", "123", "Phạm Đức Tâm", "#D97706"),
            ("huu", "123", "Hữu", "#DC2626"),
        ]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            user_ids = []
            for username, pwd, fullname, color in initial_members:
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                row = cursor.fetchone()
                if not row:
                    pwd_hash = hash_password(pwd)
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, full_name, avatar_color)
                        VALUES (?, ?, ?, ?)
                    """, (username, pwd_hash, fullname, color))
                    user_ids.append(cursor.lastrowid)
                else:
                    user_ids.append(row["id"])
            
            # Kết bạn chéo giữa các thành viên
            for i in range(len(user_ids)):
                for j in range(i + 1, len(user_ids)):
                    cursor.execute("""
                        INSERT OR IGNORE INTO friends (user_id, friend_id, status)
                        VALUES (?, ?, 'accepted')
                    """, (user_ids[i], user_ids[j]))
                    cursor.execute("""
                        INSERT OR IGNORE INTO friends (user_id, friend_id, status)
                        VALUES (?, ?, 'accepted')
                    """, (user_ids[j], user_ids[i]))

            # Tạo nhóm chat chung mặc định "Nhóm 05 - Đồ Án CNPM"
            cursor.execute("SELECT id FROM conversations WHERE name = 'Nhóm 05 - Đồ Án CNPM'")
            group_row = cursor.fetchone()
            if not group_row and len(user_ids) == 5:
                cursor.execute("""
                    INSERT INTO conversations (type, name, created_by)
                    VALUES ('group', 'Nhóm 05 - Đồ Án CNPM', ?)
                """, (user_ids[0],))
                conv_id = cursor.lastrowid
                for idx, uid in enumerate(user_ids):
                    role = 'admin' if idx == 0 else 'member'
                    cursor.execute("""
                        INSERT INTO conversation_members (conversation_id, user_id, role)
                        VALUES (?, ?, ?)
                    """, (conv_id, uid, role))
                
                # Thêm tin nhắn chào mừng mặc định
                cursor.execute("""
                    INSERT INTO messages (conversation_id, sender_id, message_type, content)
                    VALUES (?, ?, 'text', 'Chào mừng cả nhóm đến với ứng dụng nhắn tin và truyền thông tin!')
                """, (conv_id, user_ids[0]))

            conn.commit()

    # --- User APIs ---
    def register_user(self, username, password, full_name):
        username = username.strip().lower()
        full_name = full_name.strip()
        if not username or not password or not full_name:
            return {"success": False, "message": "Vui lòng nhập đầy đủ thông tin!"}
        
        colors = ["#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626", "#0891B2", "#4F46E5"]
        avatar_color = colors[len(username) % len(colors)]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return {"success": False, "message": "Tên đăng nhập đã tồn tại!"}
            
            pwd_hash = hash_password(password)
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, avatar_color)
                VALUES (?, ?, ?, ?)
            """, (username, pwd_hash, full_name, avatar_color))
            new_id = cursor.lastrowid
            
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
        username = username.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            pwd_hash = hash_password(password)
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, is_online
                FROM users
                WHERE username = ? AND password_hash = ?
            """, (username, pwd_hash))
            row = cursor.fetchone()
            if row:
                return {"success": True, "user": dict(row)}
            return {"success": False, "message": "Sai tên đăng nhập hoặc mật khẩu!"}

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
            cursor.execute("SELECT id, username, full_name, avatar_color, is_online, last_seen FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def search_users(self, keyword, current_user_id):
        keyword = f"%{keyword.strip().lower()}%"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, full_name, avatar_color, is_online
                FROM users
                WHERE (LOWER(username) LIKE ? OR LOWER(full_name) LIKE ?) AND id != ?
                LIMIT 20
            """, (keyword, keyword, current_user_id))
            return [dict(r) for r in cursor.fetchall()]

    # --- Friends & Conversations APIs ---
    def get_direct_conversation(self, user1_id, user2_id):
        """Lấy hoặc tạo cuộc trò chuyện 1-1 giữa 2 người dùng."""
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
                
                if conv["type"] == 'direct':
                    # Tìm đối phương
                    cursor.execute("""
                        SELECT u.id, u.full_name, u.avatar_color, u.is_online
                        FROM users u
                        JOIN conversation_members m ON u.id = m.user_id
                        WHERE m.conversation_id = ? AND u.id != ?
                    """, (conv_id, user_id))
                    partner = cursor.fetchone()
                    if partner:
                        conv["title"] = partner["full_name"]
                        conv["avatar_color"] = partner["avatar_color"]
                        conv["is_online"] = partner["is_online"]
                        conv["partner_id"] = partner["id"]
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
                SELECT u.id, u.username, u.full_name, u.avatar_color, u.is_online, m.role
                FROM conversation_members m
                JOIN users u ON m.user_id = u.id
                WHERE m.conversation_id = ?
            """, (conversation_id,))
            return [dict(r) for r in cursor.fetchall()]

    # --- Message & File APIs ---
    def save_message(self, conversation_id, sender_id, message_type, content, file_id=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (conversation_id, sender_id, message_type, content, file_id)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, sender_id, message_type, content, file_id))
            msg_id = cursor.lastrowid
            conn.commit()
            
            # Lấy thông tin tin nhắn vừa lưu kèm thông tin người gửi
            cursor.execute("""
                SELECT m.id, m.conversation_id, m.sender_id, m.message_type, m.content, 
                       m.file_id, m.created_at, u.full_name as sender_name, u.avatar_color,
                       f.original_name, f.file_size, f.file_type
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                LEFT JOIN files f ON m.file_id = f.id
                WHERE m.id = ?
            """, (msg_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_messages(self, conversation_id, limit=50):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT m.id, m.conversation_id, m.sender_id, m.message_type, m.content, 
                       m.file_id, m.created_at, u.full_name as sender_name, u.avatar_color,
                       f.original_name, f.file_size, f.file_type
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                LEFT JOIN files f ON m.file_id = f.id
                WHERE m.conversation_id = ?
                ORDER BY m.id ASC
                LIMIT ?
            """, (conversation_id, limit))
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

