"""Network-free DOCX field operations shared by the form service and tests."""

import io
import re
from typing import Iterator, Mapping
from zipfile import ZipFile

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from lxml import etree


FIELD_PATTERN = re.compile(r"\{\{([^{}]+)\}\}([.\u2026]*)")
TEXT_TAGS = {qn("w:t"), qn("w:tab"), qn("w:br"), qn("w:cr")}
STORY_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml",
}


def iter_paragraph_elements(document) -> Iterator:
    """Include nested tables, without processing merged cells twice.

    Only existing header/footer parts are read; accessing section.header would
    otherwise create new parts in a document that did not have them.
    """
    yield from document.element.body.iter(qn("w:p"))
    for part in document.part.related_parts.values():
        if part.content_type in STORY_TYPES:
            yield from part.element.iter(qn("w:p"))


def _text_atoms(paragraph) -> list[tuple]:
    """Read text in runs and hyperlinks, but not text in nested paragraphs."""
    atoms = []

    def visit(element):
        for child in element:
            if child.tag == qn("w:p"):
                continue
            if child.tag in TEXT_TAGS:
                text = child.text or "" if child.tag == qn("w:t") else (
                    "\t" if child.tag == qn("w:tab") else "\n"
                )
                atoms.append((child, text))
            else:
                visit(child)

    visit(paragraph)
    return atoms


def extract_docx_fields(content: bytes) -> list[str]:
    document = Document(io.BytesIO(content))
    fields = {}
    for paragraph in iter_paragraph_elements(document):
        text = "".join(value for _, value in _text_atoms(paragraph))
        for match in FIELD_PATTERN.finditer(text):
            fields.setdefault(match.group(1), None)
    return list(fields)


def _set_atom_text(atom, value: str):
    if atom.tag != qn("w:t"):
        replacement = OxmlElement("w:t")
        atom.addprevious(replacement)
        atom.getparent().remove(atom)
        atom = replacement
    chunks = re.split(r'([\n\t])', value.replace('\r\n', '\n').replace('\r', '\n'))
    atom.text = chunks[0]
    if chunks[0].startswith(" ") or chunks[0].endswith(" "):
        atom.set(qn("xml:space"), "preserve")
    tail = atom
    for chunk in chunks[1:]:
        if chunk in ('\n', '\t'):
            node = OxmlElement('w:br' if chunk == '\n' else 'w:tab')
        else:
            node = OxmlElement('w:t')
            node.text = chunk
            if chunk.startswith(' ') or chunk.endswith(' '):
                node.set(qn('xml:space'), 'preserve')
        tail.addnext(node)
        tail = node


def replace_paragraph_fields(paragraph, values: Mapping[str, str], min_dots: int = 1) -> int:
    """Replace spans only, leaving run properties, drawings and labels intact.

    Work right to left against original offsets. Values are inserted literally,
    so backslashes and placeholder-like text are never interpreted as regexes
    or substituted again. Repeated occurrences are all filled.
    """
    atoms = _text_atoms(paragraph)
    text = "".join(value for _, value in atoms)
    offsets = []
    cursor = 0
    for atom, value in atoms:
        offsets.append((atom, cursor, cursor + len(value)))
        cursor += len(value)

    count = 0
    for match in reversed(list(FIELD_PATTERN.finditer(text))):
        field = match.group(1)
        if field not in values:
            continue
        value = values[field]
        dots = match.group(2)
        # Do not append punctuation to a plain token (e.g. number of copies).
        # Preserve the old dotted-line behavior only for actual dotted fields.
        if not value:
            replacement = "." * len(match.group(0))
        elif dots:
            replacement = value + "." * max(min_dots, len(match.group(0)) - len(value))
        else:
            replacement = value

        touched = [(atom, start, end) for atom, start, end in offsets
                   if start < match.end() and end > match.start()]
        for index, (atom, start, end) in enumerate(touched):
            # Later matches may already have changed the suffix of this atom.
            current = atom.text or "" if atom.tag == qn("w:t") else (
                "\t" if atom.tag == qn("w:tab") else "\n"
            )
            local_start = max(0, match.start() - start)
            local_end = min(end, match.end()) - start
            new_text = current[:local_start] + (replacement if index == 0 else "") + current[local_end:]
            _set_atom_text(atom, new_text)
        count += 1
    return count


def fill_docx_fields(content: bytes, values: Mapping[str, str], min_dots: int = 1) -> bytes:
    document = Document(io.BytesIO(content))
    parts = [document.part] + [part for part in document.part.related_parts.values()
                               if part.content_type in STORY_TYPES]
    changed_parts = {}
    for part in parts:
        changed = False
        for paragraph in part.element.iter(qn("w:p")):
            if replace_paragraph_fields(paragraph, values, min_dots):
                changed = True
        if changed:
            changed_parts[str(part.partname).lstrip('/')] = etree.tostring(
                part.element, encoding='UTF-8', xml_declaration=True, standalone=True,
            )
    if not changed_parts:
        return content
    output = io.BytesIO()
    # Copy untouched package entries verbatim (including images and metadata),
    # rather than asking python-docx to reserialize every unrelated XML part.
    with ZipFile(io.BytesIO(content)) as original, ZipFile(output, 'w') as result:
        result.comment = original.comment
        for entry in original.infolist():
            result.writestr(entry, changed_parts.get(entry.filename, original.read(entry.filename)))
    return output.getvalue()
