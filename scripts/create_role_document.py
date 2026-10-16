import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

def set_cell_background(cell, hex_color):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def format_run(run, font_name="Times New Roman", font_size=13, bold=False, italic=False, color=RGBColor(0, 0, 0)):
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color

def add_p(doc, text="", font_size=13, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=0, space_after=6, line_spacing=1.3, color=RGBColor(0,0,0)):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line_spacing
    if text:
        run = p.add_run(text)
        format_run(run, font_size=font_size, bold=bold, italic=italic, color=color)
    return p

def create_role_document():
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(0.7875)
        s.bottom_margin = Inches(0.7875)
        s.left_margin = Inches(1.18125)
        s.right_margin = Inches(0.7875)

    # 1. QUỐC HIỆU / TIÊU NGỮ / TRƯỜNG KHOA
    add_p(doc, "BỘ GIÁO DỤC VÀ ĐÀO TẠO", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_p(doc, "TRƯỜNG ĐẠI HỌC CÔNG NGHỆ ĐÔNG Á", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
    add_p(doc, "KHOA CÔNG NGHỆ THÔNG TIN", font_size=12.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_p(doc, "--------------------***--------------------", font_size=11, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=16)

    add_p(doc, "BẢNG PHÂN CÔNG VAI TRÒ VÀ NHIỆM VỤ CHI TIẾT", font_size=16, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, color=RGBColor(0, 51, 102))
    add_p(doc, "HỌC PHẦN: ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM", font_size=13.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_p(doc, "ĐỀ TÀI: XÂY DỰNG ỨNG DỤNG NHẮN TIN VÀ TRUYỀN THÔNG TIN DESKTOP", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, color=RGBColor(180, 0, 0))
    add_p(doc, "Ứng dụng: Vibe Người Tốt (React + TypeScript + Electron + Python Socket Backend)", font_size=12, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    add_p(doc, "Nhóm thực hiện: Nhóm 05  |  Lớp: DCCNTT.14.5  |  Học kỳ I - Năm học 2025 - 2026", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)

    # 2. BẢNG TỔNG QUAN PHÂN CÔNG TRÁCH NHIỆM (THEO ĐÚNG MẪU ẢNH NGƯỜI DÙNG CUNG CẤP)
    add_p(doc, "DANH SÁCH THÀNH VIÊN VÀ PHÂN CÔNG TRÁCH NHIỆM", font_size=14, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, color=RGBColor(0, 51, 102))

    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    cols = ["STT", "Họ và tên", "Mã sinh viên", "Lớp", "Vai trò & Nhiệm vụ chính"]
    col_widths = [Inches(0.6), Inches(1.8), Inches(1.1), Inches(1.1), Inches(2.8)]
    
    for i, c_name in enumerate(cols):
        hdr[i].text = c_name
        set_cell_background(hdr[i], "003366")
        set_cell_margins(hdr[i], 120, 120, 100, 100)
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, font_size=12, bold=True, color=RGBColor(255, 255, 255))

    members_summary = [
        ("1", "Vũ Duy Thái Sơn", "20231735", "DCCNTT.14.5", "Nhóm trưởng: Định hướng đề tài, quản lý tiến độ, kiến trúc hệ thống, Socket Backend & tổng hợp báo cáo."),
        ("2", "Vy Thế Mạnh", "20231865", "DCCNTT.14.5", "Thành viên: Phân tích người dùng, thiết kế và lập trình giao diện Frontend (UI/UX), kiểm thử giao diện."),
        ("3", "Vũ Minh Dân", "20231833", "DCCNTT.14.5", "Thành viên: Khảo sát nghiệp vụ, mô hình hóa Use Case/Class Diagram, thiết kế giao diện khung chat."),
        ("4", "Phạm Đức Tâm", "20231715", "DCCNTT.14.5", "Thành viên: Nghiên cứu công nghệ mạng Socket/WebSocket, thiết kế CSDL & API truyền tệp tin đa phương tiện."),
        ("5", "Hữu", "Chờ cập nhật", "DCCNTT.14.5", "Thành viên: Khảo sát thực tế, lập kế hoạch kiểm thử, thiết kế kịch bản Test Cases và biên tập tài liệu.")
    ]

    for row_idx, data in enumerate(members_summary):
        row = table.add_row().cells
        bg = "F7F9FC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(data):
            row[col_idx].text = text
            set_cell_background(row[col_idx], bg)
            set_cell_margins(row[col_idx], 80, 80, 100, 100)
            p = row[col_idx].paragraphs[0]
            if col_idx in (0, 2, 3):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif col_idx == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    format_run(r, font_size=12, bold=True)
                continue
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, font_size=12, bold=False)

    p_camket = add_p(doc, "Bảng trên thể hiện cơ cấu tổ chức và trách nhiệm cụ thể của từng thành viên trong Nhóm 05 đối với học phần Đồ án chuyên ngành Công nghệ phần mềm. Tất cả thành viên cam kết tham gia đầy đủ các giai đoạn nghiên cứu, phân tích, thiết kế, lập trình và hoàn thiện báo cáo đúng tiến độ đề ra.", font_size=11.5, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=6, space_after=18)

    # 3. BẢN ĐẶC TẢ CHI TIẾT TỪNG THÀNH VIÊN (LÀM NHƯ THẾ NÀO, BƯỚC NÀO, SẢN PHẨM GÌ)
    add_p(doc, "PHẦN I. BẢN ĐẶC TẢ CÔNG VIỆC VÀ CÁCH THỨC THỰC HIỆN CHI TIẾT", font_size=14, bold=True, space_after=12, color=RGBColor(0, 51, 102))

    members_detail = [
        {
            "name": "1. VŨ DUY THÁI SƠN - NHÓM TRƯỞNG",
            "msv": "20231735",
            "role": "Trưởng nhóm, Kiến trúc sư hệ thống, Lập trình Socket Backend & Tự động hóa",
            "responsibility": "Chịu trách nhiệm toàn diện trước Giảng viên hướng dẫn về tiến độ, chất lượng mã nguồn, độ ổn định của hệ thống mạng và tính hoàn thiện của hồ sơ báo cáo đồ án.",
            "how_to": [
                ("Giai đoạn 1: Khởi tạo dự án & Định hướng kỹ thuật", 
                 "• Nghiên cứu tổng quan thị trường ứng dụng tin nhắn (Telegram, Zalo, Discord).\n"
                 "• Lựa chọn công nghệ: Quyết định chuyển dịch từ Python Tkinter cũ sang Kiến trúc lai (Hybrid Architecture) kết hợp Python 3.13 Socket Backend với React 18 + TypeScript + Electron Desktop để đạt hiệu năng tối đa.\n"
                 "• Thiết lập kho lưu trữ mã nguồn GitHub (repository Son3333/chat-online-) và phân quyền nhánh main cho các thành viên."),
                ("Giai đoạn 2: Thiết kế Kiến trúc mạng & Giao thức truyền tin (Wire Protocol)",
                 "• Xây dựng giao thức mạng TCP Socket tùy biến: Thiết kế cấu trúc gói tin cố định với Header 4-byte Big-Endian biểu thị độ dài Payload và Body là chuỗi UTF-8 JSON nhằm giải quyết triệt để lỗi phân mảnh gói tin TCP (Packet Fragmentation).\n"
                 "• Xây dựng mô hình Client - Server đa luồng (Multi-threading Concurrency) trong src/server/server.py: Luồng chính lắng nghe cổng 8888, mỗi máy khách kết nối được cấp phát một Worker Thread riêng biệt để xử lý song song không bị tắc nghẽn.\n"
                 "• Thiết kế mô-đun Cầu nối TCP IPC trong frontend/electron/python_bridge.ts kết nối giữa Electron Node.js và Python Server."),
                ("Giai đoạn 3: Hiện thực hóa Máy chủ WAN Internet & Cơ chế Tự động hóa All-in-One",
                 "• Lập trình run_server_wan.py: Tích hợp tiện ích Bore TCP Tunnel công cộng tự động mở cổng ra mạng diện rộng Internet (bore.pub:38888) giúp người dùng có thể nhắn tin xuyên mạng LAN/4G/Wifi mà không cần cấu hình NAT Router.\n"
                 "• Xây dựng mô-đun tự động hóa scripts/setup_all_in_one.py và scripts/create_shortcut.py: Sử dụng Windows Shell COM (IShellLinkW) native hỗ trợ trọn vẹn đường dẫn tiếng Việt có dấu để tự động tạo lối tắt ngoài Desktop ('Vibe Người Tốt.lnk') kèm biểu tượng Shin-chan (app.ico).\n"
                 "• Cài đặt tự khởi động cùng Windows: Tự động đăng ký lối tắt Server WAN ngầm vào thư mục Startup của Windows, máy tính bật là server hoạt động sẵn sàng.\n"
                 "• Lập trình cơ chế lắng nghe cập nhật Git mỗi 2 giây (frontend/electron/updater.ts) cho phép người dùng lựa chọn [Cập nhật ngay] hoặc [Để sau]."),
                ("Giai đoạn 4: Tổng hợp báo cáo, kiểm thử tích hợp & Điều phối bảo vệ",
                 "• Tổng hợp và rà soát toàn bộ các chương báo cáo Word (.docx) của đề tài.\n"
                 "• Viết kịch bản khởi chạy 1-Click duy nhất qua tệp CHAY_UNG_DUNG.bat.\n"
                 "• Điều phối các buổi họp nhóm trực tuyến, kiểm tra tiến độ hàng tuần và giải quyết các xung đột mã nguồn trên Git.")
            ],
            "deliverables": "Tệp run_server.py, run_server_wan.py, src/server/server.py, scripts/setup_all_in_one.py, scripts/create_shortcut.py, CHAY_UNG_DUNG.bat, frontend/electron/main.ts, python_bridge.ts, updater.ts, tổng hợp toàn văn báo cáo.",
            "contribution": "100% - Hoàn thành xuất sắc nhiệm vụ Trưởng nhóm."
        },
        {
            "name": "2. VY THẾ MẠNH - THÀNH VIÊN",
            "msv": "20231865",
            "role": "Lập trình viên Frontend (UI/UX), Phân tích trải nghiệm người dùng",
            "responsibility": "Chịu trách nhiệm chính trong việc thiết kế toàn bộ hệ thống giao diện người dùng, tạo component React 18, styling Tailwind CSS, tối ưu tương tác người dùng và kiểm thử giao diện.",
            "how_to": [
                ("Giai đoạn 1: Phân tích đối tượng người dùng & Khảo sát UI/UX",
                 "• Thu thập hành vi sử dụng ứng dụng nhắn tin của sinh viên và người đi làm: Thói quen gõ phím (Enter gửi tin, Shift+Enter xuống dòng), nhu cầu chuyển đổi Dark/Light mode, xem ảnh phóng to.\n"
                 "• Phác thảo Wireframe và Mockup các màn hình: Khung đăng nhập, Danh sách cuộc trò chuyện bên trái, Khung chat ở giữa, Bảng thông tin bên phải trên công cụ Figma."),
                ("Giai đoạn 2: Hiện thực hóa Giao diện React 18 & TypeScript",
                 "• Khởi tạo dự án Vite + React 18 + Tailwind CSS trong thư mục frontend/.\n"
                 "• Thiết kế hệ thống bảng màu công thái học (Dark Mode: #0e1621, #17212b; Light Mode: #ffffff, #eef2f5) và hệ thống biểu tượng chuẩn Lucide Icons.\n"
                 "• Lập trình các component giao diện chính:\n"
                 "  + TitleBar.tsx: Thanh tiêu đề ứng dụng phong cách không viền (frameless) hiện đại, tích hợp nút thu nhỏ, phóng to, đóng, ghim luôn nổi (Pin Always-on-Top), nút khóa màn hình (Ctrl+L), huy hiệu trạng thái WAN động và logo Shin-chan.\n"
                 "  + ChatArea.tsx & ChatComposer.tsx: Khu vực hiển thị tin nhắn thời gian thực, tự động cuộn xuống tin nhắn mới nhất, khung gõ tin nhắn hỗ trợ đính kèm tệp tin và bộ chọn biểu tượng cảm xúc EmojiPicker.tsx.\n"
                 "  + ChatBubble.tsx: Bong bóng tin nhắn bo góc tinh tế, hỗ trợ phân biệt tin nhắn của mình (xanh lá/xanh dương) và tin nhắn đối phương, hiển thị trạng thái đã đọc, avatar và tên người gửi."),
                ("Giai đoạn 3: Lập trình Giao diện Cuộc gọi Thoại & Video Call chuyên biệt",
                 "• Xây dựng CallModal.tsx đáp ứng 2 chế độ gọi khác biệt hoàn toàn:\n"
                 "  + Video Call: Màn hình hội nghị HD 1080p, kết nối webcam thật qua navigator.mediaDevices.getUserMedia, hiển thị khung camera của mình dạng Picture-In-Picture (PIP) ở góc màn hình, nút Bật/Tắt Camera, Bật/Tắt Mic và nút Chia sẻ màn hình.\n"
                 "  + Voice Call: Màn hình gọi thoại với Avatar tỏa sóng xung kích (Pulsing rings) và dải sóng âm thanh chuyển động (Animated Equalizer Waveform bars).\n"
                 "• Tích hợp hộp thoại xem ảnh toàn màn hình sắc nét khi nhấp đúp vào ảnh trong khung chat."),
                ("Giai đoạn 4: Kiểm thử trải nghiệm người dùng & Biên soạn Chương 3",
                 "• Kiểm thử tương thích độ phân giải màn hình từ HD (1366x768) đến Full HD (1920x1080) và 2K.\n"
                 "• Soạn thảo nội dung Chương 3 (Công nghệ áp dụng: React, TypeScript, Tailwind CSS, Vite) trong báo cáo đồ án.")
            ],
            "deliverables": "Toàn bộ giao diện frontend/src/components/, frontend/src/features/chat/, CallModal.tsx, TitleBar.tsx, globals.css, đóng góp nội dung Chương 3.",
            "contribution": "100% - Hoàn thành xuất sắc nhiệm vụ Frontend UI/UX."
        },
        {
            "name": "3. VŨ MINH DÂN - THÀNH VIÊN",
            "msv": "20231833",
            "role": "Chuyên viên Phân tích nghiệp vụ (BA), Mô hình hóa hệ thống (UML)",
            "responsibility": "Chịu trách nhiệm khảo sát các quy trình nghiệp vụ nhắn tin, mô hình hóa các biểu đồ phân tích thiết kế phần mềm (BFD, Use Case Diagram, Class Diagram, Sequence Diagram) và thiết kế giao diện danh sách bạn bè.",
            "how_to": [
                ("Giai đoạn 1: Khảo sát nghiệp vụ & Xác định tác nhân hệ thống",
                 "• Khảo sát và lập danh mục yêu cầu chức năng (Functional Requirements) và yêu cầu phi chức năng (Non-functional Requirements).\n"
                 "• Phân định 3 tác nhân chính của hệ thống: Khách (Guest), Người dùng (Member), Quản trị viên nhóm (Group Admin).\n"
                 "• Định nghĩa 22 Use Case nghiệp vụ từ đăng ký, đăng nhập, chat 1-1, chat nhóm, ghim tin, thu hồi tin đến cuộc gọi thoại/video."),
                ("Giai đoạn 2: Xây dựng các biểu đồ phân tích và thiết kế hệ thống (UML)",
                 "• Xây dựng Biểu đồ phân rã chức năng (Business Function Diagram - BFD) phân chia thành 4 phân hệ chính: Quản lý tài khoản, Quản lý danh bạ & nhóm, Truyền tin thời gian thực, Tích hợp hệ thống Desktop.\n"
                 "• Vẽ Biểu đồ Use Case tổng quát và các biểu đồ Use Case chi tiết từng phân hệ trên phần mềm StarUML / Draw.io.\n"
                 "• Xây dựng Biểu đồ lớp (Class Diagram) mô tả các thực thể: User, Conversation, Message, Reaction, Friendship và mối quan hệ giữa chúng.\n"
                 "• Xây dựng Biểu đồ tuần tự (Sequence Diagram) mô tả chi tiết luồng xử lý: Luồng gửi nhận tin nhắn thời gian thực qua Socket, luồng thiết lập cuộc gọi (Signaling Handshake), luồng thu hồi tin nhắn."),
                ("Giai đoạn 3: Phối hợp lập trình phân hệ Tìm kiếm & Danh mục cuộc trò chuyện",
                 "• Tham gia lập trình mô-đun frontend/src/features/chat/Sidebar.tsx: Xử lý bộ lọc cuộc trò chuyện theo Tab ('Tất cả', 'Cá nhân', 'Nhóm'), tính năng tìm kiếm toàn cục theo @username và #ID người dùng.\n"
                 "• Thiết kế hộp thoại thông tin cuộc trò chuyện (ChatInfoModal.tsx) hiển thị danh sách thành viên, danh mục ảnh/tệp tin đã gửi và danh sách tin nhắn đã ghim."),
                ("Giai đoạn 4: Biên tập và hoàn thiện nội dung Chương 2 & Chương 4",
                 "• Chịu trách nhiệm biên soạn trọn vẹn Chương 2 (Tổng hợp, phân tích và đánh giá thực tế) và Chương 4 (Phân tích và thiết kế hệ thống) trong hồ sơ báo cáo Word của nhóm.")
            ],
            "deliverables": "Tài liệu đặc tả yêu cầu, hệ thống biểu đồ UML (BFD, Use Case, Class, Sequence Diagrams), Sidebar.tsx (Tab & Filter), ChatInfoModal.tsx, soạn thảo hoàn chỉnh Chương 2 và Chương 4.",
            "contribution": "100% - Hoàn thành xuất sắc nhiệm vụ Phân tích & Thiết kế."
        },
        {
            "name": "4. PHẠM ĐỨC TÂM - THÀNH VIÊN",
            "msv": "20231715",
            "role": "Lập trình viên Cơ sở dữ liệu & API mạng truyền file đa phương tiện",
            "responsibility": "Chịu trách nhiệm thiết kế cấu trúc CSDL SQLite, lập trình logic xử lý truy vấn dữ liệu an toàn, xây dựng API băm mật khẩu, lưu trữ và truyền nhận tệp tin đính kèm dung lượng lớn.",
            "how_to": [
                ("Giai đoạn 1: Thiết kế Cơ sở dữ liệu quan hệ (Database Design)",
                 "• Thiết kế mô hình thực thể liên kết (ERD) cho CSDL chat_database.db gồm 6 bảng chuẩn hóa: users, conversations, conversation_members, messages, message_reactions, friendships.\n"
                 "• Thiết lập các khóa chính (PK), khóa ngoại (FK) có ràng buộc ON DELETE CASCADE để đảm bảo toàn vẹn dữ liệu.\n"
                 "• Đánh chỉ mục (Indexes) trên các trường thường xuyên tra cứu như sender_id, conversation_id, username để tối ưu tốc độ truy vấn < 5ms."),
                ("Giai đoạn 2: Lập trình mô-đun Quản trị CSDL (src/server/database.py)",
                 "• Lập trình lớp DatabaseManager trong Python sử dụng mô-đun sqlite3 kết hợp luồng thread-safe (check_same_thread=False) và Transaction an toàn.\n"
                 "• Triển khai cơ chế bảo mật mật khẩu cấp cao: Sử dụng thuật toán chuẩn công nghiệp PBKDF2-HMAC-SHA256 với 100.000 vòng lặp (iterations) kết hợp chuỗi salt ngẫu nhiên 16 bytes (os.urandom(16)), ngăn chặn hoàn toàn các cuộc tấn công Rainbow Table và Brute-force.\n"
                 "• Lập trình các phương thức truy vấn nghiệp vụ: Thêm người dùng, xác thực đăng nhập, lưu tin nhắn, truy vấn lịch sử chat phân trang (Pagination), ghim tin nhắn, thả reaction, thu hồi tin nhắn."),
                ("Giai đoạn 3: Xây dựng Hệ thống Lưu trữ & Truyền nhận Tệp tin Đa phương tiện",
                 "• Lập trình cơ chế xử lý tệp tin trong src/server/server.py và frontend/electron/main.ts:\n"
                 "  + Tải lên (Upload): Tiếp nhận tệp tin nhị phân mã hóa Base64, tạo mã định danh duy nhất (UUID), lưu an toàn vào thư mục src/server/uploads/.\n"
                 "  + Tải xuống (Download): Đọc tệp tin nhị phân từ máy chủ và gửi về Client qua gói tin JSON Base64, tích hợp hộp thoại lưu tệp Windows SaveFileDialog.\n"
                 "  + Xem trước hình ảnh (Preview): Cung cấp API phục vụ hình ảnh trực tiếp giúp Client hiển thị thumbnail ngay lập tức trên bong bóng chat."),
                ("Giai đoạn 4: Kiểm thử cơ sở dữ liệu & Viết báo cáo",
                 "• Kiểm thử chịu tải CSDL với 10.000 bản ghi tin nhắn và 100 tài khoản người dùng thử nghiệm.\n"
                 "• Đóng góp biên soạn phần thiết kế CSDL và giao thức lưu trữ file trong Chương 4.")
            ],
            "deliverables": "Tệp src/server/database.py, CSDL chat_database.db, thư mục uploads/, API upload/download file Base64, phần thiết kế CSDL trong Chương 4.",
            "contribution": "100% - Hoàn thành xuất sắc nhiệm vụ Backend Database & File API."
        },
        {
            "name": "5. HỮU - THÀNH VIÊN",
            "msv": "Chờ cập nhật (Lớp: DCCNTT.14.5)",
            "role": "Chuyên viên Kiểm thử phần mềm (QA/QC), Biên tập hồ sơ tài liệu kỹ thuật",
            "responsibility": "Chịu trách nhiệm lập kế hoạch kiểm thử chất lượng hệ thống, thiết kế bộ kịch bản kiểm thử (Test Cases), thực thi kiểm thử hồi quy, ghi nhận bug và biên tập, định dạng tài liệu đồ án.",
            "how_to": [
                ("Giai đoạn 1: Lập Kế hoạch Kiểm thử Phần mềm (Test Plan)",
                 "• Xác định mục tiêu kiểm thử: Đảm bảo toàn bộ 22 tính năng của hệ thống vận hành chuẩn xác 100%, không xảy ra sự cố sập ứng dụng (crash), rò rỉ bộ nhớ hay gián đoạn mạng.\n"
                 "• Lựa chọn phạm vi kiểm thử: Kiểm thử chức năng (Functional Testing), Kiểm thử giao diện (UI Testing), Kiểm thử bảo mật (Security Testing) và Kiểm thử hiệu năng mạng WAN (Performance Testing)."),
                ("Giai đoạn 2: Xây dựng Ma trận và Kịch bản Kiểm thử chi tiết (Test Cases)",
                 "• Thiết kế 22 ca kiểm thử tương ứng với 22 chức năng hoàn thiện của hệ thống:\n"
                 "  + TC01: Kiểm thử Đăng ký tài khoản (mật khẩu yếu, mật khẩu trùng lặp, mật khẩu hợp lệ).\n"
                 "  + TC02: Kiểm thử Đăng nhập hệ thống và cơ chế ép đăng xuất thiết bị cũ (Forced Logout).\n"
                 "  + TC03 - TC07: Kiểm thử Nhắn tin 1-1, Trả lời trích dẫn tin nhắn, Ghim tin nhắn, Thu hồi tin nhắn 2 chiều trong 5 giây, Thả 6 loại biểu cảm Reaction.\n"
                 "  + TC08 - TC10: Kiểm thử Gửi/Nhận ảnh preview trực tiếp, truyền tệp tin dung lượng lớn (.pdf, .docx, .zip) và Cloud lưu trữ cá nhân.\n"
                 "  + TC11 - TC14: Kiểm thử Tìm kiếm bạn bè qua @username, Kết bạn, Tạo nhóm chat phân quyền, Cuộc gọi thoại & Video call.\n"
                 "  + TC15 - TC18: Kiểm thử Khóa màn hình nhanh Ctrl+L, Ghim cửa sổ Always on Top, Đổi giao diện Sáng/Tối.\n"
                 "  + TC19 - TC22: Kiểm thử Tạo lối tắt Desktop tự động, Tự khởi động Server WAN cùng Windows, Lắng nghe cập nhật mã nguồn Git 2s."),
                ("Giai đoạn 3: Thực thi Kiểm thử, Ghi nhận lỗi (Bug Tracking) & Đánh giá kết quả",
                 "• Thực thi toàn bộ các ca kiểm thử trên nhiều môi trường: Windows 10, Windows 11, mạng nội bộ LAN và mạng Internet qua Bore WAN Tunnel.\n"
                 "• Ghi nhận các lỗi phát sinh (lỗi đường dẫn tiếng Việt khi tạo shortcut, lỗi camera chưa bật trong video call) và phối hợp cùng nhóm trưởng khắc phục triệt để.\n"
                 "• Tổng hợp Bảng ma trận kết quả kiểm thử (Test Matrix) với kết quả đạt 22/22 ca kiểm thử (Pass 100%)."),
                ("Giai đoạn 4: Biên tập hồ sơ, chuẩn hóa định dạng văn bản & Chuẩn bị Slide bảo vệ",
                 "• Chuẩn hóa toàn bộ định dạng font chữ Times New Roman, cỡ chữ, căn lề 2-2-3-2 cm cho các file báo cáo của nhóm theo đúng quy chuẩn trường Đại học Công nghệ Đông Á.\n"
                 "• Chịu trách nhiệm biên tập mục Kiểm thử (mục 5.3) và phần Kết luận trong Chương 5.\n"
                 "• Thiết kế bộ slide thuyết trình đồ án phục vụ buổi bảo vệ trước Hội đồng chấm thi.")
            ],
            "deliverables": "Kế hoạch kiểm thử (Test Plan), bộ 22 Kịch bản kiểm thử (Test Cases), Bảng ma trận kết quả kiểm thử (Test Matrix đạt 100% Pass), biên tập mục 5.3 Chương 5, bộ slide thuyết trình.",
            "contribution": "100% - Hoàn thành xuất sắc nhiệm vụ QA/QC & Biên tập hồ sơ."
        }
    ]

    for m in members_detail:
        add_p(doc, m["name"], font_size=13.5, bold=True, space_before=10, space_after=2, color=RGBColor(0, 51, 102))
        add_p(doc, f"• Mã sinh viên: {m['msv']}   |   Lớp: DCCNTT.14.5", font_size=12, bold=True, space_after=2)
        add_p(doc, f"• Vai trò đảm nhiệm: {m['role']}", font_size=12, bold=True, space_after=2)
        add_p(doc, f"• Trách nhiệm cốt lõi: {m['responsibility']}", font_size=12, italic=True, space_after=6)
        
        add_p(doc, "Các nhiệm vụ và các bước thực hiện chi tiết:", font_size=12.5, bold=True, space_after=4)
        for stage, content in m["how_to"]:
            add_p(doc, stage, font_size=12, bold=True, italic=True, space_after=2, color=RGBColor(180, 0, 0))
            for line in content.split("\n"):
                if line.strip():
                    add_p(doc, line.strip(), font_size=12, space_after=2)

        add_p(doc, f"• Sản phẩm bàn giao cụ thể (Deliverables): {m['deliverables']}", font_size=12, bold=True, space_before=4, space_after=2)
        add_p(doc, f"• Đánh giá mức độ hoàn thành nhiệm vụ: {m['contribution']}", font_size=12, bold=True, space_after=14, color=RGBColor(0, 128, 0))
        add_p(doc, "------------------------------------------------------------------------------------------------------------------------", font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, color=RGBColor(200, 200, 200))

    # 4. MA TRẬN PHÂN CÔNG THEO 22 CHỨC NĂNG HỆ THỐNG (RACI MATRIX)
    add_p(doc, "PHẦN II. MA TRẬN PHÂN CÔNG THEO 22 TÍNH NĂNG HỆ THỐNG (RACI MATRIX)", font_size=14, bold=True, space_before=14, space_after=6, color=RGBColor(0, 51, 102))
    add_p(doc, "Quy ước vai trò: [R - Responsible: Người trực tiếp lập trình/thực thi] | [A - Accountable: Người chịu trách nhiệm phê duyệt] | [C - Consulted: Người tư vấn/hỗ trợ nghiệp vụ] | [I - Informed: Người theo dõi/kiểm thử].", font_size=11, italic=True, space_after=8)

    t_raci = doc.add_table(rows=1, cols=6)
    t_raci.alignment = WD_TABLE_ALIGNMENT.CENTER
    r_hdr = t_raci.rows[0].cells
    r_cols = ["STT", "Tính năng hệ thống", "Sơn (TN)", "Mạnh (FE)", "Dân (BA)", "Tâm (DB) / Hữu (QA)"]
    for i, rc in enumerate(r_cols):
        r_hdr[i].text = rc
        set_cell_background(r_hdr[i], "003366")
        set_cell_margins(r_hdr[i], 100, 100, 80, 80)
        p = r_hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, font_size=11, bold=True, color=RGBColor(255, 255, 255))

    features_raci = [
        ("1", "Đăng ký & Đăng nhập (PBKDF2 Salt)", "A", "R (Giao diện)", "C (Thiết kế)", "R (CSDL Tâm) / I (Hữu)"),
        ("2", "Danh sách cuộc trò chuyện & Chấm Online", "A", "R (UI Component)", "R (Filter Tab)", "R (Socket State) / I"),
        ("3", "Nhắn tin văn bản thời gian thực", "A (Socket Core)", "R (ChatBubble)", "C (Nghiệp vụ)", "R (Lưu DB) / I"),
        ("4", "Trả lời trích dẫn tin nhắn (Reply/Quote)", "A (Packet Format)", "R (Preview Banner)", "C (Luồng tương tác)", "R (Lưu reply_to_id) / I"),
        ("5", "Thả biểu cảm cảm xúc (Reactions)", "A (Broadcast Event)", "R (Picker & Badge)", "C (UI Matrix)", "R (Bảng reactions) / I"),
        ("6", "Ghim tin nhắn quan trọng (Pin Message)", "A (Pin Event)", "R (Banner Pin)", "C (Use Case)", "R (Cột is_pinned) / I"),
        ("7", "Thu hồi tin nhắn 2 phía (Recall Message)", "A (Broadcast Recall)", "R (Cập nhật UI)", "C (Quy tắc 5s)", "R (Cột is_deleted) / I"),
        ("8", "Gửi/Xem ảnh phóng to toàn màn hình", "A (Bridge IPC)", "R (Modal Preview)", "C (Giao diện)", "R (Lưu uploads/) / I"),
        ("9", "Truyền tệp tin (.pdf, .docx, .zip)", "A (Length Packet)", "R (File Card)", "C (Giới hạn dung lượng)", "R (SaveFileDialog) / I"),
        ("10", "Cloud cá nhân (Saved Messages)", "A (Private Protocol)", "R (Saved UI)", "C (Đặc tả)", "R (Type='saved') / I"),
        ("11", "Tìm kiếm toàn cục (@user / #ID)", "A (Search API)", "R (Debounce Search)", "R (Đặc tả BA)", "R (Query LIKE) / I"),
        ("12", "Quản lý Danh bạ & Bạn bè", "A (Friend Socket)", "R (ContactsModal)", "R (Luồng kết bạn)", "R (Bảng friendships) / I"),
        ("13", "Tạo nhóm trò chuyện phân quyền", "A (Group Handler)", "R (CreateGroupModal)", "R (Use Case nhóm)", "R (Group Admin) / I"),
        ("14", "Cuộc gọi Thoại & Video (Camera PIP)", "A (Call Signaling)", "R (Webcam PIP)", "C (Kịch bản gọi)", "R (Socket Call) / I"),
        ("15", "Hiển thị đang soạn tin (Typing Indicator)", "A (Typing Event)", "R (Header Pulse)", "C (Timeout 2.5s)", "I (Kiểm thử Hữu)"),
        ("16", "Khóa ứng dụng nhanh (Ctrl + L)", "A (HotKey Hook)", "R (LockScreen.tsx)", "C (Bảo mật)", "I (Kiểm thử Hữu)"),
        ("17", "Ghim cửa sổ luôn nổi (Always on Top)", "A (Electron Window)", "R (Nút Pin TitleBar)", "C (Tiện ích)", "I (Kiểm thử Hữu)"),
        ("18", "Chuyển đổi giao diện Sáng / Tối", "A", "R (Tailwind Dark/Light)", "C (Công thái học)", "I (Kiểm thử Hữu)"),
        ("19", "Nhận diện thương hiệu Shin-chan", "A (Quản lý Icon)", "R (Logo Component)", "C (Thiết kế)", "I (Kiểm thử Hữu)"),
        ("20", "Tự động tạo lối tắt Desktop (IShellLinkW)", "R (Code C#/Python)", "C (Trải nghiệm)", "C (Hệ thống)", "I (Kiểm thử Hữu)"),
        ("21", "Tự khởi động Server WAN cùng Windows", "R (Bore Tunnel)", "C (Chỉ báo WAN)", "C (Quy trình)", "I (Kiểm thử Hữu)"),
        ("22", "Lắng nghe cập nhật Git mỗi 2 giây", "R (GitUpdater.ts)", "R (UpdateModal.tsx)", "C (Workflow)", "I (Kiểm thử Hữu)")
    ]

    for row_idx, r_data in enumerate(features_raci):
        row = t_raci.add_row().cells
        bg = "F7F9FC" if row_idx % 2 == 1 else "FFFFFF"
        for col_idx, text in enumerate(r_data):
            row[col_idx].text = text
            set_cell_background(row[col_idx], bg)
            set_cell_margins(row[col_idx], 60, 60, 80, 80)
            p = row[col_idx].paragraphs[0]
            if col_idx in (0, 2, 3, 4):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in p.runs:
                format_run(r, font_size=11, bold=(col_idx == 1))

    # 5. PHẦN KÝ TÊN VÀ CAM KẾT
    add_p(doc, "", space_after=14)
    add_p(doc, "Hà Nội, ngày 16 tháng 10 năm 2026", font_size=12, italic=True, align=WD_ALIGN_PARAGRAPH.RIGHT, space_after=10)

    t_sign = doc.add_table(rows=1, cols=2)
    t_sign.alignment = WD_TABLE_ALIGNMENT.CENTER
    s_cells = t_sign.rows[0].cells
    
    p_left = s_cells[0].paragraphs[0]
    p_left.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_l1 = p_left.add_run("GIẢNG VIÊN HƯỚNG DẪN\n")
    format_run(r_l1, font_size=12.5, bold=True)
    r_l2 = p_left.add_run("(Ký và ghi rõ họ tên)\n\n\n\n\n")
    format_run(r_l2, font_size=11, italic=True)
    r_l3 = p_left.add_run("ThS. Giảng viên Khoa CNTT")
    format_run(r_l3, font_size=12, bold=True)

    p_right = s_cells[1].paragraphs[0]
    p_right.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_r1 = p_right.add_run("TRƯỞNG NHÓM ĐỒ ÁN\n")
    format_run(r_r1, font_size=12.5, bold=True)
    r_r2 = p_right.add_run("(Ký và ghi rõ họ tên)\n\n\n\n\n")
    format_run(r_r2, font_size=11, italic=True)
    r_r3 = p_right.add_run("Vũ Duy Thái Sơn")
    format_run(r_r3, font_size=12, bold=True)

    file_name = "BẢNG PHÂN CÔNG VAI TRÒ VÀ NHIỆM VỤ CHI TIẾT THÀNH VIÊN - NHÓM 05.docx"
    doc.save(file_name)
    doc.save(os.path.join("docs", file_name))
    print(f"[OK] Da tao thanh cong file: {file_name}")

if __name__ == "__main__":
    create_role_document()

