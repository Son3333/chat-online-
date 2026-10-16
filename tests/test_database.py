import os
import tempfile
import pytest
from src.server.database import Database, hash_password, validate_password_strength

@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_chat.db")
    db = Database(db_path=db_path)
    yield db
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass

class TestPasswordSecurity:
    def test_hash_password_consistency(self):
        h1 = hash_password("Secret123!")
        h2 = hash_password("Secret123!")
        assert h1 == h2
        assert len(h1) == 64

    def test_validate_password_strength(self):
        # Too short
        ok, msg = validate_password_strength("Aa1!")
        assert not ok
        assert "tối thiểu từ 6 ký tự" in msg

        # Missing uppercase
        ok, msg = validate_password_strength("secret123!")
        assert not ok
        assert "chữ cái in hoa" in msg

        # Missing lowercase
        ok, msg = validate_password_strength("SECRET123!")
        assert not ok
        assert "chữ cái in thường" in msg

        # Missing digit
        ok, msg = validate_password_strength("Secret!@#")
        assert not ok
        assert "chữ số" in msg

        # Missing special character
        ok, msg = validate_password_strength("Secret12345")
        assert not ok
        assert "ký tự đặc biệt" in msg

        # Valid strong password
        ok, msg = validate_password_strength("StrongPass123!")
        assert ok
        assert msg == ""

class TestUserManagement:
    def test_register_and_authenticate(self, temp_db):
        res = temp_db.register_user("alice_dev", "AlicePass123!", "Alice Nguyen")
        assert res["success"] is True
        user = res["user"]
        assert user["username"] == "alice_dev"
        assert user["full_name"] == "Alice Nguyen"
        assert user["id"] >= 1000000000

        # Duplicate register
        dup = temp_db.register_user("alice_dev", "AnotherPass123!", "Alice Again")
        assert dup["success"] is False
        assert "đã có người sử dụng" in dup["message"]

        # Successful auth
        auth_ok = temp_db.authenticate_user("alice_dev", "AlicePass123!")
        assert auth_ok["success"] is True
        assert auth_ok["user"]["id"] == user["id"]

        # Failed auth (wrong password)
        auth_fail = temp_db.authenticate_user("alice_dev", "WrongPass123!")
        assert auth_fail["success"] is False

        # Nonexistent user
        auth_none = temp_db.authenticate_user("nobody_here", "Pass123!")
        assert auth_none["success"] is False

    def test_register_invalid_usernames(self, temp_db):
        # Too short (< 3)
        res = temp_db.register_user("ab", "Pass123!", "Ab")
        assert res["success"] is False

        # Invalid characters (spaces, special signs)
        res = temp_db.register_user("user name", "Pass123!", "User Name")
        assert res["success"] is False
        res = temp_db.register_user("user#name", "Pass123!", "User Name")
        assert res["success"] is False

    def test_online_status_and_get_user(self, temp_db):
        res = temp_db.register_user("bob_ross", "BobPass123!", "Bob Ross")
        user_id = res["user"]["id"]

        user = temp_db.get_user_by_id(user_id)
        assert user is not None
        assert user["username"] == "bob_ross"
        assert user["is_online"] == 0

        temp_db.set_online_status(user_id, True)
        user_online = temp_db.get_user_by_id(user_id)
        assert user_online["is_online"] == 1

        temp_db.set_online_status(user_id, False)
        user_offline = temp_db.get_user_by_id(user_id)
        assert user_offline["is_online"] == 0

    def test_search_users(self, temp_db):
        r1 = temp_db.register_user("carol_danvers", "Carol123!", "Carol Danvers")
        r2 = temp_db.register_user("charlie_brown", "Charlie123!", "Charlie Brown")
        u1_id = r1["user"]["id"]
        u2_id = r2["user"]["id"]

        # Search by name/username
        results = temp_db.search_users("charlie", u1_id)
        assert len(results) >= 1
        assert any(r["id"] == u2_id for r in results)

        # Empty search returns empty
        assert temp_db.search_users("", u1_id) == []
        assert temp_db.search_users("   ", u1_id) == []

