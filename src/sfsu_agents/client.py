"""HTTP client for SFSU public web services.

Endpoints reverse-engineered from the official public pages (no auth):

- ``GET  {WEB}/public/classservices/classsearch``               search form (term/session/subject lists)
- ``GET  {WEB}/public/classservices/classsearch/results?...``   binds a search to the cookie session
- ``GET  {WEB}/public/classservices/searchresultsjson``         JSON rows (``{"aaData": [...]}``) for the bound search
- ``GET  {WEB}/public/classservices/classsearch/detail/{term}/{cat}/{class_number}``  section detail page
- ``GET  {BULLETIN}/courses/`` and ``/courses/{dept}/``         CourseLeaf catalog
- ``POST {ALGOLIA}/1/indexes/prod_DIRECTORYSEARCH/query``       people directory (public search-only key embedded in the site bundle)
- ``GET  {WEB}/public/webcalendar/{slug}/listjson?from&to``     events (ms epoch), slugs: all, 14=general, 15=lectures, 16=arts, 4=alumni, 6=athletics
- ``GET  {WEB}/public/webcalendar/event/{id}.modal``            event detail (HTML fragment)
"""

from __future__ import annotations

import requests

from . import __version__

WEB_BASE = "https://webapps.sfsu.edu"
BULLETIN_BASE = "https://bulletin.sfsu.edu"
ALGOLIA_BASE = "https://05XYDC2NJE-dsn.algolia.net"
ALGOLIA_APP_ID = "05XYDC2NJE"
ALGOLIA_SEARCH_KEY = "ab22c79867e4fa9ccede09f3c14cc3e0"  # public search-only key from the site's JS bundle
ALGOLIA_INDEX = "prod_DIRECTORYSEARCH"

CALENDAR_SLUGS = {
    "all": "all",
    "general": "14", "general_interest": "14",
    "lectures": "15", "lectures_and_conferences": "15",
    "arts": "16", "arts_and_culture": "16",
    "alumni": "4",
    "athletics": "6",
}

UA = f"sfsu-agents/{__version__} (+https://github.com/guirguispierre/sfsu-agents)"


class SfsuClient:
    def __init__(self, timeout: float = 30.0, session: requests.Session | None = None):
        self.timeout = timeout
        self.http = session or requests.Session()
        self.http.headers.update({"User-Agent": UA})

    # ---------- class schedule ----------

    def search_form(self) -> str:
        r = self.http.get(f"{WEB_BASE}/public/classservices/classsearch", timeout=self.timeout)
        r.raise_for_status()
        return r.text

    def bind_search(self, params: dict) -> tuple[str, str]:
        """GET the results page to bind the search to this client's cookie session.

        Returns (final_url, html).
        """
        r = self.http.get(f"{WEB_BASE}/public/classservices/classsearch/results",
                          params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.url, r.text

    def search_results_json(self) -> dict:
        r = self.http.get(f"{WEB_BASE}/public/classservices/searchresultsjson",
                          headers={"X-Requested-With": "XMLHttpRequest"}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def section_detail(self, term: int, category: str, class_number: int | str) -> str:
        url = f"{WEB_BASE}/public/classservices/classsearch/detail/{term}/{category}/{class_number}"
        r = self.http.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.text

    # ---------- bulletin catalog ----------

    def catalog_index(self) -> str:
        r = self.http.get(f"{BULLETIN_BASE}/courses/", timeout=self.timeout)
        r.raise_for_status()
        return r.text

    def catalog_subject_page(self, dept_slug: str) -> str:
        r = self.http.get(f"{BULLETIN_BASE}/courses/{dept_slug}/", timeout=self.timeout)
        r.raise_for_status()
        return r.text

    # ---------- directory ----------

    def directory_query(self, query: str, hits_per_page: int = 20, page: int = 0,
                        filters: str | None = None) -> dict:
        body: dict = {"query": query, "hitsPerPage": hits_per_page, "page": page}
        if filters:
            body["filters"] = filters
        r = self.http.post(f"{ALGOLIA_BASE}/1/indexes/{ALGOLIA_INDEX}/query",
                           headers={"X-Algolia-Application-Id": ALGOLIA_APP_ID,
                                    "X-Algolia-API-Key": ALGOLIA_SEARCH_KEY},
                           json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # ---------- events calendar ----------

    def calendar_events(self, slug: str, from_ms: int, to_ms: int) -> dict:
        slug = CALENDAR_SLUGS.get(slug.lower(), slug)
        r = self.http.get(f"{WEB_BASE}/public/webcalendar/{slug}/listjson",
                          params={"from": from_ms, "to": to_ms}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def event_detail(self, event_id: int | str) -> str:
        r = self.http.get(f"{WEB_BASE}/public/webcalendar/event/{event_id}.modal", timeout=self.timeout)
        r.raise_for_status()
        return r.text
