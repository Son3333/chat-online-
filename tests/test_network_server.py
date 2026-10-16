import socket
import struct
import json
import time
import threading
import tempfile
import os
import pytest
from src.server.server import ChatServer
from src.server.database import Database

def send_test_packet(sock: socket.socket, payload: dict):
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)

def recv_test_packet(sock: socket.socket, timeout: float = 3.0) -> dict:
    sock.settimeout(timeout)
    try:
        header = sock.recv(4)
        if not header or len(header) < 4:
            return None
        length = struct.unpack("!I", header)[0]
        data = b""
        while len(data) < length:
            chunk = sock.recv(min(length - len(data), 65536))
            if not chunk:
                break
            data += chunk
        return json.loads(data.decode('utf-8'))
    except (socket.timeout, TimeoutError, ConnectionResetError, ConnectionAbortedError, OSError):
        return None

def recv_until(sock: socket.socket, predicate, timeout: float = 4.0) -> dict:
    """Read packets from socket, ignoring irrelevant async notifications until matching predicate."""
    start = time.time()
    while time.time() - start < timeout:
        pkt = recv_test_packet(sock, timeout=1.0)
        if pkt is not None and predicate(pkt):
            return pkt
    raise TimeoutError(f"Matching packet not received within {timeout}s")

@pytest.fixture
def running_server():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_net_chat.db")
    db = Database(db_path=db_path)
    
    server = ChatServer(host="127.0.0.1", port=0, db=db)
    ready_evt = threading.Event()
    server_thread = threading.Thread(target=server.start, args=(ready_evt,), daemon=True)
    server_thread.start()
    
    assert ready_evt.wait(timeout=5.0), "Server failed to start in 5 seconds"
    port = server.port
    
    yield server, port, db
    
    server.stop()
    time.sleep(0.05)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

class TestNetworkProtocol:
    def test_packet_framing_integrity(self):
        payload = {"type": "test_echo", "data": "A" * 50000, "unicode": "Xin chào thế giới 🚀"}
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        header = struct.pack("!I", len(data))
        
        unpacked_len = struct.unpack("!I", header)[0]
        assert unpacked_len == len(data)
        decoded = json.loads(data.decode('utf-8'))
        assert decoded["unicode"] == "Xin chào thế giới 🚀"

    def test_server_handshake_and_auth(self, running_server):
        server, port, db = running_server
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", port))
        
        try:
            # 1. Register Alice
            send_test_packet(sock, {
                "action": "register",
                "username": "net_alice",
                "password": "AliceNetPass123!",
                "full_name": "Alice Net Test"
            })
            resp = recv_until(sock, lambda p: p.get("action") == "register_response")
            assert resp["success"] is True
            alice_id = resp["user"]["id"]
            
            # 2. Login Alice
            send_test_packet(sock, {
                "action": "login",
                "username": "net_alice",
                "password": "AliceNetPass123!"
            })
            login_resp = recv_until(sock, lambda p: p.get("action") == "login_response")
            assert login_resp["success"] is True
            assert login_resp["user"]["id"] == alice_id
            
        finally:
            sock.close()

    def test_call_signaling_flow(self, running_server):
        server, port, db = running_server
        
        # Connect Alice
        sock_a = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_a.connect(("127.0.0.1", port))
        send_test_packet(sock_a, {
            "action": "register",
            "username": "call_alice",
            "password": "AlicePass123!",
            "full_name": "Alice Call"
        })
        reg_a = recv_until(sock_a, lambda p: p.get("action") == "register_response")
        alice_id = reg_a["user"]["id"]

        # Connect Bob
        sock_b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_b.connect(("127.0.0.1", port))
        send_test_packet(sock_b, {
            "action": "register",
            "username": "call_bob",
            "password": "BobPass123!",
            "full_name": "Bob Call"
        })
        reg_b = recv_until(sock_b, lambda p: p.get("action") == "register_response")
        bob_id = reg_b["user"]["id"]

        # Bob gets direct conversation with Alice
        conv_id = db.get_direct_conversation(alice_id, bob_id)

        try:
            # 1. Alice sends call invite to Bob
            send_test_packet(sock_a, {
                "action": "call_invite",
                "caller_id": alice_id,
                "receiver_id": bob_id,
                "call_type": "video",
                "conversation_id": conv_id
            })

            # Alice receives call_invite_response
            resp_a = recv_until(sock_a, lambda p: p.get("action") == "call_invite_response")
            assert resp_a["success"] is True
            channel_id = resp_a["channel_id"]

            # Bob receives call_incoming broadcast
            inc_b = recv_until(sock_b, lambda p: p.get("type") == "call_incoming")
            assert inc_b["caller_id"] == alice_id
            assert inc_b["channel_id"] == channel_id
            assert inc_b["call_type"] == "video"

            # 2. Bob accepts call
            send_test_packet(sock_b, {
                "action": "call_accept",
                "channel_id": channel_id
            })
            resp_b = recv_until(sock_b, lambda p: p.get("action") == "call_accept_response")
            assert resp_b["success"] is True

            # Both receive call_connected
            conn_evt = recv_until(sock_a, lambda p: p.get("type") == "call_connected")
            assert conn_evt["channel_id"] == channel_id

            # 3. Bob sends media relay packet
            send_test_packet(sock_b, {
                "action": "call_media",
                "channel_id": channel_id,
                "sender_id": bob_id,
                "media_type": "audio",
                "data": "mock_audio_bytes"
            })

            # Alice receives media relay
            relay = recv_until(sock_a, lambda p: p.get("type") == "call_media_relay")
            assert relay["media_type"] == "audio"
            assert relay["data"] == "mock_audio_bytes"

            # 4. Alice ends the call
            send_test_packet(sock_a, {
                "action": "call_end",
                "channel_id": channel_id
            })
            resp_end = recv_until(sock_a, lambda p: p.get("action") == "call_end_response")
            assert resp_end["success"] is True

            # Bob receives call_ended
            ended_b = recv_until(sock_b, lambda p: p.get("type") == "call_ended")
            assert ended_b["type"] == "call_ended"

        finally:
            sock_a.close()
            sock_b.close()

    def test_forced_logout_on_duplicate_login(self, running_server):
        server, port, db = running_server
        
        # User registers
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock1.connect(("127.0.0.1", port))
        send_test_packet(sock1, {
            "action": "register",
            "username": "multi_user",
            "password": "MultiPass123!",
            "full_name": "Multi Device User"
        })
        recv_until(sock1, lambda p: p.get("action") == "register_response")
        
        # User logs in on Device 1
        send_test_packet(sock1, {
            "action": "login",
            "username": "multi_user",
            "password": "MultiPass123!"
        })
        login1 = recv_until(sock1, lambda p: p.get("action") == "login_response")
        assert login1["success"] is True

        # User logs in on Device 2
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock2.connect(("127.0.0.1", port))
        send_test_packet(sock2, {
            "action": "login",
            "username": "multi_user",
            "password": "MultiPass123!"
        })
        login2 = recv_until(sock2, lambda p: p.get("action") == "login_response")
        assert login2["success"] is True

        # Device 1 must receive forced_logout packet!
        kick_pkt = recv_until(sock1, lambda p: p.get("type") == "forced_logout")
        assert kick_pkt["type"] == "forced_logout"
        assert "Tài khoản của bạn vừa được đăng nhập" in kick_pkt["message"]

        sock1.close()
        sock2.close()
