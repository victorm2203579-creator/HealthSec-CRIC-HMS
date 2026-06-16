"""
reports/services.py
===================
PDF generation service using ReportLab.
"""

import io
import logging
from datetime import datetime

from django.utils import timezone

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

logger = logging.getLogger('healthsec.reports')

# ── Brand palette ──────────────────────────────────────────────────────────────
NAVY        = colors.HexColor('#0d1117')
PURPLE      = colors.HexColor('#5b47fb')
PURPLE_DARK = colors.HexColor('#3d2fd6')
TEAL        = colors.HexColor('#06b6d4')
GREEN       = colors.HexColor('#10b981')
RED         = colors.HexColor('#ef4444')
AMBER       = colors.HexColor('#f59e0b')
LIGHT_BG    = colors.HexColor('#f8fafc')
BORDER      = colors.HexColor('#e2e8f0')
MUTED       = colors.HexColor('#64748b')
WHITE       = colors.white
PAGE_W, PAGE_H = A4


def _page_header_footer(canvas, doc):
    """Draw the branded page header band and footer on every page."""
    canvas.saveState()

    # ── Header band ────────────────────────────────────────────────────────────
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H - 52 * mm, PAGE_W, 52 * mm, fill=1, stroke=0)

    # Logo mark (filled shield shape approximated as a rectangle + circle cap)
    canvas.setFillColor(PURPLE)
    canvas.roundRect(18 * mm, PAGE_H - 40 * mm, 14 * mm, 18 * mm, 3, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    # Cross inside logo
    canvas.rect(23.5 * mm, PAGE_H - 31 * mm, 3 * mm, 10 * mm, fill=1, stroke=0)
    canvas.rect(20 * mm, PAGE_H - 27 * mm, 10 * mm, 3 * mm, fill=1, stroke=0)

    # Brand text
    canvas.setFillColor(WHITE)
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawString(36 * mm, PAGE_H - 26 * mm, 'HealthSec')
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#94a3b8'))
    canvas.drawString(36 * mm, PAGE_H - 33 * mm, 'Cyber Risk Intelligence & Compliance HMS')

    # Report title (right side)
    canvas.setFont('Helvetica-Bold', 10)
    canvas.setFillColor(WHITE)
    title_text = doc.report_title if hasattr(doc, 'report_title') else ''
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 26 * mm, title_text)
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.HexColor('#94a3b8'))
    canvas.drawRightString(PAGE_W - 18 * mm, PAGE_H - 34 * mm,
                           timezone.now().strftime('%d %b %Y  %H:%M WAT'))

    # ── Footer ─────────────────────────────────────────────────────────────────
    canvas.setFillColor(LIGHT_BG)
    canvas.rect(0, 0, PAGE_W, 14 * mm, fill=1, stroke=0)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0, 14 * mm, PAGE_W, 14 * mm)

    canvas.setFont('Helvetica', 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 5 * mm,
                      'CONFIDENTIAL — For authorised HealthSec users only. Do not distribute without permission.')
    canvas.drawRightString(PAGE_W - 18 * mm, 5 * mm,
                           f'Page {doc.page}')

    canvas.restoreState()


