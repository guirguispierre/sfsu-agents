"""Core tool functions — shared by the CLI and the MCP server.

Every function returns an evidence envelope (see envelope.py). Functions raise
no exceptions for upstream/parse failures; they return ``ok=False`` envelopes.
"""

from __future__ import annotations

import re
import time
from typing import Any

import requests

from . import client as client_mod
from . import envelope, parsers
from . import terms as terms_mod

SOURCES = {
    "class_search": "https://webapps.sfsu.edu/public/classservices/classsearch",
    "results_json": "https://webapps.sfsu.edu/public/classservices/searchresultsjson",
    "bulletin": "https://bulletin.sfsu.edu/courses/",
    "directory": "https://webapps.sfsu.edu/public/directorysearch/ (Algolia index prod_DIRECTORYSEARCH)",
    "calendar": "https://webapps.sfsu.edu/public/webcalendar",
}


def _client() -> client_mod.SfsuClient:
    return client_mod.SfsuClient()


def _default_term(c: client_mod.SfsuClient) -> int | None:
    """The form's checked (current) term code."""
    try:
        form = parsers.parse_search_form(c.search_form())
    except Exception:
        return None
    for t in form["terms"]:
        if t.get("checked") and str(t["value"]).isdigit():
            return int(t["value"])
    for t in form["terms"]:
        if str(t["value"]).isdigit():
            return int(t["value"])
    return None


def _try(fn, *, kind="upstream", sources=()):
    try:
        return fn()
    except requests.HTTPError as e:
        code = e.response.status_code if e.response is not None else "?"
        return envelope.err(f"HTTP {code}: {e}", kind=kind, sources=sources)
    except requests.RequestException as e:
        return envelope.err(f"network error: {e}", kind="network", sources=sources)
    except Exception as e:  # parse/contract changes
        return envelope.err(f"{type(e).__name__}: {e}", kind="parse", sources=sources)


# ------------------------------------------------------------------ metadata

def list_terms(client: client_mod.SfsuClient | None = None) -> dict:
    """Terms (with codes and names) plus session categories from the live search form."""
    c = client or _client()
    src = [SOURCES["class_search"]]

    def run():
        form = parsers.parse_search_form(c.search_form())
        terms = []
        for t in form["terms"]:
            code = t["value"]
            name = terms_mod.code_to_name(code)
            terms.append({"code": code, "name": name or t["label"], "label": t["label"]})
        sessions = []
        seen = set()
        for s in form["sessions"]:
            val = s["value"] or ""
            if ":" not in val:
                continue
            term_code, cat = val.split(":", 1)
            if not term_code or term_code in seen and cat in {x["category"] for x in sessions if x["term_code"] == term_code}:
                pass
            if (term_code, cat) in seen:
                continue
            seen.add((term_code, cat))
            sessions.append({
                "term_code": term_code,
                "term_name": terms_mod.code_to_name(term_code),
                "category": cat,
                "session": terms_mod.SESSION_LABELS.get(cat, cat),
                "form_label": s["label"],
            })
        return envelope.ok({"terms": terms, "sessions": sessions}, sources=src)

    return _try(run, sources=src)


def list_subjects(client: client_mod.SfsuClient | None = None) -> dict:
    """All subject codes (e.g. CSC) offered by the class schedule."""
    c = client or _client()
    src = [SOURCES["class_search"]]

    def run():
        form = parsers.parse_search_form(c.search_form())
        return envelope.ok({"subjects": form["subjects"], "count": len(form["subjects"])}, sources=src)

    return _try(run, sources=src)


def list_locations(client: client_mod.SfsuClient | None = None) -> dict:
    """Building/location codes usable as the ``location`` search filter."""
    c = client or _client()
    src = [SOURCES["class_search"]]

    def run():
        form = parsers.parse_search_form(c.search_form())
        locs = [loc for loc in form["locations"] if loc["value"]]
        return envelope.ok({"locations": locs, "count": len(locs)}, sources=src)

    return _try(run, sources=src)


