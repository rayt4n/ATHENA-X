#!/usr/bin/env python3
"""
ATHENA-X Stage 14.5 — Production Certification PDF Generator

Reads a CertificationState JSON from stdin (or --input file) and produces
a formal Production Readiness Certificate PDF.

Usage:
    echo '{"version":"1.0",...}' | python3 generate_certificate.py --output cert.pdf
    python3 generate_certificate.py --input state.json --output cert.pdf
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable, BaseDocTemplate, PageTemplate, Frame
)
from reportlab.platypus.flowables import HRFlowable

# ---------- Font registration ----------
FONT_DIR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/freefont",
]

def register_fonts():
    """Register fonts with CJK + symbol fallback."""
    fonts_registered = {}
    for font_dir in FONT_DIR_CANDIDATES:
        if not Path(font_dir).exists():
            continue
        for font_file in Path(font_dir).glob("*.ttf"):
            name = font_file.stem
            try:
                pdfmetrics.registerFont(TTFont(name, str(font_file)))
                fonts_registered[name] = str(font_file)
            except Exception:
                pass

    # Register font families so <b> tags work inside Paragraph()
    family_pairs = [
        ("DejaVuSans", "DejaVuSans-Bold"),
        ("DejaVuSerif", "DejaVuSerif-Bold"),
        ("DejaVuSansMono", "DejaVuSansMono-Bold"),
        ("LiberationSans", "LiberationSans-Bold"),
        ("LiberationSerif", "LiberationSerif-Bold"),
        ("LiberationMono", "LiberationMono-Bold"),
    ]
    for normal, bold in family_pairs:
        if normal in fonts_registered and bold in fonts_registered:
            try:
                pdfmetrics.registerFontFamily(normal, normal=normal, bold=bold, italic=normal, boldItalic=bold)
            except Exception:
                pass

    return fonts_registered

# ---------- Color palette ----------
class Palette:
    BG_DARK = colors.HexColor("#0a0e14")
    BG_CARD = colors.HexColor("#131820")
    BG_ROW_ALT = colors.HexColor("#0f1419")
    BORDER = colors.HexColor("#1f2937")
    BORDER_LIGHT = colors.HexColor("#2d3748")
    TEXT_PRIMARY = colors.HexColor("#e6edf3")
    TEXT_MUTED = colors.HexColor("#8b949e")
    TEXT_DIM = colors.HexColor("#6b7280")
    PRIMARY = colors.HexColor("#22d3ee")
    PRIMARY_DIM = colors.HexColor("#0e7490")
    STATUS_PASS = colors.HexColor("#34d399")
    STATUS_WARN = colors.HexColor("#fbbf24")
    STATUS_FAIL = colors.HexColor("#f87171")
    ACCENT_GOLD = colors.HexColor("#d4af37")

# ---------- Custom flowables ----------
class ScoreRing(Flowable):
    """Draws a circular score ring."""
    def __init__(self, score, size=80, label=None):
        Flowable.__init__(self)
        self.score = score
        self.size = size
        self.label = label
        self.width = size
        self.height = size + (12 if label else 0)

    def draw(self):
        c = self.canv
        radius = (self.size - 8) / 2
        cx = self.size / 2
        cy = self.size / 2

        # Background circle
        c.setStrokeColor(Palette.BORDER_LIGHT)
        c.setLineWidth(3)
        c.circle(cx, cy, radius, stroke=1, fill=0)

        # Score arc
        color = (Palette.STATUS_PASS if self.score >= 0.95 else
                 Palette.STATUS_WARN if self.score >= 0.85 else
                 Palette.STATUS_FAIL)
        c.setStrokeColor(color)
        c.setLineWidth(3)
        import math
        from reportlab.graphics.shapes import Pie
        # Use arc
        angle = 360 * self.score
        c.wedge(cx - radius, cy - radius, cx + radius, cy + radius, 90, -angle, stroke=1, fill=0)

        # Score text
        c.setFillColor(color)
        c.setFont("DejaVuSans-Bold", 12)
        c.drawCentredString(cx, cy - 4, f"{self.score * 100:.1f}%")
        if self.label:
            c.setFillColor(Palette.TEXT_MUTED)
            c.setFont("DejaVuSans", 7)
            c.drawCentredString(cx, cy - 16, self.label.upper())


class HorizontalRule(Flowable):
    def __init__(self, width, color=Palette.BORDER, thickness=0.5):
        Flowable.__init__(self)
        self.width = width
        self.color = color
        self.thickness = thickness
        self.height = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 0, self.width, 0)


# ---------- Page template ----------
def page_background(canvas, doc):
    """Dark background + decorative elements on every page."""
    canvas.saveState()
    # Full-page dark background
    canvas.setFillColor(Palette.BG_DARK)
    canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # Subtle grid
    canvas.setStrokeColor(colors.Color(1, 1, 1, alpha=0.018))
    canvas.setLineWidth(0.3)
    for x in range(0, int(A4[0]), 24):
        canvas.line(x, 0, x, A4[1])
    for y in range(0, int(A4[1]), 24):
        canvas.line(0, y, A4[0], y)

    # Header bar
    canvas.setFillColor(colors.Color(0.78, 0.14, 0.20, alpha=0.06))  # red tint
    canvas.rect(0, A4[1] - 16, A4[0], 16, stroke=0, fill=1)

    canvas.setFillColor(Palette.STATUS_FAIL)
    canvas.setFont("DejaVuSans-Bold", 7)
    canvas.drawString(15 * mm, A4[1] - 11, "INTERNAL ENGINEERING TOOL")
    canvas.setFillColor(Palette.TEXT_MUTED)
    canvas.drawRightString(A4[0] - 15 * mm, A4[1] - 11, "ATHENA-X · STAGE 14.5 · PRODUCTION CERTIFICATION")

    # Footer
    canvas.setFillColor(Palette.TEXT_DIM)
    canvas.setFont("DejaVuSans", 7)
    canvas.drawString(15 * mm, 8, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+08')}")
    canvas.drawRightString(A4[0] - 15 * mm, 8, f"Page {doc.page}")
    canvas.setStrokeColor(Palette.BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(15 * mm, 14, A4[0] - 15 * mm, 14)

    canvas.restoreState()


# ---------- Status helpers ----------
def status_color(status):
    return {
        "pass": Palette.STATUS_PASS,
        "warn": Palette.STATUS_WARN,
        "fail": Palette.STATUS_FAIL,
        "pending": Palette.TEXT_DIM,
        "running": Palette.PRIMARY,
    }.get(status, Palette.TEXT_MUTED)


def status_label(status):
    return {
        "pass": "PASS",
        "warn": "WARN",
        "fail": "FAIL",
        "pending": "PENDING",
        "running": "RUNNING",
    }.get(status, status.upper())


def verdict_color(status):
    return {
        "certified": Palette.STATUS_PASS,
        "conditional": Palette.STATUS_WARN,
        "not_certified": Palette.STATUS_FAIL,
    }.get(status, Palette.TEXT_MUTED)


def verdict_label(status):
    return {
        "certified": "CERTIFIED",
        "conditional": "CONDITIONAL",
        "not_certified": "NOT CERTIFIED",
    }.get(status, status.upper())


# ---------- Build PDF ----------
def build_pdf(state, output_path):
    register_fonts()

    # Styles
    styles = getSampleStyleSheet()

    s_h1 = ParagraphStyle("h1", parent=styles["Heading1"],
        fontName="DejaVuSans-Bold", fontSize=24, textColor=Palette.TEXT_PRIMARY,
        alignment=1, spaceAfter=4, leading=28)
    s_h2 = ParagraphStyle("h2", parent=styles["Heading2"],
        fontName="DejaVuSans-Bold", fontSize=12, textColor=Palette.PRIMARY,
        alignment=1, spaceAfter=2, leading=14)
    s_meta = ParagraphStyle("meta", parent=styles["Normal"],
        fontName="DejaVuSans", fontSize=8, textColor=Palette.TEXT_MUTED,
        alignment=1, spaceAfter=2, leading=10)
    s_verdict = ParagraphStyle("verdict", parent=styles["Heading1"],
        fontName="DejaVuSans-Bold", fontSize=32, textColor=verdict_color(state["status"]),
        alignment=1, spaceAfter=4, leading=36)
    s_score = ParagraphStyle("score", parent=styles["Normal"],
        fontName="DejaVuSans-Bold", fontSize=14, textColor=Palette.TEXT_PRIMARY,
        alignment=1, spaceAfter=2, leading=16)
    s_section = ParagraphStyle("section", parent=styles["Heading2"],
        fontName="DejaVuSans-Bold", fontSize=11, textColor=Palette.PRIMARY,
        spaceBefore=12, spaceAfter=6, leading=13)
    s_body = ParagraphStyle("body", parent=styles["Normal"],
        fontName="DejaVuSans", fontSize=9, textColor=Palette.TEXT_PRIMARY,
        leading=12, spaceAfter=4)
    s_small = ParagraphStyle("small", parent=styles["Normal"],
        fontName="DejaVuSans", fontSize=7.5, textColor=Palette.TEXT_MUTED,
        leading=10)
    s_cell = ParagraphStyle("cell", parent=styles["Normal"],
        fontName="DejaVuSans", fontSize=8, textColor=Palette.TEXT_PRIMARY,
        leading=10)
    s_cell_mono = ParagraphStyle("cellm", parent=styles["Normal"],
        fontName="DejaVuSansMono", fontSize=7.5, textColor=Palette.TEXT_PRIMARY,
        leading=10)
    s_cell_right = ParagraphStyle("cellr", parent=styles["Normal"],
        fontName="DejaVuSansMono", fontSize=8, textColor=Palette.TEXT_PRIMARY,
        alignment=2, leading=10)

    # Document
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=22 * mm, bottomMargin=18 * mm,
        title=f"ATHENA-X Production Certification v{state['version']}",
        author="ATHENA-X Certification Engine",
        subject="Production Readiness Certificate",
        creator="ATHENA-X Stage 14.5",
    )

    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    template = PageTemplate(id="main", frames=[frame], onPage=page_background)
    doc.addPageTemplates([template])

    story = []

    # ---- Title block ----
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("ATHENA-X", s_meta))
    story.append(Paragraph("Production Certification", s_h1))
    story.append(Paragraph("Institutional Acceptance Document", s_h2))
    story.append(Spacer(1, 4 * mm))

    # Build hash + environment
    meta_text = f"Certificate v{state['version']}  ·  Build {state['buildHash']}  ·  Environment: {state['environment']}"
    story.append(Paragraph(meta_text, s_meta))
    story.append(Paragraph(f"Issued: {datetime.fromtimestamp(state['generatedAt']/1000).strftime('%Y-%m-%d %H:%M:%S UTC+08')}", s_meta))
    story.append(Paragraph(f"Valid until: {datetime.fromtimestamp(state['validUntil']/1000).strftime('%Y-%m-%d %H:%M:%S UTC+08')}", s_meta))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=Palette.BORDER_LIGHT))
    story.append(Spacer(1, 6 * mm))

    # ---- Verdict block ----
    story.append(Paragraph("CERTIFICATION VERDICT", s_meta))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(verdict_label(state["status"]), s_verdict))
    story.append(Paragraph(f"Overall Score: {state['overallScore'] * 100:.2f}%", s_score))
    story.append(Paragraph(
        f"{state['criticalFailures']} critical failures  ·  {state['warnings']} warnings  ·  {len(state['modules'])} modules evaluated",
        s_meta
    ))

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=Palette.BORDER_LIGHT))
    story.append(Spacer(1, 4 * mm))

    # ---- Module results table ----
    story.append(Paragraph("MODULE RESULTS", s_section))

    module_rows = [[
        Paragraph("<b>#</b>", s_cell),
        Paragraph("<b>Module</b>", s_cell),
        Paragraph("<b>Score</b>", s_cell_right),
        Paragraph("<b>Status</b>", s_cell_right),
    ]]
    for i, m in enumerate(state["modules"], 1):
        sc = status_color(m["status"])
        score_color = (Palette.STATUS_PASS if m["score"] >= 0.95 else
                       Palette.STATUS_WARN if m["score"] >= 0.85 else
                       Palette.STATUS_FAIL)
        module_rows.append([
            Paragraph(str(i), s_cell_mono),
            Paragraph(m["name"], s_cell),
            Paragraph(f'<font color="{score_color.hexval()}">{m["score"] * 100:.2f}%</font>', s_cell_right),
            Paragraph(f'<font color="{sc.hexval()}">{status_label(m["status"])}</font>', s_cell_right),
        ])

    module_table = Table(module_rows, colWidths=[10*mm, 95*mm, 35*mm, 25*mm])
    module_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), Palette.BG_CARD),
        ("TEXTCOLOR", (0, 0), (-1, 0), Palette.TEXT_MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [Palette.BG_CARD, Palette.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, Palette.BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(module_table)

    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=Palette.BORDER_LIGHT))
    story.append(Spacer(1, 4 * mm))

    # ---- Exit criteria ----
    story.append(Paragraph("EXIT CRITERIA VERIFICATION", s_section))
    story.append(Paragraph(
        f"{sum(1 for e in state['exitCriteria'] if e['passed'])} of {len(state['exitCriteria'])} criteria passed — all must pass to advance to Stage 15 (Report Engine)",
        s_body
    ))
    story.append(Spacer(1, 2 * mm))

    ec_rows = [[
        Paragraph("<b>✓/✗</b>", s_cell),
        Paragraph("<b>Criterion</b>", s_cell),
        Paragraph("<b>Detail</b>", s_cell),
    ]]
    for ec in state["exitCriteria"]:
        marker = "✓" if ec["passed"] else "✗"
        marker_color = Palette.STATUS_PASS if ec["passed"] else Palette.STATUS_FAIL
        ec_rows.append([
            Paragraph(f'<font color="{marker_color.hexval()}"><b>{marker}</b></font>', s_cell),
            Paragraph(ec["label"], s_cell),
            Paragraph(ec.get("detail", ""), s_small),
        ])

    ec_table = Table(ec_rows, colWidths=[8*mm, 80*mm, 77*mm])
    ec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), Palette.BG_CARD),
        ("TEXTCOLOR", (0, 0), (-1, 0), Palette.TEXT_MUTED),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [Palette.BG_CARD, Palette.BG_ROW_ALT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.3, Palette.BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(ec_table)

    # ---- Page 2: Detailed checks per module ----
    story.append(PageBreak())
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("DETAILED CHECK RESULTS", s_section))
    story.append(Paragraph(
        "Per-check breakdown for each of the 8 certification modules. Each check shows measured value, target threshold, and pass/warn/fail status.",
        s_body
    ))
    story.append(Spacer(1, 3 * mm))

    # The state passed in includes the full modules array (with checks)
    modules_with_checks = state.get("modules", [])
    # If the caller sent only the certificate summary, modules won't have checks — handle gracefully
    for m in modules_with_checks:
        checks = m.get("checks", [])
        if not checks:
            continue

        story.append(Spacer(1, 3 * mm))
        mc = status_color(m["status"])
        story.append(Paragraph(
            f'<font color="{Palette.PRIMARY.hexval()}">Module {m["index"]}</font>  ·  <b>{m["name"]}</b>  ·  <font color="{mc.hexval()}">{status_label(m["status"])}</font>  ·  Score: {m["score"] * 100:.2f}%',
            s_body
        ))
        story.append(Spacer(1, 1.5 * mm))

        chk_rows = [[
            Paragraph("<b>Check</b>", s_cell),
            Paragraph("<b>Value</b>", s_cell_right),
            Paragraph("<b>Target</b>", s_cell_right),
            Paragraph("<b>Status</b>", s_cell_right),
        ]]
        for c in checks:
            cc = status_color(c["status"])
            value_str = str(c.get("value", "—"))
            if c.get("unit"):
                value_str += f' {c["unit"]}'
            chk_rows.append([
                Paragraph(f'{c["label"]}', s_cell),
                Paragraph(value_str, s_cell_right),
                Paragraph(str(c.get("target", "—")), s_cell_right),
                Paragraph(f'<font color="{cc.hexval()}">{status_label(c["status"])}</font>', s_cell_right),
            ])

        chk_table = Table(chk_rows, colWidths=[75*mm, 35*mm, 30*mm, 25*mm])
        chk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), Palette.BG_CARD),
            ("TEXTCOLOR", (0, 0), (-1, 0), Palette.TEXT_MUTED),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 7),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [Palette.BG_CARD, Palette.BG_ROW_ALT]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, Palette.BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(chk_table)

    # ---- Signature block ----
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=Palette.BORDER_LIGHT))
    story.append(Spacer(1, 4 * mm))

    sig_data = [
        [Paragraph("<b>Signed By</b>", s_small), Paragraph("<b>Issued</b>", s_small), Paragraph("<b>Valid Until</b>", s_small)],
        [
            Paragraph(state["signedBy"], s_cell),
            Paragraph(datetime.fromtimestamp(state["generatedAt"]/1000).strftime("%Y-%m-%d %H:%M"), s_cell),
            Paragraph(datetime.fromtimestamp(state["validUntil"]/1000).strftime("%Y-%m-%d %H:%M"), s_cell),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[54*mm, 54*mm, 54*mm])
    sig_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), Palette.BG_CARD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, 0), 0.3, Palette.BORDER),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, Palette.ACCENT_GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 4 * mm))
    stage_text = (
        '<font color="' + Palette.STATUS_PASS.hexval() + '">All exit criteria passed.</font> Platform is cleared to advance to Stage 15 (Report Engine).'
        if state["status"] == "certified" else
        '<font color="' + Palette.STATUS_WARN.hexval() + '">Conditional pass.</font> Warnings present; may proceed with monitoring.'
        if state["status"] == "conditional" else
        '<font color="' + Palette.STATUS_FAIL.hexval() + '">Blocked.</font> Critical failures must be resolved before advancing.'
    )
    story.append(Paragraph(stage_text, s_body))

    doc.build(story)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate ATHENA-X Production Certification PDF")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", required=True, help="Output PDF path")
    args = parser.parse_args()

    if args.input:
        with open(args.input, "r") as f:
            state = json.load(f)
    else:
        state = json.load(sys.stdin)

    build_pdf(state, args.output)
    print(f"Generated: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
