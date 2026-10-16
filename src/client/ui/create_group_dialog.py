import customtkinter as ctk
import threading
import time

class CreateGroupDialog(ctk.CTkFrame):
    """
    Modal lồng trực tiếp bên trong cửa sổ chính (In-App Overlay Modal),
    không mở cửa sổ riêng biệt trên hệ điều hành (không hiện thêm tab/taskbar).
    Có tích hợp chống spam và xác thực thành viên.
    """
    def __init__(self, master, current_user: dict, network_client, on_group_created):
        # Lớp nền mờ phủ kín toàn bộ giao diện chính
        super().__init__(master, fg_color=("#0F172A", "#020617"), corner_radius=0)
        self.current_user = current_user
        self.net = network_client
        self.on_group_created = on_group_created
        
        # Danh sách người dùng đã được thêm vào nhóm: id -> user_dict
        self.added_members = {}
        self._is_submitting = False

        # Phủ kín cửa sổ chính và đưa lên trên cùng
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()

        # Cho phép bấm phím Escape hoặc bấm ra ngoài nền để đóng modal
        self.bind("<Button-1>", self._on_backdrop_click)
        try:
            self.master.bind("<Escape>", self._on_escape_key)
        except Exception:
            pass

        self._build_ui()
        self._load_contacts()

    def _on_backdrop_click(self, event):
        if event.widget == self and not self._is_submitting:
            self.close()

    def _on_escape_key(self, event=None):
        if not self._is_submitting:
            self.close()

    def close(self):
        """Đóng modal an toàn và giải phóng sự kiện."""
        try:
            self.master.unbind("<Escape>")
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass

    def _build_ui(self):
        # Thẻ Modal Box nổi ở trung tâm màn hình
        self.card = ctk.CTkFrame(
            self,
            width=500,
            height=580,
            corner_radius=14,
            fg_color=("#FFFFFF", "#1E293B"),
            border_width=1,
            border_color=("#E2E8F0", "#334155")
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center")
        self.card.pack_propagate(False)

        # 1. Header (Tiêu đề + Nút đóng ✕)
        header_row = ctk.CTkFrame(self.card, fg_color="transparent")
        header_row.pack(fill="x", padx=20, pady=(16, 2))

        ctk.CTkLabel(
            header_row, 
            text="👥 Tạo Nhóm Trò Chuyện Mới", 
            font=ctk.CTkFont(size=17, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header_row,
            text="✕",
            width=28,
            height=28,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="transparent",
            text_color=("gray50", "gray70"),
            hover_color=("#F1F5F9", "#334155"),
            corner_radius=14,
            command=self.close
        ).pack(side="right")
        
        ctk.CTkLabel(
            self.card, 
            text="Chọn bạn bè từ Danh bạ hoặc nhập chính xác @username / ID", 
            font=ctk.CTkFont(size=11),
            text_color="gray50"
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # 2. Tên nhóm
        frame_name = ctk.CTkFrame(self.card, fg_color="transparent")
        frame_name.pack(fill="x", padx=20, pady=(0, 8))
        
        ctk.CTkLabel(frame_name, text="Tên nhóm chat:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 3))
        self.name_entry = ctk.CTkEntry(frame_name, placeholder_text="Ví dụ: Nhóm Đồ Án, Nhóm Học Tập...", height=36, corner_radius=8)
        self.name_entry.pack(fill="x")

        # 3. Ô tìm kiếm & thêm thành viên qua Username hoặc ID
        frame_search = ctk.CTkFrame(self.card, fg_color="transparent")
        frame_search.pack(fill="x", padx=20, pady=(0, 4))
        
        ctk.CTkLabel(
            frame_search, 
            text="Thêm người tham gia (Username hoặc ID):", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 3))
        
        search_row = ctk.CTkFrame(frame_search, fg_color="transparent")
        search_row.pack(fill="x")
        
        self.search_entry = ctk.CTkEntry(
            search_row, 
            placeholder_text="Nhập @username hoặc ID (vd: son hoặc #1)...", 
            height=36, 
            corner_radius=8
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self.do_search_and_add())
        
        self.btn_add = ctk.CTkButton(
            search_row, 
            text="➕ Thêm", 
            width=75, 
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            command=self.do_search_and_add
        )
        self.btn_add.pack(side="right")

        self.lbl_msg = ctk.CTkLabel(self.card, text="", font=ctk.CTkFont(size=11), text_color="#EF4444")
        self.lbl_msg.pack(padx=20, pady=(2, 4))

        # 4. Tab view nhỏ: Danh bạ của bạn / Thành viên đã chọn
        self.tabview = ctk.CTkTabview(self.card, height=220, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        self.tab_contacts = self.tabview.add("👥 Danh Bạ Bạn Bè")
        self.tab_selected = self.tabview.add("✅ Đã Chọn Vào Nhóm (0)")
        
        # Scroll frame danh bạ
        self.contacts_scroll = ctk.CTkScrollableFrame(self.tab_contacts, fg_color="transparent")
        self.contacts_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        # Scroll frame đã chọn
        self.selected_scroll = ctk.CTkScrollableFrame(self.tab_selected, fg_color="transparent")
        self.selected_scroll.pack(fill="both", expand=True, padx=4, pady=4)
        
        self._refresh_selected_view()

        # 5. Nút hành động
        btn_box = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))
        
        ctk.CTkButton(
            btn_box, 
            text="Hủy Bỏ", 
            width=100, 
            height=38, 
            fg_color="transparent", 
            border_width=1,
            hover_color=("#F1F5F9", "#334155"),
            command=self.close
        ).pack(side="left")
        
        self.btn_submit = ctk.CTkButton(
            btn_box, 
            text="Tạo Nhóm Ngay", 
            width=150, 
            height=38, 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.do_create_group
        )
        self.btn_submit.pack(side="right")

    def _load_contacts(self):
        """Tải danh sách bạn bè trong danh bạ cá nhân của người dùng."""
        def _fetch():
            res = self.net.get_friends(self.current_user["id"])
            friends = res.get("friends", []) if res else []
            self.after(0, lambda: self._render_contacts(friends))
        threading.Thread(target=_fetch, daemon=True).start()

    def _render_contacts(self, friends: list):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        for w in self.contacts_scroll.winfo_children():
            w.destroy()
            
        if not friends:
            box = ctk.CTkFrame(self.contacts_scroll, fg_color="transparent")
            box.pack(pady=30)
            ctk.CTkLabel(
                box, 
                text="Danh bạ của bạn chưa có bạn bè nào.\nHãy dùng ô tìm kiếm ở trên để thêm bạn vào nhóm nhé!",
                font=ctk.CTkFont(size=12),
                text_color="gray50"
            ).pack()
            return

        for u in friends:
            card = ctk.CTkFrame(self.contacts_scroll, fg_color=("white", "#1E293B"), corner_radius=8, height=44)
            card.pack(fill="x", padx=4, pady=3)
            
            col = u.get("avatar_color", "#2563EB")
            avatar_btn = ctk.CTkButton(
                card,
                text=u["full_name"][:1].upper(),
                width=30,
                height=30,
                corner_radius=15,
                fg_color=col,
                text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"),
                state="disabled"
            )
            avatar_btn.pack(side="left", padx=8, pady=6)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=4)
            
            ctk.CTkLabel(info, text=u["full_name"], font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"@{u['username']} • ID: #{u['id']}", font=ctk.CTkFont(size=10), text_color="gray50", anchor="w").pack(anchor="w")
            
            # Nút chọn / bỏ chọn
            is_added = u["id"] in self.added_members
            btn = ctk.CTkButton(
                card,
                text="✓ Đã chọn" if is_added else "➕ Thêm",
                width=75,
                height=26,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#10B981" if is_added else ("gray80", "#334155"),
                hover_color="#059669" if is_added else ("gray70", "#475569"),
                command=lambda user_item=u: self.toggle_contact(user_item)
            )
            btn.pack(side="right", padx=8)

    def toggle_contact(self, user_item):
        uid = user_item["id"]
        if uid in self.added_members:
            del self.added_members[uid]
        else:
            self.added_members[uid] = user_item
            
        self._load_contacts()
        self._refresh_selected_view()

    def do_search_and_add(self):
        query = self.search_entry.get().strip()
        if not query:
            self.lbl_msg.configure(text="Vui lòng nhập Username hoặc ID!", text_color="#EF4444")
            return
            
        self.btn_add.configure(state="disabled")
        self.lbl_msg.configure(text="Đang tìm kiếm...", text_color="#3B82F6")
        
        def _search():
            res = self.net.search_users(query, self.current_user["id"])
            def _apply():
                if not self.winfo_exists():
                    return
                self.btn_add.configure(state="normal")
                users = res.get("users", []) if res else []
                if not users:
                    self.lbl_msg.configure(
                        text=f"Không tìm thấy người dùng với Username/ID: '{query}'!", 
                        text_color="#EF4444"
                    )
                    return

                target_user = users[0]
                uid = target_user["id"]
                
                if uid == self.current_user["id"]:
                    self.lbl_msg.configure(text="Bạn đã là Trưởng nhóm, không cần thêm chính mình!", text_color="#EF4444")
                    return
                    
                if uid in self.added_members:
                    self.lbl_msg.configure(text=f"Người dùng @{target_user['username']} đã được chọn rồi!", text_color="#F59E0B")
                    return

                self.added_members[uid] = target_user
                self.search_entry.delete(0, "end")
                self.lbl_msg.configure(
                    text=f"Đã thêm thành công: {target_user['full_name']} (@{target_user['username']})", 
                    text_color="#10B981"
                )
                self._load_contacts()
                self._refresh_selected_view()
            self.after(0, _apply)
        threading.Thread(target=_search, daemon=True).start()

    def _refresh_selected_view(self):
        try:
            if not self.winfo_exists():
                return
        except Exception:
            return
        for w in self.selected_scroll.winfo_children():
            w.destroy()
            
        count = len(self.added_members)
        self.tabview.set("👥 Danh Bạ Bạn Bè" if count == 0 else f"✅ Đã Chọn Vào Nhóm ({count})")
        
        if not self.added_members:
            box = ctk.CTkFrame(self.selected_scroll, fg_color="transparent")
            box.pack(pady=30)
            ctk.CTkLabel(
                box, 
                text="Chưa có thành viên nào được chọn vào nhóm.\nHãy chọn từ Danh bạ hoặc tìm kiếm ở trên nhé!", 
                font=ctk.CTkFont(size=12),
                text_color="gray50"
            ).pack()
            return

        for uid, u in self.added_members.items():
            card = ctk.CTkFrame(self.selected_scroll, fg_color=("white", "#1E293B"), corner_radius=8, height=44)
            card.pack(fill="x", padx=4, pady=3)
            
            col = u.get("avatar_color", "#2563EB")
            avatar_btn = ctk.CTkButton(
                card,
                text=u["full_name"][:1].upper(),
                width=30,
                height=30,
                corner_radius=15,
                fg_color=col,
                text_color="white",
                font=ctk.CTkFont(size=12, weight="bold"),
                state="disabled"
            )
            avatar_btn.pack(side="left", padx=8, pady=6)
            
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=4)
            
            ctk.CTkLabel(info, text=u["full_name"], font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(info, text=f"@{u['username']}  •  ID: #{u['id']}", font=ctk.CTkFont(size=10), text_color="gray50", anchor="w").pack(anchor="w")
            
            ctk.CTkButton(
                card, 
                text="✕ Bỏ", 
                width=55, 
                height=26, 
                corner_radius=6,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#FEE2E2", "#7F1D1D"),
                hover_color=("#FCA5A5", "#991B1B"),
                text_color=("#DC2626", "#FCA5A5"),
                command=lambda id_val=uid: self.remove_selected(id_val)
            ).pack(side="right", padx=8)

    def remove_selected(self, uid):
        if uid in self.added_members:
            del self.added_members[uid]
            self._load_contacts()
            self._refresh_selected_view()

    def do_create_group(self):
        """Tạo nhóm với cơ chế chống spam (Debounce lock + async request)."""
        if self._is_submitting:
            return

        name = self.name_entry.get().strip()
        if not name:
            self.lbl_msg.configure(text="⚠️ Vui lòng nhập tên nhóm chat!", text_color="#EF4444")
            self.name_entry.focus_set()
            return

        if len(name) > 60:
            self.lbl_msg.configure(text="⚠️ Tên nhóm tối đa 60 ký tự!", text_color="#EF4444")
            return
            
        selected_uids = list(self.added_members.keys())
        if not selected_uids:
            self.lbl_msg.configure(text="⚠️ Vui lòng chọn ít nhất 1 thành viên tham gia!", text_color="#EF4444")
            return
            
        # Kích hoạt trạng thái khóa chống spam
        self._is_submitting = True
        self.btn_submit.configure(state="disabled", text="⏳ Đang tạo nhóm...", fg_color="gray50")
        self.lbl_msg.configure(text="Đang xử lý tạo nhóm...", text_color="#3B82F6")

        def _worker():
            try:
                res = self.net.create_group(self.current_user["id"], name, selected_uids)
                def _apply():
                    if not self.winfo_exists():
                        return
                    if res and res.get("success"):
                        conv_id = res.get("conversation_id")
                        if self.on_group_created:
                            self.on_group_created(conv_id)
                        self.close()
                    else:
                        err = res.get("message", "Tạo nhóm thất bại!") if res else "Không thể kết nối máy chủ!"
                        self.lbl_msg.configure(text=f"⚠️ {err}", text_color="#EF4444")
                        self.btn_submit.configure(state="normal", text="Tạo Nhóm Ngay", fg_color="#2563EB")
                        # Cooldown 2.5s trước khi cho phép bấm lại
                        def _unlock():
                            self._is_submitting = False
                        self.after(2500, _unlock)
                self.after(0, _apply)
            except Exception as ex:
                def _err():
                    if self.winfo_exists():
                        self.lbl_msg.configure(text=f"⚠️ Lỗi: {ex}", text_color="#EF4444")
                        self.btn_submit.configure(state="normal", text="Tạo Nhóm Ngay", fg_color="#2563EB")
                        self._is_submitting = False
                self.after(0, _err)

        threading.Thread(target=_worker, daemon=True).start()
