# MA TRẬN TÍNH NĂNG & TIẾN ĐỘ CHUYỂN ĐỔI (FEATURE MATRIX)
## DỰ ÁN ỨNG DỤNG NHẮN TIN TELEGRAM-STYLE DESKTOP (REACT + TYPESCRIPT + ELECTRON)

| ID | Nhóm chức năng | Tên tính năng | Python GUI cũ | Backend API / Action | React Component Mới | Trạng thái | Test tương ứng |
|:---:|:---|:---|:---|:---|:---|:---:|:---|
| F01 | Xác thực | Đăng nhập tài khoản | `AuthFrame` (mode login) | `action: "login"` | `src/features/auth/LoginModal.tsx` | Hoàn thành | `tests/test_auth.test.tsx`, `test_database.py` |
| F02 | Xác thực | Đăng ký tài khoản mới | `AuthFrame` (mode register) | `action: "register"` | `src/features/auth/RegisterModal.tsx` | Hoàn thành | `test_auth.test.tsx`, `test_database.py` |
| F03 | Xác thực | Đăng xuất & Dọn session | `MainWindow.logout` | `action: "logout"` | `src/features/auth/useAuth.ts` | Hoàn thành | `test_auth.test.tsx` |
| F04 | Hội thoại | Danh sách cuộc trò chuyện | `MainWindow.conv_scroll` | `action: "get_conversations"` | `src/features/chat/ChatList.tsx` | Hoàn thành | `test_chat_list.test.tsx` |
| F05 | Hội thoại | Chọn & Tải lịch sử chat | `MainWindow.select_conversation` | `action: "get_messages"` | `src/features/chat/ChatArea.tsx` | Hoàn thành | `test_chat_messages.test.tsx` |
| F06 | Tin nhắn | Gửi tin nhắn văn bản | `MainWindow.send_text_message` | `action: "send_message"` | `src/features/chat/ChatComposer.tsx` | Hoàn thành | `test_chat_composer.test.tsx`, `test_network_server.py` |
| F07 | Tin nhắn | Trả lời trích dẫn (Quote/Reply) | `MainWindow.reply_bar` | `reply_to_id` in message payload | `ChatComposer.tsx` + `ChatBubble.tsx` | Hoàn thành | `test_chat_composer.test.tsx` |
| F08 | Tin nhắn | Ghim tin nhắn hội thoại | `MainWindow.pinned_banner` | `action: "pin_message"`, `get_pinned_message` | `src/features/chat/PinnedBanner.tsx` | Hoàn thành | `test_chat_messages.test.tsx`, `test_database.py` |
| F09 | Tin nhắn | Thả cảm xúc tin nhắn (Reactions) | `ChatBubble.rx_menu` | `action: "toggle_reaction"` | `src/features/chat/ReactionPicker.tsx` | Hoàn thành | `test_reactions.test.tsx`, `test_database.py` |
| F10 | Tin nhắn | Thu hồi tin nhắn 2 phía | `ChatBubble.confirm_recall` | `action: "recall_message"` | `ChatBubble.tsx` (Context menu) | Hoàn thành | `test_chat_messages.test.tsx`, `test_database.py` |
| F11 | Đính kèm | Gửi và xem trước ảnh (Image Preview) | `ChatBubble` preview thumbnail | `action: "upload_file"`, `"download_file"` | `ChatBubble.tsx` + `MediaModal.tsx` | Hoàn thành | `test_chat_messages.test.tsx` |
| F12 | Đính kèm | Gửi và tải tài liệu (File Download) | `ChatBubble` file card | `action: "upload_file"`, `"download_file"` | `src/features/chat/FileBubble.tsx` | Hoàn thành | `test_chat_messages.test.tsx` |
| F13 | Lưu trữ | Cloud của tôi (Saved Messages) | `btn_saved_cloud` | `action: "get_saved_conversation"` | `src/features/cloud/SavedMessages.tsx` | Hoàn thành | `test_cloud.test.tsx`, `test_database.py` |
| F14 | Danh bạ | Tìm kiếm người dùng theo username/ID | `MainWindow.search_entry` | `action: "search_users"` | `src/features/contacts/SearchUsers.tsx` | Hoàn thành | `test_contacts.test.tsx`, `test_database.py` |
| F15 | Danh bạ | Gửi lời mời & kết bạn | `MainWindow.friends_scroll` | `action: "send_friend_request"`, `"accept_friend_request"` | `src/features/contacts/FriendsList.tsx` | Hoàn thành | `test_contacts.test.tsx`, `test_database.py` |
| F16 | Danh bạ | Chặn / Bỏ chặn người dùng | `MainWindow._block_partner` | `action: "block_user"`, `"unblock_user"` | `src/features/contacts/BlockManager.tsx` | Hoàn thành | `test_contacts.test.tsx`, `test_database.py` |
| F17 | Nhóm | Tạo nhóm trò chuyện mới | `CreateGroupDialog` | `action: "create_group"` | `src/features/groups/CreateGroupModal.tsx` | Hoàn thành | `test_group.test.tsx`, `test_network_server.py` |
| F18 | Cuộc gọi | Cuộc gọi Thoại & Video (WebRTC / Socket Relay) | `CallWindow` | `action: "call_request"`, `"call_accept"`, `"call_media"` | `src/features/calls/CallModal.tsx` | Hoàn thành | `test_calls.test.tsx`, `test_calling_feature.py` |
| F19 | Trực tuyến | Typing Indicator & Online/Offline status | `MainWindow.lbl_typing` | `action: "typing"`, push `user_typing`, `user_status_changed` | `src/features/chat/ChatHeader.tsx` | Hoàn thành | `test_chat_header.test.tsx`, `test_network_server.py` |
| F20 | Bảo mật | Khóa màn hình nhanh (App Lock) | `QuickLockWindow` | Client PIN verification hash | `src/features/security/LockScreen.tsx` | Hoàn thành | `test_security.test.tsx` |
| F21 | Cửa sổ | Ghim cửa sổ trên cùng (Always on Top) | `MainWindow.toggle_topmost` | Electron IPC `set-always-on-top` | `src/components/TitleBar.tsx` | Hoàn thành | `test_window.test.tsx` |
| F22 | Cửa sổ | Khay hệ thống & Thu nhỏ (System Tray) | `TrayManager` | Electron Tray API | `electron/tray.ts` | Hoàn thành | `test_electron_ipc.test.ts` |
| F23 | Giao diện | Dark Mode & Light Mode | `MainWindow.toggle_theme` | CSS theme switch (class="dark") | `src/components/ThemeToggle.tsx` | Hoàn thành | `test_theme.test.tsx` |
| F24 | Giao diện | Emoji Picker Telegram chuẩn | `MainWindow.toggle_emoji_picker` | Inline Unicode Emoji Categorized Picker | `src/components/EmojiPicker.tsx` | Hoàn thành | `test_emoji.test.tsx` |

