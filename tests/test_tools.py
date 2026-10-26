import json
import pathlib

import pytest

from sfsu_agents import client as client_mod
from sfsu_agents import tools

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


class FakeClient(client_mod.SfsuClient):
    """SfsuClient with canned responses — exercises tools end-to-end without network."""

    def __init__(self):
        self.params_seen = None

    def search_form(self):
        return (FIXTURES / "form.html").read_text()

    def bind_search(self, params):
        self.params_seen = dict(params)
        return "https://webapps.sfsu.edu/public/classservices/classsearch/results?bound=1", "<h1>Results</h1>"

    def search_results_json(self):
        return json.loads((FIXTURES / "searchresults_csc_reg.json").read_text())

    def section_detail(self, term, category, class_number):
        return (FIXTURES / "section_detail_7251.html").read_text()

    def catalog_index(self):
        return (FIXTURES / "bulletin_csc.html").read_text()

    def catalog_subject_page(self, slug):
        return (FIXTURES / "bulletin_csc.html").read_text()

    def directory_query(self, query, hits_per_page=20, page=0, filters=None):
        return json.loads((FIXTURES / "directory_smith.json").read_text())

    def calendar_events(self, slug, from_ms, to_ms):
        return {"success": 1, "result": [{"id": "58719", "title": "Fall '25 First Day of Instruction",
                                          "url": "https://webapps.sfsu.edu/public/webcalendar/event/58719.modal",
                                          "start": "1756164180000", "end": "1756164180000"}]}

    def event_detail(self, event_id):
        return "<h4>Fall '25 First Day of Instruction</h4><p>Aug 25 2025</p>"


@pytest.fixture
def fake():
    return FakeClient()


def test_envelope_shape(fake):
    env = tools.list_terms(client=fake)
    assert set(env) == {"ok", "data", "error", "evidence"}
    assert set(env["evidence"]) == {"sources", "limitations", "unknowns"}


def test_list_terms(fake):
    env = tools.list_terms(client=fake)
    assert env["ok"]
    terms = {t["code"]: t["name"] for t in env["data"]["terms"]}
    assert terms["2267"] == "Fall 2026"
    cats = {(s["term_code"], s["category"]) for s in env["data"]["sessions"]}
    assert ("2267", "REG") in cats and ("2265", "R1") in cats


def test_list_subjects(fake):
    env = tools.list_subjects(client=fake)
    assert env["ok"] and env["data"]["count"] > 100
    assert any(s["value"] == "CSC" for s in env["data"]["subjects"])


def test_search_quick_binds_searchfor(fake):
    env = tools.search_classes("CSC 413", term=2267, client=fake)
    assert env["ok"]
    assert fake.params_seen["searchFor"] == "CSC 413"
    assert fake.params_seen["term"] == 2267
    assert fake.params_seen["classCategory"] == "REG"
    assert "subject" not in fake.params_seen  # quick mode
    assert env["data"]["count"] == 132
    sec = env["data"]["sections"][0]
    assert sec["course"] == "CSC 413" and sec["class_number"] == 7251


def test_search_advanced_filters(fake):
    env = tools.search_classes(subject="CSC", term="Fall 2026", remaining_seats=True,
                               days=["w"], start_time="14", end_time="20",
                               location="TH", instructor_last_name="ortiz", client=fake)
    assert env["ok"]
    p = fake.params_seen
    assert p["subject"] == "CSC" and p["term"] == 2267
    assert p["remainingSeats"] == "y" and p["meetingDays[0]"] == "w"
    assert p["startTime"] == "14" and p["endTime"] == "20"
    assert p["location"] == "TH" and p["instructorLastName"] == "ortiz"
    assert "searchFor" not in p


def test_search_term_session_pair(fake):
    tools.search_classes("CSC", term="2265:R2", client=fake)
    assert fake.params_seen["term"] == 2265
    assert fake.params_seen["classCategory"] == "R2"


def test_section_detail(fake):
    env = tools.section_detail(7251, term=2267, client=fake)
    assert env["ok"]
    d = env["data"]
    assert d["class_number"] == 7251
    assert "Software Development" in d["heading"]
    assert d["url"].endswith("/detail/2267/REG/7251")


def test_section_detail_requires_term(fake):
    env = tools.section_detail(7251, term=None, client=fake)
    assert not env["ok"] and env["error"]["kind"] == "input"


def test_catalog_courses(fake):
    env = tools.catalog_courses("csc", client=fake)
    assert env["ok"] and env["data"]["count"] > 50


def test_course_info(fake):
    env = tools.course_info("CSC 413", client=fake)
    assert env["ok"]
    assert "Software Development" in env["data"]["title"]


def test_course_info_not_found():
    class Empty(FakeClient):
        def catalog_subject_page(self, slug):
            return "<html></html>"
    env = tools.course_info("CSC 999", client=Empty())
    assert not env["ok"] and env["error"]["kind"] == "not_found"


def test_directory_search(fake):
    env = tools.directory_search("smith", client=fake)
    assert env["ok"]
    person = env["data"]["people"][0]
    assert person["email"] == "sexample@sfsu.edu"
    assert person["positions"][0]["dept_title"] == "Nursing"


def test_calendar_events(fake):
    env = tools.calendar_events(calendar="general", start="2025-08-01", end="2025-09-01", client=fake)
    assert env["ok"]
    assert env["data"]["events"][0]["title"].startswith("Fall '25")


def test_event_detail(fake):
    env = tools.event_detail("58719", client=fake)
    assert env["ok"] and "First Day" in env["data"]["title"]


def test_doctor(fake):
    env = tools.doctor(client=fake)
    assert env["ok"]
    names = {c["name"] for c in env["data"]["checks"]}
    assert "classsearch results JSON" in names and "directory algolia" in names
