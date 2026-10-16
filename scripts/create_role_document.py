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

    add_p(doc, "BẢNG PHÂN CÔNG VAI TRÒ VÀ NHIỆM VỤ CHI TIẾT THEO CÁC GIAI ĐOẠN", font_size=15, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, color=RGBColor(0, 51, 102))
    add_p(doc, "(CÁC GIAI ĐOẠN ĐẶT CẠNH NHAU TƯƠNG ỨNG TỪNG CHƯƠNG I ĐẾN V CỦA BÁO CÁO)", font_size=12, bold=True, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4, color=RGBColor(180, 0, 0))
    add_p(doc, "HỌC PHẦN: ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=4)
    add_p(doc, "ĐỀ TÀI: XÂY DỰNG ỨNG DỤNG NHẮN TIN VÀ TRUYỀN THÔNG TIN DESKTOP", font_size=13, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2, color=RGBColor(180, 0, 0))
    add_p(doc, "Ứng dụng: Vibe Người Tốt (React 18 + TypeScript + Electron + Python Socket Backend)", font_size=11.5, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=6)
    add_p(doc, "Nhóm thực hiện: Nhóm 05  |  Lớp: DCCNTT.14.5  |  Học kỳ I - Năm học 2025 - 2026", font_size=12, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=20)

    # 2. BẢNG TỔNG QUAN PHÂN CÔNG TRÁCH NHIỆM (THEO MẪU BÁO CÁO BAN ĐẦU)
    add_p(doc, "BẢNG I. DANH SÁCH THÀNH VIÊN VÀ PHÂN CÔNG TRÁCH NHIỆM TỔNG QUÁT", font_size=13.5, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, color=RGBColor(0, 51, 102))

    table = doc.add_table(rows=1, cols=5)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    cols = ["STT", "Họ và tên", "Mã sinh viên", "Lớp", "Vai trò & Nhiệm vụ chính"]
    
    for i, c_name in enumerate(cols):
        hdr[i].text = c_name
        set_cell_background(hdr[i], "003366")
        set_cell_margins(hdr[i], 120, 120, 100, 100)
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            format_run(r, font_size=12, bold=True, color=RGBColor(255, 255, 255))

    members_summary = [
        ("1", "Vũ Duy Thái Sơn", "20231735", "DCCNTT.14.5", "Nhóm trưởng: Định hướng kỹ thuật, kiến trúc hệ thống, lập trình Socket Backend đa luồng, máy chủ WAN, tự động hóa & tổng hợp toàn văn báo cáo."),
        ("2", "Vy Thế Mạnh", "20231865", "DCCNTT.14.5", "Thành viên: Phân tích người dùng, thiết kế giao diện Figma, lập trình toàn bộ Frontend (React 18, Tailwind, TitleBar, CallModal) & kiểm thử UI/UX."),
        ("3", "Vũ Minh Dân", "20231833", "DCCNTT.14.5", "Thành viên: Khảo sát nghiệp vụ, mô hình hóa hệ thống UML (BFD, Use Case, Class, Sequence), lập trình giao diện khung chat & biên soạn Chương 2, 4."),
        ("4", "Phạm Đức Tâm", "20231715", "DCCNTT.14.5", "Thành viên: Nghiên cứu công nghệ mạng Socket, thiết kế CSDL SQLite (chat_database.db), lập trình API upload/download truyền file Base64 & bảo mật PBKDF2."),
        ("5", "Hữu", "Chờ cập nhật", "DCCNTT.14.5", "Thành viên: Lập kế hoạch kiểm thử (Test Plan), thiết kế và thực thi 22 kịch bản Test Cases (100% Pass), chuẩn hóa định dạng văn bản & làm Slide thuyết trình.")
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

    add_p(doc, "Bảng trên thể hiện cơ cấu tổ chức và trách nhiệm cốt lõi của từng thành viên trong Nhóm 05. Mỗi thành viên đều cam kết tham gia xuyên suốt từ Giai đoạn 1 đến Giai đoạn 5 (tương ứng từ Chương I đến Chương V trong đề cương báo cáo) đúng tiến độ 7 tuần đã cam kết với Khoa.", font_size=11.5, italic=True, align=WD_ALIGN_PARAGRAPH.JUSTIFY, space_before=6, space_after=18)

    # 3. CÁC GIAI ĐOẠN ĐẶT CẠNH NHAU THEO TỪNG CHƯƠNG (CHƯƠNG I -> V)
    add_p(doc, "PHẦN I. CHI TIẾT NHIỆM VỤ CỦA TỪNG THÀNH VIÊN THEO TỪNG GIAI ĐOẠN (ĐẶT GẦN NHAU THEO TỪNG CHƯƠNG)", font_size=14, bold=True, space_after=10, color=RGBColor(0, 51, 102))
    add_p(doc, "Nguyên tắc cấu trúc: Tại mỗi Giai đoạn (tương ứng với từng Chương của Báo cáo đồ án), công việc chi tiết và cách thức thực hiện của toàn bộ 5 thành viên được đặt ngay sát cạnh nhau để người đọc và giảng viên dễ dàng đối chiếu, đánh giá tính đồng bộ và đóng góp của từng người.", font_size=12, italic=True, space_after=14)

    stages_data = [
        {
            "stage_title": "GIAI ĐOẠN 1: KHỞI TẠO ĐỀ TÀI, XÁC ĐỊNH MỤC TIÊU VÀ PHẠM VI NGHIÊN CỨU",
            "chapter_ref": "TƯƠNG ỨNG: CHƯƠNG I. TỔNG QUAN VỀ ĐỀ TÀI (Tiến độ: Tuần 1)",
            "goal": "Làm rõ tính cấp thiết của ứng dụng nhắn tin trong kỷ nguyên số, xác định yêu cầu nghiệp vụ cốt lõi, thiết lập mục tiêu tổng quát và mục tiêu cụ thể đo lường được, khởi tạo kho mã nguồn Git và phân công kế hoạch 7 tuần.",
            "members": [
                {
                    "name": "1. Vũ Duy Thái Sơn (Nhóm trưởng):",
                    "tasks": [
                        "• Định hướng chiến lược kỹ thuật: Quyết định chuyển dịch đề tài từ mô hình Python Tkinter cũ sang Kiến trúc lai hiện đại (React 18 + TypeScript + Electron + Python 3.13 Socket Backend).",
                        "• Thiết lập mục tiêu tổng quát và hệ thống mục tiêu kỹ thuật cụ thể (độ trễ < 50ms, giao diện đa nền tảng, nhắn tin WAN xuyên mạng).",
                        "• Khởi tạo kho mã nguồn GitHub chính thức (Son3333/chat-online-), cấu hình phân quyền nhánh main và thiết lập quy trình làm việc nhóm.",
                        "• Phân chia lộ trình đồ án 7 tuần, phân công nhiệm vụ cụ thể cho từng thành viên và trực tiếp chắp bút phần Mục tiêu đề tài trong Chương I."
                    ]
                },
                {
                    "name": "2. Vy Thế Mạnh (Thành viên - Frontend UI/UX):",
                    "tasks": [
                        "• Khảo sát tính cấp thiết của đề tài: Thu thập số liệu về nhu cầu trao đổi thông tin tốc độ cao của sinh viên và người làm việc văn phòng.",
                        "• Phân tích những hạn chế của các ứng dụng nhắn tin hiện hành (quảng cáo phiền phức, bảo mật dữ liệu, chiếm dụng tài nguyên máy tính).",
                        "• Viết nội dung mục 1.1 Đặt vấn đề và tính cấp thiết của đề tài trong Chương I."
                    ]
                },
                {
                    "name": "3. Vũ Minh Dân (Thành viên - Phân tích nghiệp vụ BA):",
                    "tasks": [
                        "• Khảo sát và tổng hợp danh mục yêu cầu nghiệp vụ trao đổi thông tin (nhắn tin cá nhân 1-1, nhắn tin nhóm, đính kèm hình ảnh và tệp tin).",
                        "• Xác định các ràng buộc nghiệp vụ về thời gian thực (Real-time Delivery) và tính riêng tư của các cuộc hội thoại.",
                        "• Viết nội dung mục 1.2 Yêu cầu nghiệp vụ của đề tài trong văn bản Chương I."
                    ]
                },
                {
                    "name": "4. Phạm Đức Tâm (Thành viên - Backend & CSDL):",
                    "tasks": [
                        "• Thu thập tài liệu học thuật về mô hình Client - Server và các giao thức mạng Socket TCP, WebSocket.",
                        "• Khảo sát kiến trúc kỹ thuật của các nền tảng tin nhắn lớn (Telegram MTProto, Discord Gateway, Zalo).",
                        "• Đóng góp phần khảo sát công nghệ và chuẩn bị tư liệu tham khảo cho đề cương chi tiết của đề tài."
                    ]
                },
                {
                    "name": "5. Hữu (Thành viên - QA & Biên tập tài liệu):",
                    "tasks": [
                        "• Tổng hợp toàn bộ tài liệu nghiên cứu, ghi chú khảo sát ban đầu của các thành viên trong nhóm.",
                        "• Soạn thảo và chuẩn hóa định dạng văn bản Chương I theo quy chuẩn font Times New Roman, cỡ chữ 13, căn lề chuẩn Đại học Công nghệ Đông Á.",
                        "• Lập bảng theo dõi tiến độ công việc ban đầu và chuẩn bị biên bản họp nhóm Tuần 1."
                    ]
                }
            ],
            "deliverable": "Hoàn thiện trọn vẹn văn bản Chương I (Đặt vấn đề, Yêu cầu nghiệp vụ, Mục tiêu đề tài); Đề cương chi tiết; Kho mã nguồn GitHub hoạt động."
        },
        {
            "stage_title": "GIAI ĐOẠN 2: THU THẬP, PHÂN TÍCH VÀ ĐÁNH GIÁ THỰC TẾ",
            "chapter_ref": "TƯƠNG ỨNG: CHƯƠNG II. TỔNG HỢP, PHÂN TÍCH VÀ ĐÁNH GIÁ THỰC TẾ (Tiến độ: Tuần 2)",
            "goal": "Thu thập dữ liệu thực tế, phân tích chân dung người dùng, lập danh mục chi tiết các yêu cầu chức năng (FR) và phi chức năng (NFR), đánh giá ưu nhược điểm các giải pháp tương tự.",
            "members": [
                {
                    "name": "1. Vũ Duy Thái Sơn (Nhóm trưởng):",
                    "tasks": [
                        "• Xác định kiến trúc tổng quan hệ thống mạng và ranh giới hoạt động giữa Electron Node.js và Python Server.",
                        "• Thiết lập các chỉ số định lượng cho yêu cầu phi chức năng (NFR): Độ trễ truyền tin dưới 50ms, thời gian khởi động app < 2 giây, hỗ trợ tối thiểu 100 kết nối đồng thời trên một máy chủ.",
                        "• Phê duyệt ma trận phân loại chức năng và phân bổ kế hoạch thực hiện cho các thành viên."
                    ]
                },
                {
                    "name": "2. Vy Thế Mạnh (Thành viên - Frontend UI/UX):",
                    "tasks": [
                        "• Phân tích đối tượng người dùng (User Personas): Sinh viên cần trao đổi tài liệu nhóm; giảng viên cần gửi thông báo học tập; người làm việc cần bảo mật.",
                        "• Xây dựng các kịch bản tương tác người dùng (User Scenarios): Luồng đăng nhập nhanh, luồng tìm kiếm tin nhắn, luồng gửi ảnh xem trước tức thì.",
                        "• Viết nội dung mục 2.2.1 Phân tích người dùng trong Chương II."
                    ]
                },
                {
                    "name": "3. Vũ Minh Dân (Thành viên - Phân tích nghiệp vụ BA):",
                    "tasks": [
                        "• Phân tích và mô tả chi tiết danh mục 22 yêu cầu chức năng của hệ thống (Functional Requirements): Đăng ký/đăng nhập, chat 1-1, chat nhóm, ghim tin, thu hồi tin 2 chiều, reaction 6 biểu cảm, gọi thoại và gọi video.",
                        "• Phân loại chức năng theo mức độ ưu tiên (Must Have, Should Have, Could Have).",
                        "• Chịu trách nhiệm chính soạn thảo mục 2.2.2 Yêu cầu chức năng trong Chương II."
                    ]
                },
                {
                    "name": "4. Phạm Đức Tâm (Thành viên - Backend & CSDL):",
                    "tasks": [
                        "• Phân tích luồng dữ liệu truyền nhận tệp tin nhị phân và các nguy cơ nghẽn mạng khi chia sẻ file dung lượng lớn.",
                        "• Thiết lập các yêu cầu phi chức năng về an toàn dữ liệu: Mật khẩu người dùng bắt buộc phải được mã hóa một chiều, dữ liệu truyền qua socket phải có cơ chế đóng gói bảo vệ toàn vẹn.",
                        "• Soạn thảo mục 2.2.3 Yêu cầu phi chức năng (mục an toàn và bảo mật CSDL) trong Chương II."
                    ]
                },
                {
                    "name": "5. Hữu (Thành viên - QA & Biên tập tài liệu):",
                    "tasks": [
                        "• Thu thập thông tin so sánh các giải pháp nhắn tin hiện hành trên thị trường (Telegram, Messenger, Zalo) về ưu điểm, nhược điểm và sự khác biệt của đề tài.",
                        "• Soạn thảo mục 2.1 Tổng hợp và thu thập dữ liệu; lập bảng so sánh giải pháp tương tự.",
                        "• Tổng hợp, rà soát văn phong và định dạng hoàn thiện toàn bộ Chương II."
                    ]
                }
            ],
            "deliverable": "Hoàn thiện trọn vẹn văn bản Chương II; Bảng đặc tả 22 yêu cầu chức năng (FR); Bảng chỉ số yêu cầu phi chức năng (NFR); Hồ sơ phân tích chân dung người dùng."
        },
        {
            "stage_title": "GIAI ĐOẠN 3: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ ÁP DỤNG",
            "chapter_ref": "TƯƠNG ỨNG: CHƯƠNG III. CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ ÁP DỤNG (Tiến độ: Tuần 3)",
            "goal": "Nghiên cứu sâu các cơ sở lý thuyết về mạng máy tính, giao thức Socket TCP, cơ chế đa luồng, hệ sinh thái React 18, TypeScript, Tailwind CSS, Electron và hệ quản trị CSDL SQLite an toàn.",
            "members": [
                {
                    "name": "1. Vũ Duy Thái Sơn (Nhóm trưởng):",
                    "tasks": [
                        "• Nghiên cứu mô hình Client - Server hướng kết nối qua giao thức mạng TCP/IP (Transmission Control Protocol).",
                        "• Thiết kế lý thuyết Giao thức tầng ứng dụng tùy biến (Custom Wire Protocol): Cấu trúc gói tin nhị phân gồm Header 4-byte Big-Endian biểu thị độ dài và Payload là chuỗi JSON mã hóa UTF-8 để triệt tiêu hoàn toàn hiện tượng phân mảnh gói tin TCP (Packet Fragmentation).",
                        "• Nghiên cứu cơ chế Đa luồng (Multi-threading Concurrency) trong Python với threading.Thread và hàng đợi Queue để phục vụ hàng trăm kết nối đồng thời.",
                        "• Viết nội dung mục 3.3.1 Kỹ thuật truyền tin thời gian thực qua TCP Socket trong Chương III."
                    ]
                },
                {
                    "name": "2. Vy Thế Mạnh (Thành viên - Frontend UI/UX):",
                    "tasks": [
                        "• Nghiên cứu thư viện React 18: Kiến trúc Component hóa, cơ chế React Virtual DOM và Fiber Reconciler tối ưu tốc độ cập nhật tin nhắn không bị giật lag.",
                        "• Nghiên cứu TypeScript và Tailwind CSS: Kiểu tĩnh (Static Typing) giúp giảm thiểu lỗi runtime; Utility-first CSS giúp xây dựng giao diện Dark/Light mode chuẩn công thái học.",
                        "• Nghiên cứu nền tảng Electron Desktop: Mô hình Process Isolation giữa Main Process (Node.js) và Renderer Process (Chromium).",
                        "• Viết nội dung mục 3.2 Các công nghệ sử dụng (phần React, TypeScript, Tailwind, Electron) trong Chương III."
                    ]
                },
                {
                    "name": "3. Vũ Minh Dân (Thành viên - Phân tích nghiệp vụ BA):",
                    "tasks": [
                        "• Nghiên cứu hệ quản trị CSDL quan hệ nhúng SQLite: Ưu điểm không cần cấu hình máy chủ riêng (serverless), lưu trữ toàn bộ dữ liệu trong tệp đơn lẻ chat_database.db, tốc độ đọc ghi cực nhanh.",
                        "• Tìm hiểu cấu trúc bảng chỉ mục (B-Tree Indexing) trong SQLite giúp tăng tốc độ truy vấn lịch sử tin nhắn hàng nghìn dòng.",
                        "• Soạn thảo phần lý thuyết về Quản trị cơ sở dữ liệu SQLite trong mục 3.2 của Chương III."
                    ]
                },
                {
                    "name": "4. Phạm Đức Tâm (Thành viên - Backend & CSDL):",
                    "tasks": [
                        "• Nghiên cứu thuật toán bảo mật mật khẩu PBKDF2-HMAC-SHA256: Tìm hiểu cơ chế băm kết hợp chuỗi ngẫu nhiên Salt 16 bytes và 100.000 vòng lặp (iterations) nhằm chống tấn công Rainbow Table.",
                        "• Nghiên cứu phương thức mã hóa dữ liệu nhị phân Base64: Chuyển đổi tệp tin ảnh và tài liệu thành chuỗi ký tự ASCII an toàn để truyền tải qua gói tin Socket.",
                        "• Viết nội dung mục 3.3.2 Kỹ thuật mã hóa, bảo mật dữ liệu và truyền file trong Chương III."
                    ]
                },
                {
                    "name": "5. Hữu (Thành viên - QA & Biên tập tài liệu):",
                    "tasks": [
                        "• Nghiên cứu quy trình phát triển phần mềm theo mô hình Agile/Scrum: Vòng lặp phát triển ngắn, phản hồi liên tục và bàn giao sản phẩm tăng trưởng.",
                        "• Tìm hiểu các tiêu chuẩn đo lường chất lượng phần mềm ISO/IEC 25010 (tính chức năng, tính tin cậy, tính tiện dụng, tính hiệu quả).",
                        "• Soạn thảo mục 3.1 Kiến thức tổng quan về quy trình phần mềm và tổng hợp hoàn thiện toàn văn Chương III."
                    ]
                }
            ],
            "deliverable": "Hoàn thiện trọn vẹn văn bản Chương III; Báo cáo phân tích chuyên sâu về Giao thức Socket nhị phân, React/Electron và Thuật toán băm PBKDF2."
        },
        {
            "stage_title": "GIAI ĐOẠN 4: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG PHẦN MỀM (UML & CSDL)",
            "chapter_ref": "TƯƠNG ỨNG: CHƯƠNG IV. PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG (Tiến độ: Tuần 4 - 5)",
            "goal": "Xây dựng hệ thống mô hình hóa phần mềm chuẩn UML (Biểu đồ phân rã chức năng BFD, Biểu đồ Use Case tổng quát/chi tiết, Biểu đồ lớp Class Diagram, Biểu đồ tuần tự Sequence Diagram), thiết kế CSDL (ERD, Data Dictionary) và vẽ Wireframe/Mockup giao diện.",
            "members": [
                {
                    "name": "1. Vũ Duy Thái Sơn (Nhóm trưởng):",
                    "tasks": [
                        "• Thiết kế Kiến trúc tổng thể hệ thống (System Architecture Diagram): Mô hình phân tầng gồm Tầng giao diện Electron React -> Tầng cầu nối TCP IPC (python_bridge) -> Tầng máy chủ Python Socket -> Tầng CSDL SQLite.",
                        "• Xây dựng các Biểu đồ tuần tự (Sequence Diagram): Luồng xác thực đăng nhập bảo mật, Luồng gửi và phát tán tin nhắn thời gian thực qua Worker Thread, Luồng thiết lập tín hiệu cuộc gọi (Signaling Handshake).",
                        "• Phê duyệt tính tương thích giữa biểu đồ lớp và cấu trúc gói tin mạng; viết mục 4.2.1 Biểu đồ tuần tự trong Chương IV."
                    ]
                },
                {
                    "name": "2. Vy Thế Mạnh (Thành viên - Frontend UI/UX):",
                    "tasks": [
                        "• Thiết kế bản vẽ Wireframe và Mockup đồ họa toàn bộ các màn hình trên Figma: Màn hình đăng nhập/đăng ký, màn hình chat chính với danh sách hội thoại, bong bóng chat, bảng thông tin hội thoại, màn hình khóa Ctrl+L.",
                        "• Thiết kế bản vẽ giao diện Cuộc gọi Thoại (Voice Call) với sóng âm thanh Equalizer và giao diện Cuộc gọi Video (Video Call) với khung camera PIP.",
                        "• Xây dựng sơ đồ luồng chuyển trang của người dùng (User Flow Diagram); đóng góp mục thiết kế giao diện trong Chương IV."
                    ]
                },
                {
                    "name": "3. Vũ Minh Dân (Thành viên - Phân tích nghiệp vụ BA):",
                    "tasks": [
                        "• Xây dựng Biểu đồ phân rã chức năng (BFD): Chia hệ thống thành 4 phân hệ chính (Quản lý tài khoản, Quản lý hội thoại & Danh bạ, Truyền tin thời gian thực, Tích hợp Desktop).",
                        "• Vẽ Biểu đồ Use Case tổng quát và các biểu đồ Use Case chi tiết từng phân hệ trên phần mềm Draw.io / StarUML.",
                        "• Viết tập tài liệu đặc tả 22 Use Case chi tiết: Tác nhân, tiền điều kiện, luồng sự kiện chính, luồng sự kiện thay thế và hậu điều kiện.",
                        "• Xây dựng Biểu đồ lớp (Class Diagram): Mô tả các lớp thực thể (User, Conversation, Message, Reaction, Friend, FileItem) và mối quan hệ giữa chúng.",
                        "• Chịu trách nhiệm chính soạn thảo toàn bộ mục 4.1 Phân tích hệ thống trong Chương IV."
                    ]
                },
                {
                    "name": "4. Phạm Đức Tâm (Thành viên - Backend & CSDL):",
                    "tasks": [
                        "• Thiết kế Mô hình thực thể liên kết (ERD) cho CSDL chat_database.db gồm 6 bảng chuẩn hóa 3NF: users, conversations, conversation_members, messages, message_reactions, friendships.",
                        "• Thiết lập các khóa chính (PK), khóa ngoại (FK) với ràng buộc toàn vẹn ON DELETE CASCADE.",
                        "• Xây dựng Từ điển dữ liệu chi tiết (Data Dictionary): Định rõ tên cột, kiểu dữ liệu, kích thước, ràng buộc Null/Unique và mô tả ý nghĩa.",
                        "• Chịu trách nhiệm chính soạn thảo mục 4.2.2 Thiết kế cơ sở dữ liệu trong Chương IV."
                    ]
                },
                {
                    "name": "5. Hữu (Thành viên - QA & Biên tập tài liệu):",
                    "tasks": [
                        "• Rà soát và kiểm tra chéo tính nhất quán giữa Biểu đồ Use Case, Biểu đồ lớp và CSDL (đảm bảo mọi Use Case đều có thực thể và thuộc tính CSDL tương ứng).",
                        "• Chuẩn hóa hình ảnh biểu đồ UML đạt độ phân giải cao, căn lề và đánh số bảng/hình ảnh đúng quy chuẩn.",
                        "• Tổng hợp, hiệu đính toàn văn Chương IV (chương dài nhất và quan trọng nhất của đồ án)."
                    ]
                }
            ],
            "deliverable": "Hoàn thiện trọn vẹn văn bản Chương IV; Bộ biểu đồ UML hoàn chỉnh (BFD, Use Case tổng quát, Use Case chi tiết, Class Diagram, Sequence Diagram); Bản thiết kế CSDL (ERD, Data Dictionary); Bản vẽ Wireframe Figma."
        },
        {
            "stage_title": "GIAI ĐOẠN 5: CÀI ĐẶT, TRIỂN KHAI, KIỂM THỬ HỆ THỐNG VÀ BẢO VỆ ĐỒ ÁN",
            "chapter_ref": "TƯƠNG ỨNG: CHƯƠNG V. CÀI ĐẶT, TRIỂN KHAI VÀ KIỂM THỬ HỆ THỐNG (Tiến độ: Tuần 6 - 7)",
            "goal": "Hiện thực hóa mã nguồn Backend và Frontend; tích hợp máy chủ WAN Internet; xây dựng cơ chế tự động hóa All-in-One và cập nhật Git; thực thi 22 ca Test Cases đạt Pass 100%; viết phần Kết luận và bảo vệ đồ án.",
            "members": [
                {
                    "name": "1. Vũ Duy Thái Sơn (Nhóm trưởng):",
                    "tasks": [
                        "• Lập trình Máy chủ Socket đa luồng trong src/server/server.py: Tiếp nhận kết nối port 8888, phân bổ Worker Thread, định tuyến gói tin JSON và phát tán sự kiện (broadcast).",
                        "• Lập trình mô-đun Cầu nối TCP IPC trong frontend/electron/python_bridge.ts: Kết nối socket nhị phân giữa Electron Node.js và Python Server.",
                        "• Hiện thực hóa Máy chủ WAN Internet trong run_server_wan.py: Tự động khởi tạo Bore TCP Tunnel (bore.pub:38888) giúp người dùng nhắn tin xuyên mọi mạng LAN/Wifi/4G.",
                        "• Xây dựng tính năng All-in-One: Lập trình tạo shortcut Desktop kèm logo Shin-chan bằng IShellLinkW native (hỗ trợ đường dẫn tiếng Việt có dấu), tự khởi động Server cùng Windows.",
                        "• Lập trình cơ chế lắng nghe Git mỗi 2 giây (frontend/electron/updater.ts) thông báo cập nhật cho người dùng.",
                        "• Viết kịch bản 1-Click duy nhất CHAY_UNG_DUNG.bat; viết mục 5.1 Cài đặt Backend và toàn bộ phần KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN của đề tài."
                    ]
                },
                {
                    "name": "2. Vy Thế Mạnh (Thành viên - Frontend UI/UX):",
                    "tasks": [
                        "• Khởi tạo và lập trình toàn bộ dự án React 18 + Vite trong thư mục frontend/.",
                        "• Hiện thực hóa TitleBar.tsx: Thanh tiêu đề frameless phong cách Telegram, nút Pin Always-on-Top, nút Khóa màn hình Ctrl+L, logo Shin-chan và huy hiệu trạng thái mạng WAN động.",
                        "• Lập trình CallModal.tsx: Giao diện Video Call HD kết nối webcam thật qua navigator.mediaDevices.getUserMedia, khung PIP nổi, nút Bật/Tắt Cam, Mic và nút Chia Sẻ Màn Hình; giao diện Voice Call với avatar phát xung kích và equalizer chuyển động.",
                        "• Lập trình ChatBubble.tsx: Hiển thị thumbnail ảnh xem trước từ cache Base64, nút tải về và mở Lightbox xem ảnh toàn màn hình.",
                        "• Viết mục 5.1 Cài đặt Frontend và chụp ảnh minh chứng cho mục 5.2 Kết quả triển khai trong Chương V."
                    ]
                },
                {
                    "name": "3. Vũ Minh Dân (Thành viên - Phân tích nghiệp vụ BA):",
                    "tasks": [
                        "• Lập trình Sidebar.tsx: Thanh lọc hội thoại theo Tab ('Tất cả', 'Cá nhân', 'Nhóm'), ô tìm kiếm tức thì theo @username và #ID người dùng.",
                        "• Lập trình ChatComposer.tsx & EmojiPicker.tsx: Khung soạn thảo tin nhắn phím tắt thông minh (Enter gửi, Shift+Enter xuống dòng), bộ chọn biểu tượng cảm xúc đa dạng.",
                        "• Lập trình ChatInfoModal.tsx: Hiển thị thông tin hội thoại, danh sách thành viên nhóm, tab Ảnh thumbnail sắc nét, tab Tệp tin và tab Tin nhắn đã ghim.",
                        "• Phối hợp kiểm thử chức năng phân hệ tin nhắn và viết mục 5.2.1 đến 5.2.5 trong Chương V."
                    ]
                },
                {
                    "name": "4. Phạm Đức Tâm (Thành viên - Backend & CSDL):",
                    "tasks": [
                        "• Lập trình lớp quản trị CSDL DatabaseManager trong src/server/database.py: Khởi tạo bảng, quản lý transaction an toàn, bảo mật mật khẩu PBKDF2 với Salt 16 bytes ngẫu nhiên.",
                        "• Lập trình API upload/download tệp tin đa phương tiện trong src/server/server.py và frontend/src/services/api.ts: Đọc ghi file nhị phân Base64 an toàn vào thư mục uploads/.",
                        "• Xây dựng hàm getImageUrl() có bộ đệm cache Base64 giúp tải trước ảnh siêu tốc < 5ms.",
                        "• Thực hiện kiểm thử chịu tải CSDL với 10.000 bản ghi tin nhắn và 100 tài khoản người dùng; viết mục 5.1.2 Cài đặt CSDL trong Chương V."
                    ]
                },
                {
                    "name": "5. Hữu (Thành viên - QA & Biên tập tài liệu):",
                    "tasks": [
                        "• Xây dựng Kế hoạch kiểm thử hoàn chỉnh (Test Plan) tại mục 5.3.1 của Chương V.",
                        "• Thiết kế bộ 22 Kịch bản kiểm thử (Test Cases) chi tiết tương ứng trọn vẹn 22 chức năng của ứng dụng (TC01 đến TC22).",
                        "• Thực thi toàn bộ các ca kiểm thử trên môi trường Windows 10, Windows 11 và mạng WAN; lập Bảng ma trận kết quả kiểm thử (Test Matrix) đạt tỷ lệ Pass 22/22 (100%).",
                        "• Chụp ảnh giao diện minh chứng kết quả kiểm thử; hoàn thiện mục 5.3 Thực hiện kiểm thử; chuẩn hóa toàn bộ Danh mục tài liệu tham khảo.",
                        "• Thiết kế bộ Slide thuyết trình PowerPoint chuyên nghiệp phục vụ Hội đồng chấm bảo vệ đồ án."
                    ]
                }
            ],
            "deliverable": "Mã nguồn phần mềm hoàn chỉnh (chạy mượt mà qua CHAY_UNG_DUNG.bat); Báo cáo toàn văn Chương V và Kết luận; Bộ 22 Test Cases (Pass 100%); Bộ slide thuyết trình đồ án."
        }
    ]

    for stage_idx, s in enumerate(stages_data):
        # Tiêu đề Giai đoạn & Chương
        add_p(doc, f"MỤC {stage_idx + 1}. {s['stage_title']}", font_size=13, bold=True, space_before=14, space_after=2, color=RGBColor(0, 51, 102))
        add_p(doc, f"★ {s['chapter_ref']}", font_size=12, bold=True, italic=True, space_after=4, color=RGBColor(180, 0, 0))
        add_p(doc, f"Mục tiêu giai đoạn: {s['goal']}", font_size=12, italic=True, space_after=8)
        
        # Bảng chi tiết 5 thành viên đặt ngay sát cạnh nhau
        t_stage = doc.add_table(rows=1, cols=3)
        t_stage.alignment = WD_TABLE_ALIGNMENT.CENTER
        shdr = t_stage.rows[0].cells
        shdr[0].text = "STT"
        shdr[1].text = "Thành viên thực hiện"
        shdr[2].text = "Công việc chi tiết & Cách thức thực hiện trong Giai đoạn"
        
        for idx_c, c_elm in enumerate(shdr):
            set_cell_background(c_elm, "003366")
            set_cell_margins(c_elm, 100, 100, 80, 80)
            p = c_elm.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                format_run(r, font_size=11.5, bold=True, color=RGBColor(255, 255, 255))
        
        for m_idx, m_info in enumerate(s["members"]):
            srow = t_stage.add_row().cells
            bg = "F7F9FC" if m_idx % 2 == 1 else "FFFFFF"
            
            # Cột 1: STT
            srow[0].text = str(m_idx + 1)
            set_cell_background(srow[0], bg)
            set_cell_margins(srow[0], 80, 80, 60, 60)
            srow[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            format_run(srow[0].paragraphs[0].runs[0], font_size=11, bold=True)
            
            # Cột 2: Thành viên
            srow[1].text = m_info["name"]
            set_cell_background(srow[1], bg)
            set_cell_margins(srow[1], 80, 80, 80, 80)
            srow[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
            format_run(srow[1].paragraphs[0].runs[0], font_size=11, bold=True, color=RGBColor(0, 51, 102))
            
            # Cột 3: Công việc chi tiết
            set_cell_background(srow[2], bg)
            set_cell_margins(srow[2], 80, 80, 80, 80)
            p3 = srow[2].paragraphs[0]
            p3.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p3.text = ""
            for t_line in m_info["tasks"]:
                p_task = srow[2].add_paragraph()
                p_task.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_task.paragraph_format.space_before = Pt(0)
                p_task.paragraph_format.space_after = Pt(2)
                p_task.paragraph_format.line_spacing = 1.15
                r = p_task.add_run(t_line)
                format_run(r, font_size=11)
        
        add_p(doc, f"• Sản phẩm bàn giao cụ thể của {s['chapter_ref'][:18]}: {s['deliverable']}", font_size=11.5, bold=True, space_before=6, space_after=14, color=RGBColor(0, 100, 0))
        add_p(doc, "------------------------------------------------------------------------------------------------------------------------", font_size=9, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10, color=RGBColor(210, 210, 210))

    # 4. MA TRẬN PHÂN CÔNG THEO 22 CHỨC NĂNG HỆ THỐNG (RACI MATRIX)
    add_p(doc, "PHẦN II. MA TRẬN PHÂN CÔNG TRÁCH NHIỆM 22 TÍNH NĂNG THEO CHUẨN RACI", font_size=14, bold=True, space_before=14, space_after=6, color=RGBColor(0, 51, 102))
    add_p(doc, "Quy ước vai trò: [R - Responsible: Người trực tiếp lập trình/thực thi] | [A - Accountable: Nhóm trưởng chịu trách nhiệm nghiệm thu] | [C - Consulted: Người tư vấn nghiệp vụ/giao diện] | [I - Informed: Người kiểm thử/theo dõi chất lượng].", font_size=11, italic=True, space_after=8)

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
        ("8", "Gửi/Xem ảnh thumbnail & Lightbox phóng to", "A (Bridge IPC)", "R (Modal Preview)", "C (Giao diện)", "R (Lưu uploads/) / I"),
        ("9", "Truyền tệp tin (.pdf, .docx, .zip)", "A (Length Packet)", "R (File Card)", "C (Giới hạn dung lượng)", "R (SaveFileDialog) / I"),
        ("10", "Cloud cá nhân (Saved Messages)", "A (Private Protocol)", "R (Saved UI)", "C (Đặc tả)", "R (Type='saved') / I"),
        ("11", "Tìm kiếm toàn cục (@user / #ID)", "A (Search API)", "R (Debounce Search)", "R (Đặc tả BA)", "R (Query LIKE) / I"),
        ("12", "Quản lý Danh bạ & Bạn bè", "A (Friend Socket)", "R (ContactsModal)", "R (Luồng kết bạn)", "R (Bảng friendships) / I"),
        ("13", "Tạo nhóm trò chuyện phân quyền", "A (Group Handler)", "R (CreateGroupModal)", "R (Use Case nhóm)", "R (Group Admin) / I"),
        ("14", "Cuộc gọi Thoại & Video (Camera PIP, Screen Share)", "A (Call Signaling)", "R (Webcam PIP)", "C (Kịch bản gọi)", "R (Socket Call) / I"),
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
