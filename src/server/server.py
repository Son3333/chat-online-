import socket
import threading
import json
import struct
import os
import sys
import base64
import uuid
from datetime import datetime
from src.server.database import Database

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr is not None:
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def log(msg: str):
    if sys.stdout is not None:
        try:
            print(msg)
        except Exception:
            try:
                print(msg.encode('ascii', 'replace').decode('ascii'))
            except Exception:
                pass

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(SERVER_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.db = Database()
        self.running = False
        self.server_socket = None
        
        # Mapping: user_id -> client_socket
        self.active_clients = {}
        # Mapping: client_socket -> user_id
        self.socket_to_user = {}
        self.lock = threading.Lock()
        self.send_lock = threading.Lock()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        self.running = True
        log(f"==================================================")
        log(f"CHAT SERVER DA KHOI CHAY!")
        log(f"   Dia chi may chu: {self.host}:{self.port}")
        log(f"   Thu muc uploads: {UPLOADS_DIR}")
        log(f"   Dang cho cac may tram ket noi...")
        log(f"==================================================")

        try:
            while self.running:
                client_sock, client_addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_sock, client_addr), daemon=True)
                thread.start()
        except KeyboardInterrupt:
            log("\nDang dung may chu...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        log("May chu da dung.")

    def send_packet(self, sock: socket.socket, payload: dict):
        """Gửi packet JSON có tiền tố độ dài 4-byte (Big-Endian)."""
        with self.send_lock:
            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                header = struct.pack("!I", len(data))
                sock.sendall(header + data)
                return True
            except Exception as e:
                # print(f"Lỗi gửi packet: {e}")
                return False

    def receive_packet(self, sock: socket.socket):
        """Đọc chính xác 1 packet JSON theo tiền tố độ dài 4-byte."""
        try:
            header = sock.recv(4)
            if not header or len(header) < 4:
                return None
            length = struct.unpack("!I", header)[0]
            
            # Đọc đúng length bytes
            chunks = []
            bytes_read = 0
            while bytes_read < length:
                chunk = sock.recv(min(length - bytes_read, 65536))
                if not chunk:
                    return None
                chunks.append(chunk)
                bytes_read += len(chunk)
            
            raw_data = b"".join(chunks).decode('utf-8')
            return json.loads(raw_data)
        except Exception:
            return None

    def broadcast_to_users(self, user_ids: list, payload: dict):
        """Gửi thông báo tới danh sách các user_id đang online."""
        with self.lock:
            for uid in user_ids:
                if uid in self.active_clients:
                    sock = self.active_clients[uid]
                    self.send_packet(sock, payload)

    def handle_client(self, client_sock: socket.socket, client_addr):
        user_id = None
        try:
            while self.running:
                packet = self.receive_packet(client_sock)
                if packet is None:
                    break
                
                action = packet.get("action")
                response = self.process_action(client_sock, packet)
                
                if response:
                    self.send_packet(client_sock, response)
                
                # Cập nhật user_id của socket nếu đăng nhập thành công HOẶC kết nối lại (identify)
                if action in ["login", "register", "identify"] and response.get("success"):
                    user_id = response["user"]["id"]
                    with self.lock:
                        # KIỂM TRA ĐĂNG NHẬP THIẾT BỊ KHÁC (Cơ chế Facebook / Telegram):
                        # Nếu tài khoản này đang online ở một thiết bị khác -> Đăng xuất thiết bị cũ ngay lập tức!
                        if user_id in self.active_clients:
                            old_sock = self.active_clients[user_id]
                            if old_sock != client_sock:
                                try:
                                    kick_packet = {
                                        "type": "forced_logout",
                                        "message": "Tài khoản của bạn vừa được đăng nhập trên một thiết bị khác!\nThiết bị hiện tại đã bị đăng xuất để bảo vệ bảo mật."
                                    }
                                    self.send_packet(old_sock, kick_packet)
                                    if old_sock in self.socket_to_user:
                                        del self.socket_to_user[old_sock]
                                    old_sock.close()
                                    log(f"[!] Tai khoan [ID: {user_id}] dang nhap thiet bi moi -> Da buoc dang xuat thiet bi cu.")
                                except Exception:
                                    pass

                        self.active_clients[user_id] = client_sock
                        self.socket_to_user[client_sock] = user_id
                    
                    self.db.set_online_status(user_id, True)
                    # Báo trạng thái online cho các client khác
                    self.notify_status_change(user_id, True)
                    log(f"[+] Nguoi dung [{response['user']['username']}] da dang nhap tu {client_addr}")

                elif action == "identify" and response.get("success"):
                    user_id = response["user"]["id"]
                    with self.lock:
                        # Đăng ký lại socket cho user này sau khi rớt mạng / khởi động server
                        self.active_clients[user_id] = client_sock
                        self.socket_to_user[client_sock] = user_id
                    self.db.set_online_status(user_id, True)
                    self.notify_status_change(user_id, True)
                    log(f"[+] Nguoi dung [{response['user']['username']}] da ket noi lai va nhan dien tu {client_addr}")

        except Exception as e:
            log(f"[-] Loi xu ly client {client_addr}: {e}")
        finally:
            # Xử lý khi ngắt kết nối
            with self.lock:
                if client_sock in self.socket_to_user:
                    uid = self.socket_to_user.pop(client_sock)
                    if uid in self.active_clients and self.active_clients[uid] == client_sock:
                        del self.active_clients[uid]
                    self.db.set_online_status(uid, False)
                    self.notify_status_change(uid, False)
                    log(f"[-] Nguoi dung (ID: {uid}) da ngat ket noi.")
            try:
                client_sock.close()
            except Exception:
                pass

    def notify_status_change(self, user_id: int, is_online: bool):
        """Thông báo thay đổi trạng thái Online/Offline cho tất cả các cuộc trò chuyện liên quan."""
        user = self.db.get_user_by_id(user_id)
        if not user:
            return
        
        payload = {
            "type": "user_status_changed",
            "user_id": user_id,
            "is_online": 1 if is_online else 0,
            "full_name": user["full_name"]
        }
        
        # Lấy tất cả user đang online để broadcast
        with self.lock:
            all_online = list(self.active_clients.keys())
        self.broadcast_to_users(all_online, payload)

    def process_action(self, client_sock: socket.socket, packet: dict) -> dict:
        action = packet.get("action")
        
        # 1. Đăng nhập
        if action == "login":
            username = packet.get("username", "")
            password = packet.get("password", "")
            res = self.db.authenticate_user(username, password)
            res["action"] = "login_response"
            return res

        # 2. Đăng ký
        elif action == "register":
            username = packet.get("username", "")
            password = packet.get("password", "")
            full_name = packet.get("full_name", "")
            res = self.db.register_user(username, password, full_name)
            res["action"] = "register_response"
            return res

        # 2.1 Nhận diện lại sau khi rớt mạng / máy chủ khởi động lại (Session Resume)
        elif action == "identify":
            user_id = packet.get("user_id")
            user = self.db.get_user_by_id(user_id)
            if user:
                return {"action": "identify_response", "success": True, "user": user}
            return {"action": "identify_response", "success": False, "message": "User not found"}

        # 3. Lấy danh sách hội thoại
        elif action == "get_conversations":
            user_id = packet.get("user_id")
            convs = self.db.get_user_conversations(user_id)
            return {"action": "conversations_list", "conversations": convs}

        # 4. Lấy lịch sử tin nhắn
        elif action == "get_messages":
            conv_id = packet.get("conversation_id")
            messages = self.db.get_messages(conv_id)
            members = self.db.get_conversation_members(conv_id)
            return {
                "action": "messages_history", 
                "conversation_id": conv_id, 
                "messages": messages,
                "members": members
            }

        # 5. Gửi tin nhắn văn bản / emoji
        elif action == "send_message":
            conv_id = packet.get("conversation_id")
            sender_id = packet.get("sender_id")
            content = packet.get("content", "").strip()
            msg_type = packet.get("message_type", "text")
            
            if not content:
                return {"action": "send_message_response", "success": False, "message": "Nội dung rỗng"}
            
            saved_msg = self.db.save_message(conv_id, sender_id, msg_type, content)
            if saved_msg:
                # Gửi cho tất cả thành viên trong nhóm đang online
                members = self.db.get_conversation_members(conv_id)
                member_ids = [m["id"] for m in members]
                
                broadcast_packet = {
                    "type": "new_message",
                    "conversation_id": conv_id,
                    "message": saved_msg
                }
                self.broadcast_to_users(member_ids, broadcast_packet)
                return {"action": "send_message_response", "success": True, "message": saved_msg}
            return {"action": "send_message_response", "success": False, "message": "Lưu tin nhắn thất bại"}

        # 6. Tải lên tệp tin / hình ảnh
        elif action == "upload_file":
            conv_id = packet.get("conversation_id")
            sender_id = packet.get("sender_id")
            filename = packet.get("filename", "file.dat")
            file_base64 = packet.get("file_data", "")
            file_size = packet.get("file_size", 0)
            file_type = packet.get("file_type", "file") # 'image' hoặc 'file'
            
            if not file_base64:
                return {"action": "upload_response", "success": False, "message": "Dữ liệu tệp rỗng!"}
            
            try:
                # Lưu file vào thư mục uploads
                file_bytes = base64.b64decode(file_base64)
                unique_name = f"{uuid.uuid4().hex[:10]}_{filename}"
                saved_path = os.path.join(UPLOADS_DIR, unique_name)
                with open(saved_path, "wb") as f:
                    f.write(file_bytes)
                
                # Lưu vào database
                file_id = self.db.save_file_record(filename, unique_name, len(file_bytes), file_type, sender_id)
                
                # Tạo tin nhắn kèm file
                caption = packet.get("caption", "") or f"Đã gửi tệp: {filename}"
                saved_msg = self.db.save_message(conv_id, sender_id, file_type, caption, file_id)
                
                # Broadcast tin nhắn kèm tệp tin
                members = self.db.get_conversation_members(conv_id)
                member_ids = [m["id"] for m in members]
                
                broadcast_packet = {
                    "type": "new_message",
                    "conversation_id": conv_id,
                    "message": saved_msg
                }
                self.broadcast_to_users(member_ids, broadcast_packet)
                return {"action": "upload_response", "success": True, "file_id": file_id}
            except Exception as e:
                return {"action": "upload_response", "success": False, "message": str(e)}

        # 7. Tải về tệp tin
        elif action == "download_file":
            file_id = packet.get("file_id")
            file_rec = self.db.get_file_record(file_id)
            if not file_rec:
                return {"action": "download_response", "success": False, "message": "Không tìm thấy tệp!"}
            
            file_path = os.path.join(UPLOADS_DIR, file_rec["stored_path"])
            if not os.path.exists(file_path):
                return {"action": "download_response", "success": False, "message": "Tệp tin đã bị xóa trên máy chủ!"}
            
            with open(file_path, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode('utf-8')
            
            return {
                "action": "download_response",
                "success": True,
                "file_id": file_id,
                "filename": file_rec["original_name"],
                "file_data": b64,
                "file_type": file_rec["file_type"]
            }

        # 8. Tìm kiếm người dùng
        elif action == "search_users":
            keyword = packet.get("keyword", "")
            current_user_id = packet.get("user_id")
            results = self.db.search_users(keyword, current_user_id)
            return {"action": "search_results", "users": results}

        # 9. Bắt đầu chat 1-1
        elif action == "start_direct_chat":
            user1_id = packet.get("user_id")
            user2_id = packet.get("partner_id")
            conv_id = self.db.get_direct_conversation(user1_id, user2_id)
            convs = self.db.get_user_conversations(user1_id)
            # Thông báo cho đối phương cập nhật danh sách hội thoại nếu đang online
            self.broadcast_to_users([user2_id], {"type": "refresh_conversations"})
            return {
                "action": "direct_chat_started",
                "conversation_id": conv_id,
                "conversations": convs
            }

        # 10. Tạo nhóm chat
        elif action == "create_group":
            creator_id = packet.get("creator_id")
            name = packet.get("name", "").strip()
            member_ids = packet.get("member_ids", [])
            if not name:
                return {"action": "create_group_response", "success": False, "message": "Tên nhóm không được để trống!"}
            
            conv_id = self.db.create_group_conversation(name, creator_id, member_ids)
            
            # Gửi tin nhắn tạo nhóm
            self.db.save_message(conv_id, creator_id, 'text', f"Nhóm \"{name}\" đã được tạo.")
            
            # Broadcast cập nhật danh sách hội thoại cho tất cả thành viên
            all_members = set([creator_id] + member_ids)
            self.broadcast_to_users(list(all_members), {"type": "refresh_conversations"})
            
            return {"action": "create_group_response", "success": True, "conversation_id": conv_id}

        # 11. Đang soạn tin nhắn (Typing indicator)
        elif action == "typing":
            conv_id = packet.get("conversation_id")
            sender_id = packet.get("sender_id")
            sender_name = packet.get("sender_name")
            members = self.db.get_conversation_members(conv_id)
            other_ids = [m["id"] for m in members if m["id"] != sender_id]
            self.broadcast_to_users(other_ids, {
                "type": "user_typing",
                "conversation_id": conv_id,
                "sender_id": sender_id,
                "sender_name": sender_name
            })
            return None

        # 12. Quản lý Danh bạ Bạn bè & Lời mời kết bạn (Friend Request & Approval)
        elif action == "get_friends":
            user_id = packet.get("user_id")
            friends = self.db.get_friends(user_id)
            pending_reqs = self.db.get_pending_requests(user_id)
            return {
                "action": "get_friends_response", 
                "success": True, 
                "friends": friends, 
                "pending_requests": pending_reqs
            }

        elif action == "add_friend":
            user_id = packet.get("user_id")
            friend_id = packet.get("friend_id")
            res = self.db.send_friend_request(user_id, friend_id)
            # Thông báo tức thời cho bên nhận nếu đang online
            if res.get("success"):
                if res.get("accepted"):
                    # Cả 2 đã trở thành bạn bè chính thức
                    self.broadcast_to_users([user_id, friend_id], {"type": "refresh_friends"})
                else:
                    # Gửi thông báo lời mời kết bạn mới tới friend_id
                    self.broadcast_to_users([friend_id], {
                        "type": "new_friend_request",
                        "sender_id": user_id
                    })
            return {"action": "add_friend_response", **res}

        elif action == "accept_friend":
            user_id = packet.get("user_id")
            requester_id = packet.get("requester_id")
            res = self.db.accept_friend_request(user_id, requester_id)
            if res.get("success"):
                # Cập nhật danh bạ ngay lập tức cho cả 2 bên
                self.broadcast_to_users([user_id, requester_id], {"type": "refresh_friends"})
            return {"action": "accept_friend_response", **res}

        elif action == "reject_friend":
            user_id = packet.get("user_id")
            requester_id = packet.get("requester_id")
            res = self.db.reject_friend_request(user_id, requester_id)
            if res.get("success"):
                self.broadcast_to_users([user_id], {"type": "refresh_friends"})
            return {"action": "reject_friend_response", **res}

        elif action == "remove_friend":
            user_id = packet.get("user_id")
            friend_id = packet.get("friend_id")
            res = self.db.remove_friend(user_id, friend_id)
            if res.get("success"):
                self.broadcast_to_users([user_id, friend_id], {"type": "refresh_friends"})
            return {"action": "remove_friend_response", **res}

        elif action == "check_friend":
            user_id = packet.get("user_id")
            friend_id = packet.get("friend_id")
            status = self.db.get_friendship_status(user_id, friend_id)
            return {
                "action": "check_friend_response", 
                "is_friend": (status == "friends"),
                "friendship_status": status
            }

        return None

if __name__ == "__main__":
    server = ChatServer()
    server.start()

