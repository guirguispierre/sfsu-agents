import json
import pathlib

import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture
def form_html() -> str:
    return (FIXTURES / "form.html").read_text()


@pytest.fixture
def csc_rows() -> list:
    return json.loads((FIXTURES / "searchresults_csc_reg.json").read_text())["aaData"]


@pytest.fixture
def section_detail_html() -> str:
    return (FIXTURES / "section_detail_7251.html").read_text()


@pytest.fixture
def bulletin_csc_html() -> str:
    return (FIXTURES / "bulletin_csc.html").read_text()


@pytest.fixture
def directory_smith() -> dict:
    return json.loads((FIXTURES / "directory_smith.json").read_text())