def list_attributes(client: client_mod.SfsuClient | None = None) -> dict:
    """Course-attribute (GE) codes usable as the ``attributes`` search filter."""
    c = client or _client()
    src = [SOURCES["class_search"]]

    def run():
        form = parsers.parse_search_form(c.search_form())
        attrs = [a for a in form["attributes"] if a["value"]]
        return envelope.ok({"attributes": attrs, "count": len(attrs)}, sources=src)

    return _try(run, sources=src)


# ------------------------------------------------------------- class search

def search_classes(
    query: str | None = None,
    *,
    subject: str | None = None,
    term: int | str | None = None,
    category: str | None = None,
    open_university: bool | None = None,
    remaining_seats: bool | None = None,
    days: list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    instructor_last_name: str | None = None,
    attributes: str | None = None,
    catalog_number: str | None = None,
    online_async: bool | None = None,
    online_sync: bool | None = None,
    online_bichronous: bool | None = None,
    hybrid: bool | None = None,
    in_person: bool | None = None,
    client: client_mod.SfsuClient | None = None,
) -> dict:
    """Search the live class schedule.

    Two modes matching the site's forms:
      * quick  — ``query`` like ``"CSC"`` or ``"CSC 413"`` (filters below are ignored by the site)
      * advanced — ``subject="CSC"`` plus any filter combination
    ``term`` accepts ``2267``, ``"2267:REG"``, or ``"Fall 2026"``. Default: the form's checked term.
    """
    c = client or _client()
    used_query = query or (subject if subject and not any([
        catalog_number, instructor_last_name, attributes, days, start_time, end_time,
        location, remaining_seats, online_async, online_sync, online_bichronous,
        hybrid, in_person]) else None)

    def run():
        params: dict[str, Any] = {}
        term_code, cat = terms_mod.resolve_session_pair(term, category)
        defaulted = term_code is None
        if defaulted:
            term_code = _default_term(c)
        if term_code is not None:
            params["term"] = term_code
        params["classCategory"] = cat
        if open_university is not None:
            params["openUniversity"] = "y" if open_university else "n"

        if used_query:
            params["searchFor"] = used_query
        else:
            if subject:
                params["subject"] = subject
            if catalog_number:
                params["categoryNumber"] = catalog_number
            if instructor_last_name:
                params["instructorLastName"] = instructor_last_name
            if attributes:
                params["courseAttributes"] = attributes
            if remaining_seats:
                params["remainingSeats"] = "y"
            if online_async:
                params["onlineAsynchronous"] = "y"
            if online_sync:
                params["onlineSynchronous"] = "y"
            if online_bichronous:
                params["onlineBichronous"] = "y"
            if hybrid:
                params["hybridClass"] = "y"
            if in_person:
                params["inPersonClass"] = "y"
            if location:
                params["location"] = location
            if start_time:
                params["startTime"] = start_time
            if end_time:
                params["endTime"] = end_time
            for i, d in enumerate(days or []):
                params[f"meetingDays[{i}]"] = d

        url, html = c.bind_search(params)
        meta = parsers.parse_results_page(html)
        data = c.search_results_json()
        rows = [parsers.parse_aa_row(r) for r in data.get("aaData", [])]
        lims = [
            "Enrollment/seat counts are snapshots at the 'as_of' timestamp, refreshed periodically by SFSU.",
            "Quick-search mode (searchFor) ignores the advanced filters — this mirrors the site.",
        ]
        if defaulted and term_code is not None:
            lims.append(f"No term supplied: used the form's current term ({term_code} = {terms_mod.code_to_name(term_code)}).")
        elif term_code is None:
            lims.append("No term supplied and none could be resolved; upstream may 500.")
        return envelope.ok(
            {"query_params": params, "bound_url": url, "as_of": meta.get("as_of"),
             "heading": meta.get("heading"), "count": len(rows), "sections": rows},
            sources=[url, SOURCES["results_json"]], limitations=lims)

    return _try(run, sources=[SOURCES["class_search"]])


