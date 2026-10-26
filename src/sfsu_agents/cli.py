"""``sfsu-agents`` command-line interface.

Every command prints one JSON evidence envelope to stdout::

    sfsu-agents search --subject CSC --term "Fall 2026" --seats
    sfsu-agents section 7251 --term 2267
    sfsu-agents course "CSC 413"
    sfsu-agents directory "smith" --role FACULTY
    sfsu-agents events --calendar all --start 2026-08-01 --end 2026-12-31
    sfsu-agents doctor | mcp | setup
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import tools


def _print(env: dict) -> int:
    try:
        json.dump(env, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
    return 0 if env.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sfsu-agents",
        description="Agent-facing toolkit for SFSU public web services (class schedule, catalog, directory, calendar). "
                    "Every command emits a JSON evidence envelope.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="probe all upstream endpoints")
    sub.add_parser("terms", help="list terms and session categories")
    sub.add_parser("subjects", help="list class-schedule subjects")
    sub.add_parser("locations", help="list building/location codes")
    sub.add_parser("attributes", help="list GE course-attribute codes")
    sub.add_parser("catalog-subjects", help="list Bulletin (catalog) departments")

    s = sub.add_parser("search", help="search the class schedule")
    s.add_argument("query", nargs="?", help="quick search, e.g. 'CSC' or 'CSC 413'")
    s.add_argument("--subject", help="advanced: subject code, e.g. CSC")
    s.add_argument("--number", dest="catalog_number", help="advanced: catalog number, e.g. 413")
    s.add_argument("--term", help="term code (2267) or name ('Fall 2026'); '2267:REG' also works")
    s.add_argument("--category", "--session", dest="category",
                   help="session category: REG (default), CEL (CPaGE), R1-R4 (summer)")
    s.add_argument("--open-university", action="store_true", help="include Open University sections")
    s.add_argument("--seats", dest="remaining_seats", action="store_true", help="only sections with seats left")
    s.add_argument("--days", nargs="+", metavar="D", help="meeting days: m tu w th f sa su")
    s.add_argument("--start", dest="start_time", help="earliest start hour, e.g. 14")
    s.add_argument("--end", dest="end_time", help="latest end hour, e.g. 20")
    s.add_argument("--location", help="building code (see 'locations')")
    s.add_argument("--instructor", dest="instructor_last_name", help="instructor last name")
    s.add_argument("--attr", dest="attributes", help="course attribute code (see 'attributes')")
    s.add_argument("--online-async", action="store_true", help="online asynchronous only")
    s.add_argument("--online-sync", action="store_true", help="online synchronous only")
    s.add_argument("--online-bichronous", action="store_true", help="online bichronous only")
    s.add_argument("--hybrid", action="store_true", help="hybrid only")
    s.add_argument("--in-person", action="store_true", help="in-person only")

    s = sub.add_parser("section", help="section detail page")
    s.add_argument("class_number", help="class number, e.g. 7251")
    s.add_argument("--term", required=True, help="term code (2267) or name ('Fall 2026')")
    s.add_argument("--category", "--session", dest="category", help="session category (default REG)")

    s = sub.add_parser("courses", help="Bulletin catalog courses for a subject")
    s.add_argument("subject", help="subject slug/code, e.g. csc")

    s = sub.add_parser("course", help="one Bulletin catalog course, e.g. 'CSC 413'")
    s.add_argument("course", help="course code")

    s = sub.add_parser("directory", help="search the people directory")
    s.add_argument("query", help="name/email search text")
    s.add_argument("--limit", type=int, default=20, help="hits per page (default 20)")
    s.add_argument("--page", type=int, default=0)
    s.add_argument("--role", help="convenience filter -> sfo_classificatn:<ROLE> (e.g. FACULTY)")
    s.add_argument("--filters", help="raw Algolia filters string")

    s = sub.add_parser("events", help="public calendar events")
    s.add_argument("--calendar", default="all",
                   help="all | general | lectures | arts | alumni | athletics | raw id (default all)")
    s.add_argument("--start", help="YYYY-MM-DD or epoch ms (default: now)")
    s.add_argument("--end", help="YYYY-MM-DD or epoch ms (default: +60 days)")

    s = sub.add_parser("event", help="one calendar event's detail")
    s.add_argument("event_id")

    sub.add_parser("mcp", help="run the MCP stdio server")
    sub.add_parser("setup", help="print agent MCP-config snippet")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "doctor":
        return _print(tools.doctor())
    if args.cmd == "terms":
        return _print(tools.list_terms())
    if args.cmd == "subjects":
        return _print(tools.list_subjects())
    if args.cmd == "locations":
        return _print(tools.list_locations())
    if args.cmd == "attributes":
        return _print(tools.list_attributes())
    if args.cmd == "catalog-subjects":
        return _print(tools.catalog_subjects())
    if args.cmd == "search":
        return _print(tools.search_classes(
            args.query, subject=args.subject, catalog_number=args.catalog_number,
            term=args.term, category=args.category,
            open_university=True if args.open_university else None,
            remaining_seats=True if args.remaining_seats else None,
            days=args.days, start_time=args.start_time, end_time=args.end_time,
            location=args.location, instructor_last_name=args.instructor_last_name,
            attributes=args.attributes, online_async=True if args.online_async else None,
            online_sync=True if args.online_sync else None,
            online_bichronous=True if args.online_bichronous else None,
            hybrid=True if args.hybrid else None, in_person=True if args.in_person else None))
    if args.cmd == "section":
        return _print(tools.section_detail(args.class_number, term=args.term, category=args.category))
    if args.cmd == "courses":
        return _print(tools.catalog_courses(args.subject))
    if args.cmd == "course":
        return _print(tools.course_info(args.course))
    if args.cmd == "directory":
        filters = args.filters
        if args.role:
            filters = f"sfo_classificatn:{args.role}" + (f" AND {filters}" if filters else "")
        return _print(tools.directory_search(args.query, hits_per_page=args.limit,
                                             page=args.page, filters=filters))
    if args.cmd == "events":
        return _print(tools.calendar_events(calendar=args.calendar, start=args.start, end=args.end))
    if args.cmd == "event":
        return _print(tools.event_detail(args.event_id))
    if args.cmd == "mcp":
        from . import mcp_server
        return mcp_server.run()
    if args.cmd == "setup":
        from . import setup_cmd
        return setup_cmd.run()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
