"""HTML parsers for SFSU's server-rendered pages and DataTables JSON rows."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

DETAIL_HREF = re.compile(r"/classservices/classsearch/detail/(\d+)/([A-Z0-9]+)/(\d+)")
COURSE_LABEL = re.compile(r"^(.+?)\s*\[(\w+)\]\s*$")
DATE_RANGE = re.compile(r"\d{2}-[A-Za-z]{3}-\d{4}")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_of(node) -> str:
    return clean(node.get_text(" ")) if node is not None else ""


# ---------------------------------------------------------------- search form

def parse_search_form(html: str) -> dict:
    """Extract the form vocabularies: terms, sessions, subjects, locations, attributes."""
    soup = BeautifulSoup(html, "html.parser")

    def radios(div_id: str) -> list[dict]:
        out = []
        for inp in soup.select(f'#{div_id} input[type=radio]'):
            label = soup.find("label", {"for": inp.get("id")})
            out.append({"value": inp.get("value"),
                        "label": clean(label.get_text()) if label else inp.get("value"),
                        "checked": inp.has_attr("checked")})
        return out

    def options(select_id: str) -> list[dict]:
        sel = soup.find("select", id=select_id)
        if not sel:
            return []
        return [{"value": o.get("value"), "label": clean(o.get_text())}
                for o in sel.find_all("option") if o.get("value") not in (None, "X")]

    terms = radios("classScheduleAdvanced_term") or radios("classScheduleQuick_term")
    sessions = radios("classScheduleAdvanced_termClassCategory") or radios("classScheduleQuick_termClassCategory")
    subjects = options("classScheduleAdvanced_subject")
    locations = options("classScheduleAdvanced_location")
    attributes = options("classScheduleAdvanced_courseAttributes")
    return {"terms": terms, "sessions": sessions, "subjects": subjects,
            "locations": locations, "attributes": attributes}


# ---------------------------------------------------------------- aaData rows

def _parse_course_cell(cell_html: str) -> dict:
    soup = BeautifulSoup(cell_html, "html.parser")
    a = soup.find("a")
    label = clean(a.get_text()) if a else clean(soup.get_text())
    m = COURSE_LABEL.match(label)
    out: dict[str, Any] = {"label": label}
    if m:
        code = m.group(1).strip()
        parts = code.rsplit(" ", 1)
        out["course"] = code
        out["subject"] = parts[0].strip() if len(parts) > 1 else code
        out["catalog_number"] = parts[1].strip() if len(parts) > 1 else ""
        out["section_bracket"] = m.group(2)
    if a and a.get("href"):
        dm = DETAIL_HREF.search(a["href"])
        if dm:
            out["detail_url_path"] = a["href"]
            out["term"], out["category"], out["class_number"] = dm.group(1), dm.group(2), int(dm.group(3))
    return out


def _parse_attributes(cell_html: str) -> list[str]:
    soup = BeautifulSoup(cell_html, "html.parser")
    return [t for t in (clean(s.get_text()) for s in soup.find_all("span")) if t]


def _parse_meetings(cell_html: str) -> list[dict]:
    soup = BeautifulSoup(cell_html, "html.parser")
    meetings = []
    for row in soup.select("div.row"):
        days = row.select_one(".col-md-5")
        times = row.select_one(".col-md-7")
        loc = row.select_one(".col-md-12")
        meetings.append({"days": text_of(days) or None,
                         "times": text_of(times) or None,
                         "location": text_of(loc) or None})
    if not meetings:
        txt = clean(soup.get_text(" "))
        if txt:
            meetings.append({"days": None, "times": None, "location": txt})
    return meetings


def _parse_mode(cell_html: str) -> str:
    soup = BeautifulSoup(cell_html, "html.parser")
    txt = clean(soup.get_text(" "))
    # strip the "(see description)" helper text
    txt = re.sub(r"\(see description\).*$", "", txt).strip()
    return txt


def _parse_instructors(cell_html: str) -> list[str]:
    soup = BeautifulSoup(cell_html, "html.parser")
    divs = [clean(d.get_text()) for d in soup.find_all("div")]
    return [d if d != "To be announced" else "TBA" for d in divs if d]


def _int_or_none(s: str) -> int | None:
    s = s.strip()
    return int(s) if re.fullmatch(r"-?\d+", s) else None


def parse_aa_row(row: list[str]) -> dict:
    """Parse one ``aaData`` row (HTML cell fragments) into a normalized section.

    Column layout (SF State's own field comment):
      course | type | title | units | class_number | attributes | meetings |
      [date: summer only] | instruction_mode | instructors | [fee: CEL only] |
      seats | waitlist | section | enroll_total
    """
    cells = list(row)
    section: dict[str, Any] = {"raw_cell_count": len(cells)}
    section.update(_parse_course_cell(cells[0]))
    section["component"] = clean(BeautifulSoup(cells[1], "html.parser").get_text())
    section["title"] = clean(BeautifulSoup(cells[2], "html.parser").get_text())
    section["units"] = clean(BeautifulSoup(cells[3], "html.parser").get_text())
    section["class_number"] = _int_or_none(clean(BeautifulSoup(cells[4], "html.parser").get_text())) or section.get("class_number")
    section["attributes"] = _parse_attributes(cells[5])
    section["meetings"] = _parse_meetings(cells[6])

    idx = 7
    # optional summer-only "Date" column
    if idx < len(cells) and DATE_RANGE.search(clean(BeautifulSoup(cells[idx], "html.parser").get_text())):
        section["session_dates"] = clean(BeautifulSoup(cells[idx], "html.parser").get_text())
        idx += 1
    section["instruction_mode"] = _parse_mode(cells[idx]) if idx < len(cells) else None
    idx += 1
    section["instructors"] = _parse_instructors(cells[idx]) if idx < len(cells) else []
    idx += 1
    # optional CEL-only fee column
    if idx < len(cells) - 3 and "$" in cells[idx]:
        section["fee"] = clean(BeautifulSoup(cells[idx], "html.parser").get_text())
        idx += 1

    def cell(i: int) -> str:
        return clean(BeautifulSoup(cells[i], "html.parser").get_text()) if i < len(cells) else ""

    section["seats_remaining"] = _int_or_none(cell(idx))
    section["waitlist_remaining"] = _int_or_none(cell(idx + 1))
    section["section"] = cell(idx + 2)
    section["enrolled"] = _int_or_none(cell(idx + 3))
    return section


def parse_results_page(html: str) -> dict:
    """Metadata from the results page: term label, applied filters, as-of timestamp."""
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    asof = soup.select_one("p.class-search-date-time") or soup.find("p", string=re.compile("As of"))
    info = {}
    li = soup.select("#classschedule-search-info li")
    for el in li:
        strong = el.find("strong")
        if strong:
            key = clean(strong.get_text()).rstrip(":")
            val = clean(el.get_text()).split(":", 1)[-1].strip()
            info[key.lower().replace(" ", "_")] = val
    return {
        "heading": clean(h1.get_text()) if h1 else None,
        "as_of": clean(asof.get_text()).replace("As of ", "") if asof else None,
        "search_info": info,
    }


# ------------------------------------------------------------- section detail

def parse_section_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find(id="main") or soup
    out: dict[str, Any] = {}

    container = main.select_one(".detail-container") or main
    h = container.find("h2") or main.find(re.compile("^h[12]$"))
    if h:
        heading = clean(h.get_text())
        out["heading"] = heading
        m = re.match(r"^(.+?)\s*\[(\w+)\]\s*-\s*(.+)$", heading)
        if m:
            code = m.group(1).strip()
            parts = code.rsplit(" ", 1)
            out["course"] = code
            out["subject"] = parts[0].strip() if len(parts) > 1 else code
            out["catalog_number"] = parts[1].strip() if len(parts) > 1 else ""
            out["section_bracket"] = m.group(2)
            out["title"] = m.group(3).strip()
    txt = clean(main.get_text(" "))

    m = re.search(r"Class number:\s*(\d+)\s*\|\s*Units:\s*([\d.]+)", txt)
    if m:
        out["class_number"], out["units"] = int(m.group(1)), m.group(2)

    desc_node = main.find(string=re.compile(r"^\s*Description\s*$"))
    if desc_node:
        nxt = desc_node.find_next()
        out["description"] = clean(nxt.get_text(" ")) if nxt else None
    else:
        # fallback: 'Description' heading markup
        dh = main.find(lambda t: t.name in ("h2", "h3", "h4", "strong", "b") and clean(t.get_text()) == "Description")
        if dh and dh.find_next():
            out["description"] = clean(dh.find_next().get_text(" "))

    notes = []
    nh = main.find(lambda t: t.name in ("h2", "h3", "h4", "strong", "b") and "Class Notes" in t.get_text())
    if nh:
        for sib in nh.find_all_next():
            if sib.name in ("h2", "h3", "h4") and "Class Notes" not in sib.get_text():
                break
            if sib.name == "li":
                notes.append(clean(sib.get_text(" ")))
            if len(notes) > 20:
                break
    out["class_notes"] = notes

    meetings = []
    tbl = main.find("table")
    if tbl:
        rows = tbl.find_all("tr")
        headers = [clean(th.get_text()) for th in rows[0].find_all(["th", "td"])] if rows else []
        for tr in rows[1:]:
            vals = [clean(td.get_text(" ")) for td in tr.find_all(["td", "th"])]
            if vals:
                meetings.append(dict(zip(headers, vals, strict=False)) if headers else {"cells": vals})
    out["meetings"] = meetings

    tb = main.find(string=re.compile(r"Textbook"))
    if tb:
        nxt = tb.find_next()
        out["textbooks"] = clean(nxt.get_text(" ")) if nxt else None
    return out


# -------------------------------------------------------------------- catalog

def parse_catalog_index(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select('a[href^="/courses/"]'):
        slug = a.get("href", "").strip("/").split("/")[-1]
        if slug and slug != "courses" and slug != "courses-terms":
            out.append({"slug": slug, "label": clean(a.get_text())})
    seen, uniq = set(), []
    for e in out:
        if e["slug"] not in seen:
            seen.add(e["slug"])
            uniq.append(e)
    return uniq


def parse_courseblocks(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    courses = []
    for block in soup.select("div.courseblock"):
        title_el = block.select_one(".courseblocktitle")
        desc_el = block.select_one(".courseblockdesc")
        extra_el = block.select_one(".courseblockextra")
        title_txt = clean(title_el.get_text(" ")) if title_el else ""
        m = re.match(r"^([A-Z_ ]+?)\s+([\dA-Z]+)\s+(.+?)\s*\((.+?)\)\s*$", title_txt)
        entry: dict[str, Any] = {"title_raw": title_txt}
        if m:
            entry.update({"subject": m.group(1).strip(), "catalog_number": m.group(2),
                          "title": m.group(3).strip(), "units": m.group(4)})
        desc_txt = clean(desc_el.get_text(" ")) if desc_el else ""
        extra_txt = clean(extra_el.get_text(" ")) if extra_el else ""
        if extra_txt and desc_txt.startswith(extra_txt):
            desc_txt = desc_txt[len(extra_txt):].strip()
        entry["prerequisites"] = extra_txt or None
        entry["description"] = desc_txt or None
        link = block.find("a", href=re.compile(r"/courses/"))
        if link:
            entry["url_path"] = link.get("href")
        courses.append(entry)
    return courses


# -------------------------------------------------------------------- events

def parse_event_modal(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find(["h1", "h2", "h3", "h4"])
    return {"title": clean(title.get_text()) if title else None,
            "body": clean(soup.get_text(" "))}
