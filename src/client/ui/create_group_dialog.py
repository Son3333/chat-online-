import customtkinter as ctk
from tkinter import messagebox

class CreateGroupDialog(ctk.CTkToplevel):
    def __init__(self, master, current_user: dict, network_client, on_group_created):
        super().__init__(master)
        self.current_user = current_user
        self.net = network_client
        self.on_group_created = on_group_created
        
        # Danh sách người dùng đã được thêm vào nhóm: id -> user_dict
        self.added_members = {}

        self.title("Tạo Nhóm Trò Chuyện Riêng Tư")
        self.geometry("460x560")
        self.resizable(False, False)
        self.grab_set()
        
        self._build_ui()

    def _build_ui(self):
        # 1. Header
        ctk.CTkLabel(
            self, 
            text="👥 Tạo Nhóm Trò Chuyện Mới", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(16, 2))
        
        ctk.CTkLabel(
            self, 
            text="Bảo mật: Chỉ thêm được thành viên khi biết chính xác Username hoặc ID", 
            font=ctk.CTkFont(size=11),
            text_color="gray60"
        ).pack(pady=(0, 12))

        # 2. Tên nhóm
        frame_name = ctk.CTkFrame(self, fg_color="transparent")
        frame_name.pack(fill="x", padx=20, pady=(0, 8))
        
        ctk.CTkLabel(frame_name, text="Tên nhóm chat:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 3))
        self.name_entry = ctk.CTkEntry(frame_name, placeholder_text="Ví dụ: Nhóm Đồ Án, Team Công Việc...", height=36, corner_radius=8)
        self.name_entry.pack(fill="x")

        # 3. Ô tìm kiếm & thêm thành viên qua Username hoặc ID
        frame_search = ctk.CTkFrame(self, fg_color="transparent")
        frame_search.pack(fill="x", padx=20, pady=(0, 4))
        
        ctk.CTkLabel(
            frame_search, 
            text="Thêm người tham gia (Nhập đúng Username hoặc ID):", 
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", pady=(0, 3))
        
        search_row = ctk.CTkFrame(frame_search, fg_color="transparent")
        search_row.pack(fill="x")
        
        self.search_entry = ctk.CTkEntry(
            search_row, 
            placeholder_text="Nhập Username (vd: thaison) hoặc ID (vd: #2)...", 
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

        # Nhãn thông báo kết quả tìm kiếm (lỗi hoặc thành công)
        self.lbl_msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=11), text_color="#EF4444")
        self.lbl_msg.pack(padx=20, pady=(2, 6))

        # 4. Danh sách thành viên đã chọn
        list_header_row = ctk.CTkFrame(self, fg_color="transparent")
        list_header_row.pack(fill="x", padx=20, pady=(0, 4))
        
        self.lbl_count = ctk.CTkLabel(
            list_header_row, 
            text="Danh sách thành viên sẽ vào nhóm (0 người):", 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_count.pack(side="left")

        self.members_scroll = ctk.CTkScrollableFrame(self, height=190, corner_radius=10, fg_color=("gray95", "#0F172A"))
        self.members_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        
        self._refresh_members_list()

        # 5. Nút hành động
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))
        
        ctk.CTkButton(
            btn_box, 
            text="Hủy Bỏ", 
            width=100, 
            height=38, 
            fg_color="transparent", 
            border_width=1,
            command=self.destroy
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

    def do_search_and_add(self):
        query = self.search_entry.get().strip()
        if not query:
            self.lbl_msg.configure(text="Vui lòng nhập Username hoặc ID người bạn muốn thêm!", text_color="#EF4444")
            return
            
        self.btn_add.configure(state="disabled")
        self.lbl_msg.configure(text="Đang tìm kiếm...", text_color="#3B82F6")
        self.update_idletasks()
        
        res = self.net.search_users(query, self.current_user["id"])
        self.btn_add.configure(state="normal")
        
        users = res.get("users", []) if res else []
        if not users:
            self.lbl_msg.configure(
                text=f"Không tìm thấy người dùng với Username/ID: '{query}'!", 
                text_color="#EF4444"
            )
            return

        # Lấy người dùng phù hợp nhất
        target_user = users[0]
        uid = target_user["id"]
        
        if uid == self.current_user["id"]:
            self.lbl_msg.configure(text="Bạn đã là Trưởng nhóm, không cần thêm chính mình!", text_color="#EF4444")
            return
            
        if uid in self.added_members:
            self.lbl_msg.configure(text=f"Người dùng @{target_user['username']} đã có trong danh sách rồi!", text_color="#F59E0B")
            return

        # Thêm vào danh sách
        self.added_members[uid] = target_user
        self.search_entry.delete(0, "end")
        self.lbl_msg.configure(
            text=f"Đã thêm thành công: {target_user['full_name']} (@{target_user['username']})", 
            text_color="#10B981"
        )
        self._refresh_members_list()

    def remove_member(self, uid):
        if uid in self.added_members:
            del self.added_members[uid]
            self.lbl_msg.configure(text="")
            self._refresh_members_list()

    def _refresh_members_list(self):
        for w in self.members_scroll.winfo_children():
            w.destroy()
            
        self.lbl_count.configure(text=f"Danh sách thành viên sẽ vào nhóm ({len(self.added_members)} người):")
        
        if not self.added_members:
            empty_box = ctk.CTkFrame(self.members_scroll, fg_color="transparent")
            empty_box.pack(pady=35)
            ctk.CTkLabel(
                empty_box, 
                text="Chưa có thành viên nào được thêm.\nHãy gõ Username hoặc ID ở trên rồi bấm [➕ Thêm].", 
                font=ctk.CTkFont(size=12),
                text_color="gray50"
            ).pack()
            return

        for uid, u in self.added_members.items():
            card = ctk.CTkFrame(self.members_scroll, fg_color=("white", "#1E293B"), corner_radius=8, height=44)
            card.pack(fill="x", padx=4, pady=3)
            
            # Avatar circle
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
            
            # Info text
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, pady=4)
            
            ctk.CTkLabel(
                info_frame, 
                text=u["full_name"], 
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, 
                text=f"@{u['username']}  •  ID: #{u['id']}", 
                font=ctk.CTkFont(size=10),
                text_color="gray50",
                anchor="w"
            ).pack(anchor="w")
            
            # Nút xóa X
            ctk.CTkButton(
                card, 
                text="✕", 
                width=28, 
                height=28, 
                corner_radius=14,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("gray90", "#334155"),
                hover_color=("#FEE2E2", "#7F1D1D"),
                text_color=("#EF4444", "#F87171"),
                command=lambda id_val=uid: self.remove_member(id_val)
            ).pack(side="right", padx=8)

    def do_create_group(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên nhóm chat!")
            return
            
        selected_uids = list(self.added_members.keys())
        if not selected_uids:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập Username hoặc ID và bấm [➕ Thêm] ít nhất 1 thành viên!")
            return
            
        res = self.net.create_group(self.current_user["id"], name, selected_uids)
        if res and res.get("success"):
            messagebox.showinfo("Thành công", f"Đã tạo nhóm riêng tư \"{name}\" thành công với {len(selected_uids) + 1} thành viên!")
            self.on_group_created(res.get("conversation_id"))
            self.destroy()
        else:
            messagebox.showerror("Lỗi", res.get("message", "Tạo nhóm thất bại!"))
