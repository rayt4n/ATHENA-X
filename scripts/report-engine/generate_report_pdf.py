#!/usr/bin/env python3
"""
ATHENA-X Stage 15 — Institutional Report PDF Generator

Reads a ReportContent JSON (with audit metadata) and produces a multi-page
PDF rendering of the report. Mirrors the dark engineering-cockpit theme
so reports are visually consistent with the platform.

Usage:
    echo '{...}' | python3 generate_report_pdf.py --output report.pdf
    python3 generate_report_pdf.py --input report.json --output report.pdf
"""

import argparse
import json
import sys
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.platypus.flowables import HRFlowable

# ---------- Font registration ----------
FONT_DIR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
]

def register_fonts():
    fonts = {}
    for d in FONT_DIR_CANDIDATES:
        if not Path(d).exists():
            continue
        for f in Path(d).glob("*.ttf"):
            try:
                pdfmetrics.registerFont(TTFont(f.stem, str(f)))
                fonts[f.stem] = str(f)
            except Exception:
                pass
    pairs = [
        ("DejaVuSans", "DejaVuSans-Bold"),
        ("DejaVuSerif", "DejaVuSerif-Bold"),
        ("DejaVuSansMono", "DejaVuSansMono-Bold"),
        ("LiberationSans", "LiberationSans-Bold"),
    ]
    for n, b in pairs:
        if n in fonts and b in fonts:
            try:
                pdfmetrics.registerFontFamily(n, normal=n, bold=b, italic=n, boldItalic=b)
            except Exception:
                pass
    return fonts


# ---------- Palette ----------
class P:
    BG = colors.HexColor("#0a0e14")
    BG_CARD = colors.HexColor("#131820")
    BG_ROW_ALT = colors.HexColor("#0f1419")
    BORDER = colors.HexColor("#1f2937")
    BORDER_LIGHT = colors.HexColor("#2d3748")
    TEXT = colors.HexColor("#e6edf3")
    MUTED = colors.HexColor("#8b949e")
    DIM = colors.HexColor("#6b7280")
    PRIMARY = colors.HexColor("#22d3ee")
    PRIMARY_DIM = colors.HexColor("#0e7490")
    PASS = colors.HexColor("#34d399")
    WARN = colors.HexColor("#fbbf24")
    FAIL = colors.HexColor("#f87171")
    ACCENT = colors.HexColor("#d4af37")


# ---------- Page background ----------
def page_bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(P.BG)
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # Subtle grid
    canvas.setStrokeColor(colors.Color(1, 1, 1, alpha=0.018))
    canvas.setLineWidth(0.3)
    for x in range(0, int(A4[0]), 24):
        canvas.line(x, 0, x, A4[1])
    for y in range(0, int(A4[1]), 24):
        canvas.line(0, y, A4[0], y)

    # Header bar — institutional blue/teal accent (not red — this is a trader-facing doc)
    canvas.setFillColor(colors.Color(0.13, 0.83, 0.93, alpha=0.08))
    canvas.rect(0, A4[1] - 16, A4[0], 16, stroke=0, fill=1)
    canvas.setFillColor(P.PRIMARY)
    canvas.setFont("DejaVuSans-Bold", 7)
    canvas.drawString(15 * mm, A4[1] - 11, "ATHENA-X · INSTITUTIONAL REPORT")
    canvas.setFillColor(P.MUTED)
    canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 11, f"STAGE 15 · REPORT ENGINE · PAGE {doc.page}")

    # Footer
    canvas.setFillColor(P.DIM)
    canvas.setFont("DejaVuSans", 7)
    canvas.drawString(15 * mm, 8, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+08')}")
    canvas.drawRightString(A4[0] - 15 * mm, 8, f"Hash: {getattr(doc, '_hash_short', '—')}")
    canvas.setStrokeColor(P.BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(15 * mm, 14, A4[0] - 15 * mm, 14)
    canvas.restoreState()


# ---------- Markdown → ReportLab paragraphs (simplified) ----------
def md_to_flowables(md: str, styles: dict):
    """Convert a subset of markdown to ReportLab flowables."""
    flowables = []
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip empty
        if not stripped:
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            flowables.append(HRFlowable(width="100%", thickness=0.3, color=P.BORDER_LIGHT))
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue

        # Headings
        if stripped.startswith("# "):
            flowables.append(Paragraph(_inline(stripped[2:]), styles["h1"]))
            flowables.append(Spacer(1, 2 * mm))
            i += 1
            continue
        if stripped.startswith("## "):
            flowables.append(Paragraph(_inline(stripped[3:]), styles["h2"]))
            flowables.append(Spacer(1, 1.5 * mm))
            i += 1
            continue
        if stripped.startswith("### "):
            flowables.append(Paragraph(_inline(stripped[4:]), styles["h3"]))
            i += 1
            continue

        # Tables (lines starting with |)
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            flowables.append(_build_table(table_lines, styles))
            flowables.append(Spacer(1, 2 * mm))
            continue

        # Bullet list
        if stripped.startswith("- ") or stripped.startswith("* "):
            items = []
            while i < len(lines) and (lines[i].strip().startswith("- ") or lines[i].strip().startswith("* ")):
                items.append(lines[i].strip()[2:])
                i += 1
            for item in items:
                flowables.append(Paragraph(f"• {_inline(item)}", styles["bullet"]))
            flowables.append(Spacer(1, 1 * mm))
            continue

        # Numbered list
        if re.match(r"^\d+\.\s", stripped):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i].strip()):
                m = re.match(r"^(\d+)\.\s+(.*)$", lines[i].strip())
                if m:
                    items.append((m.group(1), m.group(2)))
                i += 1
            for num, item in items:
                flowables.append(Paragraph(f"{num}. {_inline(item)}", styles["bullet"]))
            flowables.append(Spacer(1, 1 * mm))
            continue

        # Regular paragraph
        flowables.append(Paragraph(_inline(stripped), styles["body"]))
        i += 1

    return flowables


