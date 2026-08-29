"""
PDF Forensic Audit Report Generator for SIH PS26188
Generates official, timestamped forensic audit certificates.
Includes a standalone zero-dependency PDF-1.4 generator fallback.
"""

import io
import time
import uuid
import re
from typing import Dict, Any, List

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


def _escape_pdf_text(text: str) -> str:
    """Escapes special PDF characters and strips non-latin1 unicode."""
    t = str(text)
    # Replace common unicode chars with ASCII equivalents
    t = t.replace('\u2022', '-').replace('\u2019', "'").replace('\u2018', "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"').replace('\u2013', '-').replace('\u2014', '--')
    t = t.replace('\u00a0', ' ').replace('\u2026', '...')
    # Strip anything else that can't be encoded as latin-1
    t = t.encode('latin-1', errors='replace').decode('latin-1')
    return t.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')


def _build_raw_pdf_certificate(data: Dict[str, Any]) -> bytes:
    """
    Generates a valid PDF-1.4 binary document using standard PDF objects.
    Guarantees 100% working PDF download with ZERO external dependencies.
    """
    report_id = f"MHA-AUDIT-{str(uuid.uuid4())[:8].upper()}"
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    verdict = data.get("verdict", "SUSPICIOUS")
    score = data.get("authenticity_score", 0)
    doc_type = data.get("document_type", "UNKNOWN")

    # Construct PDF Stream commands
    stream = []
    
    # 1. Background header bar (Dark Navy / Black)
    stream.append("0.05 0.08 0.14 rg")  # RGB Fill
    stream.append("36 710 540 70 re f")  # Rectangle
    
    # Orange Accent Line
    stream.append("0.92 0.35 0.05 rg")
    stream.append("36 706 540 4 re f")

    # Header Text
    stream.append("BT")
    stream.append("/F2 9 Tf 0.92 0.35 0.05 rg") # Orange Subtitle
    stream.append("200 760 Td (MINISTRY OF HOME AFFAIRS  -  GOVERNMENT OF INDIA) Tj")
    stream.append("ET")

    stream.append("BT")
    stream.append("/F2 14 Tf 1.0 1.0 1.0 rg") # White Title
    stream.append("120 740 Td (AI Fake Identity & Document Screening System) Tj")
    stream.append("ET")

    stream.append("BT")
    stream.append("/F1 8 Tf 0.7 0.75 0.8 rg") # Metadata
    stream.append(f"140 722 Td (Certificate Ref: {report_id}  |  Generated: {timestamp_str}) Tj")
    stream.append("ET")

    # 2. Executive Verdict Card
    if verdict == "AUTHENTIC":
        card_bg = "0.85 0.98 0.90 rg"
        card_stroke = "0.08 0.55 0.25 RG"
        badge_text = "VERIFIED AUTHENTIC"
        badge_color = "0.08 0.45 0.20 rg"
    elif verdict == "TAMPERED":
        card_bg = "0.99 0.88 0.88 rg"
        card_stroke = "0.75 0.15 0.15 RG"
        badge_text = "TAMPERING / FORGERY DETECTED"
        badge_color = "0.70 0.10 0.10 rg"
    else:
        card_bg = "0.99 0.95 0.82 rg"
        card_stroke = "0.85 0.55 0.05 RG"
        badge_text = "SUSPICIOUS / UNVERIFIED IDENTITY"
        badge_color = "0.75 0.40 0.00 rg"

    stream.append(card_bg)
    stream.append("36 625 540 65 re f")
    stream.append(card_stroke)
    stream.append("1 w 36 625 540 65 re S")

    # Score Box
    stream.append("0.05 0.08 0.14 rg")
    stream.append("50 635 55 45 re f")
    stream.append("BT /F2 20 Tf 1 1 1 rg 60 652 Td (" + str(score) + ") Tj ET")
    stream.append("BT /F1 7 Tf 0.9 0.4 0.1 rg 58 640 Td (SCORE) Tj ET")

    # Verdict Text
    stream.append(f"BT /F2 12 Tf {badge_color} 120 668 Td ({_escape_pdf_text(badge_text)}) Tj ET")
    stream.append(f"BT /F1 9 Tf 0.1 0.15 0.2 rg 120 652 Td (Document Classification: {_escape_pdf_text(doc_type)}  |  Confidence: {score}%) Tj ET")
    stream.append(f"BT /F1 8 Tf 0.3 0.35 0.4 rg 120 638 Td (Screening Engine: v4.2-Forensic  |  Status: Analysis Concluded) Tj ET")

    # 3. Section 1: Extracted Demographic Fields Table
    stream.append("BT /F2 10 Tf 0.05 0.08 0.14 rg 36 600 Td (1. Extracted Identity Fields (OCR & Layout Analytics)) Tj ET")
    stream.append("0.05 0.08 0.14 rg 36 578 540 16 re f")
    stream.append("BT /F2 8 Tf 1 1 1 rg 45 583 Td (FIELD NAME) Tj 180 583 Td (EXTRACTED VALUE) Tj 380 583 Td (STATUS) Tj 480 583 Td (CONFIDENCE) Tj ET")

    curr_y = 560
    fields = data.get("extracted_fields", [])
    for idx, f in enumerate(fields[:6]):
        bg = "0.97 0.98 0.99 rg" if idx % 2 == 0 else "1.0 1.0 1.0 rg"
        stream.append(f"{bg} 36 {curr_y - 4} 540 18 re f")
        stream.append(f"0.85 0.88 0.92 RG 0.5 w 36 {curr_y - 4} 540 18 re S")

        f_name = _escape_pdf_text(str(f.get("field_name", ""))[:22])
        f_val = _escape_pdf_text(str(f.get("value", "N/A"))[:32])
        f_status = _escape_pdf_text(str(f.get("status", "")).upper())
        f_conf = f"{f.get('confidence', 0)}%"

        stat_col = "0.08 0.6 0.2 rg" if f_status == "VERIFIED" else ("0.8 0.1 0.1 rg" if f_status == "FLAGGED" else "0.8 0.45 0 rg")

        stream.append(f"BT /F1 8.5 Tf 0.2 0.25 0.3 rg 45 {curr_y} Td ({f_name}) Tj ET")
        stream.append(f"BT /F2 8.5 Tf 0.05 0.08 0.14 rg 180 {curr_y} Td ({f_val}) Tj ET")
        stream.append(f"BT /F2 8.5 Tf {stat_col} 380 {curr_y} Td ({f_status}) Tj ET")
        stream.append(f"BT /F1 8.5 Tf 0.3 0.35 0.4 rg 480 {curr_y} Td ({f_conf}) Tj ET")
        curr_y -= 18

    # 4. Section 2: Forensic Matrix
    curr_y -= 14
    stream.append(f"BT /F2 10 Tf 0.05 0.08 0.14 rg 36 {curr_y} Td (2. Multi-Pillar Forensic Verification Matrix) Tj ET")
    curr_y -= 18
    stream.append(f"0.05 0.08 0.14 rg 36 {curr_y} 540 16 re f")
    stream.append(f"BT /F2 8 Tf 1 1 1 rg 45 {curr_y + 4} Td (PILLAR / VALIDATION CHECK) Tj 240 {curr_y + 4} Td (RESULT) Tj 310 {curr_y + 4} Td (SCORE) Tj 380 {curr_y + 4} Td (METRIC DETAILS) Tj ET")
    curr_y -= 16

    checks = data.get("validation_checks", [])
    for idx, c in enumerate(checks[:6]):
        bg = "0.97 0.98 0.99 rg" if idx % 2 == 0 else "1.0 1.0 1.0 rg"
        stream.append(f"{bg} 36 {curr_y - 4} 540 18 re f")
        stream.append(f"0.85 0.88 0.92 RG 0.5 w 36 {curr_y - 4} 540 18 re S")

        c_name = _escape_pdf_text(str(c.get("name", ""))[:32])
        c_status = _escape_pdf_text(str(c.get("status", "fail")).upper())
        c_score = f"{c.get('score', 0)}/100"
        c_details = _escape_pdf_text(str(c.get("details", ""))[:38])

        stat_col = "0.08 0.6 0.2 rg" if c_status == "PASS" else ("0.8 0.1 0.1 rg" if c_status == "FAIL" else "0.8 0.45 0 rg")

        stream.append(f"BT /F1 8 Tf 0.15 0.2 0.25 rg 45 {curr_y} Td ({c_name}) Tj ET")
        stream.append(f"BT /F2 8 Tf {stat_col} 240 {curr_y} Td ({c_status}) Tj ET")
        stream.append(f"BT /F1 8 Tf 0.2 0.25 0.3 rg 310 {curr_y} Td ({c_score}) Tj ET")
        stream.append(f"BT /F1 7.5 Tf 0.35 0.4 0.45 rg 380 {curr_y} Td ({c_details}) Tj ET")
        curr_y -= 18

    # 5. Section 3: Telemetry Log
    curr_y -= 14
    stream.append(f"BT /F2 10 Tf 0.05 0.08 0.14 rg 36 {curr_y} Td (3. Forensic Audit Telemetry Trace) Tj ET")
    curr_y -= 14
    stream.append(f"0.94 0.96 0.98 rg 36 {curr_y - 42} 540 46 re f")
    stream.append(f"0.8 0.84 0.9 RG 0.5 w 36 {curr_y - 42} 540 46 re S")

    traces = data.get("forensic_trace", [])
    trace_y = curr_y - 10
    for t in traces[:3]:
        t_clean = _escape_pdf_text(f"> {t[:80]}")
        stream.append(f"BT /F1 7.5 Tf 0.2 0.25 0.3 rg 44 {trace_y} Td ({t_clean}) Tj ET")
        trace_y -= 12

    # 6. Official Footer
    stream.append("0.85 0.88 0.92 RG 1 w 36 50 540 0 re S")
    stream.append("BT /F1 7.5 Tf 0.4 0.45 0.5 rg 110 38 Td (CONFIDENTIAL - MINISTRY OF HOME AFFAIRS (MHA) AI SCREENING PLATFORM PS26188) Tj ET")
    stream.append("BT /F1 7 Tf 0.55 0.6 0.65 rg 180 26 Td (Automated certificate for law enforcement and border screening verification.) Tj ET")

    stream_content = "\n".join(stream)
    # Safety: ensure no non-latin1 chars sneak through
    stream_bytes = stream_content.encode('latin-1', errors='replace')
    stream_len = len(stream_bytes)

    # Assemble raw PDF objects
    objects = []
    
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    
    # 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    
    # 3: Page (Letter 612 x 792)
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 6 0 R >> >> >>\nendobj")
    
    # 4: Stream
    objects.append(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n{stream_content}\nendstream\nendobj")
    
    # 5: Font F1 (Helvetica)
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")
    
    # 6: Font F2 (Helvetica-Bold)
    objects.append("6 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>\nendobj")

    # Compute xref table
    pdf_output = ["%PDF-1.4\n"]
    offsets = []
    
    current_offset = len(pdf_output[0].encode('latin-1', errors='replace'))
    for obj in objects:
        offsets.append(current_offset)
        pdf_output.append(obj + "\n")
        current_offset += len(obj.encode('latin-1', errors='replace')) + 1

    xref_offset = current_offset
    pdf_output.append("xref\n")
    pdf_output.append(f"0 {len(objects) + 1}\n")
    pdf_output.append("0000000000 65535 f \n")
    for off in offsets:
        pdf_output.append(f"{off:010d} 00000 n \n")

    pdf_output.append("trailer\n")
    pdf_output.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n")
    pdf_output.append("startxref\n")
    pdf_output.append(f"{xref_offset}\n")
    pdf_output.append("%%EOF\n")

    return "".join(pdf_output).encode('latin-1', errors='replace')


def generate_pdf_report(screening_data: Dict[str, Any]) -> bytes:
    """
    Builds a professional PDF forensic audit certificate using ReportLab if available,
    or the built-in standalone PDF generator.
    """
    if not HAS_REPORTLAB:
        return _build_raw_pdf_certificate(screening_data)

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'DocTitle', parent=styles['Heading1'], fontSize=15, leading=18, textColor=colors.HexColor('#0f172a'), alignment=1, fontName='Helvetica-Bold'
        )
        subtitle_style = ParagraphStyle(
            'DocSubtitle', parent=styles['Normal'], fontSize=8.5, leading=11, textColor=colors.HexColor('#ea580c'), alignment=1, fontName='Helvetica-Bold'
        )
        meta_style = ParagraphStyle(
            'DocMeta', parent=styles['Normal'], fontSize=7.5, leading=9.5, textColor=colors.HexColor('#64748b'), alignment=1
        )
        section_heading = ParagraphStyle(
            'SectionHeading', parent=styles['Heading2'], fontSize=10.5, leading=13, textColor=colors.HexColor('#0f172a'), fontName='Helvetica-Bold', spaceBefore=8, spaceAfter=3
        )
        body_style = ParagraphStyle(
            'Body', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.HexColor('#1e293b')
        )
        table_header_style = ParagraphStyle(
            'TableHeader', parent=styles['Normal'], fontSize=8, leading=9.5, textColor=colors.white, fontName='Helvetica-Bold'
        )
        code_style = ParagraphStyle(
            'CodeStyle', parent=styles['Normal'], fontSize=7, leading=9, textColor=colors.HexColor('#334155'), fontName='Courier'
        )

        story = []
        story.append(Paragraph("MINISTRY OF HOME AFFAIRS (MHA)", subtitle_style))
        story.append(Paragraph("AI Fake Identity & Document Screening System", title_style))
        story.append(Paragraph("SMART INDIA HACKATHON (PS26188) - FORENSIC AUDIT CERTIFICATE", subtitle_style))
        story.append(Spacer(1, 3))
        
        report_id = f"MHA-AUDIT-{str(uuid.uuid4())[:8].upper()}"
        timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        story.append(Paragraph(f"Ref: <b>{report_id}</b> | Generated: <b>{timestamp_str}</b> | Engine: <b>v4.2-Forensic</b>", meta_style))
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#ea580c'), spaceBefore=0, spaceAfter=6))

        # Verdict Box
        verdict = screening_data.get("verdict", "SUSPICIOUS")
        score = screening_data.get("authenticity_score", 0)
        doc_type = screening_data.get("document_type", "UNKNOWN")
        verdict_bg = colors.HexColor('#dcfce7') if verdict == 'AUTHENTIC' else (colors.HexColor('#fee2e2') if verdict == 'TAMPERED' else colors.HexColor('#fef3c7'))
        verdict_col = colors.HexColor('#166534') if verdict == 'AUTHENTIC' else (colors.HexColor('#991b1b') if verdict == 'TAMPERED' else colors.HexColor('#92400e'))

        verdict_html = f"<b>EXECUTIVE VERDICT:</b> <font color='{verdict_col.hexval()}'><b>{verdict}</b></font> &nbsp;|&nbsp; <b>Score:</b> {score}/100 &nbsp;|&nbsp; <b>Doc Type:</b> {doc_type}"
        v_table = Table([[Paragraph(verdict_html, body_style)]], colWidths=[540])
        v_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), verdict_bg),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        story.append(v_table)
        story.append(Spacer(1, 8))

        # Fields Table
        story.append(Paragraph("1. Extracted Demographic Fields (OCR)", section_heading))
        field_rows = [[Paragraph("Field Name", table_header_style), Paragraph("Extracted Value", table_header_style), Paragraph("Status", table_header_style), Paragraph("Confidence", table_header_style)]]
        for f in screening_data.get("extracted_fields", []):
            st = f.get("status", "flagged").upper()
            st_col = "#16a34a" if st == "VERIFIED" else ("#dc2626" if st == "FLAGGED" else "#d97706")
            field_rows.append([Paragraph(f.get("field_name", ""), body_style), Paragraph(f"<b>{f.get('value', 'N/A')}</b>", body_style), Paragraph(f'<font color="{st_col}"><b>{st}</b></font>', body_style), Paragraph(f"{f.get('confidence', 0)}%", body_style)])
        f_table = Table(field_rows, colWidths=[130, 220, 110, 80])
        f_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 4)
        ]))
        story.append(f_table)
        story.append(Spacer(1, 8))

        # Checks Table
        story.append(Paragraph("2. Multi-Pillar Forensic Matrix", section_heading))
        chk_rows = [[Paragraph("Check Name", table_header_style), Paragraph("Category", table_header_style), Paragraph("Result", table_header_style), Paragraph("Score", table_header_style), Paragraph("Details", table_header_style)]]
        for c in screening_data.get("validation_checks", []):
            c_st = c.get("status", "fail").upper()
            c_col = "#16a34a" if c_st == "PASS" else ("#dc2626" if c_st == "FAIL" else "#d97706")
            chk_rows.append([Paragraph(c.get("name", ""), body_style), Paragraph(c.get("category", ""), body_style), Paragraph(f'<font color="{c_col}"><b>{c_st}</b></font>', body_style), Paragraph(f"{c.get('score', 0)}/100", body_style), Paragraph(c.get("details", ""), body_style)])
        c_table = Table(chk_rows, colWidths=[140, 80, 55, 55, 210])
        c_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f172a')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 4)
        ]))
        story.append(c_table)

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        # Fallback to standalone zero-dependency builder if reportlab hits an error
        return _build_raw_pdf_certificate(screening_data)
