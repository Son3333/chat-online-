import os
import tempfile
import pytest
from src.server.database import Database, validate_password_strength, hash_password


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = Database(path)
    yield db
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


class TestPasswordValidation:
    def test_valid_password(self):
        ok, msg = validate_password_strength("Test@1234")
        assert ok is True
        assert msg == ""

    def test_short_password(self):
        ok, msg = validate_password_strength("T@1a")
        assert ok is False
        assert "6 ký tự" in msg

    def test_missing_uppercase(self):
        ok, msg = validate_password_strength("test@1234")
        assert ok is False
        assert "in hoa" in msg

    def test_missing_lowercase(self):
        ok, msg = validate_password_strength("TEST@1234")
        assert ok is False
        assert "in thường" in msg

    def test_missing_number(self):
        ok, msg = validate_password_strength("Test@abcd")
        assert ok is False
        assert "chữ số" in msg

    def test_missing_special_char(self):
        ok, msg = validate_password_strength("Test12345")
        assert ok is False
        assert "ký tự đặc biệt" in msg

    def test_password_hash_deterministic(self):
        h1 = hash_password("Secret123!")
        h2 = hash_password("Secret123!")
        h3 = hash_password("Different123!")
        assert h1 == h2
        assert h1 != h3


class TestUserManagement:
    def test_register_and_authenticate_success(self, temp_db):
        res = temp_db.register_user("alice", "Pass@123", "Alice Nguyen")
        assert res["success"] is True
        user = res["user"]
        assert user["username"] == "alice"
        assert user["full_name"] == "Alice Nguyen"
        assert len(str(user["id"])) == 10  # 10-digit ID

        # Authenticate correct
        auth_res = temp_db.authenticate_user("alice", "Pass@123")
        assert auth_res["success"] is True
        auth_user = auth_res["user"]
        assert auth_user["id"] == user["id"]

    def test_register_duplicate_username(self, temp_db):
        temp_db.register_user("bob", "Pass@123", "Bob Tran")
        res2 = temp_db.register_user("bob", "Pass@123", "Bob Different")
        assert res2["success"] is False
        assert "đã có người sử dụng" in res2["message"]

    def test_authenticate_wrong_password(self, temp_db):
        temp_db.register_user("charlie", "Pass@123", "Charlie Pham")
        res = temp_db.authenticate_user("charlie", "WrongPass@123")
        assert res["success"] is False
        assert "Sai tên đăng nhập hoặc mật khẩu" in res["message"]

    def test_authenticate_nonexistent_user(self, temp_db):
        res = temp_db.authenticate_user("ghost_user", "Pass@123")
        assert res["success"] is False
        assert "Sai tên đăng nhập hoặc mật khẩu" in res["message"]

    def test_search_users(self, temp_db):
        u1 = temp_db.register_user("user_alpha", "Pass@123", "Alpha Nguyen")["user"]
        u2 = temp_db.register_user("user_beta", "Pass@123", "Beta Le")["user"]

        # Search by username substring
        results = temp_db.search_users("alpha", u2["id"])
        assert len(results) == 1
        assert results[0]["id"] == u1["id"]

        # Search by exact #ID
        id_search = temp_db.search_users(f"#{u1['id']}", u2["id"])
        assert len(id_search) == 1
        assert id_search[0]["username"] == "user_alpha"


class TestFriendsAndBlocks:
    def test_friend_request_lifecycle(self, temp_db):
        u1 = temp_db.register_user("friend_one", "Pass@123", "User One")["user"]
        u2 = temp_db.register_user("friend_two", "Pass@123", "User Two")["user"]

        # Status initially none
        st = temp_db.get_friendship_status(u1["id"], u2["id"])
        assert st == "none"

        # Send friend request
        res_req = temp_db.send_friend_request(u1["id"], u2["id"])
        assert res_req["success"] is True
        assert temp_db.get_friendship_status(u1["id"], u2["id"]) == "sent_pending"
        assert temp_db.get_friendship_status(u2["id"], u1["id"]) == "received_pending"

        # Accept friend request
        res_acc = temp_db.accept_friend_request(u2["id"], u1["id"])
        assert res_acc["success"] is True
        assert temp_db.get_friendship_status(u1["id"], u2["id"]) == "friends"

        # Friends list
        friends_1 = temp_db.get_friends(u1["id"])
        assert len(friends_1) == 1
        assert friends_1[0]["id"] == u2["id"]

        # Remove friend
        res_rem = temp_db.remove_friend(u1["id"], u2["id"])
        assert res_rem["success"] is True
        assert temp_db.get_friendship_status(u1["id"], u2["id"]) == "none"

    def test_block_and_unblock(self, temp_db):
        u1 = temp_db.register_user("blocker_one", "Pass@123", "Blocker")["user"]
        u2 = temp_db.register_user("target_two", "Pass@123", "Target")["user"]

        assert temp_db.is_blocked(u1["id"], u2["id"]) is False

        # Cannot block self
        ok_self, msg_self = temp_db.block_user(u1["id"], u1["id"])
        assert ok_self is False
        assert "chính mình" in msg_self

        # Block target
        ok_b, msg_b = temp_db.block_user(u1["id"], u2["id"])
        assert ok_b is True
        assert temp_db.is_blocked(u1["id"], u2["id"]) is True
        assert temp_db.is_blocked(u2["id"], u1["id"]) is True  # Mutual block check
        assert temp_db.is_user_blocked_by_me(u1["id"], u2["id"]) is True
        assert temp_db.is_user_blocked_by_me(u2["id"], u1["id"]) is False

        # Unblock
        ok_unb, _ = temp_db.unblock_user(u1["id"], u2["id"])
        assert ok_unb is True
        assert temp_db.is_blocked(u1["id"], u2["id"]) is False


