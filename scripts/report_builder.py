# -*- coding: utf-8 -*-
"""
Script tu dong tao lap toan bo Bao cao Do an chuyen nganh tu Chuong 2 den Chuong 5
Chuan Nhom 21 - Dai hoc Cong nghe Dong A
Khoa Cong nghe Thong tin
GVHD: Ngo Thuy Giang
"""

import os
import sys
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

sys.stdout.reconfigure(encoding='utf-8')

def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="D1D5DB", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def setup_document():
    doc = docx.Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.79)     # ~2.0 cm
    sec.bottom_margin = Inches(0.79)  # ~2.0 cm
    sec.left_margin = Inches(1.18)    # ~3.0 cm
    sec.right_margin = Inches(0.79)   # ~2.0 cm

    # Style mac dinh
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(13)
    normal_style.font.color.rgb = RGBColor(0x1F, 0x29, 0x37) # Slate-800
    normal_style.paragraph_format.line_spacing = 1.3
    normal_style.paragraph_format.space_after = Pt(4)
    return doc

def add_header_box(doc, chapter_num, chapter_title):
    p0 = doc.add_paragraph()
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ ĐÔNG Á\nKHOA CÔNG NGHỆ THÔNG TIN\n--------------------***--------------------")
    r0.font.name = 'Times New Roman'
    r0.font.size = Pt(12)
    r0.font.bold = True
    r0.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run("BÁO CÁO TIẾN ĐỘ ĐỒ ÁN CHUYÊN NGÀNH CÔNG NGHỆ PHẦN MỀM\n")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(14)
    r1.font.bold = True
    r1.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A) # Deep blue

    r1_sub = p1.add_run("ĐỀ TÀI: XÂY DỰNG ỨNG DỤNG NHẮN TIN VÀ TRUYỀN THÔNG TIN\n")
    r1_sub.font.name = 'Times New Roman'
    r1_sub.font.size = Pt(15)
    r1_sub.font.bold = True
    r1_sub.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

    r1_ch = p1.add_run(f"CHƯƠNG {chapter_num}: {chapter_title}\n")
    r1_ch.font.name = 'Times New Roman'
    r1_ch.font.size = Pt(14)
    r1_ch.font.bold = True
    r1_ch.font.color.rgb = RGBColor(0x25, 0x63, 0xEB) # Blue 600

    r1_loc = p1.add_run("Hà Nội, Năm 2026")
    r1_loc.font.name = 'Times New Roman'
    r1_loc.font.size = Pt(11)
    r1_loc.font.italic = True

    # Bang thong tin nhom
    t = doc.add_table(rows=6, cols=2)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="CBD5E1")

    info_data = [
        ("Học phần:", "Đồ án chuyên ngành Công nghệ phần mềm"),
        ("Giảng viên hướng dẫn:", "ThS. Ngô Thùy Giang"),
        ("Lớp tín chỉ:", "Đồ án chuyên ngành CNPM-1-1-26(N05) - DCCNTT.14.5"),
        ("Nhóm thực hiện:", "Nhóm 21"),
        ("Sinh viên thực hiện:", "1. Vũ Duy Thái Sơn (Nhóm trưởng - MSV: 20231735)\n2. Vy Thế Mạnh (MSV: 20231865)\n3. Vũ Minh Dân (MSV: 20231833)\n4. Phạm Đức Tâm (MSV: 20231715)\n5. Long Đức Hữu (MSV: 20231824)"),
        ("Thời gian thực hiện:", "Học kỳ 1 - Năm học 2026"),
    ]

    col_widths = [Inches(1.8), Inches(4.7)]
    for r_idx, (k, v) in enumerate(info_data):
        row = t.rows[r_idx]
        cell_k, cell_v = row.cells[0], row.cells[1]
        cell_k.width, cell_v.width = col_widths[0], col_widths[1]
        set_cell_margins(cell_k, 60, 60, 100, 100)
        set_cell_margins(cell_v, 60, 60, 100, 100)
        set_cell_background(cell_k, "F8FAFC")

        pk = cell_k.paragraphs[0]
        pk.paragraph_format.space_after = Pt(2)
        rk = pk.add_run(k)
        rk.font.name = 'Times New Roman'
        rk.font.size = Pt(11)
        rk.font.bold = True

        pv = cell_v.paragraphs[0]
        pv.paragraph_format.space_after = Pt(2)
        rv = pv.add_run(v)
        rv.font.name = 'Times New Roman'
        rv.font.size = Pt(11)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_after = Pt(8)

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.italic = True
    r.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
    return p

def add_p(doc, text, bold_prefix="", italic=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(4)
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = 'Times New Roman'
        rb.font.size = Pt(12)
        rb.font.bold = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    if italic:
        r.font.italic = True
    return p

def add_bullet(doc, text, bold_prefix=""):
    p = doc.add_paragraph(style='List Bullet')
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.25
    if bold_prefix:
        rb = p.add_run(bold_prefix)
        rb.font.name = 'Times New Roman'
        rb.font.size = Pt(12)
        rb.font.bold = True
    r = p.add_run(text)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    return p

def add_table_data(doc, headers, data, col_widths=None):
    t = doc.add_table(rows=len(data) + 1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t, color="94A3B8")

    # Header
    hdr_row = t.rows[0]
    for c_idx, h in enumerate(headers):
        cell = hdr_row.cells[c_idx]
        set_cell_background(cell, "E2E8F0")
        set_cell_margins(cell, 80, 80, 100, 100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(11)
        r.font.bold = True

    # Rows
    for r_idx, row_data in enumerate(data):
        row = t.rows[r_idx + 1]
        bg = "FFFFFF" if r_idx % 2 == 0 else "F8FAFC"
        for c_idx, val in enumerate(row_data):
            cell = row.cells[c_idx]
            set_cell_background(cell, bg)
            set_cell_margins(cell, 60, 60, 100, 100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (c_idx == 0 or len(val) < 15) else WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.2
            r = p.add_run(str(val))
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10.5)

    if col_widths:
        for row in t.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

print("Core helper functions initialized.")