def _inline(text: str) -> str:
    """Convert inline markdown (bold, italic, code) to ReportLab tags."""
    # Code blocks (inline)
    text = re.sub(r"`([^`]+)`", r'<font face="DejaVuSansMono" color="#22d3ee">\1</font>', text)
    # Bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", text)
    return text


def _build_table(table_lines, styles):
    """Build a ReportLab table from markdown pipe-table lines."""
    rows = []
    for line in table_lines:
        # Skip separator rows (|---|---|)
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return Spacer(1, 0)

    # Wrap each cell in a Paragraph for proper wrapping
    para_rows = []
    for ri, row in enumerate(rows):
        para_row = []
        for cell in row:
            style = styles["cell_header"] if ri == 0 else styles["cell"]
            para_row.append(Paragraph(_inline(cell), style))
        para_rows.append(para_row)

    # Compute column widths — equal distribution
    n_cols = len(rows[0])
    avail = A4[0] - 30 * mm  # page width minus margins
    col_w = avail / n_cols

    t = Table(para_rows, colWidths=[col_w] * n_cols)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P.BG_CARD),
        ("TEXTCOLOR", (0, 0), (-1, 0), P.PRIMARY),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [P.BG_CARD, P.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, P.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


# ---------- Build PDF ----------
def build_pdf(payload: dict, output_path: str):
    register_fonts()

    content = payload["content"]
    audit = payload["audit"]

    styles = {
        "h1": ParagraphStyle("h1", fontName="DejaVuSans-Bold", fontSize=18, textColor=P.TEXT, spaceBefore=10, spaceAfter=4, leading=22),
        "h2": ParagraphStyle("h2", fontName="DejaVuSans-Bold", fontSize=12, textColor=P.PRIMARY, spaceBefore=8, spaceAfter=3, leading=14),
        "h3": ParagraphStyle("h3", fontName="DejaVuSans-Bold", fontSize=10, textColor=P.PRIMARY, spaceBefore=4, spaceAfter=2, leading=12),
        "body": ParagraphStyle("body", fontName="DejaVuSans", fontSize=9, textColor=P.TEXT, leading=12, spaceAfter=2),
        "bullet": ParagraphStyle("bullet", fontName="DejaVuSans", fontSize=9, textColor=P.TEXT, leading=11, leftIndent=8, spaceAfter=1),
        "small": ParagraphStyle("small", fontName="DejaVuSans", fontSize=7.5, textColor=P.MUTED, leading=10),
        "cell": ParagraphStyle("cell", fontName="DejaVuSans", fontSize=8, textColor=P.TEXT, leading=10),
        "cell_header": ParagraphStyle("cellh", fontName="DejaVuSans-Bold", fontSize=8, textColor=P.PRIMARY, leading=10),
        "meta": ParagraphStyle("meta", fontName="DejaVuSans", fontSize=8, textColor=P.MUTED, leading=10),
        "title": ParagraphStyle("title", fontName="DejaVuSans-Bold", fontSize=26, textColor=P.TEXT, alignment=1, spaceAfter=4, leading=30),
        "subtitle": ParagraphStyle("subtitle", fontName="DejaVuSans", fontSize=12, textColor=P.PRIMARY, alignment=1, spaceAfter=8, leading=14),
    }

    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
        title=f"ATHENA-X {content['title']}",
        author="ATHENA-X Report Engine",
        subject=f"{content['type']} report for {content['sessionDate']}",
        creator="ATHENA-X Stage 15",
    )
    doc._hash_short = audit["hash"][:12]

    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=page_bg)])

    story = []

    # Cover page
    story.append(Spacer(1, 30 * mm))
    story.append(Paragraph("ATHENA-X", styles["meta"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(content["title"], styles["title"]))
    if content.get("subtitle"):
        story.append(Paragraph(content["subtitle"], styles["subtitle"]))

    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="60%", thickness=0.5, color=P.PRIMARY_DIM, hAlign="CENTER"))
    story.append(Spacer(1, 8 * mm))

    # Cover metadata table
    cover_rows = [
        ["Session Date", content["sessionDate"]],
        ["Report Type", content["type"]],
        ["Generated", datetime.fromtimestamp(content["generatedAt"] / 1000).strftime("%Y-%m-%d %H:%M:%S UTC+08")],
        ["Report ID", content["id"]],
        ["Schema Version", audit["schemaVersion"]],
        ["Generator Version", audit["generatorVersion"]],
        ["Build Version", audit["buildVersion"]],
        ["Forecast Version", audit["forecastVersion"]],
        ["Content Hash", audit["hash"]],
        ["Workspace", audit["workspace"]],
        ["User", audit["user"]],
    ]
    cover_data = [[Paragraph(f"<b>{k}</b>", styles["cell"]), Paragraph(v, styles["cell"])] for k, v in cover_rows]
    cover_table = Table(cover_data, colWidths=[50 * mm, 110 * mm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P.BG_CARD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [P.BG_CARD, P.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, P.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cover_table)

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "This report was generated by the ATHENA-X Institutional Report Engine. The engine is "
        "<b>read-only</b> and performs no calculations — every value originates from validated "
        "canonical databases or one of the seven DNA intelligence objects.",
        styles["meta"]
    ))

    # DNA snapshot table on cover
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("DNA Objects Consumed", styles["h3"]))
    dna_rows = [["DNA Object", "Version", "Confidence"]]
    for key in ["technical", "options", "market", "narrative", "forecast", "trade", "operations"]:
        dna = content["dnaSnapshot"][key]
        conf_pct = f"{dna['confidence'] * 100:.1f}%"
        conf_color = P.PASS if dna["confidence"] >= 0.75 else P.WARN if dna["confidence"] >= 0.55 else P.FAIL
        dna_rows.append([dna["id"].capitalize(), dna["version"], conf_pct])

    dna_data = []
    for ri, row in enumerate(dna_rows):
        if ri == 0:
            dna_data.append([Paragraph(f"<b>{c}</b>", styles["cell_header"]) for c in row])
        else:
            conf_pct = row[2]
            dna_data.append([
                Paragraph(row[0], styles["cell"]),
                Paragraph(row[1], styles["cell"]),
                Paragraph(conf_pct, styles["cell"]),
            ])

    dna_table = Table(dna_data, colWidths=[40 * mm, 80 * mm, 40 * mm])
    dna_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), P.BG_CARD),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [P.BG_CARD, P.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, P.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(dna_table)

    story.append(PageBreak())

    # Table of contents
    story.append(Paragraph("Table of Contents", styles["h1"]))
    story.append(Spacer(1, 4 * mm))
    for i, s in enumerate(content["sections"]):
        story.append(Paragraph(f"{i + 1}. {s['title']}", styles["body"]))
    story.append(PageBreak())

    # Sections
    for i, section in enumerate(content["sections"]):
        if i > 0:
            story.append(PageBreak())
        story.extend(md_to_flowables(section["markdown"], styles))

        # Sources appendix at the end of each section
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.3, color=P.BORDER_LIGHT))
        story.append(Spacer(1, 2 * mm))
        sources_str = ", ".join(f"{s['id']} ({s['version']}, conf {(s['confidence'] * 100):.1f}%)" for s in section["sources"])
        story.append(Paragraph(f"<b>Sources:</b> {sources_str}", styles["small"]))

    # Final page — audit trail
    story.append(PageBreak())
    story.append(Paragraph("Audit Trail", styles["h1"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Every stored report carries immutable audit metadata. The hash below is a deterministic "
        "SHA-256 of the report's structured content — identical inputs always produce identical hashes.",
        styles["body"]
    ))
    story.append(Spacer(1, 4 * mm))

    audit_rows = [
        ["Schema Version", audit["schemaVersion"]],
        ["Generator Version", audit["generatorVersion"]],
        ["Build Version", audit["buildVersion"]],
        ["Forecast Version", audit["forecastVersion"]],
        ["Content Hash (SHA-256)", audit["hash"]],
        ["DNA Versions", json.dumps(audit["dnaVersions"], indent=2)],
        ["Workspace", audit["workspace"]],
        ["User", audit["user"]],
    ]
    audit_data = [[Paragraph(f"<b>{k}</b>", styles["cell"]), Paragraph(v, styles["cell"])] for k, v in audit_rows]
    audit_table = Table(audit_data, colWidths=[50 * mm, 110 * mm])
    audit_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), P.BG_CARD),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [P.BG_CARD, P.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, P.BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(audit_table)

    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph(
        "<i>ATHENA-X Institutional Report Engine — Stage 15. This document is read-only and "
        "contains no values computed by the report engine itself.</i>",
        styles["small"]
    ))

    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if args.input:
        with open(args.input) as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)

    build_pdf(payload, args.output)
    print(f"Generated: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
