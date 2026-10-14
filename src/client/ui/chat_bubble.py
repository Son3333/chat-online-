import customtkinter as ctk
from tkinter import filedialog, messagebox
import base64
import os
import io
from PIL import Image

def format_file_size(bytes_size: int) -> str:
    if not bytes_size:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def format_time(ts_str: str) -> str:
    if not ts_str:
        return ""
    try:
        # Giữ lại HH:MM
        if " " in ts_str:
            time_part = ts_str.split(" ")[1]
            return ":".join(time_part.split(":")[:2])
        return ts_str
    except Exception:
        return ts_str

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, message: dict, current_user_id: int, network_client):
        super().__init__(master, fg_color="transparent")
        self.message = message
        self.current_user_id = current_user_id
        self.net = network_client
        self.is_self = (message.get("sender_id") == current_user_id)
        
        self.grid_columnconfigure(0, weight=1)
        self._build_bubble()

    def _build_bubble(self):
        # Container cho bong bóng (để căn lề trái hoặc phải)
        bubble_align = "e" if self.is_self else "w"
        
        bubble_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        bubble_wrapper.pack(anchor=bubble_align, padx=12, pady=4)
        
        # Màu bong bóng
        # Self: Xanh dương #2563EB
        # Other: Xám đen #334155 (Dark) / #E2E8F0 (Light)
        bg_color = "#2563EB" if self.is_self else ("#E2E8F0", "#334155")
        text_color = "white" if self.is_self else ("#0F172A", "#F8FAFC")
        
        # Nếu là tin nhắn của người khác, hiển thị tên người gửi
        if not self.is_self:
            sender_name = self.message.get("sender_name", "Thành viên")
            name_label = ctk.CTkLabel(
                bubble_wrapper, 
                text=sender_name, 
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=("#475569", "#94A3B8")
            )
            name_label.pack(anchor="w", padx=4, pady=(0, 2))

        # Khung bong bóng nội dung chính
        bubble_card = ctk.CTkFrame(
            bubble_wrapper, 
            fg_color=bg_color, 
            corner_radius=14
        )
        bubble_card.pack(anchor=bubble_align)

        msg_type = self.message.get("message_type", "text")
        content = self.message.get("content", "")
        file_id = self.message.get("file_id")

        # 1. Tin nhắn Text
        if msg_type == "text" or not file_id:
            msg_label = ctk.CTkLabel(
                bubble_card, 
                text=content, 
                font=ctk.CTkFont(size=13),
                text_color=text_color,
                wraplength=450,
                justify="left"
            )
            msg_label.pack(padx=14, pady=(8, 4), anchor="w")

        # 2. Tin nhắn Hình ảnh
        elif msg_type == "image":
            # Tiêu đề tệp ảnh
            orig_name = self.message.get("original_name", "Hình ảnh")
            img_card = ctk.CTkFrame(bubble_card, fg_color="transparent")
            img_card.pack(padx=10, pady=8)
            
            # Label ảnh placeholder hoặc nút xem
            ctk.CTkLabel(
                img_card, 
                text="🖼️ " + orig_name, 
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=text_color
            ).pack(anchor="w", pady=(0, 4))
            
            btn_view = ctk.CTkButton(
                img_card, 
                text="📥 Xem & Tải ảnh về", 
                height=30, 
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#3B82F6", "#1D4ED8") if not self.is_self else ("#1D4ED8", "#1E40AF"),
                command=self.download_and_save_file
            )
            btn_view.pack(anchor="w", pady=(2, 4))

        # 3. Tin nhắn Tệp tin (Document, PDF, ZIP, ...)
        elif msg_type == "file":
            orig_name = self.message.get("original_name", "Tài liệu đính kèm")
            f_size = format_file_size(self.message.get("file_size", 0))
            
            file_box = ctk.CTkFrame(bubble_card, fg_color=("gray85", "#1E293B"), corner_radius=10)
            file_box.pack(padx=8, pady=8)
            
            row_file = ctk.CTkFrame(file_box, fg_color="transparent")
            row_file.pack(padx=10, pady=8)
            
            ctk.CTkLabel(row_file, text="📄", font=ctk.CTkFont(size=26)).pack(side="left", padx=(0, 10))
            
            info_col = ctk.CTkFrame(row_file, fg_color="transparent")
            info_col.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                info_col, 
                text=orig_name, 
                font=ctk.CTkFont(size=13, weight="bold"),
                wraplength=300,
                justify="left"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_col, 
                text=f"Dung lượng: {f_size}", 
                font=ctk.CTkFont(size=11),
                text_color=("gray40", "gray60")
            ).pack(anchor="w")
            
            btn_dl = ctk.CTkButton(
                file_box, 
                text="📥 Tải Về Máy", 
                height=30, 
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#10B981",
                hover_color="#059669",
                command=self.download_and_save_file
            )
            btn_dl.pack(fill="x", padx=10, pady=(0, 8))

        # Dòng thời gian và trạng thái gửi
        meta_row = ctk.CTkFrame(bubble_card, fg_color="transparent")
        meta_row.pack(anchor="e", padx=10, pady=(0, 5))
        
        t_str = format_time(self.message.get("created_at", ""))
        time_label = ctk.CTkLabel(
            meta_row, 
            text=t_str + ("  ✓" if self.is_self else ""), 
            font=ctk.CTkFont(size=10),
            text_color=("white" if self.is_self else ("#64748B", "#94A3B8"))
        )
        time_label.pack(side="right")

    def download_and_save_file(self):
        file_id = self.message.get("file_id")
        orig_name = self.message.get("original_name", "downloaded_file")
        if not file_id:
            messagebox.showwarning("Thông báo", "Tệp tin không tồn tại!")
            return
        
        # Hỏi vị trí lưu tệp
        save_path = filedialog.asksaveasfilename(
            initialfile=orig_name,
            title="Lưu tệp tin",
            defaultextension=".*"
        )
        if not save_path:
            return
        
        res = self.net.download_file(file_id)
        if not res or not res.get("success"):
            messagebox.showerror("Lỗi", res.get("message", "Không thể tải tệp từ máy chủ!"))
            return
        
        try:
            raw_bytes = base64.b64decode(res.get("file_data", ""))
            with open(save_path, "wb") as f:
                f.write(raw_bytes)
            messagebox.showinfo("Thành công", f"Đã lưu tệp thành công tại:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi lưu tệp: {e}")

