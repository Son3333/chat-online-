import customtkinter as ctk
from tkinter import messagebox

class CreateGroupDialog(ctk.CTkToplevel):
    def __init__(self, master, current_user: dict, network_client, on_group_created):
        super().__init__(master)
        self.current_user = current_user
        self.net = network_client
        self.on_group_created = on_group_created
        
        self.title("Tạo Nhóm Trò Chuyện Mới")
        self.geometry("420x520")
        self.resizable(False, False)
        self.grab_set()
        
        self._build_ui()

    def _build_ui(self):
        # Header
        ctk.CTkLabel(
            self, 
            text="👥 Tạo Nhóm Trò Chuyện Mới", 
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(18, 4))
        
        ctk.CTkLabel(
            self, 
            text="Đặt tên nhóm và chọn các thành viên tham gia", 
            font=ctk.CTkFont(size=12),
            text_color="gray60"
        ).pack(pady=(0, 14))

        # Tên nhóm
        frame_name = ctk.CTkFrame(self, fg_color="transparent")
        frame_name.pack(fill="x", padx=25, pady=(0, 10))
        
        ctk.CTkLabel(frame_name, text="Tên nhóm:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(0, 4))
        self.name_entry = ctk.CTkEntry(frame_name, placeholder_text="Ví dụ: Nhóm học tập, Dự án CNPM...", height=38, corner_radius=8)
        self.name_entry.pack(fill="x")

        # Danh sách thành viên để chọn
        ctk.CTkLabel(self, text="Chọn thành viên tham gia:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=25, pady=(4, 4))
        
        self.members_scroll = ctk.CTkScrollableFrame(self, height=220, corner_radius=10)
        self.members_scroll.pack(fill="both", expand=True, padx=25, pady=(0, 14))
        
        # Lấy danh sách thành viên khả dụng từ server
        self.checkboxes = {}
        self._load_users()

        # Nút hành động
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=25, pady=(0, 18))
        
        ctk.CTkButton(
            btn_box, 
            text="Hủy", 
            width=100, 
            height=38, 
            fg_color="transparent", 
            border_width=1,
            command=self.destroy
        ).pack(side="left")
        
        ctk.CTkButton(
            btn_box, 
            text="Tạo Nhóm", 
            width=140, 
            height=38, 
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.do_create_group
        ).pack(side="right")

    def _load_users(self):
        # Tìm tất cả người dùng khác
        res = self.net.search_users("", self.current_user["id"])
        users = res.get("users", []) if res else []
        
        if not users:
            ctk.CTkLabel(self.members_scroll, text="Không có thành viên nào khác.", text_color="gray60").pack(pady=20)
            return
            
        for u in users:
            var = ctk.BooleanVar(value=False)
            self.checkboxes[u["id"]] = var
            
            row = ctk.CTkFrame(self.members_scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)
            
            cb = ctk.CTkCheckBox(
                row, 
                text=f"{u['full_name']} (@{u['username']})",
                variable=var,
                font=ctk.CTkFont(size=13)
            )
            cb.pack(side="left", padx=4)

    def do_create_group(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên nhóm!")
            return
            
        selected_uids = [uid for uid, var in self.checkboxes.items() if var.get()]
        if not selected_uids:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất 1 thành viên tham gia!")
            return
            
        res = self.net.create_group(self.current_user["id"], name, selected_uids)
        if res and res.get("success"):
            messagebox.showinfo("Thành công", f"Đã tạo nhóm \"{name}\" thành công!")
            self.on_group_created(res.get("conversation_id"))
            self.destroy()
        else:
            messagebox.showerror("Lỗi", res.get("message", "Tạo nhóm thất bại!"))

