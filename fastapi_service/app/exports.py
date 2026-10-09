import csv
from io import BytesIO, StringIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_csv(s: dict) -> str:
    out = StringIO()
    w = csv.writer(out)

    w.writerow(["Monthly Spending Summary"])
    w.writerow(["Month", "Total Spent", "Payments"])
    for r in s["monthly"]:
        w.writerow([r["month"], r["total"], r["count"]])

    w.writerow([])
    w.writerow(["Category-wise Expenses"])
    w.writerow(["Category", "Total Spent", "Payments"])
    for r in s["categories"]:
        w.writerow([r["category"], r["total"], r["count"]])

    w.writerow([])
    w.writerow(["Credit Utilization", f"{s['utilization']['overall_percent']}%"])
    w.writerow(["Card", "Credit Limit", "Spent", "Utilization %"])
    for c in s["utilization"]["cards"]:
        w.writerow([c["card"], c["limit"], c["spent"], c["percent"]])

    return out.getvalue()


def _table(rows):
    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return t


def build_pdf(s: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="Analytics Summary")
    st = getSampleStyleSheet()
    story = [Paragraph("Card Usage Analytics Summary", st["Title"]), Spacer(1, 12)]

    story.append(Paragraph("Monthly Spending Summary", st["Heading2"]))
    story.append(_table([["Month", "Total Spent", "Payments"]]
                        + [[r["month"], f"{r['total']:,.2f}", r["count"]] for r in s["monthly"]]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Category-wise Expenses", st["Heading2"]))
    story.append(_table([["Category", "Total Spent", "Payments"]]
                        + [[r["category"], f"{r['total']:,.2f}", r["count"]] for r in s["categories"]]))
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        f"Credit Utilization (overall {s['utilization']['overall_percent']}%)", st["Heading2"]))
    story.append(_table([["Card", "Credit Limit", "Spent", "Utilization %"]]
                        + [[c["card"], f"{c['limit']:,.2f}", f"{c['spent']:,.2f}", c["percent"]]
                           for c in s["utilization"]["cards"]]))

    doc.build(story)
    return buf.getvalue()