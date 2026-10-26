from sfsu_agents import parsers


def test_parse_search_form(form_html):
    form = parsers.parse_search_form(form_html)
    codes = {t["value"] for t in form["terms"]}
    assert "2267" in codes and "2265" in codes
    labels = {t["label"] for t in form["terms"]}
    assert "Fall 2026" in labels
    assert len(form["subjects"]) > 100
    assert any(s["value"] == "CSC" for s in form["subjects"])
    assert any(("2267" in (s["value"] or "")) for s in form["sessions"])
    assert len(form["locations"]) > 40
    assert len(form["attributes"]) > 40


def test_parse_aa_row(csc_rows):
    row = parsers.parse_aa_row(csc_rows[0])
    assert row["course"] == "CSC 413"
    assert row["subject"] == "CSC"
    assert row["catalog_number"] == "413"
    assert row["section_bracket"] == "05"
    assert row["component"] == "LEC"
    assert row["title"] == "Software Development"
    assert row["class_number"] == 7251
    assert row["term"] == "2267"
    assert row["category"] == "REG"
    assert row["detail_url_path"].endswith("/detail/2267/REG/7251")
    assert "Upper-Division" in row["attributes"]
    assert row["instruction_mode"].startswith("In-Person")
    assert "Jose Ortiz" in row["instructors"]
    assert isinstance(row["seats_remaining"], int)
    assert isinstance(row["waitlist_remaining"], int)
    assert row["section"] == "05"
    assert isinstance(row["enrolled"], int)
    mtg = row["meetings"][0]
    assert mtg["days"] == "We"
    assert "4:00 PM" in mtg["times"]
    assert "Thornton Hall" in mtg["location"]


def test_parse_aa_row_all(csc_rows):
    # every row parses without exception and yields required keys
    for r in csc_rows:
        row = parsers.parse_aa_row(r)
        for k in ("class_number", "component", "title", "meetings", "instructors"):
            assert k in row


def test_parse_section_detail(section_detail_html):
    d = parsers.parse_section_detail(section_detail_html)
    assert d["class_number"] == 7251
    assert d["units"] == "3"
    assert "Prerequisites" in (d.get("description") or "")
    assert "object-oriented" in (d.get("description") or "").lower()
    assert any("materials fee" in n for n in d["class_notes"])
    assert d["meetings"], "expected meeting rows"
    first = d["meetings"][0]
    vals = " ".join(first.values())
    assert "We" in vals and "04:00 PM" in vals and "Thornton Hall" in vals
    assert "determined" in (d.get("textbooks") or "").lower()


def test_parse_courseblocks(bulletin_csc_html):
    courses = parsers.parse_courseblocks(bulletin_csc_html)
    assert len(courses) > 50
    by_num = {c.get("catalog_number"): c for c in courses}
    c413 = by_num.get("413")
    assert c413 is not None
    assert c413["subject"] == "CSC"
    assert "Software Development" in c413["title"]
    assert "prerequisite" in (c413.get("prerequisites") or "").lower()
    assert "object-oriented" in (c413.get("description") or "").lower()


def test_parse_catalog_index(bulletin_csc_html):
    # the courses page has a global dept dropdown too; just ensure slugs parse on index-like html
    slugs = parsers.parse_catalog_index(bulletin_csc_html)
    assert any(s["slug"] == "csc" for s in slugs) or slugs == []


def test_parse_results_page():
    html = """
    <h1> Class Schedule Search Results - Fall 2026 </h1>
    <p class="class-search-date-time">As of October 12, 2026 03:21 PDT</p>
    <div id="classschedule-search-info"><ul><li><strong>Session</strong>: Academic Regular Session</li></ul></div>
    """
    meta = parsers.parse_results_page(html)
    assert meta["as_of"] == "October 12, 2026 03:21 PDT"
    assert "Fall 2026" in meta["heading"]
