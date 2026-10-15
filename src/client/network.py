import socket
import threading
import json
import struct
import base64
import os
from typing import Callable, Optional

class NetworkClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 8888):
        self.host = host
        self.port = port
        self.sock: Optional[socket.socket] = None
        self.connected = False
        self.running = False
        self.current_user_id: Optional[int] = None
        self.auto_reconnect_enabled = True
        self.is_reconnecting = False
        
        # Callbacks
        self.callbacks = {
            "new_message": None,
            "user_status_changed": None,
            "user_typing": None,
            "refresh_conversations": None,
            "forced_logout": None,
            "new_friend_request": None,
            "refresh_friends": None,
            "on_reconnected": None,
            "connection_lost": None,
        }
        
        # Pending synchronous responses (action_name -> event & response)
        self.pending_responses = {}
        self.lock = threading.Lock()
        self.send_lock = threading.Lock()

    def set_server(self, host: str, port: int):
        if self.connected:
            self.disconnect()
        self.host = host.strip()
        self.port = int(port)

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(4.0) # Hỗ trợ timeout khi kết nối mạng LAN / WAN
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            self.connected = True
            self.running = True
            
            # Khởi chạy thread lắng nghe dữ liệu từ server
            self.recv_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.recv_thread.start()
            return True
        except Exception:
            # Fallback nếu kết nối WAN thất bại nhưng máy này đang chạy Server local 8888
            if self.host != "127.0.0.1":
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.settimeout(1.0)
                    self.sock.connect(("127.0.0.1", 8888))
                    self.sock.settimeout(None)
                    self.host = "127.0.0.1"
                    self.port = 8888
                    self.connected = True
                    self.running = True
                    self.recv_thread = threading.Thread(target=self._listen_loop, daemon=True)
                    self.recv_thread.start()
                    return True
                except Exception:
                    pass
            self.connected = False
            return False

    def disconnect(self):
        self.auto_reconnect_enabled = False
        self.current_user_id = None
        self.running = False
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

    def register_callback(self, event_type: str, callback: Callable):
        self.callbacks[event_type] = callback

    def _send_packet(self, payload: dict) -> bool:
        if not self.connected or not self.sock:
            return False
        with self.send_lock:
            try:
                data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                header = struct.pack("!I", len(data))
                self.sock.sendall(header + data)
                return True
            except Exception:
                self.connected = False
                return False

    def _recv_exact(self, num_bytes: int) -> Optional[bytes]:
        """Đọc chính xác num_bytes từ TCP socket, không bao giờ ngắt kết nối do phân mảnh gói tin."""
        data = bytearray()
        while len(data) < num_bytes and self.running:
            try:
                chunk = self.sock.recv(num_bytes - len(data))
                if not chunk:
                    return None
                data.extend(chunk)
            except Exception:
                return None
        return bytes(data) if len(data) == num_bytes else None

    def _listen_loop(self):
        while self.running:
            try:
                header = self._recv_exact(4)
                if not header:
                    break
                length = struct.unpack("!I", header)[0]
                
                raw_bytes = self._recv_exact(length)
                if not raw_bytes:
                    break
                
                packet = json.loads(raw_bytes.decode('utf-8'))
                
                # Phân loại packet: Event broadcast hay Response của request
                pkt_type = packet.get("type")
                action = packet.get("action")
                
                if pkt_type and pkt_type in self.callbacks and self.callbacks[pkt_type]:
                    self.callbacks[pkt_type](packet)
                elif action:
                    # Kiểm tra xem có ai đang đợi response này không
                    with self.lock:
                        if action in self.pending_responses:
                            event, res_container = self.pending_responses[action]
                            res_container.append(packet)
                            event.set()
                        elif pkt_type in self.callbacks and self.callbacks[pkt_type]:
                            self.callbacks[pkt_type](packet)
            except Exception:
                break
        
        self.connected = False
        self.running = False
        
        # Báo sự kiện mất kết nối
        if self.callbacks.get("connection_lost"):
            try:
                self.callbacks["connection_lost"]({})
            except Exception:
                pass
                
        # Tự động kích hoạt cơ chế kết nối lại
        if self.auto_reconnect_enabled:
            self._start_reconnect_thread()

    def _start_reconnect_thread(self):
        """Khởi chạy luồng chạy ngầm cố gắng kết nối lại mỗi 2 giây."""
        with self.lock:
            if self.is_reconnecting:
                return
            self.is_reconnecting = True
            
        def _loop():
            import time
            while not self.connected and self.auto_reconnect_enabled:
                time.sleep(2.0)
                if self.reconnect_and_identify():
                    break
            with self.lock:
                self.is_reconnecting = False
                
        threading.Thread(target=_loop, daemon=True).start()

    def reconnect_and_identify(self) -> bool:
        """Tự động kết nối lại và khôi phục phiên làm việc (Identify) với máy chủ."""
        if self.connected:
            return True
        if not self.connect():
            return False
        if self.current_user_id:
            res = self.send_request({
                "action": "identify",
                "user_id": self.current_user_id
            }, expected_action="identify_response", timeout=5.0)
            if not res or not res.get("success"):
                return False
        if self.callbacks.get("on_reconnected"):
            try:
                self.callbacks["on_reconnected"]({})
            except Exception:
                pass
        return True

    def identify(self, user_id: int):
        self.current_user_id = user_id
        return self.send_request({
            "action": "identify",
            "user_id": user_id
        }, expected_action="identify_response", timeout=5.0)

    def send_request(self, payload: dict, expected_action: str, timeout: float = 10.0) -> Optional[dict]:
        """Gửi request và đồng bộ chờ phản hồi từ Server."""
        if not self.connected:
            if not self.connect():
                return None
        
        event = threading.Event()
        res_container = []
        with self.lock:
            self.pending_responses[expected_action] = (event, res_container)
        
        if not self._send_packet(payload):
            with self.lock:
                self.pending_responses.pop(expected_action, None)
            return None
        
        # Chờ response
        signaled = event.wait(timeout)
        with self.lock:
            self.pending_responses.pop(expected_action, None)
        
        if signaled and res_container:
            return res_container[0]
        return None

    def send_fire_and_forget(self, payload: dict) -> bool:
        """Gửi packet không cần đợi phản hồi (như typing)."""
        return self._send_packet(payload)

    # --- API gọi tiện ích ---
    def login(self, username, password):
        self.auto_reconnect_enabled = True
        res = self.send_request({
            "action": "login",
            "username": username,
            "password": password
        }, expected_action="login_response")
        if res and res.get("success") and "user" in res:
            self.current_user_id = res["user"]["id"]
        return res

    def register(self, username, password, full_name):
        self.auto_reconnect_enabled = True
        res = self.send_request({
            "action": "register",
            "username": username,
            "password": password,
            "full_name": full_name
        }, expected_action="register_response")
        if res and res.get("success") and "user" in res:
            self.current_user_id = res["user"]["id"]
        return res

    def get_conversations(self, user_id):
        return self.send_request({
            "action": "get_conversations",
            "user_id": user_id
        }, expected_action="conversations_list")

    def get_messages(self, conversation_id):
        return self.send_request({
            "action": "get_messages",
            "conversation_id": conversation_id
        }, expected_action="messages_history")

    def send_message(self, conversation_id, sender_id, content, msg_type="text") -> bool:
        """Gửi tin nhắn đảm bảo có xác nhận từ server và tự động kết nối lại nếu mất mạng."""
        payload = {
            "action": "send_message",
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": msg_type
        }
        # Nếu chưa kết nối, tự động kết nối lại
        if not self.connected:
            if not self.reconnect_and_identify():
                return False
        
        res = self.send_request(payload, expected_action="send_message_response", timeout=5.0)
        if res and res.get("success"):
            return True
        
        # Thử lại lần 2 nếu bị ngắt kết nối đúng thời điểm gửi
        if self.reconnect_and_identify():
            res = self.send_request(payload, expected_action="send_message_response", timeout=5.0)
            if res and res.get("success"):
                return True
        return False

    def upload_file(self, conversation_id, sender_id, filepath, caption=""):
        if not self.connected:
            self.reconnect_and_identify()
        try:
            filename = os.path.basename(filepath)
            filesize = os.path.getsize(filepath)
            ext = os.path.splitext(filename)[1].lower()
            file_type = "image" if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"] else "file"
            
            with open(filepath, "rb") as f:
                data = f.read()
                b64 = base64.b64encode(data).decode('utf-8')
            
            return self.send_request({
                "action": "upload_file",
                "conversation_id": conversation_id,
                "sender_id": sender_id,
                "filename": filename,
                "file_data": b64,
                "file_size": filesize,
                "file_type": file_type,
                "caption": caption
            }, expected_action="upload_response", timeout=25.0)
        except Exception as e:
            return {"success": False, "message": str(e)}

    def download_file(self, file_id):
        if not self.connected:
            self.reconnect_and_identify()
        return self.send_request({
            "action": "download_file",
            "file_id": file_id
        }, expected_action="download_response", timeout=25.0)

    def search_users(self, keyword, current_user_id):
        return self.send_request({
            "action": "search_users",
            "keyword": keyword,
            "user_id": current_user_id
        }, expected_action="search_results")

    def start_direct_chat(self, user_id, partner_id):
        return self.send_request({
            "action": "start_direct_chat",
            "user_id": user_id,
            "partner_id": partner_id
        }, expected_action="direct_chat_started")

    def create_group(self, creator_id, name, member_ids):
        return self.send_request({
            "action": "create_group",
            "creator_id": creator_id,
            "name": name,
            "member_ids": member_ids
        }, expected_action="create_group_response")

    def send_typing(self, conversation_id, sender_id, sender_name):
        return self.send_fire_and_forget({
            "action": "typing",
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "sender_name": sender_name
        })

    # --- Danh bạ Bạn bè (Contacts) ---
    def get_friends(self, user_id):
        return self.send_request({
            "action": "get_friends",
            "user_id": user_id
        }, expected_action="get_friends_response")

    def add_friend(self, user_id, friend_id):
        return self.send_request({
            "action": "add_friend",
            "user_id": user_id,
            "friend_id": friend_id
        }, expected_action="add_friend_response")

    def accept_friend(self, user_id, requester_id):
        return self.send_request({
            "action": "accept_friend",
            "user_id": user_id,
            "requester_id": requester_id
        }, expected_action="accept_friend_response")

    def reject_friend(self, user_id, requester_id):
        return self.send_request({
            "action": "reject_friend",
            "user_id": user_id,
            "requester_id": requester_id
        }, expected_action="reject_friend_response")

    def remove_friend(self, user_id, friend_id):
        return self.send_request({
            "action": "remove_friend",
            "user_id": user_id,
            "friend_id": friend_id
        }, expected_action="remove_friend_response")

    def check_friend(self, user_id, friend_id):
        return self.send_request({
            "action": "check_friend",
            "user_id": user_id,
            "friend_id": friend_id
        }, expected_action="check_friend_response")

    # --- Xóa tin nhắn, Xóa đoạn chat & Chặn người dùng ---
    def recall_message(self, message_id, user_id):
        return self.send_request({
            "action": "recall_message",
            "message_id": message_id,
            "user_id": user_id
        }, expected_action="recall_message_response", timeout=8.0)

    def delete_conversation(self, conversation_id, user_id):
        return self.send_request({
            "action": "delete_conversation",
            "conversation_id": conversation_id,
            "user_id": user_id
        }, expected_action="delete_conversation_response", timeout=8.0)

    def block_user(self, user_id, target_id):
        return self.send_request({
            "action": "block_user",
            "user_id": user_id,
            "target_id": target_id
        }, expected_action="block_user_response", timeout=8.0)

    def unblock_user(self, user_id, target_id):
        return self.send_request({
            "action": "unblock_user",
            "user_id": user_id,
            "target_id": target_id
        }, expected_action="unblock_user_response", timeout=8.0)

    def get_block_status(self, user_id, target_id):
        return self.send_request({
            "action": "get_block_status",
            "user_id": user_id,
            "target_id": target_id
        }, expected_action="get_block_status_response", timeout=6.0)


