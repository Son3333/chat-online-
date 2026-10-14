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
        
        # Callbacks
        self.callbacks = {
            "new_message": None,
            "user_status_changed": None,
            "user_typing": None,
            "refresh_conversations": None,
        }
        
        # Pending synchronous responses (action_name -> event & response)
        self.pending_responses = {}
        self.lock = threading.Lock()

    def set_server(self, host: str, port: int):
        if self.connected:
            self.disconnect()
        self.host = host.strip()
        self.port = int(port)

    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0) # Hỗ trợ timeout khi kết nối mạng LAN / WAN
            self.sock.connect((self.host, self.port))
            self.sock.settimeout(None)
            self.connected = True
            self.running = True
            
            # Khởi chạy thread lắng nghe dữ liệu từ server
            self.recv_thread = threading.Thread(target=self._listen_loop, daemon=True)
            self.recv_thread.start()
            return True
        except Exception as e:
            self.connected = False
            return False

    def disconnect(self):
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
        try:
            data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            header = struct.pack("!I", len(data))
            self.sock.sendall(header + data)
            return True
        except Exception:
            self.connected = False
            return False

    def _listen_loop(self):
        while self.running:
            try:
                header = self.sock.recv(4)
                if not header or len(header) < 4:
                    break
                length = struct.unpack("!I", header)[0]
                
                chunks = []
                bytes_read = 0
                while bytes_read < length:
                    chunk = self.sock.recv(min(length - bytes_read, 65536))
                    if not chunk:
                        break
                    chunks.append(chunk)
                    bytes_read += len(chunk)
                
                if bytes_read < length:
                    break
                
                raw_data = b"".join(chunks).decode('utf-8')
                packet = json.loads(raw_data)
                
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
        """Gửi packet không cần đợi phản hồi (như typing, gửi tin nhắn nhanh)."""
        return self._send_packet(payload)

    # --- API gọi tiện ích ---
    def login(self, username, password):
        return self.send_request({
            "action": "login",
            "username": username,
            "password": password
        }, expected_action="login_response")

    def register(self, username, password, full_name):
        return self.send_request({
            "action": "register",
            "username": username,
            "password": password,
            "full_name": full_name
        }, expected_action="register_response")

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

    def send_message(self, conversation_id, sender_id, content, msg_type="text"):
        return self.send_fire_and_forget({
            "action": "send_message",
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": msg_type
        })

    def upload_file(self, conversation_id, sender_id, filepath, caption=""):
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


