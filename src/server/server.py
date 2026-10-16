import socket
import threading
import json
import struct
import os
import sys
import time
import base64
import uuid
from typing import Optional
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
            print(msg, flush=True)
        except Exception:
            try:
                print(msg.encode('ascii', 'replace').decode('ascii'), flush=True)
            except Exception:
                pass

SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(SERVER_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

class ChatServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8888, db: Optional[Database] = None):  # nosec B104
        self.host = host
        self.port = port
        self.db = db if db is not None else Database()
        self.running = False
        self.server_socket = None

        # Mapping: user_id -> client_socket
        self.active_clients = {}
        # Mapping: client_socket -> user_id
        self.socket_to_user = {}
        self.lock = threading.RLock()
        self.send_lock = threading.RLock()

    def start(self, ready_event: Optional[threading.Event] = None):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(50)
        self.port = self.server_socket.getsockname()[1]
        self.running = True
        try:
            self.db.reset_all_online_status()
        except Exception:
            pass
        if ready_event:
            ready_event.set()
        log("==================================================")
        log("CHAT SERVER DA KHOI CHAY!")
        log(f"   Dia chi may chu: {self.host}:{self.port}")
        log(f"   Thu muc uploads: {UPLOADS_DIR}")
        log("   Dang cho cac may tram ket noi...")
        log("==================================================")

        try:
            while self.running:
                try:
                    client_sock, client_addr = self.server_socket.accept()
                except (OSError, socket.error):
                    if not self.running:
                        break
                    continue
                thread = threading.Thread(target=self.handle_client, args=(client_sock, client_addr), daemon=True)
                thread.start()
        except KeyboardInterrupt:
            log("\nDang dung may chu...")
        finally:
            self.stop()

    def stop(self):
        if not self.running and not self.server_socket:
            return
        self.running = False
        with self.lock:
            for sock in list(self.socket_to_user.keys()):
                try:
                    sock.close()
                except Exception:
                    pass
            self.active_clients.clear()
            self.socket_to_user.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        log("May chu da dung.")

    def send_packet(self, sock: socket.socket, payload: dict):
        """Gửi packet JSON có tiền tố độ dài 4-byte (Big-Endian)."""
        with self.send_lock:
            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                header = struct.pack("!I", len(data))
                sock.sendall(header + data)
                return True
            except Exception:
                # print(f"Lỗi gửi packet: {e}")
                return False

    def _recv_exact(self, sock: socket.socket, num_bytes: int) -> Optional[bytes]:
        """Đọc chính xác num_bytes từ TCP socket, không bao giờ ngắt kết nối do phân mảnh gói tin."""
        data = bytearray()
        while len(data) < num_bytes and self.running:
            try:
                chunk = sock.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data.extend(chunk)
            except Exception:
                return None
        return bytes(data) if len(data) == num_bytes else None

    def receive_packet(self, sock: socket.socket):
        """Đọc chính xác 1 packet JSON theo tiền tố độ dài 4-byte."""
        try:
            header = self._recv_exact(sock, 4)
            if not header:
                return None
            length = struct.unpack("!I", header)[0]

            raw_bytes = self._recv_exact(sock, length)
            if not raw_bytes:
                return None

            return json.loads(raw_bytes.decode('utf-8'))
        except Exception:
            return None

    def broadcast_to_users(self, user_ids: list, payload: dict):
        """Gửi thông báo tới danh sách các user_id đang online."""
        sockets = []
        with self.lock:
            for uid in user_ids:
                if uid in self.active_clients:
                    sockets.append(self.active_clients[uid])
        for sock in sockets:
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
                if action in ["login", "register"] and response.get("success"):
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
                                    def _graceful_close(s):
                                        time.sleep(0.1)
                                        try:
                                            s.shutdown(socket.SHUT_WR)
                                        except Exception:
                                            pass
                                        try:
                                            s.close()
                                        except Exception:
                                            pass
                                    threading.Thread(target=_graceful_close, args=(old_sock,), daemon=True).start()
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
                        # Đăng ký lại socket cho user này sau khi rớt mạng / khởi động server (không kích forced_logout)
                        if user_id in self.active_clients:
                            old_sock = self.active_clients[user_id]
                            if old_sock != client_sock:
                                if old_sock in self.socket_to_user:
                                    del self.socket_to_user[old_sock]
                                try:
                                    old_sock.close()
                                except Exception:
                                    pass
                        self.active_clients[user_id] = client_sock
                        self.socket_to_user[client_sock] = user_id
                    self.db.set_online_status(user_id, True)
                    self.notify_status_change(user_id, True)
                    log(f"[+] Nguoi dung [{response['user']['username']}] da ket noi lai va nhan dien tu {client_addr}")

        except Exception as e:
            log(f"[-] Loi xu ly client {client_addr}: {e}")
        finally:
            uid = None
            with self.lock:
                if client_sock in self.socket_to_user:
                    uid = self.socket_to_user.pop(client_sock, None)
                    if uid in self.active_clients and self.active_clients[uid] == client_sock:
                        del self.active_clients[uid]
            if uid:
                try:
                    self.db.set_online_status(uid, False)
                    self.notify_status_change(uid, False)
                    log(f"[-] Nguoi dung (ID: {uid}) da ngat ket noi.")
                except Exception:
                    pass
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

        # 2.2 Cập nhật hồ sơ cá nhân
        elif action == "update_profile":
            user_id = packet.get("user_id")
            full_name = packet.get("full_name")
            avatar_color = packet.get("avatar_color")
            new_password = packet.get("new_password")
            pin_code = packet.get("pin_code")
            avatar_url = packet.get("avatar_url")
            phone_number = packet.get("phone_number")
            is_phone_verified = packet.get("is_phone_verified")
            res = self.db.update_user_profile(
                user_id,
                full_name=full_name,
                avatar_color=avatar_color,
                new_password=new_password,
                pin_code=pin_code,
                avatar_url=avatar_url,
                phone_number=phone_number,
                is_phone_verified=is_phone_verified
            )
            if res.get("success"):
                with self.lock:
                    all_online = list(self.active_clients.keys())
                self.broadcast_to_users(all_online, {
                    "type": "profile_updated",
                    "user": res.get("user")
                })
            return {"action": "update_profile_response", **res}

        # 3. Lấy danh sách hội thoại
        elif action == "get_conversations":
            user_id = packet.get("user_id")
            convs = self.db.get_user_conversations(user_id)
            with self.lock:
                for conv in convs:
                    if conv.get("type") == "direct" and conv.get("partner_id"):
                        conv["is_online"] = 1 if (conv["partner_id"] in self.active_clients) else 0
                    elif conv.get("type") == "saved":
                        conv["is_online"] = 1
            return {"action": "conversations_list", "success": True, "conversations": convs}

        # 4. Lấy lịch sử tin nhắn
        elif action == "get_messages":
            conv_id = packet.get("conversation_id")
            messages = self.db.get_messages(conv_id)
            members = self.db.get_conversation_members(conv_id)
            return {
                "action": "messages_history",
                "success": True,
                "conversation_id": conv_id,
                "messages": messages,
                "members": members
            }

        # 5. Gửi tin nhắn văn bản / emoji / tệp / vị trí
        elif action == "send_message":
            conv_id = packet.get("conversation_id")
            sender_id = packet.get("sender_id")
            content = packet.get("content", "").strip()
            msg_type = packet.get("msg_type") or packet.get("message_type") or "text"
            file_id = packet.get("file_id")

            if not content and not file_id:
                return {"action": "send_message_response", "success": False, "message": "Nội dung rỗng"}

            # Kiểm tra xem cuộc trò chuyện có bị chặn không (đối với chat 1-1)
            members = self.db.get_conversation_members(conv_id)
            if len(members) == 2:
                other_members = [m for m in members if m["id"] != sender_id]
                if other_members:
                    other_id = other_members[0]["id"]
                    if self.db.is_blocked(sender_id, other_id):
                        return {
                            "action": "send_message_response",
                            "success": False,
                            "message": "Không thể gửi tin nhắn vì cuộc trò chuyện đã bị chặn!"
                        }

            reply_to_id = packet.get("reply_to_id")
            saved_msg = self.db.save_message(conv_id, sender_id, msg_type, content, file_id=file_id, reply_to_id=reply_to_id)
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
                log(f"[+] Tin nhan moi ({msg_type}) trong Hoi thoai #{conv_id} tu User #{sender_id}: {content[:30]}")
                return {"action": "send_message_response", "success": True, "message": saved_msg}
            return {"action": "send_message_response", "success": False, "message": "Lưu tin nhắn thất bại"}

        # 6. Tải lên tệp tin / hình ảnh / video
        elif action == "upload_file":
            conv_id = packet.get("conversation_id")
            sender_id = packet.get("sender_id")
            filename = packet.get("filename") or packet.get("original_name") or "file.dat"
            file_base64 = packet.get("file_data", "")
            file_size = packet.get("file_size", 0)
            file_type = packet.get("file_type") or packet.get("msg_type") or "file"

            if not file_base64:
                return {"action": "upload_response", "success": False, "message": "Dữ liệu tệp rỗng!"}

            # Kiểm tra xem cuộc trò chuyện có bị chặn không nếu có conv_id
            if conv_id and sender_id:
                members = self.db.get_conversation_members(conv_id)
                if len(members) == 2:
                    other_members = [m for m in members if m["id"] != sender_id]
                    if other_members:
                        other_id = other_members[0]["id"]
                        if self.db.is_blocked(sender_id, other_id):
                            return {
                                "action": "upload_response",
                                "success": False,
                                "message": "Không thể gửi tệp vì cuộc trò chuyện đã bị chặn!"
                            }

            try:
                # Lưu file vào thư mục uploads
                file_bytes = base64.b64decode(file_base64)
                unique_name = f"{uuid.uuid4().hex[:10]}_{filename}"
                saved_path = os.path.join(UPLOADS_DIR, unique_name)
                with open(saved_path, "wb") as f:
                    f.write(file_bytes)

                # Lưu vào database
                actual_size = file_size if file_size else len(file_bytes)
                file_id = self.db.save_file_record(filename, unique_name, actual_size, file_type, sender_id or 0)

                # Nếu truyền kèm conv_id -> Lưu luôn tin nhắn kèm file và broadcast
                if conv_id and sender_id:
                    caption = packet.get("caption", "") or f"Đã gửi tệp: {filename}"
                    reply_to_id = packet.get("reply_to_id")
                    saved_msg = self.db.save_message(conv_id, sender_id, file_type, caption, file_id, reply_to_id=reply_to_id)

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
            keyword = packet.get("keyword") or packet.get("query", "")
            current_user_id = packet.get("user_id")
            results = self.db.search_users(keyword, current_user_id)
            with self.lock:
                for u in results:
                    u["is_online"] = 1 if (u["id"] in self.active_clients) else 0
            return {"action": "search_results", "success": True, "users": results}

        # 9. Bắt đầu chat 1-1
        elif action == "start_direct_chat":
            user1_id = packet.get("user_id")
            user2_id = packet.get("partner_id") or packet.get("target_id")
            conv_id = self.db.get_direct_conversation(user1_id, user2_id)
            convs = self.db.get_user_conversations(user1_id)
            # Thông báo cho đối phương cập nhật danh sách hội thoại nếu đang online
            if user2_id:
                self.broadcast_to_users([user2_id], {"type": "refresh_conversations"})
            return {
                "action": "direct_chat_started",
                "success": True,
                "conversation_id": conv_id,
                "conversations": convs
            }

        # 10. Tạo nhóm chat (Có chống spam & kiểm tra hợp lệ)
        elif action == "create_group":
            creator_id = packet.get("creator_id")
            name = packet.get("name", "").strip()
            raw_member_ids = packet.get("member_ids", [])

            if not name:
                return {"action": "create_group_response", "success": False, "message": "Tên nhóm không được để trống!"}
            if len(name) > 60:
                return {"action": "create_group_response", "success": False, "message": "Tên nhóm quá dài (tối đa 60 ký tự)!"}

            # Lọc thành viên hợp lệ (không bao gồm chính người tạo)
            try:
                member_ids = list({int(m) for m in raw_member_ids if int(m) != int(creator_id)})
            except Exception:
                member_ids = []

            if not member_ids:
                return {"action": "create_group_response", "success": False, "message": "Nhóm phải có ít nhất 1 thành viên khác!"}
            if len(member_ids) > 100:
                return {"action": "create_group_response", "success": False, "message": "Số lượng thành viên vượt quá giới hạn (tối đa 100)!"}

            # 1. Chống spam: Giới hạn tần suất tạo nhóm (tối thiểu cách nhau 3 giây)
            now = time.time()
            if not hasattr(self, "_group_create_cooldown"):
                self._group_create_cooldown = {}
            last_create = self._group_create_cooldown.get(creator_id, 0)
            if now - last_create < 3.0:
                wait_sec = int(3.0 - (now - last_create)) + 1
                return {"action": "create_group_response", "success": False, "message": f"Bạn đang tạo nhóm quá nhanh! Vui lòng chờ {wait_sec} giây."}

            # 2. Chống tạo nhóm trùng lặp trong 15 giây gần nhất
            if not hasattr(self, "_recent_created_groups"):
                self._recent_created_groups = []
            self._recent_created_groups = [g for g in self._recent_created_groups if now - g[0] < 15.0]
            mems_tuple = tuple(sorted(member_ids))
            for _, c_id, prev_name, prev_mems in self._recent_created_groups:
                if c_id == creator_id and prev_name.lower() == name.lower() and prev_mems == mems_tuple:
                    return {"action": "create_group_response", "success": False, "message": "Nhóm với tên và các thành viên này vừa mới được tạo!"}

            self._group_create_cooldown[creator_id] = now
            self._recent_created_groups.append((now, creator_id, name, mems_tuple))

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
            sent_req_ids = self.db.get_sent_requests(user_id)
            with self.lock:
                for f in friends:
                    f["is_online"] = 1 if (f["id"] in self.active_clients) else 0
            return {
                "action": "get_friends_response",
                "success": True,
                "friends": friends,
                "pending_requests": pending_reqs,
                "sent_request_ids": sent_req_ids
            }

        elif action in ("add_friend", "send_friend_request"):
            user_id = packet.get("user_id") or packet.get("sender_id")
            friend_id = packet.get("friend_id") or packet.get("target_id")
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

        # 16. Thu hồi tin nhắn ở cả 2 phía
        elif action == "recall_message":
            msg_id = packet.get("message_id")
            user_id = packet.get("user_id")
            success, msg, conv_id = self.db.recall_message(msg_id, user_id)
            if success and conv_id:
                members = self.db.get_conversation_members(conv_id)
                member_ids = [m["id"] for m in members]
                self.broadcast_to_users(member_ids, {
                    "type": "message_recalled",
                    "conversation_id": conv_id,
                    "message_id": msg_id
                })
                log(f"[+] User #{user_id} da thu hoi Tin nhan #{msg_id} trong Hoi thoai #{conv_id}")
                return {"action": "recall_message_response", "success": True, "message_id": msg_id, "conversation_id": conv_id}
            return {"action": "recall_message_response", "success": False, "message": msg}

        # 17. Xóa cuộc trò chuyện
        elif action == "delete_conversation":
            conv_id = packet.get("conversation_id")
            user_id = packet.get("user_id")
            members = self.db.get_conversation_members(conv_id)
            member_ids = [m["id"] for m in members]
            ok = self.db.delete_conversation(conv_id, user_id)
            if ok:
                self.broadcast_to_users(member_ids, {
                    "type": "conversation_deleted",
                    "conversation_id": conv_id
                })
                log(f"[+] User #{user_id} da xoa Cuoc tro chuyen #{conv_id}")
                return {"action": "delete_conversation_response", "success": True, "conversation_id": conv_id}
            return {"action": "delete_conversation_response", "success": False, "message": "Xóa cuộc trò chuyện thất bại"}

        # 18. Chặn người dùng (Block)
        elif action == "block_user":
            user_id = packet.get("user_id")
            target_id = packet.get("target_id")
            success, msg = self.db.block_user(user_id, target_id)
            if success:
                log(f"[+] User #{user_id} da chan User #{target_id}")
                self.broadcast_to_users([user_id, target_id], {
                    "type": "block_status_changed",
                    "user_id": user_id,
                    "target_id": target_id,
                    "is_blocked": True
                })
            return {"action": "block_user_response", "success": success, "message": msg, "target_id": target_id}

        # 19. Bỏ chặn người dùng (Unblock)
        elif action == "unblock_user":
            user_id = packet.get("user_id")
            target_id = packet.get("target_id")
            success, msg = self.db.unblock_user(user_id, target_id)
            if success:
                log(f"[+] User #{user_id} da bo chan User #{target_id}")
                self.broadcast_to_users([user_id, target_id], {
                    "type": "block_status_changed",
                    "user_id": user_id,
                    "target_id": target_id,
                    "is_blocked": False
                })
            return {"action": "unblock_user_response", "success": success, "message": msg, "target_id": target_id}

        # 20. Kiểm tra trạng thái chặn
        elif action == "get_block_status":
            user_id = packet.get("user_id")
            target_id = packet.get("target_id")
            is_blocked_by_me = self.db.is_user_blocked_by_me(user_id, target_id)
            is_blocked_by_them = self.db.is_user_blocked_by_me(target_id, user_id)
            return {
                "action": "get_block_status_response",
                "success": True,
                "target_id": target_id,
                "is_blocked_by_me": is_blocked_by_me,
                "is_blocked_by_them": is_blocked_by_them,
                "is_blocked": (is_blocked_by_me or is_blocked_by_them)
            }

        # 21. Thả / Đổi / Gỡ cảm xúc tin nhắn (Reactions: ❤️, 👍, 😂, 😮, 😢, 😡)
        elif action == "toggle_reaction":
            message_id = packet.get("message_id")
            user_id = packet.get("user_id")
            reaction = packet.get("reaction")
            reactions, conv_id = self.db.toggle_reaction(message_id, user_id, reaction)
            if conv_id:
                members = self.db.get_conversation_members(conv_id)
                self.broadcast_to_users([m["id"] for m in members], {
                    "type": "reaction_updated",
                    "conversation_id": conv_id,
                    "message_id": message_id,
                    "reactions": reactions
                })
            return {"action": "toggle_reaction_response", "success": True, "message_id": message_id, "reactions": reactions}

        # 22. Ghim tin nhắn (Pin Message)
        elif action == "pin_message":
            conv_id = packet.get("conversation_id")
            message_id = packet.get("message_id")
            user_id = packet.get("user_id")
            pinned = self.db.pin_message(conv_id, message_id, user_id)
            members = self.db.get_conversation_members(conv_id)
            self.broadcast_to_users([m["id"] for m in members], {
                "type": "pinned_updated",
                "conversation_id": conv_id,
                "pinned": pinned
            })
            return {"action": "pin_message_response", "success": True, "pinned": pinned}

        # 23. Bỏ ghim tin nhắn (Unpin Message)
        elif action == "unpin_message":
            conv_id = packet.get("conversation_id")
            self.db.unpin_message(conv_id)
            members = self.db.get_conversation_members(conv_id)
            self.broadcast_to_users([m["id"] for m in members], {
                "type": "pinned_updated",
                "conversation_id": conv_id,
                "pinned": None
            })
            return {"action": "unpin_message_response", "success": True}

        # 24. Lấy tin nhắn ghim hiện tại của cuộc hội thoại
        elif action == "get_pinned_message":
            conv_id = packet.get("conversation_id")
            pinned = self.db.get_pinned_message(conv_id)
            return {"action": "get_pinned_message_response", "success": True, "pinned": pinned}

        # 25. Lấy hoặc tạo cuộc trò chuyện "Cloud của tôi (Saved Messages)"
        elif action == "get_saved_conversation":
            user_id = packet.get("user_id")
            conv_id = self.db.get_or_create_saved_conversation(user_id)
            return {"action": "get_saved_conversation_response", "success": True, "conversation_id": conv_id}

        # 26. Yêu cầu cuộc gọi (Voice Call / Video Call Signaling)
        elif action == "call_invite":
            caller_id = packet.get("caller_id")
            receiver_id = packet.get("receiver_id")
            call_type = packet.get("call_type", "voice") # 'voice' hoặc 'video'
            conv_id = packet.get("conversation_id")

            # Kiểm tra xem có bị chặn không
            if self.db.is_blocked(caller_id, receiver_id):
                return {"action": "call_invite_response", "success": False, "message": "Không thể gọi vì cuộc trò chuyện đã bị chặn!"}

            caller = self.db.get_user_by_id(caller_id)
            caller_name = caller["full_name"] if caller else "Người dùng"
            avatar_color = caller["avatar_color"] if caller else "#2563EB"

            channel_id = f"call_{caller_id}_{receiver_id}_{int(time.time())}"
            if not hasattr(self, "active_calls"):
                self.active_calls = {}
            self.active_calls[channel_id] = {
                "caller_id": caller_id,
                "receiver_id": receiver_id,
                "call_type": call_type,
                "conversation_id": conv_id,
                "status": "ringing"
            }

            # Gửi thông báo chuông đến người nhận
            self.broadcast_to_users([receiver_id], {
                "type": "call_incoming",
                "channel_id": channel_id,
                "caller_id": caller_id,
                "caller_name": caller_name,
                "avatar_color": avatar_color,
                "call_type": call_type,
                "conversation_id": conv_id
            })
            return {"action": "call_invite_response", "success": True, "channel_id": channel_id}

        # 27. Chấp nhận cuộc gọi (Accept Call)
        elif action == "call_accept":
            channel_id = packet.get("channel_id")
            call = getattr(self, "active_calls", {}).get(channel_id)
            if call:
                call["status"] = "connected"
                call["start_time"] = time.time()
                self.broadcast_to_users([call["caller_id"], call["receiver_id"]], {
                    "type": "call_connected",
                    "channel_id": channel_id,
                    "call_type": call["call_type"]
                })
            return {"action": "call_accept_response", "success": True}

        # 28. Từ chối cuộc gọi (Reject Call)
        elif action == "call_reject":
            channel_id = packet.get("channel_id")
            call = getattr(self, "active_calls", {}).pop(channel_id, None)
            if call:
                self.broadcast_to_users([call["caller_id"]], {
                    "type": "call_rejected",
                    "channel_id": channel_id,
                    "reason": "Đối phương đã từ chối cuộc gọi."
                })
            return {"action": "call_reject_response", "success": True}

        # 29. Kết thúc cuộc gọi (End Call)
        elif action == "call_end":
            channel_id = packet.get("channel_id")
            call = getattr(self, "active_calls", {}).pop(channel_id, None)
            if call:
                duration_sec = 0
                if "start_time" in call:
                    duration_sec = int(time.time() - call["start_time"])
                mins, secs = divmod(duration_sec, 60)
                dur_str = f"{mins:02d}:{secs:02d}"

                self.broadcast_to_users([call["caller_id"], call["receiver_id"]], {
                    "type": "call_ended",
                    "channel_id": channel_id,
                    "duration": dur_str
                })

                # Ghi lịch sử cuộc gọi vào hội thoại
                icon = "📞 Cuộc gọi thoại" if call["call_type"] == "voice" else "📹 Cuộc gọi video"
                msg_text = f"{icon} ({dur_str})" if duration_sec > 0 else f"{icon} nhỡ"
                if call.get("conversation_id"):
                    saved_m = self.db.save_message(call["conversation_id"], call["caller_id"], "text", msg_text)
                    members = self.db.get_conversation_members(call["conversation_id"])
                    self.broadcast_to_users([m["id"] for m in members], {
                        "type": "new_message",
                        "conversation_id": call["conversation_id"],
                        "message": saved_m
                    })
            return {"action": "call_end_response", "success": True}

        # 30. Chuyển tiếp luồng Audio / Video thời gian thực (Media Relay)
        elif action == "call_media":
            channel_id = packet.get("channel_id")
            sender_id = packet.get("sender_id")
            call = getattr(self, "active_calls", {}).get(channel_id)
            if call:
                target_id = call["receiver_id"] if sender_id == call["caller_id"] else call["caller_id"]
                self.broadcast_to_users([target_id], {
                    "type": "call_media_relay",
                    "channel_id": channel_id,
                    "media_type": packet.get("media_type"), # 'audio' hoặc 'video'
                    "data": packet.get("data")
                })
            return None

if __name__ == "__main__":
    server = ChatServer()
    server.start()

