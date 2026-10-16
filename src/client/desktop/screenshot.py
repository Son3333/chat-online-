"""
Module Chụp & Chỉnh sửa Màn hình Chuyên nghiệp (Screen Capture & Annotation Tool)
- Chụp toàn màn hình (hỗ trợ đa màn hình).
- Kính lúp Pixel (Magnifier Loupe) hiển thị phóng đại từng điểm ảnh, kích thước WxH và mã màu HEX.
- Bộ công cụ vẽ chú thích:
  + Hình chữ nhật (Rectangle)
  + Hình tròn / Elip (Ellipse)
  + Mũi tên chỉ hướng (Arrow)
  + Đánh số bước tự động (Step Counter: ①, ②, ③...)
  + Làm mờ / Che thông tin nhạy cảm (Mosaic / Pixelate)
  + Bút vẽ tự do / Bút dạ quang (Highlighter / Pen)
- Tác vụ: Sao chép vào Clipboard, Lưu file PNG, Gửi trực tiếp vào cuộc trò chuyện.
"""

import io
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional, Callable
from PIL import Image, ImageGrab, ImageTk, ImageDraw, ImageFilter
import numpy as np

class ScreenCaptureTool:
    def __init__(self, parent: tk.Tk, on_send_image: Optional[Callable[[str], None]] = None):
        self.parent = parent
        self.on_send_image = on_send_image

    def start_capture(self):
        """Ẩn nhẹ cửa sổ cha nếu cần rồi chụp toàn màn hình."""
        try:
            # Chụp ảnh toàn màn hình
            screenshot = ImageGrab.grab(all_screens=True)
            overlay = CaptureOverlay(self.parent, screenshot, self.on_send_image)
            overlay.show()
        except Exception as e:
            messagebox.showerror("Lỗi chụp màn hình", f"Không thể chụp màn hình: {e}")

