import customtkinter as ctk
from tkinter import filedialog, messagebox
import base64
import os
import io
import re
import threading
from PIL import Image

# Thư mục lưu đệm ảnh thu nhỏ để xem trực tiếp
CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

EMOJI_PATTERN = re.compile(
    r"^[\s"
    r"\U0001F600-\U0001F64F"  # emoticons
    r"\U0001F300-\U0001F5FF"  # symbols & pictographs
    r"\U0001F680-\U0001F6FF"  # transport & map symbols
    r"\U0001F1E0-\U0001F1FF"  # flags
    r"\U00002702-\U000027B0"
    r"\U000024C2-\U0001F251"
    r"\U0001F900-\U0001F9FF"  # supplemental
    r"\U0001FA00-\U0001FAFF"  # extended
    r"\u2600-\u26FF"
    r"\u2700-\u27BF"
    r"\ufe0e\ufe0f"
    r"]+$",
    flags=re.UNICODE
)

def is_pure_emoji(text: str) -> bool:
    """Kiểm tra tin nhắn có phải thuần biểu tượng cảm xúc không (để hiển thị cỡ lớn kiểu Facebook)."""
    if not text:
        return False
    stripped = text.strip().replace(" ", "").replace("\n", "")
    if 0 < len(stripped) <= 6:
        # Nếu không chứa chữ cái a-z hoặc số mà khớp pattern emoji
        if not re.search(r'[a-zA-Z0-9\u00C0-\u1EF9]', stripped):
            return bool(EMOJI_PATTERN.match(stripped)) or any(char in stripped for char in "😀😃😄😁😆😅😂🤣🥲🥹😊😇🙂🙃😉😌😍🥰😘😗😋😛😜🤪😎🤓🧐🥳😏😒😞😔😟😕🙁😣😖😫😩🥺😢😭😮‍💨😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤗🫡🤫🫠👍👎👊✊🤛🤜👏🙌👐🤲🤝🙏❤️🧡💛💚💙💜🖤🤍🤎💔❤️‍🔥❤️‍🩹💖💗💓💞💕💌💘💝🎉🎊🎈🎂🔥✨🌟💫💥💯🚀🏆🥇🎯⭐🔔🍕🍔🍟☕🧋🍵🍺🍻🐶🐱")
    return False

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
        self.img_ref = None  # Giữ tham chiếu ảnh CTkImage tránh bị garbage collect
        
        self.grid_columnconfigure(0, weight=1)
        self._build_bubble()

    def _build_bubble(self):
        bubble_align = "e" if self.is_self else "w"
        
        bubble_wrapper = ctk.CTkFrame(self, fg_color="transparent")
        bubble_wrapper.pack(anchor=bubble_align, padx=12, pady=4)
        
        msg_type = self.message.get("message_type", "text")
        content = self.message.get("content", "")
        file_id = self.message.get("file_id")

        # Kiểm tra tin nhắn Emoji siêu to phong cách Facebook
        pure_emoji = (msg_type == "text" and is_pure_emoji(content))

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

        # Thiết lập màu nền bóng chat
        if pure_emoji:
            bg_color = "transparent"
        else:
            bg_color = "#2563EB" if self.is_self else ("#E2E8F0", "#334155")
        
        text_color = "white" if self.is_self else ("#0F172A", "#F8FAFC")
        
        bubble_card = ctk.CTkFrame(
            bubble_wrapper, 
            fg_color=bg_color, 
            corner_radius=14 if not pure_emoji else 0
        )
        bubble_card.pack(anchor=bubble_align)

        # 1. Tin nhắn Text hoặc Emoji
        if msg_type == "text" or not file_id:
            if pure_emoji:
                # Emoji to kiểu Facebook Messenger
                emoji_font_size = 42 if len(content.strip()) <= 2 else 32
                msg_label = ctk.CTkLabel(
                    bubble_card, 
                    text=content, 
                    font=ctk.CTkFont(size=emoji_font_size),
                    wraplength=450,
                    justify="left"
                )
                msg_label.pack(padx=6, pady=2, anchor=bubble_align)
            else:
                msg_label = ctk.CTkLabel(
                    bubble_card, 
                    text=content, 
                    font=ctk.CTkFont(size=13),
                    text_color=text_color,
                    wraplength=450,
                    justify="left"
                )
                msg_label.pack(padx=14, pady=(8, 4), anchor="w")

        # 2. Tin nhắn Hình ảnh (Hỗ trợ Inline Image Preview trực tiếp)
        elif msg_type == "image":
            orig_name = self.message.get("original_name", "Hình ảnh")
            self.img_container = ctk.CTkFrame(bubble_card, fg_color="transparent")
            self.img_container.pack(padx=8, pady=8)

            # Label hiển thị trạng thái đang tải hoặc xem trước
            self.preview_label = ctk.CTkLabel(
                self.img_container,
                text="🖼️ Đang tải ảnh xem trước...",
                font=ctk.CTkFont(size=12),
                text_color=text_color,
                cursor="hand2"
            )
            self.preview_label.pack(padx=4, pady=4)
            self.preview_label.bind("<Button-1>", lambda e: self.open_or_download_image())

            # Bắt đầu luồng tải thumbnail và hiển thị ảnh trực tiếp
            threading.Thread(target=self._load_and_display_thumbnail, daemon=True).start()

            # Dòng nút hành động tải về máy bên dưới ảnh
            action_bar = ctk.CTkFrame(self.img_container, fg_color="transparent")
            action_bar.pack(fill="x", padx=2, pady=(4, 0))

            btn_dl = ctk.CTkButton(
                action_bar,
                text="💾 Lưu ảnh",
                height=26,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color=("#3B82F6", "#1D4ED8") if not self.is_self else ("#1D4ED8", "#1E40AF"),
                command=self.download_and_save_file
            )
            btn_dl.pack(side="left", padx=(0, 4))

            btn_open = ctk.CTkButton(
                action_bar,
                text="🔍 Phóng to",
                height=26,
                font=ctk.CTkFont(size=11),
                fg_color="transparent",
                hover_color=("gray85", "#334155"),
                text_color=text_color,
                command=self.open_or_download_image
            )
            btn_open.pack(side="left")

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
        meta_row.pack(anchor="e", padx=10 if not pure_emoji else 2, pady=(0, 5))
        
        t_str = format_time(self.message.get("created_at", ""))
        time_label = ctk.CTkLabel(
            meta_row, 
            text=t_str + ("  ✓" if self.is_self else ""), 
            font=ctk.CTkFont(size=10),
            text_color=("white" if self.is_self else ("#64748B", "#94A3B8")) if not pure_emoji else ("#64748B", "#94A3B8")
        )
        time_label.pack(side="right")

    def _get_cache_path(self) -> str:
        file_id = self.message.get("file_id")
        orig_name = self.message.get("original_name", "image.png")
        clean_name = re.sub(r'[^\w\.-]', '_', orig_name)
        return os.path.join(CACHE_DIR, f"cached_{file_id}_{clean_name}")

    def _load_and_display_thumbnail(self):
        """Tải dữ liệu ảnh và hiển thị xem trước thumbnail bo góc trực tiếp trong tin nhắn."""
        file_id = self.message.get("file_id")
        if not file_id:
            return

        cache_path = self._get_cache_path()

        # Nếu chưa có trong cache thì tải về
        if not os.path.exists(cache_path):
            res = self.net.download_file(file_id)
            if res and res.get("success"):
                try:
                    data = base64.b64decode(res.get("file_data", ""))
                    with open(cache_path, "wb") as f:
                        f.write(data)
                except Exception:
                    pass

        if os.path.exists(cache_path):
            try:
                pil_img = Image.open(cache_path)
                # Tính tỉ lệ co giãn ảnh xem trước
                max_w, max_h = 280, 200
                orig_w, orig_h = pil_img.size
                ratio = min(max_w / orig_w, max_h / orig_h, 1.0)
                thumb_w = max(int(orig_w * ratio), 60)
                thumb_h = max(int(orig_h * ratio), 60)

                resized_img = pil_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                ctk_thumb = ctk.CTkImage(light_image=resized_img, dark_image=resized_img, size=(thumb_w, thumb_h))

                def _apply():
                    try:
                        if self.winfo_exists() and self.preview_label.winfo_exists():
                            self.img_ref = ctk_thumb  # Lưu ref
                            self.preview_label.configure(image=ctk_thumb, text="")
                    except Exception:
                        pass
                self.master.after(0, _apply)
            except Exception:
                pass

    def open_or_download_image(self):
        """Mở xem ảnh toàn màn hình bằng ứng dụng xem ảnh mặc định của Windows."""
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            file_id = self.message.get("file_id")
            if file_id:
                res = self.net.download_file(file_id)
                if res and res.get("success"):
                    try:
                        data = base64.b64decode(res.get("file_data", ""))
                        with open(cache_path, "wb") as f:
                            f.write(data)
                    except Exception:
                        pass

        if os.path.exists(cache_path):
            try:
                os.startfile(cache_path)
            except Exception:
                self.download_and_save_file()
        else:
            self.download_and_save_file()

    def download_and_save_file(self):
        file_id = self.message.get("file_id")
        orig_name = self.message.get("original_name", "downloaded_file")
        if not file_id:
            messagebox.showwarning("Thông báo", "Tệp tin không tồn tại!")
            return
        
        save_path = filedialog.asksaveasfilename(
            initialfile=orig_name,
            title="Lưu tệp tin",
            defaultextension=".*"
        )
        if not save_path:
            return
        
        # Nếu đã có trong cache thì copy nhanh
        cache_path = self._get_cache_path()
        if os.path.exists(cache_path):
            try:
                import shutil
                shutil.copyfile(cache_path, save_path)
                messagebox.showinfo("Thành công", f"Đã lưu tệp thành công tại:\n{save_path}")
                return
            except Exception:
                pass

        def _do_download():
            res = self.net.download_file(file_id)
            def _done():
                if not res or not res.get("success"):
                    messagebox.showerror("Lỗi tải tệp", res.get("message", "Không thể tải tệp từ máy chủ!"))
                    return
                try:
                    raw_bytes = base64.b64decode(res.get("file_data", ""))
                    with open(save_path, "wb") as f:
                        f.write(raw_bytes)
                    messagebox.showinfo("Thành công", f"Đã lưu tệp thành công tại:\n{save_path}")
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Lỗi khi lưu tệp: {e}")
            self.after(0, _done)

        threading.Thread(target=_do_download, daemon=True).start()
