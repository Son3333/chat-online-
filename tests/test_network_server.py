import os
import tempfile
import threading
import time
import socket
import pytest
from src.server.database import Database
from src.server.server import ChatServer
from src.client.network import NetworkClient


@pytest.fixture
def running_test_server():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)

    # Use port 0 for automatic free ephemeral port assignment
    server = ChatServer(host="127.0.0.1", port=0, db=db)
    ready = threading.Event()

    server_thread = threading.Thread(target=lambda: server.start(ready_event=ready), daemon=True)
    server_thread.start()
    assert ready.wait(timeout=5.0), "Server failed to start in 5 seconds"

    assigned_port = server.port
    yield server, assigned_port

    # Cleanup server
    server.running = False
    if server.server_socket:
        try:
            server.server_socket.close()
        except Exception:
            pass
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


class TestNetworkIntegration:
    def test_client_connect_and_disconnect(self, running_test_server):
        server, port = running_test_server
        client = NetworkClient(host="127.0.0.1", port=port)
        ok = client.connect()
        assert ok is True
        assert client.connected is True
        client.disconnect()
        assert client.connected is False

    def test_client_register_and_login_flow(self, running_test_server):
        server, port = running_test_server
        client = NetworkClient(host="127.0.0.1", port=port)
        assert client.connect() is True

        # Register
        res_reg = client.register("net_user_1", "Pass@1234", "Net User One")
        assert res_reg is not None
        assert res_reg.get("success") is True
        user = res_reg.get("user")
        assert user["username"] == "net_user_1"

        # Login
        res_login = client.login("net_user_1", "Pass@1234")
        assert res_login is not None
        assert res_login.get("success") is True
        assert res_login["user"]["id"] == user["id"]

        client.disconnect()

    def test_messaging_between_two_clients(self, running_test_server):
        server, port = running_test_server

        # Client 1
        c1 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() is True
        u1 = c1.register("chat_alice", "Pass@1234", "Alice Chat")["user"]
        c1.login("chat_alice", "Pass@1234")

        # Client 2
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c2.connect() is True
        u2 = c2.register("chat_bob", "Pass@1234", "Bob Chat")["user"]
        c2.login("chat_bob", "Pass@1234")

        # Register real-time push callback on Client 2
        received_msgs = []
        msg_event = threading.Event()

        def _on_msg(pkt):
            received_msgs.append(pkt)
            msg_event.set()

        c2.register_callback("new_message", _on_msg)

        # Start direct chat from Alice to Bob
        start_res = c1.start_direct_chat(u1["id"], u2["id"])
        assert start_res is not None
        conv_id = start_res["conversation_id"]

        # Alice sends message to Bob
        send_ok = c1.send_message(conv_id, u1["id"], "Hello Bob, this is live real-time!")
        assert send_ok is True

        # Bob receives message via real-time push event
        assert msg_event.wait(timeout=4.0), "Client 2 did not receive pushed message"
        assert len(received_msgs) == 1
        pushed = received_msgs[0]
        assert pushed["type"] == "new_message"
        assert pushed["message"]["content"] == "Hello Bob, this is live real-time!"
        assert pushed["message"]["sender_name"] == "Alice Chat"

        c1.disconnect()
        c2.disconnect()

    def test_typing_indicator_broadcast(self, running_test_server):
        server, port = running_test_server
        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("type_user_1", "Pass@1234", "Typer One")["user"]
        c1.login("type_user_1", "Pass@1234")
        u2 = c2.register("type_user_2", "Pass@1234", "Typer Two")["user"]
        c2.login("type_user_2", "Pass@1234")

        typing_events = []
        type_done = threading.Event()

        def _on_typing(pkt):
            typing_events.append(pkt)
            type_done.set()

        c2.register_callback("user_typing", _on_typing)

        conv_id = c1.start_direct_chat(u1["id"], u2["id"])["conversation_id"]
        c1.send_typing(conv_id, u1["id"], "Typer One")

        assert type_done.wait(timeout=3.0), "Typing indicator was not broadcasted"
        assert len(typing_events) == 1
        assert typing_events[0]["sender_name"] == "Typer One"

        c1.disconnect()
        c2.disconnect()

    def test_group_creation_and_rate_limiting(self, running_test_server):
        server, port = running_test_server
        c = NetworkClient(host="127.0.0.1", port=port)
        assert c.connect()
        u1 = c.register("grp_creator", "Pass@1234", "Creator")["user"]
        c.login("grp_creator", "Pass@1234")

        u2 = c.register("grp_member", "Pass@1234", "Member")["user"]

        # Valid group creation
        res = c.create_group(u1["id"], "Team Project", [u2["id"]])
        assert res is not None
        assert res.get("success") is True
        assert res.get("conversation_id") is not None

        # Negative test: Empty name
        res_empty = c.create_group(u1["id"], "   ", [u2["id"]])
        assert res_empty.get("success") is False
        assert "không được để trống" in res_empty.get("message", "")

        # Negative test: No other members
        res_no_mem = c.create_group(u1["id"], "Solo Team", [])
        assert res_no_mem.get("success") is False

        c.disconnect()