class PDFReportService:
    """Build and return a ReportLab PDF as a bytes buffer."""

    def __init__(self, title: str, subtitle: str = '', author: str = 'HealthSec System'):
        self.title = title
        self.subtitle = subtitle
        self.author = author
        self.buffer = io.BytesIO()
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        s = self.styles
        s.add(ParagraphStyle('SectionHeading',
            fontSize=13, textColor=PURPLE, spaceBefore=14, spaceAfter=6,
            fontName='Helvetica-Bold'))
        s.add(ParagraphStyle('SubHeading',
            fontSize=10, textColor=NAVY, spaceBefore=10, spaceAfter=4,
            fontName='Helvetica-Bold'))
        s.add(ParagraphStyle('BodyText2',
            fontSize=9, textColor=colors.HexColor('#374151'),
            spaceAfter=4, leading=14))
        s.add(ParagraphStyle('MetaText',
            fontSize=8, textColor=MUTED, spaceAfter=2))
        s.add(ParagraphStyle('TableCell',
            fontSize=8.5, textColor=NAVY, leading=12))
        s.add(ParagraphStyle('TableCellMuted',
            fontSize=8, textColor=MUTED, leading=11))

    def _make_doc(self):
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=1.8 * cm,
            leftMargin=1.8 * cm,
            topMargin=6 * cm,
            bottomMargin=2.5 * cm,
            title=self.title,
            author=self.author,
        )
        doc.report_title = self.title
        return doc

    # ── Risk Summary ─────────────────────────────────────────────────────────
    def build_risk_summary(self, risk_scores: list) -> bytes:
        doc = self._make_doc()
        story = []

        story.append(Paragraph('Risk Score Summary', self.styles['SectionHeading']))
        if self.subtitle:
            story.append(Paragraph(self.subtitle, self.styles['MetaText']))
        story.append(HRFlowable(width='100%', color=PURPLE, thickness=1.5, spaceAfter=10))

        if risk_scores:
            # Summary KPI row
            total    = len(risk_scores)
            avg      = sum(rs.score for rs in risk_scores) / total if total else 0
            critical = sum(1 for rs in risk_scores if rs.risk_level in ('CRITICAL', 'HIGH'))

            kpi_data = [
                [_kpi_cell('Systems Assessed', str(total)),
                 _kpi_cell('Avg Risk Score', f'{avg:.1f}/10'),
                 _kpi_cell('High/Critical', str(critical))],
            ]
            kpi_table = Table(kpi_data, colWidths=[5.5 * cm, 5.5 * cm, 5.5 * cm])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
                ('ROUNDEDCORNERS', [4]),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.5 * cm))

            # Detailed table
            story.append(Paragraph('Detailed Risk Scores', self.styles['SubHeading']))
            header = ['System', 'Risk Score', 'Level', 'Top Vulnerability', 'Computed At']
            rows = [header]
            for rs in risk_scores:
                level_colour = {
                    'CRITICAL': RED, 'HIGH': AMBER, 'MEDIUM': AMBER,
                    'LOW': GREEN, 'MINIMAL': GREEN,
                }.get(rs.risk_level, MUTED)
                rows.append([
                    Paragraph(rs.system.name, self.styles['TableCell']),
                    Paragraph(f'<b>{rs.score}</b>/10', self.styles['TableCell']),
                    Paragraph(f'<font color="{level_colour.hexval()}">'
                              f'<b>{rs.risk_level}</b></font>', self.styles['TableCell']),
                    Paragraph(getattr(rs, 'top_vulnerability', '—') or '—',
                              self.styles['TableCellMuted']),
                    Paragraph(rs.computed_at.strftime('%d %b %Y  %H:%M'),
                              self.styles['TableCellMuted']),
                ])

            col_widths = [6 * cm, 2.5 * cm, 2.5 * cm, 4.5 * cm, 3.5 * cm]
            tbl = Table(rows, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(_standard_table_style())
            story.append(tbl)
        else:
            story.append(Paragraph(
                'No risk scores have been recorded yet. Run a risk assessment to populate this report.',
                self.styles['BodyText2']))

        doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
        return self.buffer.getvalue()

    # ── Compliance Report ─────────────────────────────────────────────────────
    def build_compliance_report(self, framework, assessments: list) -> bytes:
        doc = self._make_doc()
        story = []

        story.append(Paragraph(f'Compliance Report: {framework.name}',
                                self.styles['SectionHeading']))
        story.append(Paragraph(
            f'{framework.short_name} · Region: {framework.applicable_region}',
            self.styles['MetaText']))
        story.append(HRFlowable(width='100%', color=GREEN, thickness=1.5, spaceAfter=10))

        if assessments:
            total   = len(assessments)
            passing = sum(1 for a in assessments if a.status == 'PASS')
            failing = sum(1 for a in assessments if a.status == 'FAIL')
            partial = sum(1 for a in assessments if a.status == 'PARTIAL')
            avg_score = sum(a.score for a in assessments) / total if total else 0

            # KPI row
            kpi_data = [[
                _kpi_cell('Total Controls', str(total)),
                _kpi_cell('Passing', str(passing), GREEN),
                _kpi_cell('Failing', str(failing), RED),
                _kpi_cell('Avg Score', f'{avg_score:.0f}%'),
            ]]
            kpi_table = Table(kpi_data, colWidths=[4 * cm, 4 * cm, 4 * cm, 4 * cm])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.5 * cm))

            story.append(Paragraph('Control Assessment Details', self.styles['SubHeading']))
            header = ['Control ID', 'Title', 'Status', 'Score', 'Assessed']
            rows = [header]
            for a in assessments:
                status_colour = {'PASS': GREEN, 'FAIL': RED, 'PARTIAL': AMBER}.get(a.status, MUTED)
                rows.append([
                    Paragraph(f'<b>{a.control.control_id}</b>', self.styles['TableCell']),
                    Paragraph(a.control.title[:55], self.styles['TableCell']),
                    Paragraph(f'<font color="{status_colour.hexval()}"><b>{a.status}</b></font>',
                              self.styles['TableCell']),
                    Paragraph(f'{a.score}%', self.styles['TableCell']),
                    Paragraph(a.assessed_at.strftime('%d %b %Y'), self.styles['TableCellMuted']),
                ])

            col_widths = [2.5 * cm, 7.5 * cm, 2.5 * cm, 2 * cm, 3 * cm]
            tbl = Table(rows, colWidths=col_widths, repeatRows=1)
            tbl.setStyle(_standard_table_style())
            story.append(tbl)
        else:
            story.append(Paragraph(
                'No compliance assessments have been recorded for this framework yet.',
                self.styles['BodyText2']))

        doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
        return self.buffer.getvalue()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _kpi_cell(label: str, value: str, val_colour=None):
    """Return a Paragraph pair for a KPI summary cell."""
    colour = val_colour.hexval() if val_colour else NAVY.hexval()
    return Paragraph(
        f'<font size="18" color="{colour}"><b>{value}</b></font><br/>'
        f'<font size="8" color="{MUTED.hexval()}">{label}</font>',
        ParagraphStyle('kpi', alignment=TA_CENTER, leading=24))


def _standard_table_style() -> TableStyle:
    return TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        # Alternating rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.4, BORDER),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, PURPLE),
        # Padding
        ('TOPPADDING', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 7),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ])