class TestConversationsAndMessaging:
    def test_direct_conversation_singleton(self, temp_db):
        u1 = temp_db.register_user("user_one", "Pass123!", "User One")["user"]["id"]
        u2 = temp_db.register_user("user_two", "Pass123!", "User Two")["user"]["id"]

        conv1 = temp_db.get_direct_conversation(u1, u2)
        conv2 = temp_db.get_direct_conversation(u2, u1)
        assert conv1 == conv2

    def test_group_conversation(self, temp_db):
        admin = temp_db.register_user("admin_user", "Admin123!", "Admin User")["user"]["id"]
        m1 = temp_db.register_user("member_one", "Member123!", "Member One")["user"]["id"]
        m2 = temp_db.register_user("member_two", "Member123!", "Member Two")["user"]["id"]

        group_id = temp_db.create_group_conversation("Project Team", admin, [m1, m2])
        assert group_id > 0

        members = temp_db.get_conversation_members(group_id)
        member_ids = {m["id"] for m in members}
        assert member_ids == {admin, m1, m2}

        # Check roles
        admin_member = next(m for m in members if m["id"] == admin)
        assert admin_member["role"] == "admin"

    def test_saved_messages_cloud(self, temp_db):
        u = temp_db.register_user("cloud_user", "Cloud123!", "Cloud User")["user"]["id"]
        saved_id1 = temp_db.get_or_create_saved_conversation(u)
        saved_id2 = temp_db.get_or_create_saved_conversation(u)
        assert saved_id1 == saved_id2

        convs = temp_db.get_user_conversations(u)
        saved_conv = next((c for c in convs if c["id"] == saved_id1), None)
        assert saved_conv is not None
        assert saved_conv["type"] == "saved"
        assert "Cloud của tôi" in saved_conv["title"]

    def test_send_and_get_messages_with_reply(self, temp_db):
        u1 = temp_db.register_user("sender_u", "Pass123!", "Sender User")["user"]["id"]
        u2 = temp_db.register_user("receiver_u", "Pass123!", "Receiver User")["user"]["id"]
        conv_id = temp_db.get_direct_conversation(u1, u2)

        # Message 1
        msg1 = temp_db.save_message(conv_id, u1, "text", "Xin chao!")
        assert msg1 is not None
        assert msg1["content"] == "Xin chao!"
        assert msg1["reply_to_id"] is None

        # Message 2 replying to Message 1
        msg2 = temp_db.save_message(conv_id, u2, "text", "Chao ban!", reply_to_id=msg1["id"])
        assert msg2 is not None
        assert msg2["reply_to_id"] == msg1["id"]
        assert msg2["reply_content"] == "Xin chao!"

        # Fetch messages
        messages = temp_db.get_messages(conv_id)
        assert len(messages) == 2
        assert messages[0]["id"] == msg1["id"]
        assert messages[1]["id"] == msg2["id"]
        assert messages[1]["reply_content"] == "Xin chao!"

    def test_recall_message(self, temp_db):
        u1 = temp_db.register_user("recall_user", "Pass123!", "Recall User")["user"]["id"]
        u2 = temp_db.register_user("other_user", "Pass123!", "Other User")["user"]["id"]
        conv_id = temp_db.get_direct_conversation(u1, u2)

        msg = temp_db.save_message(conv_id, u1, "text", "Tin nhan bi nham")
        assert msg["is_deleted"] == 0

        # Cannot recall as another user (returns (False, msg, None))
        ok, reason, c_id = temp_db.recall_message(msg["id"], u2)
        assert ok is False

        # Can recall as sender (returns (True, msg, conv_id))
        ok, reason, c_id = temp_db.recall_message(msg["id"], u1)
        assert ok is True
        assert c_id == conv_id

        messages = temp_db.get_messages(conv_id)
        assert messages[0]["is_deleted"] == 1

class TestReactionsAndPins:
    def test_reactions_toggle(self, temp_db):
        u1 = temp_db.register_user("react_u1", "Pass123!", "React User 1")["user"]["id"]
        u2 = temp_db.register_user("react_u2", "Pass123!", "React User 2")["user"]["id"]
        conv_id = temp_db.get_direct_conversation(u1, u2)
        msg = temp_db.save_message(conv_id, u1, "text", "Tuyet voi!")

        # 1. Add reaction ❤️
        rx_list, c_id = temp_db.toggle_reaction(msg["id"], u2, "❤️")
        assert len(rx_list) == 1
        assert rx_list[0]["reaction"] == "❤️"
        assert rx_list[0]["count"] == 1
        assert c_id == conv_id

        # 2. Change reaction ❤️ -> 👍
        rx_list2, _ = temp_db.toggle_reaction(msg["id"], u2, "👍")
        assert len(rx_list2) == 1
        assert rx_list2[0]["reaction"] == "👍"

        # 3. Toggle off (remove) 👍
        rx_list3, _ = temp_db.toggle_reaction(msg["id"], u2, "👍")
        assert len(rx_list3) == 0

    def test_pinned_messages(self, temp_db):
        u1 = temp_db.register_user("pin_u1", "Pass123!", "Pin User 1")["user"]["id"]
        conv_id = temp_db.get_or_create_saved_conversation(u1)
        msg1 = temp_db.save_message(conv_id, u1, "text", "Thong bao quan trong so 1")
        msg2 = temp_db.save_message(conv_id, u1, "text", "Thong bao quan trong so 2")

        # Pin msg1
        pinned = temp_db.pin_message(conv_id, msg1["id"], u1)
        assert pinned is not None
        assert pinned["id"] == msg1["id"]
        assert pinned["content"] == "Thong bao quan trong so 1"

        # Overwrite with msg2
        pinned2 = temp_db.pin_message(conv_id, msg2["id"], u1)
        assert pinned2 is not None
        assert pinned2["id"] == msg2["id"]

        # Unpin
        ok = temp_db.unpin_message(conv_id)
        assert ok is True
        assert temp_db.get_pinned_message(conv_id) is None

class TestBlockAndFiles:
    def test_block_and_unblock(self, temp_db):
        u1 = temp_db.register_user("blocker_u", "Pass123!", "Blocker")["user"]["id"]
        u2 = temp_db.register_user("spammer_u", "Pass123!", "Spammer")["user"]["id"]

        assert not temp_db.is_blocked(u1, u2)
        assert not temp_db.is_blocked(u2, u1)

        # Block (returns (bool, str))
        ok, msg = temp_db.block_user(u1, u2)
        assert ok is True
        assert temp_db.is_blocked(u1, u2) is True
        assert temp_db.is_blocked(u2, u1) is True

        # Unblock (returns (bool, str))
        ok, msg = temp_db.unblock_user(u1, u2)
        assert ok is True
        assert temp_db.is_blocked(u1, u2) is False

    def test_file_records(self, temp_db):
        u = temp_db.register_user("file_uploader", "Pass123!", "File Uploader")["user"]["id"]
        file_id = temp_db.save_file_record(
            original_name="document.pdf",
            stored_path="uploads/test_document.pdf",
            file_size=1048576,
            file_type="application/pdf",
            uploader_id=u
        )
        assert file_id > 0

        rec = temp_db.get_file_record(file_id)
        assert rec is not None
        assert rec["original_name"] == "document.pdf"
        assert rec["file_size"] == 1048576
