"""Render the canonical readiness reference as one printable Letter page."""
from pathlib import Path
from xml.sax.saxutils import escape

from markdown_it import MarkdownIt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

ROOT = Path(__file__).resolve().parent
INK, OLIVE = colors.HexColor("#292e26"), colors.HexColor("#515e3a")
styles = getSampleStyleSheet()
styles.add(ParagraphStyle("Body", fontName="Helvetica", fontSize=9, leading=12, textColor=INK, spaceAfter=6))
styles.add(ParagraphStyle("Section", parent=styles["Body"], fontName="Helvetica-Bold", fontSize=11, leading=13, textColor=OLIVE, spaceBefore=5))
styles.add(ParagraphStyle("TitleLocal", parent=styles["Section"], fontSize=22, leading=25, spaceAfter=8))
styles.add(ParagraphStyle("Cell", parent=styles["Body"], fontSize=8.5, leading=10.5, spaceAfter=0))
styles.add(ParagraphStyle("Footer", parent=styles["Body"], fontSize=8, alignment=TA_CENTER))


def ascii_text(value):
    return value.replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-").replace("−", "-")


def inline(token):
    parts = []
    for child in token.children or []:
        if child.type == "strong_open":
            parts.append("<b>")
        elif child.type == "strong_close":
            parts.append("</b>")
        elif child.type in ("text", "code_inline"):
            parts.append(escape(ascii_text(child.content)))
        elif child.type == "softbreak":
            parts.append(" ")
    return "".join(parts)


def main():
    tokens = MarkdownIt("commonmark").enable("table").parse((ROOT / "readiness-reference.md").read_text(encoding="utf-8"))
    story, i = [], 0
    while i < len(tokens):
        token = tokens[i]
        if token.type in ("heading_open", "paragraph_open"):
            style = "TitleLocal" if token.tag == "h1" else "Section" if token.type == "heading_open" else "Body"
            story.append(Paragraph(inline(tokens[i+1]), styles[style]))
        elif token.type == "table_open":
            rows, row = [], []
            i += 1
            while tokens[i].type != "table_close":
                if tokens[i].type == "tr_open":
                    row = []
                elif tokens[i].type == "inline":
                    row.append(Paragraph(inline(tokens[i]), styles["Cell"]))
                elif tokens[i].type == "tr_close":
                    rows.append(row)
                i += 1
            widths = [74, 104, 350] if len(rows[0]) == 3 else [160, 66, 96, 66, 140]
            table = Table(rows, colWidths=widths, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eade")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#c4c8b9")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]))
            story.extend([table, Spacer(1, 7)])
        i += 1
    doc = SimpleDocTemplate(str(ROOT / "readiness-reference.pdf"), pagesize=(612, 792),
                            leftMargin=42, rightMargin=42, topMargin=30, bottomMargin=30,
                            title="MechWarrior Revived - Readiness reference v0.3", author="MechWarrior Revived",
                            invariant=1)
    doc.build(story)
    print("Generated readiness reference from rules/readiness-reference.md.")


if __name__ == "__main__":
    main()
