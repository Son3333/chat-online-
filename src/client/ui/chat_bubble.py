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

import tkinter as tk

class ChatBubble(ctk.CTkFrame):
    def __init__(self, master, message: dict, current_user_id: int, network_client, 
                 on_recall_callback=None, on_reply_callback=None, on_reaction_callback=None, on_pin_callback=None):
        super().__init__(master, fg_color="transparent")
        self.message = message
        self.current_user_id = current_user_id
        self.net = network_client
        self.on_recall_callback = on_recall_callback
        self.on_reply_callback = on_reply_callback
        self.on_reaction_callback = on_reaction_callback
        self.on_pin_callback = on_pin_callback
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
        is_deleted = self.message.get("is_deleted", 0)

        # Kiểm tra tin nhắn Emoji siêu to phong cách Facebook
        pure_emoji = (not is_deleted and msg_type == "text" and is_pure_emoji(content))

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
        if is_deleted:
            bg_color = ("#F1F5F9", "#1E293B")
            text_color = ("#64748B", "#94A3B8")
        elif pure_emoji:
            bg_color = "transparent"
            text_color = "white" if self.is_self else ("#0F172A", "#F8FAFC")
        else:
            bg_color = "#2563EB" if self.is_self else ("#E2E8F0", "#334155")
            text_color = "white" if self.is_self else ("#0F172A", "#F8FAFC")
        
        bubble_card = ctk.CTkFrame(
            bubble_wrapper, 
            fg_color=bg_color, 
            corner_radius=14 if not pure_emoji else 0
        )
        bubble_card.pack(anchor=bubble_align)

        # Trích dẫn trả lời tin nhắn (Reply Quote Box)
        if not is_deleted and self.message.get("reply_to_id"):
            reply_sender = self.message.get("reply_sender_name") or "Người dùng"
            reply_txt = self.message.get("reply_content") or "Tệp đính kèm / Hình ảnh"
            quote_box = ctk.CTkFrame(
                bubble_card,
                fg_color=("#1D4ED8" if self.is_self else ("#CBD5E1", "#1E293B")),
                corner_radius=6
            )
            quote_box.pack(fill="x", padx=8, pady=(6, 2))

            bar_col = "#93C5FD" if self.is_self else "#0284C7"
            ctk.CTkFrame(quote_box, width=3, fg_color=bar_col, corner_radius=2).pack(side="left", fill="y", padx=(2, 6), pady=2)

            text_col = ctk.CTkFrame(quote_box, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True, pady=2)

            ctk.CTkLabel(
                text_col,
                text=f"↩️ {reply_sender}",
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#93C5FD" if self.is_self else "#0284C7",
                anchor="w"
            ).pack(anchor="w")

            ctk.CTkLabel(
                text_col,
                text=reply_txt[:55] + ("..." if len(reply_txt) > 55 else ""),
                font=ctk.CTkFont(size=10),
                text_color="#E0E7FF" if self.is_self else ("#475569", "#94A3B8"),
                anchor="w"
            ).pack(anchor="w")

        # 0. Nếu là tin nhắn đã bị thu hồi
        if is_deleted:
            recalled_label = ctk.CTkLabel(
                bubble_card,
                text="🚫 Tin nhắn đã được thu hồi",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color=text_color,
                wraplength=450,
                justify="left"
            )
            recalled_label.pack(padx=14, pady=(8, 4), anchor="w")

        # 1. Tin nhắn Text hoặc Emoji
        elif msg_type == "text" or not file_id:
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
            
            btn_row = ctk.CTkFrame(file_box, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(0, 8))

            btn_open = ctk.CTkButton(
                btn_row,
                text="▶ Mở file",
                height=28,
                width=80,
                font=ctk.CTkFont(size=11, weight="bold"),
                fg_color="#3B82F6",
                hover_color="#2563EB",
                command=self.open_file
            )
            btn_open.pack(side="left", padx=(0, 4))

            btn_folder = ctk.CTkButton(
                btn_row,
                text="📂 Thư mục",
                height=28,
                width=80,
                font=ctk.CTkFont(size=11),
                fg_color=("gray75", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
                hover_color=("gray70", "#475569"),
                command=self.reveal_in_folder
            )
            btn_folder.pack(side="left", padx=(0, 4))

            btn_dl = ctk.CTkButton(
                btn_row, 
                text="💾 Lưu...", 
                height=28, 
                width=70,
                font=ctk.CTkFont(size=11),
                fg_color="#10B981",
                hover_color="#059669",
                command=self.download_and_save_file
            )
            btn_dl.pack(side="left")

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

        # Thẻ biểu cảm cảm xúc (Reaction Badges)
        if not is_deleted and self.message.get("reactions"):
            reactions = self.message.get("reactions", [])
            rx_frame = ctk.CTkFrame(bubble_wrapper, fg_color="transparent")
            rx_frame.pack(anchor=bubble_align, padx=4, pady=(2, 0))
            for r in reactions:
                symbol = r.get("reaction")
                cnt = r.get("count", 1)
                my_rx = any(u.get("id") == self.current_user_id for u in r.get("users", []))
                badge = ctk.CTkButton(
                    rx_frame,
                    text=f"{symbol} {cnt}",
                    height=20,
                    width=38,
                    corner_radius=10,
                    font=ctk.CTkFont(size=10, weight="bold"),
                    fg_color="#3B82F6" if my_rx else ("#E2E8F0", "#334155"),
                    text_color="white" if my_rx else ("#0F172A", "#F8FAFC"),
                    hover_color="#2563EB" if my_rx else ("#CBD5E1", "#475569"),
                    command=lambda s=symbol: self._trigger_reaction(s)
                )
                badge.pack(side="left", padx=2)

        # Gắn menu chuột phải tiện lợi (Sao chép, Thả cảm xúc, Trả lời, Ghim, Thu hồi)
        self._bind_context_menu(bubble_card)
        self._bind_context_menu(bubble_wrapper)

    def _bind_context_menu(self, widget):
        try:
            widget.bind("<Button-3>", self._show_context_menu)
            for child in widget.winfo_children():
                self._bind_context_menu(child)
        except Exception:
            pass

    def _show_context_menu(self, event):
        try:
            import tkinter as tk
            is_dark = ctk.get_appearance_mode() == "Dark"
            bg_color = "#1E293B" if is_dark else "#FFFFFF"
            fg_color = "#F8FAFC" if is_dark else "#0F172A"
            active_bg = "#334155" if is_dark else "#E2E8F0"
            active_fg = "#38BDF8" if is_dark else "#0284C7"

            menu = tk.Menu(
                self,
                tearoff=0,
                bg=bg_color,
                fg=fg_color,
                activebackground=active_bg,
                activeforeground=active_fg,
                font=("Segoe UI", 10),
                relief="solid",
                bd=1
            )
            content = self.message.get("content", "")
            is_deleted = self.message.get("is_deleted", 0)

            if not is_deleted:
                # 1. Menu thả cảm xúc
                rx_menu = tk.Menu(menu, tearoff=0, bg=bg_color, fg=fg_color, activebackground=active_bg, activeforeground=active_fg)
                for emo in ["❤️ Yêu thích", "👍 Thích", "😂 Haha", "😮 Wow", "😢 Buồn", "😡 Phẫn nộ"]:
                    symbol = emo.split()[0]
                    rx_menu.add_command(label=emo, command=lambda s=symbol: self._trigger_reaction(s))
                menu.add_cascade(label="💖 Thả cảm xúc...", menu=rx_menu)

                # 2. Trả lời trích dẫn
                menu.add_command(label="↩️ Trả lời tin nhắn này", command=self._trigger_reply)

                # 3. Ghim tin nhắn
                menu.add_command(label="📌 Ghim tin nhắn này", command=self._trigger_pin)
                menu.add_separator()

            if not is_deleted and content:
                menu.add_command(label="📋 Sao chép nội dung", command=self._copy_text)

            if self.is_self and not is_deleted:
                menu.add_separator()
                menu.add_command(label="🗑️ Thu hồi tin nhắn", command=self._confirm_recall)

            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _trigger_reaction(self, reaction_symbol):
        if self.on_reaction_callback:
            self.on_reaction_callback(self.message.get("id"), reaction_symbol)

    def _trigger_reply(self):
        if self.on_reply_callback:
            self.on_reply_callback(self.message)

    def _trigger_pin(self):
        if self.on_pin_callback:
            self.on_pin_callback(self.message)

    def update_reactions(self, new_reactions: list):
        self.message["reactions"] = new_reactions
        for w in self.winfo_children():
            w.destroy()
        self._build_bubble()

    def _copy_text(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(self.message.get("content", ""))
        except Exception:
            pass

    def _confirm_recall(self):
        msg_id = self.message.get("id")
        if not msg_id or not self.on_recall_callback:
            return
        if messagebox.askyesno("Thu hồi tin nhắn", "Bạn có chắc chắn muốn thu hồi tin nhắn này ở cả hai phía không?"):
            self.on_recall_callback(msg_id)

    def mark_as_recalled(self):
        """Cập nhật giao diện bong bóng thành trạng thái đã thu hồi."""
        self.message["is_deleted"] = 1
        self.message["content"] = "Tin nhắn đã được thu hồi"
        for w in self.winfo_children():
            w.destroy()
        self._build_bubble()

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

    def _ensure_cached(self) -> Optional[str]:
        """Tải tệp vào thư mục cache nếu chưa có."""
        cache_path = self._get_cache_path()
        if not os.path.exists(cache_path):
            file_id = self.message.get("file_id")
            if not file_id:
                return None
            res = self.net.download_file(file_id)
            if res and res.get("success"):
                try:
                    data = base64.b64decode(res.get("file_data", ""))
                    with open(cache_path, "wb") as f:
                        f.write(data)
                except Exception:
                    return None
            else:
                return None
        return cache_path

    def open_file(self):
        """Mở tệp tin trực tiếp bằng ứng dụng mặc định của hệ thống."""
        def _task():
            cache_path = self._ensure_cached()
            if cache_path and os.path.exists(cache_path):
                try:
                    os.startfile(cache_path)
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Lỗi mở file", f"Không thể mở tệp: {e}"))
            else:
                self.after(0, lambda: messagebox.showerror("Lỗi", "Không thể tải tệp để mở!"))
        threading.Thread(target=_task, daemon=True).start()

    def reveal_in_folder(self):
        """Mở File Explorer và chọn ngay tệp tin này."""
        def _task():
            cache_path = self._ensure_cached()
            if cache_path and os.path.exists(cache_path):
                try:
                    import subprocess
                    subprocess.run(["explorer", f"/select,{os.path.normpath(cache_path)}"])
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}"))
            else:
                self.after(0, lambda: messagebox.showerror("Lỗi", "Không thể tải tệp để định vị!"))
        threading.Thread(target=_task, daemon=True).start()