class TestConversationsAndMessages:
    def test_direct_conversation_and_messages(self, temp_db):
        u1 = temp_db.register_user("member_one", "Pass@123", "Member One")["user"]
        u2 = temp_db.register_user("member_two", "Pass@123", "Member Two")["user"]

        conv_id = temp_db.get_direct_conversation(u1["id"], u2["id"])
        assert conv_id > 0

        # Sending messages
        m1 = temp_db.save_message(conv_id, u1["id"], "text", "Hello World!")
        assert m1["content"] == "Hello World!"
        assert m1["sender_name"] == "Member One"

        # Reply message
        m2 = temp_db.save_message(conv_id, u2["id"], "text", "Reply back", reply_to_id=m1["id"])
        assert m2["reply_to_id"] == m1["id"]

        messages = temp_db.get_messages(conv_id)
        assert len(messages) == 2

    def test_message_reactions(self, temp_db):
        u1 = temp_db.register_user("reactor_one", "Pass@123", "React One")["user"]
        u2 = temp_db.register_user("reactor_two", "Pass@123", "React Two")["user"]
        conv_id = temp_db.get_direct_conversation(u1["id"], u2["id"])
        msg = temp_db.save_message(conv_id, u1["id"], "text", "React to this!")

        # Toggle reaction (add)
        rx_list, _ = temp_db.toggle_reaction(msg["id"], u2["id"], "❤️")
        assert len(rx_list) == 1
        assert rx_list[0]["reaction"] == "❤️"
        assert rx_list[0]["count"] == 1

        # Toggle reaction again (remove)
        rx_list_after, _ = temp_db.toggle_reaction(msg["id"], u2["id"], "❤️")
        assert len(rx_list_after) == 0

    def test_recall_message_permissions(self, temp_db):
        u1 = temp_db.register_user("recall_sender", "Pass@123", "Sender")["user"]
        u2 = temp_db.register_user("recall_recv", "Pass@123", "Receiver")["user"]
        conv_id = temp_db.get_direct_conversation(u1["id"], u2["id"])
        msg = temp_db.save_message(conv_id, u1["id"], "text", "Secret Message")

        # Receiver cannot recall sender's message
        ok_fail, msg_fail, _ = temp_db.recall_message(msg["id"], u2["id"])
        assert ok_fail is False
        assert "chính mình gửi" in msg_fail

        # Sender recalls successfully
        ok_succ, msg_succ, ret_conv_id = temp_db.recall_message(msg["id"], u1["id"])
        assert ok_succ is True
        assert ret_conv_id == conv_id

        # Verify recalled message state in DB
        msgs = temp_db.get_messages(conv_id)
        assert msgs[0]["is_deleted"] == 1
        assert msgs[0]["content"] == "Tin nhắn đã được thu hồi"

    def test_pinned_message(self, temp_db):
        u1 = temp_db.register_user("pinner_one", "Pass@123", "Pinner")["user"]
        conv_id = temp_db.get_or_create_saved_conversation(u1["id"])
        msg = temp_db.save_message(conv_id, u1["id"], "text", "Important Note")

        # Pin message
        pinned = temp_db.pin_message(conv_id, msg["id"], u1["id"])
        assert pinned is not None
        assert pinned["id"] == msg["id"]

        # Unpin message
        ok_unpin = temp_db.unpin_message(conv_id)
        assert ok_unpin is True
        assert temp_db.get_pinned_message(conv_id) is None

    def test_saved_messages_cloud(self, temp_db):
        u1 = temp_db.register_user("cloud_user", "Pass@123", "Cloud User")["user"]
        conv1 = temp_db.get_or_create_saved_conversation(u1["id"])
        conv2 = temp_db.get_or_create_saved_conversation(u1["id"])
        assert conv1 == conv2  # Idempotent

    def test_delete_conversation_cascading(self, temp_db):
        u1 = temp_db.register_user("delete_one", "Pass@123", "Del One")["user"]
        u2 = temp_db.register_user("delete_two", "Pass@123", "Del Two")["user"]
        conv_id = temp_db.get_direct_conversation(u1["id"], u2["id"])
        msg = temp_db.save_message(conv_id, u1["id"], "text", "To be deleted")
        temp_db.toggle_reaction(msg["id"], u2["id"], "👍")

        assert len(temp_db.get_messages(conv_id)) == 1

        # Delete conversation
        del_ok = temp_db.delete_conversation(conv_id, u1["id"])
        assert del_ok is True
        assert len(temp_db.get_messages(conv_id)) == 0
