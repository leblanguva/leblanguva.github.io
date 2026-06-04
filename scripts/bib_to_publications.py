#!/usr/bin/env python3
"""
Convert a Scopus BibTeX export into academicpages `_publications/*.md` files.

Usage:
    python3 scripts/bib_to_publications.py files/scopus.bib

Re-running overwrites only the files this script produced (those tagged with
`auto_generated: scopus`). Hand-edited entries without that tag are preserved.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_publications"

# BibTeX entry type → default academicpages publication_category key.
# We refine this using the Scopus `type` field below (e.g., to distinguish
# books from book chapters).
DEFAULT_CATEGORY = {
    "ARTICLE": "manuscripts",
    "BOOK": "books",
    "CONFERENCE": "conferences",
    "INPROCEEDINGS": "conferences",
}

# ---------- BibTeX parsing ----------

ENTRY_RE = re.compile(r"@(?P<type>[A-Za-z]+)\{(?P<key>[^,]+),(?P<body>.*?)\n\}", re.DOTALL)
FIELD_RE = re.compile(r"\s*(?P<name>[A-Za-z_]+)\s*=\s*\{(?P<value>.*?)\}\s*,?\s*\n", re.DOTALL)


def parse_bib(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    # Drop the Scopus header lines before the first @
    text = text[text.index("@"):]
    entries = []
    for m in ENTRY_RE.finditer(text):
        entry = {"_type": m.group("type").upper(), "_key": m.group("key").strip()}
        for f in FIELD_RE.finditer(m.group("body") + "\n"):
            entry[f.group("name").lower()] = f.group("value").strip()
        entries.append(entry)
    return entries


# ---------- Helpers ----------

def slugify(text: str, max_len: int = 70) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return s[:max_len].rstrip("-")


def format_authors(raw: str) -> str:
    """'Leblang, David and Smith, Michael D.' → 'Leblang, D., and M. D. Smith'"""
    authors = [a.strip() for a in raw.split(" and ")]
    formatted = []
    for i, a in enumerate(authors):
        if "," in a:
            last, given = [p.strip() for p in a.split(",", 1)]
        else:
            parts = a.rsplit(" ", 1)
            last = parts[-1]
            given = parts[0] if len(parts) > 1 else ""
        initials = " ".join(p[0] + "." for p in given.split() if p) if given else ""
        if i == 0:
            formatted.append(f"{last}, {initials}".strip(", "))
        else:
            formatted.append(f"{initials} {last}".strip())
    if len(formatted) == 1:
        return formatted[0]
    if len(formatted) == 2:
        return f"{formatted[0]}, and {formatted[1]}"
    return ", ".join(formatted[:-1]) + f", and {formatted[-1]}"


def normalize_pages(p: str) -> str:
    # Scopus uses en-dash with spaces: "720 – 728"; normalize to "720-728"
    return re.sub(r"\s*[–-]\s*", "-", p)


def yaml_escape(s: str) -> str:
    return s.replace('"', '\\"')


# ---------- Per-entry renderer ----------

def render(entry: dict) -> tuple[str, str] | None:
    typ = entry["_type"]
    category = DEFAULT_CATEGORY.get(typ)
    if category is None:
        return None

    title = entry.get("title", "").strip()
    year = entry.get("year", "").strip()
    if not title or not year:
        return None

    authors_raw = entry.get("author", "")
    authors = format_authors(authors_raw)

    venue = entry.get("journal", "").strip()
    volume = entry.get("volume", "").strip()
    number = entry.get("number", "").strip()
    pages = normalize_pages(entry.get("pages", ""))
    doi = entry.get("doi", "").strip()

    # Refine the category using Scopus's `type` field
    scopus_type = entry.get("type", "").strip().lower()
    is_chapter = (typ == "BOOK" and scopus_type == "book chapter")
    is_monograph = (typ == "BOOK" and scopus_type == "book")
    if is_chapter:
        category = "book_chapters"

    # Build citation string per entry kind
    if is_monograph:
        # "Authors (Year). *Title*."
        citation = f"{authors} ({year}). *{title}*."
        venue = ""  # the book IS the venue; suppress to avoid duplication
    elif is_chapter:
        # "Authors (Year). 'Chapter title.' In *Book Title*, pp. X-Y."
        cite_bits = [f"{authors} ({year}). \"{title}{'' if title.endswith(('?', '!', '.')) else '.'}\""]
        if venue:
            cite_bits.append(f"In *{venue}*,")
        if pages:
            cite_bits.append(f"pp. {pages}.")
        citation = " ".join(cite_bits).rstrip(",")
    else:
        # Article / review / conference paper
        cite_bits = [f"{authors} ({year}). \"{title}{'' if title.endswith(('?', '!', '.')) else '.'}\""]
        if venue:
            cite_bits.append(f"*{venue}*")
        vol_bit = ""
        if volume:
            vol_bit = volume
            if number:
                vol_bit += f"({number})"
        if vol_bit and pages:
            cite_bits.append(f"{vol_bit}: {pages}.")
        elif vol_bit:
            cite_bits.append(f"{vol_bit}.")
        elif pages:
            cite_bits.append(f"pp. {pages}.")
        citation = " ".join(cite_bits)

    # External link: prefer DOI
    paperurl = f"https://doi.org/{doi}" if doi else ""

    # Filename / permalink
    date = f"{year}-01-01"
    slug = slugify(title)
    filename = f"{year}-01-01-{slug}.md"
    permalink = f"/publication/{year}-01-01-{slug}"

    # Excerpt: short venue/pages note (omit for monographs since title == venue)
    excerpt_parts = []
    if venue and not is_monograph:
        excerpt_parts.append(f"In *{venue}*")
    if pages and not is_monograph:
        excerpt_parts.append(pages)
    excerpt = ", ".join(excerpt_parts)

    yaml = [
        "---",
        f'title: "{yaml_escape(title)}"',
        "collection: publications",
        f"category: {category}",
        f"permalink: {permalink}",
        f"date: {date}",
        f'venue: "{yaml_escape(venue)}"',
    ]
    if paperurl:
        yaml.append(f'paperurl: "{paperurl}"')
    if excerpt:
        yaml.append(f"excerpt: '{excerpt.replace(chr(39), chr(39)*2)}'")
    yaml.append(f"citation: '{citation.replace(chr(39), chr(39)*2)}'")
    yaml.append("auto_generated: scopus")
    yaml.append("---")

    body = ""
    return filename, "\n".join(yaml) + "\n" + body + "\n"


# ---------- Main ----------

def main(bib_path: str) -> None:
    entries = parse_bib(Path(bib_path))
    print(f"Parsed {len(entries)} BibTeX entries from {bib_path}")

    # Wipe previously auto-generated files (preserve hand-written ones)
    removed = 0
    for f in OUT.glob("*.md"):
        try:
            if "auto_generated: scopus" in f.read_text(encoding="utf-8"):
                f.unlink()
                removed += 1
        except Exception:
            pass
    print(f"Removed {removed} previously auto-generated files")

    OUT.mkdir(exist_ok=True)
    written = 0
    skipped = 0
    for e in entries:
        result = render(e)
        if result is None:
            skipped += 1
            continue
        filename, content = result
        (OUT / filename).write_text(content, encoding="utf-8")
        written += 1

    print(f"Wrote {written} publication files to {OUT}/")
    print(f"Skipped {skipped} entries (missing required fields or unrecognized type)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: bib_to_publications.py <path-to-bib>")
        sys.exit(1)
    main(sys.argv[1])
