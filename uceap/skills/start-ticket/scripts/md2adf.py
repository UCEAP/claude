#!/usr/bin/env python3
"""Convert a practical subset of Markdown to Atlassian Document Format (ADF).

Reads Markdown on stdin, writes an ADF `doc` node as JSON on stdout.

Block syntax:  ATX headings (# .. ######), fenced code blocks, blockquotes,
bullet lists (-, *) with 2-space nesting, ordered lists (1.), pipe tables with
a |---| delimiter row, thematic breaks (---), and paragraphs. Single newlines
inside a paragraph become hard breaks.

Inline syntax: `code`, **strong**, *em*, _em_, ~~strike~~ and [text](url).
Inline code wins over everything, so `**not bold**` stays literal. Bare URLs
are left alone -- Jira's renderer linkifies them.

Anything unrecognised is emitted as plain paragraph text rather than dropped.
"""

import json
import re
import sys

# --- inline -------------------------------------------------------------------

# Ordered by precedence. Inline code is first so its contents are never
# re-scanned for other marks.
INLINE = [
    ("code",   re.compile(r"`([^`]+)`")),
    ("strong", re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", re.S)),
    ("strike", re.compile(r"~~(?=\S)(.+?)(?<=\S)~~", re.S)),
    ("em",     re.compile(r"\*(?=\S)([^*]+?)(?<=\S)\*")),
    ("em_",    re.compile(r"(?<![A-Za-z0-9_])_(?=\S)([^_]+?)(?<=\S)_(?![A-Za-z0-9_])")),
    ("link",   re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")),
]

MARK_NAME = {"code": "code", "strong": "strong", "strike": "strike",
             "em": "em", "em_": "em"}


def text_node(text, marks):
    node = {"type": "text", "text": text}
    if marks:
        node["marks"] = list(marks)
    return node


def inline(text, marks=()):
    """Parse inline markup into a list of ADF inline nodes."""
    if not text:
        return []

    best = None
    for kind, pattern in INLINE:
        # A mark already in effect is not re-applied (no <strong><strong>).
        if kind == "link":
            if any(m["type"] == "link" for m in marks):
                continue
        elif MARK_NAME[kind] in {m["type"] for m in marks}:
            continue
        match = pattern.search(text)
        if match and (best is None or match.start() < best[1].start()):
            best = (kind, match, pattern)

    if best is None:
        return hard_breaks(text, marks)

    kind, match, _ = best
    nodes = []
    nodes += inline(text[: match.start()], marks)

    if kind == "link":
        mark = {"type": "link", "attrs": {"href": match.group(2)}}
        label = match.group(1) or match.group(2)
        nodes += inline(label, tuple(marks) + (mark,))
    elif kind == "code":
        # Code spans are literal: no further inline parsing, no hard breaks.
        nodes.append(text_node(match.group(1),
                               tuple(marks) + ({"type": "code"},)))
    else:
        nodes += inline(match.group(1),
                        tuple(marks) + ({"type": MARK_NAME[kind]},))

    nodes += inline(text[match.end():], marks)
    return nodes


def hard_breaks(text, marks):
    """Turn literal newlines into hardBreak nodes."""
    nodes = []
    for i, part in enumerate(text.split("\n")):
        if i:
            nodes.append({"type": "hardBreak"})
        if part:
            nodes.append(text_node(part, marks))
    return nodes


def paragraph(text):
    content = inline(text)
    # ADF rejects an empty paragraph content array.
    return {"type": "paragraph", "content": content or [text_node("", ())]}


# --- blocks -------------------------------------------------------------------

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^```\s*([A-Za-z0-9_+-]*)\s*$")
BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
ORDERED = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
QUOTE = re.compile(r"^>\s?(.*)$")
RULE = re.compile(r"^(?:-{3,}|\*{3,}|_{3,})$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|(?:\s*:?-{1,}:?\s*\|)+\s*$")


def split_row(line):
    """Split a table row on unescaped pipes, honouring \\| inside a cell."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    # Only an unescaped trailing pipe is a delimiter.
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]

    cells, buf, i = [], [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            buf.append("|")
            i += 2
        elif s[i] == "|":
            cells.append("".join(buf).strip())
            buf = []
            i += 1
        else:
            buf.append(s[i])
            i += 1
    cells.append("".join(buf).strip())
    return cells


def table(lines):
    header = split_row(lines[0])
    rows = [
        {"type": "tableRow",
         "content": [{"type": "tableHeader", "content": [paragraph(c)]}
                     for c in header]}
    ]
    for line in lines[2:]:
        cells = split_row(line)
        # Pad or trim so every row matches the header width.
        cells += [""] * (len(header) - len(cells))
        rows.append({
            "type": "tableRow",
            "content": [{"type": "tableCell", "content": [paragraph(c)]}
                        for c in cells[: len(header)]],
        })
    return {"type": "table",
            "attrs": {"isNumberColumnEnabled": False, "layout": "default"},
            "content": rows}


def list_block(lines, ordered):
    """Build a (possibly nested) list from consecutive list lines."""
    pattern = ORDERED if ordered else BULLET
    items = []
    i = 0
    while i < len(lines):
        match = pattern.match(lines[i])
        if match is None:  # continuation of the previous item's text
            if items:
                items[-1]["text"] += "\n" + lines[i].strip()
            i += 1
            continue
        indent = len(match.group(1).expandtabs(2))
        items.append({"indent": indent, "text": match.group(2), "children": []})
        i += 1

    base = min((it["indent"] for it in items), default=0)
    top, stack = [], []
    for item in items:
        node = {"type": "listItem", "content": [paragraph(item["text"])]}
        depth = (item["indent"] - base) // 2
        while len(stack) > depth:
            stack.pop()
        if not stack:
            top.append(node)
        else:
            parent = stack[-1]
            sub = next((c for c in parent["content"]
                        if c["type"] in ("bulletList", "orderedList")), None)
            if sub is None:
                sub = {"type": "orderedList" if ordered else "bulletList",
                       "content": []}
                if ordered:
                    sub["attrs"] = {"order": 1}
                parent["content"].append(sub)
            sub["content"].append(node)
        stack.append(node)

    block = {"type": "orderedList" if ordered else "bulletList", "content": top}
    if ordered:
        block["attrs"] = {"order": 1}
    return block


def convert(md):
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        fence = FENCE.match(line)
        if fence:
            lang = fence.group(1)
            i += 1
            body = []
            while i < n and not FENCE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # closing fence (or EOF)
            node = {"type": "codeBlock"}
            if lang:
                node["attrs"] = {"language": lang}
            if body:
                node["content"] = [{"type": "text", "text": "\n".join(body)}]
            blocks.append(node)
            continue

        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            blocks.append({"type": "heading", "attrs": {"level": level},
                           "content": inline(heading.group(2))})
            i += 1
            continue

        if RULE.match(line.strip()):
            blocks.append({"type": "rule"})
            i += 1
            continue

        # Table: a pipe row followed by a |---| delimiter row.
        if (TABLE_ROW.match(line) and i + 1 < n and TABLE_SEP.match(lines[i + 1])):
            group = [line, lines[i + 1]]
            i += 2
            while i < n and TABLE_ROW.match(lines[i]):
                group.append(lines[i])
                i += 1
            blocks.append(table(group))
            continue

        if QUOTE.match(line):
            group = []
            while i < n and QUOTE.match(lines[i]):
                group.append(QUOTE.match(lines[i]).group(1))
                i += 1
            inner = convert("\n".join(group))["content"]
            blocks.append({"type": "blockquote",
                           "content": inner or [paragraph("")]})
            continue

        for pattern, ordered in ((ORDERED, True), (BULLET, False)):
            if pattern.match(line):
                group = []
                while i < n and lines[i].strip() and not HEADING.match(lines[i]) \
                        and not FENCE.match(lines[i]) and not TABLE_ROW.match(lines[i]):
                    group.append(lines[i])
                    i += 1
                blocks.append(list_block(group, ordered))
                break
        else:
            group = []
            while i < n and lines[i].strip():
                if (HEADING.match(lines[i]) or FENCE.match(lines[i])
                        or BULLET.match(lines[i]) or ORDERED.match(lines[i])
                        or QUOTE.match(lines[i]) or TABLE_ROW.match(lines[i])
                        or RULE.match(lines[i].strip())):
                    break
                group.append(lines[i])
                i += 1
            if group:
                blocks.append(paragraph("\n".join(group)))
            else:
                i += 1
            continue
        continue

    return {"type": "doc", "version": 1,
            "content": blocks or [paragraph("")]}


if __name__ == "__main__":
    json.dump(convert(sys.stdin.read()), sys.stdout, ensure_ascii=False)
