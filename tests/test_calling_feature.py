import threading
import time
import pytest
from src.server.database import Database
from src.server.server import ChatServer
from src.client.network import NetworkClient


@pytest.fixture
def call_test_environment(tmp_path):
    db_path = str(tmp_path / "call_test.db")
    db = Database(db_path)
    server = ChatServer(host="127.0.0.1", port=0, db=db)
    ready = threading.Event()

    server_thread = threading.Thread(target=lambda: server.start(ready_event=ready), daemon=True)
    server_thread.start()
    assert ready.wait(timeout=5.0), "Server failed to start in 5 seconds"

    yield server, server.port

    server.running = False
    if server.server_socket:
        try:
            server.server_socket.close()
        except Exception:
            pass


class TestCallingFeature:
    def test_voice_call_full_lifecycle(self, call_test_environment):
        """Kiểm thử trọn vẹn vòng đời cuộc gọi thoại: Mời -> Đổ chuông -> Nhấc máy -> Truyền Audio -> Kết thúc."""
        server, port = call_test_environment

        # Khởi tạo 2 Client
        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("caller_alice", "Pass@1234", "Alice Calling")["user"]
        c1.login("caller_alice", "Pass@1234")

        u2 = c2.register("callee_bob", "Pass@1234", "Bob Receiving")["user"]
        c2.login("callee_bob", "Pass@1234")

        conv_res = c1.start_direct_chat(u1["id"], u2["id"])
        conv_id = conv_res["conversation_id"]

        # Đăng ký các sự kiện nhận cuộc gọi phía Bob
        incoming_events = []
        incoming_done = threading.Event()
        connected_events = []
        connected_done = threading.Event()
        media_events = []
        media_done = threading.Event()
        ended_events = []
        ended_done = threading.Event()

        def _on_incoming(pkt):
            incoming_events.append(pkt)
            incoming_done.set()

        def _on_connected(pkt):
            connected_events.append(pkt)
            connected_done.set()

        def _on_media(pkt):
            media_events.append(pkt)
            media_done.set()

        def _on_ended(pkt):
            ended_events.append(pkt)
            ended_done.set()

        c2.register_callback("call_incoming", _on_incoming)
        c2.register_callback("call_connected", _on_connected)
        c2.register_callback("call_media_relay", _on_media)
        c2.register_callback("call_ended", _on_ended)

        # 1. Alice gọi cho Bob
        invite_res = c1.call_invite(u1["id"], u2["id"], conv_id, call_type="voice")
        assert invite_res is not None
        assert invite_res.get("success") is True
        channel_id = invite_res.get("channel_id")
        assert channel_id is not None

        # 2. Bob nhận được thông báo chuông đến
        assert incoming_done.wait(timeout=3.0), "Bob không nhận được sự kiện cuộc gọi đến"
        assert len(incoming_events) == 1
        assert incoming_events[0]["caller_name"] == "Alice Calling"
        assert incoming_events[0]["call_type"] == "voice"
        assert incoming_events[0]["channel_id"] == channel_id

        # 3. Bob chấp nhận cuộc gọi
        accept_res = c2.call_accept(channel_id)
        assert accept_res is not None
        assert accept_res.get("success") is True

        assert connected_done.wait(timeout=3.0), "Không nhận được sự kiện kết nối thành công"
        assert len(connected_events) == 1

        # 4. Truyền gói tin âm thanh giả lập
        c1.send_call_media(channel_id, u1["id"], "audio", "base64_fake_pcm_audio_data")
        assert media_done.wait(timeout=3.0), "Bob không nhận được dữ liệu âm thanh chuyển tiếp"
        assert media_events[0]["media_type"] == "audio"
        assert media_events[0]["data"] == "base64_fake_pcm_audio_data"

        # 5. Kết thúc cuộc gọi
        time.sleep(1.0) # Đợi 1 giây để thời lượng > 0
        end_res = c1.call_end(channel_id)
        assert end_res is not None
        assert end_res.get("success") is True

        assert ended_done.wait(timeout=3.0), "Không nhận được sự kiện kết thúc cuộc gọi"
        assert len(ended_events) == 1

        # 6. Kiểm tra tin nhắn lịch sử cuộc gọi tự động lưu vào hội thoại
        msgs_res = c1.get_messages(conv_id)
        assert msgs_res is not None
        msgs = msgs_res.get("messages", [])
        assert len(msgs) >= 1
        last_msg = msgs[-1]
        assert "Cuộc gọi thoại" in last_msg["content"]

        c1.disconnect()
        c2.disconnect()

    def test_video_call_reject_lifecycle(self, call_test_environment):
        """Kiểm thử cuộc gọi video bị đối phương từ chối."""
        server, port = call_test_environment

        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("vid_caller", "Pass@1234", "Video Caller")["user"]
        c1.login("vid_caller", "Pass@1234")

        u2 = c2.register("vid_callee", "Pass@1234", "Video Callee")["user"]
        c2.login("vid_callee", "Pass@1234")

        conv_id = c1.start_direct_chat(u1["id"], u2["id"])["conversation_id"]

        rejected_events = []
        reject_done = threading.Event()
        incoming_done = threading.Event()
        incoming_pkt = {}

        def _on_incoming(pkt):
            incoming_pkt.update(pkt)
            incoming_done.set()

        def _on_rejected(pkt):
            rejected_events.append(pkt)
            reject_done.set()

        c2.register_callback("call_incoming", _on_incoming)
        c1.register_callback("call_rejected", _on_rejected)

        # 1. Gọi video
        res = c1.call_invite(u1["id"], u2["id"], conv_id, call_type="video")
        assert res.get("success") is True
        channel_id = res.get("channel_id")

        # 2. Callee nhận cuộc gọi
        assert incoming_done.wait(timeout=3.0)
        assert incoming_pkt["call_type"] == "video"

        # 3. Callee từ chối cuộc gọi
        c2.call_reject(channel_id)

        # 4. Caller nhận được thông báo từ chối
        assert reject_done.wait(timeout=3.0), "Caller không nhận được phản hồi từ chối"
        assert len(rejected_events) == 1
        assert "từ chối" in rejected_events[0]["reason"]

        c1.disconnect()
        c2.disconnect()

    def test_call_blocked_user_prevented(self, call_test_environment):
        """Kiểm thử bảo mật: Người bị chặn không thể thực hiện cuộc gọi tới người chặn."""
        server, port = call_test_environment

        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("block_caller", "Pass@1234", "Block Caller")["user"]
        c1.login("block_caller", "Pass@1234")

        u2 = c2.register("block_callee", "Pass@1234", "Block Callee")["user"]
        c2.login("block_callee", "Pass@1234")

        conv_id = c1.start_direct_chat(u1["id"], u2["id"])["conversation_id"]

        # Bob (u2) chặn Alice (u1)
        block_res = c2.block_user(u2["id"], u1["id"])
        assert block_res.get("success") is True

        # Alice cố tình gọi điện cho Bob
        call_res = c1.call_invite(u1["id"], u2["id"], conv_id, call_type="voice")
        assert call_res.get("success") is False
        assert "bị chặn" in call_res.get("message", "")

        c1.disconnect()
        c2.disconnect()

    def test_missed_call_logging(self, call_test_environment):
        """Kiểm thử cuộc gọi nhỡ (Caller hủy máy trước khi Callee nghe)."""
        server, port = call_test_environment

        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("miss_caller", "Pass@1234", "Miss Caller")["user"]
        c1.login("miss_caller", "Pass@1234")

        u2 = c2.register("miss_callee", "Pass@1234", "Miss Callee")["user"]
        c2.login("miss_callee", "Pass@1234")

        conv_id = c1.start_direct_chat(u1["id"], u2["id"])["conversation_id"]

        # 1. Gọi video
        res = c1.call_invite(u1["id"], u2["id"], conv_id, call_type="video")
        channel_id = res["channel_id"]

        # 2. Hủy máy ngay lập tức (chưa kết nối)
        c1.call_end(channel_id)

        # 3. Tin nhắn phải lưu là 'Cuộc gọi video nhỡ'
        time.sleep(0.3)
        msgs_res = c1.get_messages(conv_id)
        msgs = msgs_res.get("messages", [])
        assert len(msgs) >= 1
        assert "Cuộc gọi video nhỡ" in msgs[-1]["content"]

        c1.disconnect()
        c2.disconnect()

    def test_media_relay_video_frames(self, call_test_environment):
        """Kiểm thử chuyển tiếp khung hình Video Base64 qua kênh media relay."""
        server, port = call_test_environment

        c1 = NetworkClient(host="127.0.0.1", port=port)
        c2 = NetworkClient(host="127.0.0.1", port=port)
        assert c1.connect() and c2.connect()

        u1 = c1.register("vid_user_1", "Pass@1234", "Vid One")["user"]
        c1.login("vid_user_1", "Pass@1234")
        u2 = c2.register("vid_user_2", "Pass@1234", "Vid Two")["user"]
        c2.login("vid_user_2", "Pass@1234")

        conv_id = c1.start_direct_chat(u1["id"], u2["id"])["conversation_id"]

        video_received = []
        video_done = threading.Event()

        def _on_media(pkt):
            if pkt.get("media_type") == "video":
                video_received.append(pkt)
                video_done.set()

        c2.register_callback("call_media_relay", _on_media)

        invite = c1.call_invite(u1["id"], u2["id"], conv_id, call_type="video")
        ch_id = invite["channel_id"]
        c2.call_accept(ch_id)

        # Gửi 1 khung hình JPEG base64 giả lập
        fake_frame = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBD"
        c1.send_call_media(ch_id, u1["id"], "video", fake_frame)

        assert video_done.wait(timeout=3.0), "Client 2 không nhận được khung hình video relay"
        assert len(video_received) == 1
        assert video_received[0]["data"] == fake_frame

        c1.call_end(ch_id)
        c1.disconnect()
        c2.disconnect()

    def test_active_call_receive_media_handler(self):
        """Kiểm thử tính năng tiếp nhận packet media an toàn qua method receive_media."""
        from src.client.call.call_window import ActiveCallWindow

        # Tạo mock object không cần render GUI thật
        class DummyWindow:
            running = True
            def on_media_received(self, m_type, data):
                self.last_received = (m_type, data)

        dummy = DummyWindow()
        ActiveCallWindow.receive_media(dummy, {
            "media_type": "audio",
            "data": "dummy_audio_b64"
        })
        assert getattr(dummy, "last_received", None) == ("audio", "dummy_audio_b64")

