"""
Converts RESEARCH_ANALYSIS_AND_CRITICAL_DISCUSSION.md (and VIVA_VOCE_GUIDE.md)
into richly formatted Microsoft Word (.docx) and PDF documents.
"""

from __future__ import annotations
import re
import sys
import zipfile
from pathlib import Path
from typing import List, Sequence, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _latex_to_unicode(expr: str) -> str:
    """Convert LaTeX math expressions into clean, readable Unicode mathematical notation."""
    s = expr.strip()

    # Specific full display/inline equations in RESEARCH_ANALYSIS_AND_CRITICAL_DISCUSSION.md
    s = re.sub(
        r"\\frac\{\\sqrt\{\(x_n\s*-\s*x_g\)\^2\s*\+\s*\(y_n\s*-\s*y_g\)\^2\}\s*\+\s*\|x_n\s*-\s*x_g\|\s*\+\s*\|y_n\s*-\s*y_g\|\}\{2\}",
        "[√((xₙ − x₉)² + (yₙ − y₉)²) + |xₙ − x₉| + |yₙ − y₉|] / 2",
        s,
    )
    s = re.sub(r"\\ln\\left\(1\s*\+\s*e\^\{\\frac\{d\}\{D\}\}\\right\)", "ln(1 + e^(d/D))", s)
    s = re.sub(r"\\ln\\left\(1\s*\+\s*e\^\{d/D\}\\right\)", "ln(1 + e^(d/D))", s)
    s = re.sub(r"\\ln\(1\s*\+\s*e\^\{d/D\}\)", "ln(1 + e^(d/D))", s)
    s = re.sub(r"\\ln\(1\+e\^\{d/D\}\)", "ln(1 + e^(d/D))", s)
    s = re.sub(r"\\omega_\{\\text\{eff\}\}", "ω_eff", s)
    s = re.sub(r"\\vec\{AB\}\s*\\times\s*\\vec\{BC\}", "AB⃗ × BC⃗", s)
    s = re.sub(r"\\overline\{AC\}", "AC̅", s)

    # \text{...}
    s = re.sub(r"\\text\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\mathrm\{([^}]*)\}", r"\1", s)

    # \frac{a}{b}
    s = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", s)

    # \sqrt{...}
    s = re.sub(r"\\sqrt\{([^}]+)\}", r"√(\1)", s)
    s = s.replace("√(2)", "√2")

    # Greek & operators
    replacements = [
        (r"\omega", "ω"),
        (r"\theta", "θ"),
        (r"\ge", "≥"),
        (r"\le", "≤"),
        (r"\times", "×"),
        (r"\cdot", "·"),
        (r"\to", "→"),
        (r"\rightarrow", "→"),
        (r"\approx", "≈"),
        (r"\pm", "±"),
        (r"\in", "∈"),
        (r"\dots", "…"),
        (r"\sim", "~"),
        (r"\ln", "ln"),
        (r"\exp", "exp"),
        (r"\min", "min"),
        (r"\max", "max"),
        (r"\left", ""),
        (r"\right", ""),
        (r"\quad", "   "),
        (r"\,", " "),
        (r"\%", "%"),
        (r"\{", "{"),
        (r"\}", "}"),
        (r"^\circ", "°"),
        (r"^2", "²"),
        (r"^0", "⁰"),
        (r"_n", "ₙ"),
        (r"_s", "ₛ"),
        (r"_k", "ₖ"),
        (r"_i", "ᵢ"),
        (r"_j", "ⱼ"),
        (r"_1", "₁"),
        (r"_2", "₂"),
        (r"_3", "₃"),
        (r"_4", "₄"),
        (r"_0", "₀"),
        (r"_E", "_E"),
        (r"_M", "_M"),
        (r"_H", "_H"),
        (r"_g", "_g"),
        (r"^{d/D}", "^(d/D)"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)

    # Clean up remaining braces around superscripts/subscripts
    s = re.sub(r"\^\{([^}]+)\}", r"^(\1)", s)
    s = re.sub(r"_\{([^}]+)\}", r"_\1", s)
    return s


def preprocess_markdown_line(line: str) -> str:
    r"""Replace inline $...$ math and escaped characters (\*) in a Markdown line."""
    # Replace escaped asterisks \* with a placeholder so bold/italic parser doesn't consume them
    line = line.replace(r"\*", "AST_ESC_TOKEN")

    # Replace inline $...$ math
    def _math_repl(match: re.Match) -> str:
        return _latex_to_unicode(match.group(1))

    line = re.sub(r"\$([^$]+)\$", _math_repl, line)
    return line


def parse_inline_runs(
    text: str,
    base_size_half_pt: int = 21,
    base_bold: bool = False,
    base_italic: bool = False,
    base_color: str = "1A1A1A",
) -> str:
    """
    Parse inline Markdown (**bold**, *italic*, `code`) into WordprocessingML <w:r> elements.
    """
    text = preprocess_markdown_line(text)

    # Tokenize by `code`, **bold**, *italic*
    pattern = re.compile(r"(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)")
    parts = pattern.split(text)

    runs_xml: List[str] = []
    for part in parts:
        if not part:
            continue
        is_code = False
        is_bold = base_bold
        is_italic = base_italic
        color = base_color
        content = part

        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            is_code = True
            content = part[1:-1]
            color = "0F4C81"
        elif part.startswith("**") and part.endswith("**") and len(part) >= 4:
            is_bold = True
            content = part[2:-2]
        elif part.startswith("*") and part.endswith("*") and len(part) >= 2:
            is_italic = True
            content = part[1:-1]

        content = content.replace("AST_ESC_TOKEN", "*")
        if not content:
            continue

        rpr: List[str] = []
        if is_code:
            rpr.append('<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>')
            rpr.append(f'<w:sz w:val="{max(16, base_size_half_pt - 2)}"/>')
            rpr.append(f'<w:szCs w:val="{max(16, base_size_half_pt - 2)}"/>')
            rpr.append('<w:shd w:val="clear" w:color="auto" w:fill="F1F5F9"/>')
        else:
            rpr.append('<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>')
            rpr.append(f'<w:sz w:val="{base_size_half_pt}"/>')
            rpr.append(f'<w:szCs w:val="{base_size_half_pt}"/>')

        if is_bold:
            rpr.append("<w:b/>")
        if is_italic:
            rpr.append("<w:i/>")
        if color:
            rpr.append(f'<w:color w:val="{color}"/>')

        runs_xml.append(
            f"<w:r><w:rPr>{''.join(rpr)}</w:rPr>"
            f'<w:t xml:space="preserve">{_xml_escape(content)}</w:t></w:r>'
        )

    return "".join(runs_xml)


def build_table_xml(table_lines: Sequence[str]) -> str:
    """Convert Markdown table lines into a styled WordprocessingML <w:tbl>."""
    parsed_rows: List[List[str]] = []
    alignments: List[str] = []

    for idx, raw in enumerate(table_lines):
        stripped = raw.strip()
        if stripped.startswith("|"):
            stripped = stripped[1:]
        if stripped.endswith("|"):
            stripped = stripped[:-1]
        cells = [c.strip() for c in stripped.split("|")]

        # Separator row e.g. | :--- | :---: |
        if idx == 1 and all(re.match(r"^:?-+:?$", c.replace(" ", "")) for c in cells):
            for c in cells:
                c_clean = c.replace(" ", "")
                if c_clean.startswith(":") and c_clean.endswith(":"):
                    alignments.append("center")
                elif c_clean.endswith(":"):
                    alignments.append("right")
                else:
                    alignments.append("left")
            continue

        parsed_rows.append(cells)

    if not parsed_rows:
        return ""

    num_cols = max(len(r) for r in parsed_rows)
    if not alignments:
        alignments = ["center"] * num_cols

    tbl_xml: List[str] = [
        "<w:tbl>"
        "<w:tblPr>"
        '<w:tblW w:w="5000" w:type="pct"/>'
        "<w:tblBorders>"
        '<w:top w:val="single" w:sz="10" w:space="0" w:color="1F4E79"/>'
        '<w:bottom w:val="single" w:sz="10" w:space="0" w:color="1F4E79"/>'
        '<w:left w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        '<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
        "</w:tblBorders>"
        "<w:tblCellMar>"
        '<w:top w:w="70" w:type="dxa"/>'
        '<w:bottom w:w="70" w:type="dxa"/>'
        '<w:left w:w="90" w:type="dxa"/>'
        '<w:right w:w="90" w:type="dxa"/>'
        "</w:tblCellMar>"
        "</w:tblPr>"
    ]

    for r_idx, row in enumerate(parsed_rows):
        is_header = r_idx == 0
        tr_pr = "<w:trPr><w:tblHeader/></w:trPr>" if is_header else ""
        tbl_xml.append(f"<w:tr>{tr_pr}")

        for c_idx in range(num_cols):
            cell_text = row[c_idx] if c_idx < len(row) else ""
            align = "center" if is_header else (alignments[c_idx] if c_idx < len(alignments) else "center")

            if is_header:
                shd = '<w:shd w:val="clear" w:color="auto" w:fill="1F4E79"/>'
                runs = parse_inline_runs(
                    cell_text,
                    base_size_half_pt=17,
                    base_bold=True,
                    base_color="FFFFFF",
                )
            else:
                fill = "F8FAFC" if r_idx % 2 == 0 else "FFFFFF"
                # Highlight Adaptive A* row slightly
                if "Adaptive A" in cell_text or ("Adaptive A" in " ".join(row)):
                    fill = "EFF6FF"
                shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
                runs = parse_inline_runs(
                    cell_text,
                    base_size_half_pt=17,
                    base_bold=False,
                    base_color="1A1A1A",
                )

            tbl_xml.append(
                f"<w:tc>"
                f"<w:tcPr>{shd}<w:vAlign w:val=\"center\"/></w:tcPr>"
                f"<w:p><w:pPr><w:jc w:val=\"{align}\"/><w:spacing w:before=\"30\" w:after=\"30\"/></w:pPr>"
                f"{runs}</w:p>"
                f"</w:tc>"
            )
        tbl_xml.append("</w:tr>")

    tbl_xml.append("</w:tbl>")
    # Add a small spacing paragraph after the table
    tbl_xml.append('<w:p><w:pPr><w:spacing w:before="40" w:after="80"/></w:pPr></w:p>')
    return "".join(tbl_xml)


def convert_markdown_to_docx(md_path: Path, docx_path: Path) -> None:
    """Parse a Markdown file and generate a rich, native OpenXML (.docx) file."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    body_elements: List[str] = []

    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i]
        stripped = raw_line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # Horizontal rule ---
        if re.match(r"^-{3,}$", stripped):
            body_elements.append(
                "<w:p><w:pPr>"
                '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="CBD5E1"/></w:pBdr>'
                '<w:spacing w:before="80" w:after="120"/>'
                "</w:pPr></w:p>"
            )
            i += 1
            continue

        # Display math block $$ ... $$
        if stripped.startswith("$$"):
            eq_content = stripped
            if stripped.endswith("$$") and len(stripped) > 4:
                eq_content = stripped[2:-2]
                i += 1
            else:
                parts = [stripped[2:]]
                i += 1
                while i < n and not lines[i].strip().endswith("$$"):
                    parts.append(lines[i].strip())
                    i += 1
                if i < n:
                    parts.append(lines[i].strip()[:-2])
                    i += 1
                eq_content = " ".join(parts)

            unicode_eq = _latex_to_unicode(eq_content)
            body_elements.append(
                "<w:p><w:pPr>"
                '<w:jc w:val="center"/>'
                '<w:shd w:val="clear" w:color="auto" w:fill="F8FAFC"/>'
                '<w:spacing w:before="100" w:after="100"/>'
                '<w:ind w:left="360" w:right="360"/>'
                "</w:pPr>"
                '<w:r><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>'
                '<w:b/><w:i/><w:sz w:val="21"/><w:color w:val="0F172A"/></w:rPr>'
                f'<w:t xml:space="preserve">{_xml_escape(unicode_eq)}</w:t></w:r></w:p>'
            )
            continue

        # Markdown Table
        if stripped.startswith("|") and "|" in stripped[1:]:
            table_block: List[str] = []
            while i < n and lines[i].strip().startswith("|"):
                table_block.append(lines[i])
                i += 1
            body_elements.append(build_table_xml(table_block))
            continue

        # Headings #, ##, ###, ####
        h_match = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if h_match:
            level = len(h_match.group(1))
            h_text = h_match.group(2).strip()
            if level == 1:
                runs = parse_inline_runs(h_text, base_size_half_pt=32, base_bold=True, base_color="0F172A")
                body_elements.append(
                    "<w:p><w:pPr>"
                    '<w:jc w:val="left"/>'
                    '<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="4" w:color="1F4E79"/></w:pBdr>'
                    '<w:spacing w:before="120" w:after="180"/>'
                    f"</w:pPr>{runs}</w:p>"
                )
            elif level == 2:
                runs = parse_inline_runs(h_text, base_size_half_pt=26, base_bold=True, base_color="1F4E79")
                body_elements.append(
                    "<w:p><w:pPr>"
                    '<w:jc w:val="left"/>'
                    '<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="2" w:color="93C5FD"/></w:pBdr>'
                    '<w:spacing w:before="220" w:after="100"/>'
                    f"</w:pPr>{runs}</w:p>"
                )
            elif level == 3:
                runs = parse_inline_runs(h_text, base_size_half_pt=23, base_bold=True, base_color="1E3A8A")
                body_elements.append(
                    "<w:p><w:pPr>"
                    '<w:jc w:val="left"/>'
                    '<w:spacing w:before="160" w:after="80"/>'
                    f"</w:pPr>{runs}</w:p>"
                )
            else:
                runs = parse_inline_runs(h_text, base_size_half_pt=21, base_bold=True, base_color="334155")
                body_elements.append(
                    "<w:p><w:pPr>"
                    '<w:jc w:val="left"/>'
                    '<w:spacing w:before="120" w:after="60"/>'
                    f"</w:pPr>{runs}</w:p>"
                )
            i += 1
            continue

        # Bullet or Numbered List Item
        list_match = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", raw_line)
        if list_match:
            indent_spaces = len(list_match.group(1))
            marker = list_match.group(2)
            item_text = list_match.group(3).strip()

            # Continuation lines that are indented underneath this bullet (and not new bullets/equations/headings)
            i += 1
            while i < n:
                next_raw = lines[i]
                next_strip = next_raw.strip()
                if (
                    not next_strip
                    or next_strip.startswith("#")
                    or next_strip.startswith("$$")
                    or next_strip.startswith("|")
                    or re.match(r"^-{3,}$", next_strip)
                    or re.match(r"^(\s*)([-*]|\d+\.)\s+", next_raw)
                ):
                    break
                item_text += " " + next_strip
                i += 1

            nest_level = 1 if indent_spaces >= 2 else 0
            left_twips = 360 + nest_level * 360
            hanging_twips = 240

            prefix = "•  " if marker in ("-", "*") else f"{marker} "
            prefix_run = (
                '<w:r><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>'
                '<w:b/><w:sz w:val="21"/><w:color w:val="1F4E79"/></w:rPr>'
                f'<w:t xml:space="preserve">{_xml_escape(prefix)}</w:t></w:r>'
            )
            runs = parse_inline_runs(item_text, base_size_half_pt=21, base_color="1A1A1A")
            body_elements.append(
                "<w:p><w:pPr>"
                '<w:jc w:val="both"/>'
                f'<w:ind w:left="{left_twips}" w:hanging="{hanging_twips}"/>'
                '<w:spacing w:before="40" w:after="70" w:line="276" w:lineRule="auto"/>'
                f"</w:pPr>{prefix_run}{runs}</w:p>"
            )
            continue

        # Standard Paragraph (accumulate contiguous lines)
        para_lines = [stripped]
        i += 1
        while i < n:
            next_raw = lines[i]
            next_strip = next_raw.strip()
            if (
                not next_strip
                or next_strip.startswith("#")
                or next_strip.startswith("$$")
                or next_strip.startswith("|")
                or re.match(r"^-{3,}$", next_strip)
                or re.match(r"^(\s*)([-*]|\d+\.)\s+", next_raw)
            ):
                break
            para_lines.append(next_strip)
            i += 1

        para_text = " ".join(para_lines)
        runs = parse_inline_runs(para_text, base_size_half_pt=21, base_color="1A1A1A")
        body_elements.append(
            "<w:p><w:pPr>"
            '<w:jc w:val="both"/>'
            '<w:spacing w:before="40" w:after="100" w:line="276" w:lineRule="auto"/>'
            f"</w:pPr>{runs}</w:p>"
        )

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        + "".join(body_elements)
        + '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080"/></w:sectPr>'
        "</w:body></w:document>"
    )

    styles_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:docDefaults>"
        "<w:rPrDefault><w:rPr>"
        '<w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>'
        '<w:sz w:val="21"/><w:szCs w:val="21"/>'
        '<w:lang w:val="en-US"/>'
        "</w:rPr></w:rPrDefault>"
        "</w:docDefaults>"
        "</w:styles>"
    )

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
        "</Types>"
    )

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )

    doc_rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
        "</Relationships>"
    )

    docx_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("word/_rels/document.xml.rels", doc_rels_xml)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("word/document.xml", document_xml)

    print(f"[OK] Generated Word DOCX -> {docx_path} ({docx_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    md_file = PROJECT_ROOT / "RESEARCH_ANALYSIS_AND_CRITICAL_DISCUSSION.md"
    out_root_docx = PROJECT_ROOT / "RESEARCH_ANALYSIS_AND_CRITICAL_DISCUSSION.docx"
    out_report_docx = PROJECT_ROOT / "report" / "RESEARCH_ANALYSIS_AND_CRITICAL_DISCUSSION.docx"

    convert_markdown_to_docx(md_file, out_root_docx)
    convert_markdown_to_docx(md_file, out_report_docx)

    viva_md = PROJECT_ROOT / "VIVA_VOCE_GUIDE.md"
    if viva_md.exists():
        convert_markdown_to_docx(viva_md, PROJECT_ROOT / "VIVA_VOCE_GUIDE.docx")
