# docx_sections.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Union

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph


@dataclass
class Section:
    title: str
    level: int
    # Content items preserve order: {"type": "paragraph", ...} or {"type": "table", ...}
    content: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def iter_block_items(doc: Document):
    """
    Yield Paragraph and Table objects in document order.
    """
    parent = doc.element.body
    for child in parent.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, doc)
        elif child.tag.endswith("}tbl"):
            yield Table(child, doc)


def heading_level(paragraph: Paragraph) -> Optional[int]:
    """
    Return heading level if paragraph is styled as Heading 1..9, else None.
    """
    style = paragraph.style
    if not style or not style.name:
        return None
    name = style.name.strip().lower()
    if name.startswith("heading "):
        # "Heading 1", "Heading 2", ...
        try:
            lvl = int(name.split("heading ")[1])
            return lvl
        except Exception:
            return None
    return None


def table_to_matrix(table: Table) -> List[List[str]]:
    """
    Convert a docx table to a 2D list of cell text.
    """
    matrix: List[List[str]] = []
    for row in table.rows:
        matrix.append([cell.text.strip() for cell in row.cells])
    return matrix


def parse_docx_sections(
    path: str,
    *,
    include_tables: bool = True,
    include_empty_paragraphs: bool = False,
    merge_paragraph_runs: bool = True,
) -> List[Dict[str, Any]]:
    """
    Parse a .docx into sections keyed by Word heading styles.

    Returns a list like:
    [
      {"title": "Intro", "level": 1, "content": [...]},
      {"title": "Scope", "level": 2, "content": [...]},
      ...
    ]

    Notes:
    - Everything before the first heading becomes a synthetic section:
      title="(preamble)", level=0
    - A new section starts at each Heading paragraph.
    - Content continues until the next heading of same-or-higher level, or end of doc.
    """
    doc = Document(path)

    sections: List[Section] = []
    current = Section(title="(preamble)", level=0, content=[])

    def push_current_if_has_content():
        nonlocal current
        # Keep preamble even if empty? Here: only if it has content or it's not preamble.
        if current.title != "(preamble)" or current.content:
            sections.append(current)

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text if merge_paragraph_runs else "".join(run.text for run in block.runs)
            text = (text or "").rstrip("\n")

            lvl = heading_level(block)
            if lvl is not None:
                # Start new section
                push_current_if_has_content()
                current = Section(title=text.strip(), level=lvl, content=[])
                continue

            if not include_empty_paragraphs and not text.strip():
                continue

            current.content.append(
                {
                    "type": "paragraph",
                    "text": text.strip() if text is not None else "",
                    "style": (block.style.name if block.style else None),
                }
            )

        elif isinstance(block, Table) and include_tables:
            current.content.append(
                {
                    "type": "table",
                    "rows": table_to_matrix(block),
                }
            )

    # finalize
    push_current_if_has_content()

    return [s.to_dict() for s in sections]


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python docx_sections.py <file.docx>")
        raise SystemExit(2)

    sections = parse_docx_sections(sys.argv[1])
    print(json.dumps(sections, ensure_ascii=False, indent=2))
