"""MCP stdio server exposing every tool over the Model Context Protocol.

Works on both MCP Python SDK generations:

- ``mcp < 2``: ``from mcp.server.fastmcp import FastMCP``
- ``mcp >= 2``: ``from mcp.server.mcpserver import MCPServer``

Every tool returns the evidence envelope as JSON text.
"""

from __future__ import annotations

import asyncio
import json

from . import tools

try:  # mcp >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
    _V2 = True
except ImportError:  # mcp < 2.0
    try:
        from mcp.server.fastmcp import FastMCP as _Server  # type: ignore
        _V2 = False
    except ImportError:
        _Server = None  # type: ignore


def _dump(env: dict) -> str:
    return json.dumps(env, indent=2, default=str)


def build_server():
    if _Server is None:
        raise RuntimeError("the 'mcp' package is required: pip install 'sfsu-agents[mcp]'")
    srv = _Server(name="sfsu-agents",
                  instructions="SFSU public data: class schedule, catalog, people directory, events. "
                               "All tools return an evidence envelope {ok,data|error,evidence{sources,limitations,unknowns}}.")

    @srv.tool()
    def sfsu_terms() -> str:
        """List SFSU terms (codes + names) and session categories (REG/CEL/R1-R4)."""
        return _dump(tools.list_terms())

    @srv.tool()
    def sfsu_subjects() -> str:
        """List all class-schedule subject codes (e.g. CSC, MATH) with names."""
        return _dump(tools.list_subjects())

    @srv.tool()
    def sfsu_locations() -> str:
        """List building/location codes for the class-search location filter."""
        return _dump(tools.list_locations())

    @srv.tool()
    def sfsu_attributes() -> str:
        """List GE course-attribute codes for the class-search attributes filter."""
        return _dump(tools.list_attributes())

    @srv.tool()
    def sfsu_search_classes(
        query: str | None = None,
        subject: str | None = None,
        catalog_number: str | None = None,
        term: str | None = None,
        category: str | None = None,
        open_university: bool | None = None,
        remaining_seats: bool | None = None,
        days: list[str] | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        location: str | None = None,
        instructor_last_name: str | None = None,
        attributes: str | None = None,
        online_async: bool | None = None,
        online_sync: bool | None = None,
        online_bichronous: bool | None = None,
        hybrid: bool | None = None,
        in_person: bool | None = None,
    ) -> str:
        """Search the live SFSU class schedule.

        Quick mode: ``query='CSC'`` or ``'CSC 413'``.
        Advanced mode: ``subject='CSC'`` plus filters (the site ignores advanced
        filters in quick mode). ``term`` accepts 2267, 'Fall 2026', or '2267:REG';
        omit for the current term. ``category``: REG (default), CEL, R1-R4.
        ``days`` values: m tu w th f sa su. ``start_time``/``end_time``: 2-digit hour.
        Returns normalized sections: course, section, component, title, units,
        class_number, attributes, meetings, instruction_mode, instructors,
        seats_remaining, waitlist_remaining, enrolled, detail link.
        """
        return _dump(tools.search_classes(
            query, subject=subject, catalog_number=catalog_number, term=term,
            category=category, open_university=open_university,
            remaining_seats=remaining_seats, days=days, start_time=start_time,
            end_time=end_time, location=location,
            instructor_last_name=instructor_last_name, attributes=attributes,
            online_async=online_async, online_sync=online_sync,
            online_bichronous=online_bichronous, hybrid=hybrid, in_person=in_person))

    @srv.tool()
    def sfsu_section_detail(class_number: int, term: str, category: str | None = None) -> str:
        """Full detail for one section: description, prerequisites, class notes,
        meetings (days/times/location/dates/instructor), textbooks.
        ``term`` required: 2267 or 'Fall 2026'. ``category`` defaults to REG."""
        return _dump(tools.section_detail(class_number, term=term, category=category))

    @srv.tool()
    def sfsu_catalog_subjects() -> str:
        """List departments/subjects in the SFSU Bulletin (course catalog)."""
        return _dump(tools.catalog_subjects())

    @srv.tool()
    def sfsu_catalog_courses(subject: str) -> str:
        """All Bulletin catalog courses for a subject (e.g. 'csc') with
        descriptions and prerequisites. This is the policy catalog, not
        term offerings — combine with sfsu_search_classes for sections."""
        return _dump(tools.catalog_courses(subject))

    @srv.tool()
    def sfsu_course_info(course: str) -> str:
        """One catalog course by code, e.g. 'CSC 413': title, units, description,
        prerequisites."""
        return _dump(tools.course_info(course))

    @srv.tool()
    def sfsu_directory_search(query: str, hits_per_page: int = 20, page: int = 0,
                              filters: str | None = None) -> str:
        """Search the public SFSU people directory (faculty/staff) by name or
        email. ``filters`` accepts Algolia syntax, e.g.
        ``sfo_classificatn:FACULTY``. Returns name, email, phone, office,
        positions (college/dept/title)."""
        return _dump(tools.directory_search(query, hits_per_page=hits_per_page,
                                            page=page, filters=filters))

    @srv.tool()
    def sfsu_calendar_events(calendar: str = "all", start: str | None = None,
                             end: str | None = None) -> str:
        """Public SFSU web-calendar events.

        ``calendar``: all | general | lectures | arts | alumni | athletics
        (or a raw calendar id). ``start``/``end``: 'YYYY-MM-DD' or epoch ms;
        default is now through +60 days."""
        return _dump(tools.calendar_events(calendar=calendar, start=start, end=end))

    @srv.tool()
    def sfsu_event_detail(event_id: str) -> str:
        """Detail for one calendar event (from sfsu_calendar_events)."""
        return _dump(tools.event_detail(event_id))

    @srv.tool()
    def sfsu_doctor() -> str:
        """Probe every upstream endpoint and parser contract."""
        return _dump(tools.doctor())

    return srv


def run() -> int:
    srv = build_server()
    if _V2:
        asyncio.run(srv.run_stdio_async())
    else:
        srv.run()  # FastMCP 1.x defaults to stdio
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