def section_detail(class_number: int | str, term: int | str | None = None,
                   category: str | None = None,
                   client: client_mod.SfsuClient | None = None) -> dict:
    """Full detail page for one section: description, prereqs, notes, meetings, textbooks."""
    c = client or _client()
    term_code, cat = terms_mod.resolve_session_pair(term, category)
    if term_code is None:
        return envelope.err("term is required for section detail (e.g. 2267 or 'Fall 2026')", kind="input",
                            sources=[SOURCES["class_search"]])

    def run():
        html = c.section_detail(term_code, cat, class_number)
        detail = parsers.parse_section_detail(html)
        detail["term"], detail["category"], detail["class_number"] = term_code, cat, int(class_number)
        detail["url"] = f"{client_mod.WEB_BASE}/public/classservices/classsearch/detail/{term_code}/{cat}/{class_number}"
        return envelope.ok(detail, sources=[detail["url"]],
                           limitations=["Parsed from a server-rendered page; field presence varies by section."])

    return _try(run, sources=[SOURCES["class_search"]])


# -------------------------------------------------------------- bulletin

def catalog_subjects(client: client_mod.SfsuClient | None = None) -> dict:
    """Departments/subjects in the Bulletin (course catalog)."""
    c = client or _client()
    src = [SOURCES["bulletin"]]

    def run():
        subs = parsers.parse_catalog_index(c.catalog_index())
        return envelope.ok({"subjects": subs, "count": len(subs)}, sources=src)

    return _try(run, sources=src)


def catalog_courses(subject: str, client: client_mod.SfsuClient | None = None) -> dict:
    """All catalog courses for a subject (descriptions + prerequisites from the Bulletin)."""
    c = client or _client()
    slug = subject.strip().lower().replace(" ", "_")
    url = f"{client_mod.BULLETIN_BASE}/courses/{slug}/"

    def run():
        courses = parsers.parse_courseblocks(c.catalog_subject_page(slug))
        return envelope.ok({"subject": subject.upper(), "count": len(courses), "courses": courses},
                           sources=[url])

    return _try(run, sources=[url])


def course_info(course: str, client: client_mod.SfsuClient | None = None) -> dict:
    """One catalog course by code, e.g. ``'CSC 413'`` (subject page scanned)."""
    c = client or _client()
    m = re.match(r"^\s*([A-Za-z_ ]+?)\s+([A-Za-z]?\d[\dA-Za-z]*)\s*$", course.strip())
    if not m:
        return envelope.err(f"could not parse course code: {course!r}", kind="input",
                            sources=[SOURCES["bulletin"]])
    subj, num = m.group(1).strip(), m.group(2)
    slug = subj.lower().replace(" ", "_")
    url = f"{client_mod.BULLETIN_BASE}/courses/{slug}/"

    def run():
        courses = parsers.parse_courseblocks(c.catalog_subject_page(slug))
        want = f"{subj.upper()} {num}".replace("  ", " ")
        hits = [x for x in courses
                if f"{x.get('subject','')} {x.get('catalog_number','')}".upper() == want.upper()]
        if not hits:
            return envelope.err(f"{want} not found in catalog subject {subj.upper()}",
                                kind="not_found", sources=[url],
                                unknowns=["Course may not exist in the current Bulletin, or the code has a suffix."])
        return envelope.ok(hits[0], sources=[url],
                           limitations=["Catalog data is the Bulletin (policy view) — not term-specific offerings."])

    return _try(run, sources=[url])


# ------------------------------------------------------------------ directory

def directory_search(query: str, hits_per_page: int = 20, page: int = 0,
                     filters: str | None = None,
                     client: client_mod.SfsuClient | None = None) -> dict:
    """Search the public people directory (faculty/staff) via the site's Algolia index."""
    c = client or _client()

    def run():
        data = c.directory_query(query, hits_per_page=hits_per_page, page=page, filters=filters)
        people = [{
            "name": " ".join(p for p in [h.get("first_name"), h.get("middle_name") or None, h.get("last_name")] if p and p.strip()),
            "name_suffix": h.get("name_suffix"),
            "email": h.get("email_addr"),
            "phone": h.get("phone"),
            "office": h.get("sfo_office_locatn"),
            "positions": h.get("positions"),
        } for h in data.get("hits", [])]
        return envelope.ok({
            "query": query, "page": data.get("page"), "nb_pages": data.get("nbPages"),
            "nb_hits": data.get("nbHits"), "people": people},
            sources=[SOURCES["directory"]],
            limitations=["Directory covers public employee listings; students are not listed.",
                         "Algolia 'filters' syntax available (e.g. \"sfo_classificatn:FACULTY\")."])

    return _try(run, sources=[SOURCES["directory"]])


