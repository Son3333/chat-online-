import customtkinter as ctk
from PIL import Image, ImageTk
import threading
import time
import base64
import zlib
import os

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import sounddevice as sd
    import numpy as np
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False


class IncomingCallDialog(ctk.CTkToplevel):
    """Hộp thoại thông báo cuộc gọi đến kèm chuông reo (Telegram / Messenger style)."""
    def __init__(self, master, call_info: dict, on_accept_cb, on_reject_cb):
        super().__init__(master)
        self.call_info = call_info
        self.on_accept_cb = on_accept_cb
        self.on_reject_cb = on_reject_cb
        self.answered = False

        self.title("Cuộc gọi đến...")
        self.geometry("360x420")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self._on_reject)

        self._build_ui()
        self._start_ringtone()

    def _build_ui(self):
        c_type = self.call_info.get("call_type", "voice")
        type_str = "📹 Cuộc gọi Video đến" if c_type == "video" else "📞 Cuộc gọi Thoại đến"
        name = self.call_info.get("caller_name", "Người dùng")
        color = self.call_info.get("avatar_color", "#2563EB")

        ctk.CTkLabel(
            self,
            text=type_str,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#38BDF8"
        ).pack(pady=(24, 16))

        # Avatar to
        avatar_btn = ctk.CTkButton(
            self,
            text=name[:1].upper(),
            width=90,
            height=90,
            corner_radius=45,
            fg_color=color,
            text_color="white",
            font=ctk.CTkFont(size=36, weight="bold"),
            state="disabled"
        )
        avatar_btn.pack(pady=10)

        ctk.CTkLabel(
            self,
            text=name,
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            self,
            text="Đang đổ chuông...",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="gray60"
        ).pack(pady=(0, 24))

        # Nút trả lời & từ chối
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=40, pady=10)

        # Nút từ chối (Đỏ)
        ctk.CTkButton(
            btn_box,
            text="🔴 Từ Chối",
            width=120,
            height=44,
            corner_radius=22,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self._on_reject
        ).pack(side="left")

        # Nút chấp nhận (Xanh)
        ctk.CTkButton(
            btn_box,
            text="📞 Trả Lời",
            width=120,
            height=44,
            corner_radius=22,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#10B981",
            hover_color="#059669",
            command=self._on_accept
        ).pack(side="right")

    def _start_ringtone(self):
        """Phát âm thanh chuông reo định kỳ cho đến khi có phản hồi hoặc timeout 30s."""
        def _loop():
            start = time.time()
            while not self.answered and time.time() - start < 30:
                try:
                    if HAS_WINSOUND:
                        winsound.Beep(587, 250)
                        time.sleep(0.1)
                        winsound.Beep(659, 350)
                    time.sleep(1.2)
                except Exception:
                    time.sleep(1.5)
            if not self.answered:
                self.after(0, self._on_reject)
        threading.Thread(target=_loop, daemon=True).start()

    def _on_accept(self):
        self.answered = True
        self.on_accept_cb(self.call_info)
        self.destroy()

    def _on_reject(self):
        self.answered = True
        self.on_reject_cb(self.call_info)
        try:
            self.destroy()
        except Exception:
            pass


