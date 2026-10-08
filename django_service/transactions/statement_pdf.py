from decimal import Decimal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

BRAND = colors.HexColor("#4338ca")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6b7280")
LINE = colors.HexColor("#e5e7eb")
STRIPE = colors.HexColor("#f5f6fb")
STATUS_COLOR = {"SUCCESS": "#059669", "FAILED": "#dc2626", "PENDING": "#d97706"}

_base = getSampleStyleSheet()["Normal"]
BODY = ParagraphStyle("body", parent=_base, fontName="Helvetica", fontSize=9, leading=12, textColor=INK)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, textColor=MUTED)
RIGHT = ParagraphStyle("right", parent=BODY, alignment=TA_RIGHT)
HEAD = ParagraphStyle("head", parent=BODY, fontName="Helvetica-Bold", textColor=colors.white)
HEAD_R = ParagraphStyle("head_r", parent=HEAD, alignment=TA_RIGHT)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Helvetica-Bold", fontSize=11,
                    spaceBefore=14, spaceAfter=6, textColor=BRAND)
TITLE = ParagraphStyle("title", parent=BODY, fontSize=9, leading=20, textColor=colors.white)


def inr(value) -> str:
    return f"INR {Decimal(value):,.2f}"


def _p(text, style=BODY):
    # escape() stops user text such as a payment description breaking the layout
    return Paragraph(escape(str(text)), style)


def _grid() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, STRIPE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 10 * mm,
                      "SecurePay - computer-generated statement. Card numbers are masked.")
    canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_statement_pdf(buffer, data: dict) -> None:
    """Draw the statement into `buffer`.

    `data` keys: holder, period_start, period_end, generated_at, cards, rows,
    total_spent, counts, available_credit (built by statement_views.py).
    """
    period = f"{data['period_start']:%d %b %Y} - {data['period_end']:%d %b %Y}"
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=20 * mm,
        title=f"SecurePay statement {period}", author="SecurePay",
    )
    width = doc.width
    story = []

    # Header band
    header = Table(
        [[Paragraph('<font size="18"><b>SecurePay</b></font><br/>Monthly account statement', TITLE)]],
        colWidths=[width],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story += [header, Spacer(1, 10)]

    # Account and period
    info = Table(
        [
            [_p("Account holder", SMALL), _p(data["holder"]),
             _p("Statement period", SMALL), _p(period)],
            [_p("Generated on", SMALL), _p(f"{data['generated_at']:%d %b %Y, %H:%M}"),
             _p("Currency", SMALL), _p("INR")],
        ],
        colWidths=[28 * mm, 52 * mm, 32 * mm, width - 112 * mm],
    )
    info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(info)

    # Cards (masked only)
    story.append(Paragraph("Card details", H2))
    card_rows = [[_p("Card", HEAD), _p("Brand", HEAD), _p("Credit limit", HEAD_R),
                  _p("Available credit", HEAD_R), _p("Status", HEAD)]]
    for c in data["cards"]:
        card_rows.append([
            _p(c["masked"]), _p(c["brand"]), _p(inr(c["limit"]), RIGHT),
            _p(inr(c["available"]), RIGHT), _p("Blocked" if c["blocked"] else "Active"),
        ])
    if len(card_rows) == 1:
        card_rows.append([_p("No cards on file."), "", "", "", ""])
    cards_table = Table(card_rows, colWidths=[40 * mm, 28 * mm, 42 * mm, 42 * mm, 28 * mm])
    cards_table.setStyle(_grid())
    story.append(cards_table)

    # Summary
    counts = data["counts"]
    story.append(Paragraph("Summary", H2))
    summary = Table(
        [
            [_p("Total spending (successful payments)"), _p(inr(data["total_spent"]), RIGHT)],
            [_p("Transactions in this period"), _p(counts["total"], RIGHT)],
            [_p("Successful"), _p(counts["success"], RIGHT)],
            [_p("Failed"), _p(counts["failed"], RIGHT)],
            [_p("Pending"), _p(counts["pending"], RIGHT)],
            [_p("Available credit today (all cards)"), _p(inr(data["available_credit"]), RIGHT)],
        ],
        colWidths=[width - 50 * mm, 50 * mm],
    )
    summary.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, STRIPE]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, LINE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary)

    # Transactions
    story.append(Paragraph("Transactions", H2))
    if not data["rows"]:
        story.append(_p("No transactions in this period.", SMALL))
    else:
        rows = [[_p("Date", HEAD), _p("Card", HEAD), _p("Description", HEAD),
                 _p("Status", HEAD), _p("Amount", HEAD_R)]]
        for r in data["rows"]:
            colour = STATUS_COLOR.get(r["status"], "#6b7280")
            rows.append([
                _p(f"{r['date']:%d %b %Y %H:%M}"),
                _p(r["card"]),
                _p(r["description"] or "-"),
                Paragraph(f'<font color="{colour}">{escape(r["status"])}</font>', BODY),
                _p(inr(r["amount"]), RIGHT),
            ])
        txn_table = Table(
            rows, colWidths=[32 * mm, 24 * mm, 66 * mm, 22 * mm, 36 * mm], repeatRows=1
        )
        txn_table.setStyle(_grid())
        story.append(txn_table)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)