# ------------------------------------------------------------------ calendar

def calendar_events(calendar: str = "all", start: str | int | None = None,
                    end: str | int | None = None,
                    client: client_mod.SfsuClient | None = None) -> dict:
    """Events from the public web calendar.

    ``calendar``: all | general | lectures | arts | alumni | athletics (or raw numeric id).
    ``start``/``end``: ``YYYY-MM-DD`` or epoch ms. Default: next 60 days.
    """
    c = client or _client()

    def to_ms(v, default_ms):
        if v is None:
            return default_ms
        if isinstance(v, int) or (isinstance(v, str) and v.isdigit()):
            return int(v)
        return int(time.mktime(time.strptime(str(v), "%Y-%m-%d")) * 1000)

    now = int(time.time() * 1000)
    from_ms = to_ms(start, now)
    to_ms_ = to_ms(end, now + 60 * 24 * 3600 * 1000)
    slug = client_mod.CALENDAR_SLUGS.get(calendar.lower(), calendar)
    url = f"{client_mod.WEB_BASE}/public/webcalendar/{slug}/listjson?from={from_ms}&to={to_ms_}"

    def run():
        data = c.calendar_events(slug, from_ms, to_ms_)
        events = [{
            "id": e.get("id"), "title": e.get("title"), "url": e.get("url"),
            "start_ms": int(e["start"]) if e.get("start") else None,
            "end_ms": int(e["end"]) if e.get("end") else None,
        } for e in data.get("result", [])]
        return envelope.ok({"calendar": slug, "from_ms": from_ms, "to_ms": to_ms_,
                            "count": len(events), "events": events},
                           sources=[url],
                           limitations=["Academic-calendar dates flow through 'all'/'general' — the dedicated 'acad' feed is empty upstream."])

    return _try(run, sources=[url])


def event_detail(event_id: int | str, client: client_mod.SfsuClient | None = None) -> dict:
    """Detail modal for one calendar event."""
    c = client or _client()
    url = f"{client_mod.WEB_BASE}/public/webcalendar/event/{event_id}.modal"

    def run():
        d = parsers.parse_event_modal(c.event_detail(event_id))
        d["id"] = event_id
        d["url"] = url
        return envelope.ok(d, sources=[url])

    return _try(run, sources=[url])


# ------------------------------------------------------------------ doctor

def doctor(client: client_mod.SfsuClient | None = None) -> dict:
    """Connectivity + contract checks against every upstream."""
    c = client or _client()
    checks = []

    def probe(name, fn):
        try:
            extra = fn() or ""
            checks.append({"name": name, "ok": True, "detail": extra})
        except Exception as e:
            checks.append({"name": name, "ok": False, "detail": f"{type(e).__name__}: {e}"})

    probe("classsearch form", lambda: f"subjects={len(parsers.parse_search_form(c.search_form())['subjects'])}")

    def _search():
        c.bind_search({"searchFor": "CSC", "term": _default_term(c) or 2267, "classCategory": "REG"})
        n = len(c.search_results_json().get("aaData", []))
        return f"rows={n}"
    probe("classsearch results JSON", _search)
    probe("section detail", lambda: f"{len(c.section_detail(2267, 'REG', 7251))}B")
    probe("bulletin catalog", lambda: f"courses={len(parsers.parse_courseblocks(c.catalog_subject_page('csc')))}")
    probe("directory algolia", lambda: f"nbHits={c.directory_query('a', hits_per_page=1).get('nbHits')}")
    probe("calendar all", lambda: f"events={len(c.calendar_events('all', 0, 9**13).get('result', []))}")

    ok_all = all(x["ok"] for x in checks)
    return envelope.ok({"checks": checks, "all_ok": ok_all},
                       sources=list(SOURCES.values()),
                       limitations=["Live probe — failures usually mean the site changed its contract or is down."])