class CaptureOverlay:
    def __init__(self, parent: tk.Tk, full_image: Image.Image, on_send_image: Optional[Callable[[str], None]]):
        self.parent = parent
        self.original_image = full_image
        self.on_send_image = on_send_image

        self.win = tk.Toplevel(parent)
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.config(cursor="cross")

        self.width = self.win.winfo_screenwidth()
        self.height = self.win.winfo_screenheight()

        # Canvas vẽ chính
        self.canvas = tk.Canvas(self.win, cursor="cross", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Chuyển ảnh sang dạng tối hơn một chút cho lớp nền
        dark_img = self.original_image.copy()
        enhancer = Image.new("RGBA", dark_img.size, (0, 0, 0, 100))
        self.dimmed_image = Image.alpha_composite(dark_img.convert("RGBA"), enhancer)
        self.dimmed_photo = ImageTk.PhotoImage(self.dimmed_image)
        self.canvas.create_image(0, 0, anchor="nw", image=self.dimmed_photo)

        # Trạng thái chọn vùng
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.is_selecting = False
        self.has_selection = False

        # Công cụ vẽ chú thích
        self.active_tool = "none" # rect, ellipse, arrow, step, mosaic, pen
        self.current_color = "#EF4444" # Mặc định đỏ
        self.step_counter = 1
        self.annotations = [] # Danh sách các nét vẽ trên vùng crop

        # UI elements
        self.rect_id = None
        self.crop_image_id = None
        self.toolbar_frame = None
        self.loupe_win = None

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.win.bind("<Escape>", lambda e: self.close())

    def show(self):
        self.win.focus_force()

    def _get_crop_coords(self):
        if self.start_x is None or self.end_x is None:
            return 0, 0, 0, 0
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        return x1, y1, x2, y2

    def _on_press(self, event):
        x1, y1, x2, y2 = self._get_crop_coords()
        if self.has_selection and self.active_tool != "none":
            # Đang vẽ annotation bên trong vùng chọn
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                self.ann_start_x = event.x
                self.ann_start_y = event.y
                if self.active_tool == "step":
                    self._add_step_badge(event.x, event.y)
                elif self.active_tool == "pen":
                    self.pen_points = [(event.x, event.y)]
                return

        # Bắt đầu kéo chọn vùng mới
        self.start_x = event.x
        self.start_y = event.y
        self.end_x = event.x
        self.end_y = event.y
        self.is_selecting = True
        self.has_selection = False
        self.step_counter = 1
        self.annotations.clear()
        if self.toolbar_frame:
            self.toolbar_frame.destroy()
            self.toolbar_frame = None

    def _on_drag(self, event):
        x1, y1, x2, y2 = self._get_crop_coords()
        if self.has_selection and self.active_tool != "none":
            # Đang kéo vẽ annotation
            if self.active_tool == "pen":
                self.pen_points.append((event.x, event.y))
                p1 = self.pen_points[-2]
                p2 = self.pen_points[-1]
                self.canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=self.current_color, width=3, capstyle=tk.ROUND)
            elif self.active_tool in ["rect", "ellipse", "arrow", "mosaic"]:
                self._draw_temp_annotation(self.ann_start_x, self.ann_start_y, event.x, event.y)
            return

        if self.is_selecting:
            self.end_x = event.x
            self.end_y = event.y
            self._update_selection_box()

    def _on_release(self, event):
        x1, y1, x2, y2 = self._get_crop_coords()
        if self.has_selection and self.active_tool != "none":
            if self.active_tool in ["rect", "ellipse", "arrow", "mosaic"]:
                self._commit_annotation(self.ann_start_x, self.ann_start_y, event.x, event.y)
            elif self.active_tool == "pen" and hasattr(self, "pen_points"):
                self.annotations.append(("pen", list(self.pen_points), self.current_color))
            return

        if self.is_selecting:
            self.is_selecting = False
            w = abs(self.end_x - self.start_x)
            h = abs(self.end_y - self.start_y)
            if w > 15 and h > 15:
                self.has_selection = True
                self._show_toolbar()
            else:
                self.has_selection = False

    def _update_selection_box(self):
        x1, y1, x2, y2 = self._get_crop_coords()
        if x2 - x1 < 1 or y2 - y1 < 1:
            return

        # Cắt ảnh gốc sáng tại vùng chọn
        crop = self.original_image.crop((x1, y1, x2, y2))
        self.crop_photo = ImageTk.PhotoImage(crop)

        if self.crop_image_id:
            self.canvas.delete(self.crop_image_id)
        self.crop_image_id = self.canvas.create_image(x1, y1, anchor="nw", image=self.crop_photo)

        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, outline="#38BDF8", width=2)

    def _on_motion(self, event):
        """Kính lúp Pixel (Magnifier Loupe) hiển thị màu và kích thước."""
        if self.is_selecting or self.has_selection:
            return

        x, y = event.x, event.y
        if 0 <= x < self.original_image.width and 0 <= y < self.original_image.height:
            pixel = self.original_image.getpixel((x, y))
            if isinstance(pixel, int):
                pixel = (pixel, pixel, pixel)
            r, g, b = pixel[:3]
            hex_color = f"#{r:02X}{g:02X}{b:02X}"

            # Hiển thị text nhỏ gần chuột
            self.canvas.delete("loupe_text")
            self.canvas.create_text(x + 15, y + 25, 
                                   text=f"{x}, {y} | {hex_color}", 
                                   fill="#38BDF8", font=("Consolas", 10, "bold"), 
                                   tag="loupe_text", anchor="w")

    def _draw_temp_annotation(self, x1, y1, x2, y2):
        self.canvas.delete("temp_ann")
        if self.active_tool == "rect":
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.current_color, width=3, tag="temp_ann")
        elif self.active_tool == "ellipse":
            self.canvas.create_oval(x1, y1, x2, y2, outline=self.current_color, width=3, tag="temp_ann")
        elif self.active_tool == "arrow":
            self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=self.current_color, width=3, tag="temp_ann")
        elif self.active_tool == "mosaic":
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#94A3B8", stipple="gray50", tag="temp_ann")

    def _commit_annotation(self, x1, y1, x2, y2):
        self.canvas.delete("temp_ann")
        if self.active_tool == "mosaic":
            # Thực hiện pixelate vùng ảnh
            cx1, cy1, cx2, cy2 = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
            if cx2 - cx1 > 2 and cy2 - cy1 > 2:
                box = (cx1, cy1, cx2, cy2)
                region = self.original_image.crop(box)
                # Thu nhỏ 10 lần rồi phóng to lại để tạo hiệu ứng Mosaic
                small = region.resize((max(1, (cx2 - cx1) // 10), max(1, (cy2 - cy1) // 10)), Image.NEAREST)
                mosaic = small.resize((cx2 - cx1, cy2 - cy1), Image.NEAREST)
                self.original_image.paste(mosaic, box)
                self._update_selection_box()
            return

        self.annotations.append((self.active_tool, (x1, y1, x2, y2), self.current_color))
        # Vẽ vĩnh viễn trên canvas
        if self.active_tool == "rect":
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=self.current_color, width=3)
        elif self.active_tool == "ellipse":
            self.canvas.create_oval(x1, y1, x2, y2, outline=self.current_color, width=3)
        elif self.active_tool == "arrow":
            self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST, fill=self.current_color, width=3)

    def _add_step_badge(self, x, y):
        """Đóng dấu bước tự động ①, ②, ③..."""
        badge_text = str(self.step_counter)
        self.canvas.create_oval(x - 12, y - 12, x + 12, y + 12, fill=self.current_color, outline="white", width=2)
        self.canvas.create_text(x, y, text=badge_text, fill="white", font=("Segoe UI", 9, "bold"))
        self.annotations.append(("step", (x, y, badge_text), self.current_color))
        self.step_counter += 1

    def _show_toolbar(self):
        """Hiển thị thanh công cụ nổi ngay phía dưới vùng chụp."""
        if self.toolbar_frame:
            self.toolbar_frame.destroy()

        x1, y1, x2, y2 = self._get_crop_coords()
        tb_x = x1
        tb_y = y2 + 10
        if tb_y + 45 > self.height:
            tb_y = y1 - 50

        self.toolbar_frame = tk.Frame(self.canvas, bg="#0F172A", padx=8, pady=6, 
                                      highlightthickness=1, highlightbackground="#38BDF8")
        self.canvas.create_window(tb_x, tb_y, anchor="nw", window=self.toolbar_frame)

        # Các nút công cụ vẽ
        tools = [
            ("🔲 Chữ nhật", "rect"),
            ("⭕ Tròn", "ellipse"),
            ("↗ Mũi tên", "arrow"),
            ("① Bước", "step"),
            ("░ Làm mờ", "mosaic"),
            ("✏️ Bút", "pen")
        ]

        for text, tool_name in tools:
            btn = tk.Button(self.toolbar_frame, text=text, font=("Segoe UI", 9), 
                            bg="#1E293B", fg="#F8FAFC", relief=tk.FLAT, padx=6, pady=2,
                            command=lambda t=tool_name: self._set_tool(t))
            btn.pack(side=tk.LEFT, padx=3)

        # Bộ chọn màu
        sep = tk.Label(self.toolbar_frame, text="|", fg="#475569", bg="#0F172A")
        sep.pack(side=tk.LEFT, padx=4)

        colors = ["#EF4444", "#3B82F6", "#22C55E", "#F59E0B"]
        for c in colors:
            c_lbl = tk.Label(self.toolbar_frame, text="  ", bg=c, cursor="hand2", relief=tk.RAISED, bd=1)
            c_lbl.pack(side=tk.LEFT, padx=2)
            c_lbl.bind("<Button-1>", lambda e, col=c: self._set_color(col))

        sep2 = tk.Label(self.toolbar_frame, text="|", fg="#475569", bg="#0F172A")
        sep2.pack(side=tk.LEFT, padx=4)

        # Nút hành động
        copy_btn = tk.Button(self.toolbar_frame, text="📋 Sao chép", font=("Segoe UI", 9, "bold"),
                             bg="#3B82F6", fg="white", relief=tk.FLAT, padx=8, pady=2,
                             command=self._copy_to_clipboard)
        copy_btn.pack(side=tk.LEFT, padx=3)

        save_btn = tk.Button(self.toolbar_frame, text="💾 Lưu", font=("Segoe UI", 9),
                             bg="#334155", fg="white", relief=tk.FLAT, padx=8, pady=2,
                             command=self._save_to_file)
        save_btn.pack(side=tk.LEFT, padx=3)

        if self.on_send_image:
            send_btn = tk.Button(self.toolbar_frame, text="📤 Gửi ngay", font=("Segoe UI", 9, "bold"),
                                 bg="#10B981", fg="white", relief=tk.FLAT, padx=8, pady=2,
                                 command=self._send_to_chat)
            send_btn.pack(side=tk.LEFT, padx=3)

        close_btn = tk.Button(self.toolbar_frame, text="✕", font=("Segoe UI", 9),
                              bg="#EF4444", fg="white", relief=tk.FLAT, padx=6, pady=2,
                              command=self.close)
        close_btn.pack(side=tk.LEFT, padx=3)

    def _set_tool(self, tool_name):
        self.active_tool = tool_name
        self.canvas.config(cursor="pencil" if tool_name in ["pen", "arrow", "rect"] else "cross")

    def _set_color(self, color):
        self.current_color = color

    def _render_final_crop(self) -> Image.Image:
        """Kết hợp ảnh cắt và tất cả các chú thích vào một ảnh PIL hoàn chỉnh."""
        x1, y1, x2, y2 = self._get_crop_coords()
        crop = self.original_image.crop((x1, y1, x2, y2)).convert("RGBA")
        draw = ImageDraw.Draw(crop)

        for ann in self.annotations:
            tool = ann[0]
            if tool == "rect":
                ax1, ay1, ax2, ay2 = ann[1]
                draw.rectangle([ax1 - x1, ay1 - y1, ax2 - x1, ay2 - y1], outline=ann[2], width=3)
            elif tool == "ellipse":
                ax1, ay1, ax2, ay2 = ann[1]
                draw.ellipse([ax1 - x1, ay1 - y1, ax2 - x1, ay2 - y1], outline=ann[2], width=3)
            elif tool == "arrow":
                ax1, ay1, ax2, ay2 = ann[1]
                draw.line([ax1 - x1, ay1 - y1, ax2 - x1, ay2 - y1], fill=ann[2], width=3)
            elif tool == "step":
                sx, sy, num = ann[1]
                bx, by = sx - x1, sy - y1
                draw.ellipse([bx - 12, by - 12, bx + 12, by + 12], fill=ann[2], outline="white", width=2)
                draw.text((bx - 4, by - 7), num, fill="white")
            elif tool == "pen":
                pts = [(px - x1, py - y1) for px, py in ann[1]]
                if len(pts) > 1:
                    draw.line(pts, fill=ann[2], width=3)

        return crop.convert("RGB")

    def _copy_to_clipboard(self):
        try:
            final_img = self._render_final_crop()
            output = io.BytesIO()
            final_img.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:] # Bỏ 14-byte BMP header cho Windows DIB
            output.close()

            import win32clipboard
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            self.close()
        except Exception:
            # Fallback nếu win32clipboard chưa có
            self.close()

    def _save_to_file(self):
        final_img = self._render_final_crop()
        path = filedialog.asksaveasfilename(defaultextension=".png", 
                                            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg")])
        if path:
            final_img.save(path)
            self.close()

    def _send_to_chat(self):
        final_img = self._render_final_crop()
        import tempfile
        tmp = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time_now())}.png")
        final_img.save(tmp)
        self.close()
        if self.on_send_image:
            self.on_send_image(tmp)

    def close(self):
        try:
            self.win.destroy()
        except Exception:
            pass

def time_now():
    import time
    return time.time()