class ActiveCallWindow(ctk.CTkToplevel):
    """
    Cửa sổ cuộc gọi thoại / cuộc gọi video trực tiếp (Real-time Audio/Video Stream).
    Hỗ trợ truyền hình ảnh camera, micrô, Picture-in-Picture (PIP) và đồng hồ đếm giờ.
    """
    def __init__(self, master, channel_id: str, current_user_id: int, partner_name: str,
                 partner_avatar_color: str, call_type: str, network_client, on_ended_cb):
        super().__init__(master)
        self.channel_id = channel_id
        self.current_user_id = current_user_id
        self.partner_name = partner_name
        self.partner_avatar_color = partner_avatar_color
        self.call_type = call_type # 'voice' hoặc 'video'
        self.net = network_client
        self.on_ended_cb = on_ended_cb

        self.running = True
        self.connected = False
        self.mic_muted = False
        self.camera_enabled = (call_type == "video")
        self.start_time = None
        self.cap = None

        title_prefix = "Cuộc gọi Video" if call_type == "video" else "Cuộc gọi Thoại"
        self.title(f"{title_prefix} - {self.partner_name}")
        self.geometry("520x620" if call_type == "video" else "380x460")
        self.protocol("WM_DELETE_WINDOW", self.end_call)

        self._build_ui()
        self._setup_media()

    def _build_ui(self):
        # 1. Header cuộc gọi
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.lbl_title = ctk.CTkLabel(
            self.header_frame,
            text=f"Đang gọi cho {self.partner_name}...",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_title.pack()

        self.lbl_timer = ctk.CTkLabel(
            self.header_frame,
            text="00:00",
            font=ctk.CTkFont(size=13, slant="italic"),
            text_color="#38BDF8"
        )
        self.lbl_timer.pack()

        # 2. Vùng hiển thị chính (Video hoặc Avatar lớn)
        self.display_frame = ctk.CTkFrame(self, fg_color=("#F1F5F9", "#0F172A"), corner_radius=12)
        self.display_frame.pack(fill="both", expand=True, padx=16, pady=6)

        if self.call_type == "video":
            # Video đối phương (Main Remote Video)
            self.lbl_remote_video = ctk.CTkLabel(self.display_frame, text="", fg_color="black", corner_radius=8)
            self.lbl_remote_video.pack(fill="both", expand=True, padx=4, pady=4)

            # PIP Video của chính mình (Góc dưới bên phải)
            self.lbl_local_video = ctk.CTkLabel(
                self.display_frame,
                text="Camera bạn",
                width=110,
                height=85,
                fg_color="#1E293B",
                corner_radius=6,
                font=ctk.CTkFont(size=10)
            )
            self.lbl_local_video.place(relx=0.96, rely=0.96, anchor="se")
        else:
            # Cuộc gọi thoại: Avatar lớn ở chính giữa
            avatar_btn = ctk.CTkButton(
                self.display_frame,
                text=self.partner_name[:1].upper(),
                width=100,
                height=100,
                corner_radius=50,
                fg_color=self.partner_avatar_color,
                text_color="white",
                font=ctk.CTkFont(size=42, weight="bold"),
                state="disabled"
            )
            avatar_btn.place(relx=0.5, rely=0.45, anchor="center")

            self.lbl_voice_status = ctk.CTkLabel(
                self.display_frame,
                text="Đang kết nối âm thanh...",
                font=ctk.CTkFont(size=13),
                text_color="gray60"
            )
            self.lbl_voice_status.place(relx=0.5, rely=0.75, anchor="center")

        # 3. Thanh công cụ điều khiển ở đáy
        self.controls_bar = ctk.CTkFrame(self, height=70, fg_color="transparent")
        self.controls_bar.pack(fill="x", padx=16, pady=(6, 16))

        # Nút Mic (Bật / Tắt mic)
        self.btn_mic = ctk.CTkButton(
            self.controls_bar,
            text="🎤 Mic Bật",
            width=85,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=self.toggle_mic
        )
        self.btn_mic.pack(side="left", padx=5)

        # Nút Camera (Nếu là cuộc gọi video)
        if self.call_type == "video":
            self.btn_cam = ctk.CTkButton(
                self.controls_bar,
                text="📷 Cam Bật",
                width=90,
                height=40,
                corner_radius=20,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=("#E2E8F0", "#334155"),
                text_color=("#0F172A", "#F8FAFC"),
                hover_color=("#CBD5E1", "#475569"),
                command=self.toggle_camera
            )
            self.btn_cam.pack(side="left", padx=5)

        # Nút Chia sẻ Màn hình (Screen Share)
        self.sharing_screen = False
        self.btn_screen_share = ctk.CTkButton(
            self.controls_bar,
            text="🖥️ Chia Sẻ",
            width=90,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=self.toggle_screen_share
        )
        self.btn_screen_share.pack(side="left", padx=5)

        # Nút Ghim Trên Cùng (Always on Top)
        self.is_topmost = False
        self.btn_topmost = ctk.CTkButton(
            self.controls_bar,
            text="📌 Ghim",
            width=75,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=("#E2E8F0", "#334155"),
            text_color=("#0F172A", "#F8FAFC"),
            hover_color=("#CBD5E1", "#475569"),
            command=self.toggle_topmost
        )
        self.btn_topmost.pack(side="left", padx=5)

        # Nút Kết Thúc Cuộc Gọi (Đỏ)
        self.btn_end = ctk.CTkButton(
            self.controls_bar,
            text="🔴 Kết Thúc",
            width=100,
            height=40,
            corner_radius=20,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.end_call
        )
        self.btn_end.pack(side="right", padx=5)

    def set_connected(self):
        """Khi cuộc gọi chính thức kết nối thành công."""
        self.connected = True
        self.start_time = time.time()
        self.lbl_title.configure(text=f"Đang đàm thoại với {self.partner_name}")
        if hasattr(self, "lbl_voice_status"):
            self.lbl_voice_status.configure(text="Đã kết nối thoại trực tiếp (Âm thanh HD)")
        self._start_timer()

    def _start_timer(self):
        def _tick():
            if not self.running or not self.connected:
                return
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            try:
                if self.winfo_exists():
                    self.lbl_timer.configure(text=f"{mins:02d}:{secs:02d}")
                    self.after(1000, _tick)
            except Exception:
                pass
        self.after(1000, _tick)

    def _setup_media(self):
        """Khởi động luồng truyền & nhận âm thanh và hình ảnh."""
        # Luồng gửi âm thanh (Mic)
        if HAS_AUDIO:
            threading.Thread(target=self._audio_sender_loop, daemon=True).start()
            threading.Thread(target=self._audio_player_worker, daemon=True).start()

        # Luồng quay camera & gửi video
        if self.call_type == "video" and HAS_CV2:
            threading.Thread(target=self._video_capture_loop, daemon=True).start()

    def _audio_sender_loop(self):
        """Ghi âm từ mic (16000Hz, int16, mono) và nén gửi qua TCP Relay."""
        try:
            samplerate = 16000
            blocksize = 1024 # ~64ms
            with sd.RawInputStream(samplerate=samplerate, blocksize=blocksize,
                                   dtype='int16', channels=1) as stream:
                while self.running:
                    data, overflowed = stream.read(blocksize)
                    if not self.mic_muted and self.connected and data:
                        comp = zlib.compress(bytes(data))
                        b64 = base64.b64encode(comp).decode('utf-8')
                        self.net.send_call_media(self.channel_id, self.current_user_id, 'audio', b64)
                    else:
                        time.sleep(0.05)
        except Exception:
            pass

    def _audio_player_worker(self):
        """Phát âm thanh nhận được từ đối phương ra loa."""
        try:
            self._audio_queue = []
            samplerate = 16000
            with sd.RawOutputStream(samplerate=samplerate, dtype='int16', channels=1) as stream:
                while self.running:
                    if self._audio_queue:
                        chunk = self._audio_queue.pop(0)
                        stream.write(chunk)
                    else:
                        time.sleep(0.01)
        except Exception:
            pass

    def _video_capture_loop(self):
        """Quay camera cục bộ hoặc chia sẻ màn hình, nén JPEG và truyền cho đối phương."""
        try:
            self.cap = cv2.VideoCapture(0)
            while self.running:
                frame = None
                if self.sharing_screen:
                    try:
                        from PIL import ImageGrab
                        screen_img = ImageGrab.grab()
                        screen_np = np.array(screen_img)
                        frame = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
                    except Exception:
                        frame = None
                elif self.camera_enabled and self.cap.isOpened():
                    ret, f = self.cap.read()
                    if ret and f is not None:
                        frame = f

                if frame is not None:
                    # 1. Hiển thị PIP cục bộ
                    small_local = cv2.resize(frame, (110, 85))
                    rgb_local = cv2.cvtColor(small_local, cv2.COLOR_BGR2RGB)
                    img_local = Image.fromarray(rgb_local)
                    ctk_img_local = ctk.CTkImage(light_image=img_local, dark_image=img_local, size=(110, 85))
                    self.after(0, lambda ci=ctk_img_local: self._update_local_video(ci))

                    # 2. Nén và gửi cho đối phương nếu đã kết nối
                    if self.connected:
                        target_size = (640, 360) if self.sharing_screen else (360, 270)
                        resized = cv2.resize(frame, target_size)
                        quality = 65 if self.sharing_screen else 55
                        _, enc = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
                        b64 = base64.b64encode(enc.tobytes()).decode('utf-8')
                        self.net.send_call_media(self.channel_id, self.current_user_id, 'video', b64)

                time.sleep(0.08) # ~12-15 FPS tiết kiệm băng thông và CPU
        except Exception:
            pass
        finally:
            if self.cap:
                self.cap.release()

    def _update_local_video(self, ctk_img):
        try:
            if self.winfo_exists() and hasattr(self, "lbl_local_video"):
                self.lbl_local_video.configure(image=ctk_img, text="")
        except Exception:
            pass

    def on_media_received(self, media_type: str, b64_data: str):
        """Nhận gói tin media (audio/video) từ đối phương được server relay tới."""
        if not self.running:
            return
        try:
            raw = base64.b64decode(b64_data)
            if media_type == 'audio' and hasattr(self, "_audio_queue"):
                pcm = zlib.decompress(raw)
                self._audio_queue.append(pcm)
            elif media_type == 'video' and hasattr(self, "lbl_remote_video") and HAS_CV2:
                np_arr = np.frombuffer(raw, dtype=np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                if frame is not None:
                    # Lấy kích thước hiển thị hiện tại của khung hình
                    h, w, _ = frame.shape
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(rgb)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(460, 345))
                    self.after(0, lambda ci=ctk_img: self._update_remote_video(ci))
        except Exception:
            pass

    def _update_remote_video(self, ctk_img):
        try:
            if self.winfo_exists() and hasattr(self, "lbl_remote_video"):
                self.lbl_remote_video.configure(image=ctk_img, text="")
        except Exception:
            pass

    def toggle_mic(self):
        self.mic_muted = not self.mic_muted
        if self.mic_muted:
            self.btn_mic.configure(text="🔇 Mic Tắt", fg_color="#EF4444", text_color="white")
        else:
            self.btn_mic.configure(text="🎤 Mic Bật", fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"))

    def toggle_camera(self):
        self.camera_enabled = not self.camera_enabled
        if not self.camera_enabled:
            self.btn_cam.configure(text="🚫 Cam Tắt", fg_color="#EF4444", text_color="white")
            if hasattr(self, "lbl_local_video"):
                self.lbl_local_video.configure(image=None, text="Cam tắt")
        else:
            self.btn_cam.configure(text="📷 Cam Bật", fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"))

    def toggle_screen_share(self):
        self.sharing_screen = not self.sharing_screen
        if self.sharing_screen:
            self.btn_screen_share.configure(text="🛑 Dừng Chia Sẻ", fg_color="#F59E0B", text_color="white")
            if hasattr(self, "lbl_local_video"):
                self.lbl_local_video.configure(text="Chia sẻ màn hình")
        else:
            self.btn_screen_share.configure(text="🖥️ Chia Sẻ", fg_color=("#E2E8F0", "#334155"), text_color=("#0F172A", "#F8FAFC"))

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.attributes("-topmost", self.is_topmost)
        if self.is_topmost:
            self.btn_topmost.configure(fg_color="#3B82F6", text="📌 Đang Ghim", text_color="white")
        else:
            self.btn_topmost.configure(fg_color=("#E2E8F0", "#334155"), text="📌 Ghim", text_color=("#0F172A", "#F8FAFC"))

    def end_call(self):
        """Kết thúc cuộc gọi và dọn dẹp tài nguyên âm thanh/camera."""
        if not self.running:
            return
        self.running = False
        try:
            self.net.call_end(self.channel_id)
        except Exception:
            pass
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
        if self.on_ended_cb:
            try:
                self.on_ended_cb(self.channel_id)
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass

