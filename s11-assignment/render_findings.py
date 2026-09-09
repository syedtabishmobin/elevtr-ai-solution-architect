"""Render the Markdown findings as the required one-page submission write-up."""
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

BASE = Path(__file__).resolve().parent
BODY = ParagraphStyle("body", fontName="Helvetica", fontSize=9.2, leading=12, spaceAfter=6)
HEAD = ParagraphStyle("heading", parent=BODY, fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=5, spaceAfter=5, textColor=colors.HexColor("#153e52"))
TITLE = ParagraphStyle("title", parent=HEAD, fontSize=16, leading=20, spaceAfter=8)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.3, leading=10.6, spaceAfter=0)


def inline(text):
    return re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', escape(text))


def main():
    story = []
    blocks = (BASE / "FINDINGS.md").read_text().strip().split("\n\n")
    for block in blocks:
        if block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), TITLE))
        elif block.startswith("## "):
            story.append(Paragraph(inline(block[3:]), HEAD))
        elif block.startswith("|"):
            rows = [[Paragraph(inline(c.strip()), CELL) for c in line.strip("|").split("|")]
                    for line in block.splitlines() if not re.match(r"^\|[-| ]+\|$", line)]
            table = Table(rows, colWidths=[119, 224, 180], hAlign="LEFT")
            table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e7f0f3")),
                ("VALIGN",(0,0),(-1,-1),"TOP"), ("GRID",(0,0),(-1,-1),0.4,colors.HexColor("#b6c6cd")),
                ("LEFTPADDING",(0,0),(-1,-1),6), ("RIGHTPADDING",(0,0),(-1,-1),6),
                ("TOPPADDING",(0,0),(-1,-1),5), ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
            story += [table, Spacer(1,5)]
        else:
            story.append(Paragraph(inline(block), BODY))
    SimpleDocTemplate(str(BASE / "FINDINGS.pdf"), pagesize=A4, rightMargin=36, leftMargin=36,
                      topMargin=30, bottomMargin=30, title="Assignment 6 - Trace It, Then Gate It",
                      author="Syed Tabish Mobin").build(story)


if __name__ == "__main__":
    main()
