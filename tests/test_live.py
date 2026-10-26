"""Live smoke tests against sfsu.edu — run with: pytest -m live"""

import re

import pytest

from sfsu_agents import tools

pytestmark = pytest.mark.live


def test_live_terms():
    env = tools.list_terms()
    assert env["ok"], env["error"]
    names = [t["name"] for t in env["data"]["terms"]]
    assert names and all(re.fullmatch(r"(Winter|Spring|Summer|Fall) 20\d\d", n or "") for n in names)


def test_live_subjects():
    env = tools.list_subjects()
    assert env["ok"] and env["data"]["count"] > 100


def test_live_search_quick():
    env = tools.search_classes("CSC", term=2267, category="REG")
    assert env["ok"], env["error"]
    assert env["data"]["count"] > 0
    sec = env["data"]["sections"][0]
    assert sec["subject"] == "CSC" and sec["class_number"]


def test_live_search_advanced_filter():
    env = tools.search_classes(subject="CSC", term=2267, remaining_seats=True, in_person=True)
    assert env["ok"]
    for s in env["data"]["sections"]:
        assert s["seats_remaining"] is None or s["seats_remaining"] >= 0


def test_live_section_detail():
    env = tools.search_classes("CSC 413", term=2267)
    assert env["ok"] and env["data"]["sections"]
    cn = env["data"]["sections"][0]["class_number"]
    det = tools.section_detail(cn, term=2267)
    assert det["ok"] and det["data"]["class_number"] == cn


def test_live_catalog():
    env = tools.catalog_courses("csc")
    assert env["ok"] and env["data"]["count"] > 50
    env2 = tools.course_info("CSC 413")
    assert env2["ok"] and "Software Development" in env2["data"]["title"]


def test_live_directory():
    env = tools.directory_search("smith", hits_per_page=3)
    assert env["ok"] and env["data"]["nb_hits"] > 0
    assert env["data"]["people"][0]["email"].endswith("@sfsu.edu")


def test_live_calendar():
    env = tools.calendar_events(calendar="all", start="2025-08-01", end="2025-12-31")
    assert env["ok"] and env["data"]["count"] > 50


def test_live_doctor():
    env = tools.doctor()
    assert env["ok"]
    failed = [c for c in env["data"]["checks"] if not c["ok"]]
    assert not failed, failed
