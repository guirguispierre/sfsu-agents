from sfsu_agents import terms


def test_code_to_name():
    assert terms.code_to_name(2267) == "Fall 2026"
    assert terms.code_to_name(2265) == "Summer 2026"
    assert terms.code_to_name(2263) == "Spring 2026"
    assert terms.code_to_name(2261) == "Winter 2026"
    assert terms.code_to_name(2155) == "Summer 2015"
    assert terms.code_to_name("2267") == "Fall 2026"
    assert terms.code_to_name(9999) is None


def test_name_to_code():
    assert terms.name_to_code("Fall 2026") == 2267
    assert terms.name_to_code("spring 2026") == 2263
    assert terms.name_to_code("Summer 2027") == 2275
    assert terms.name_to_code("Q3 2026") is None


def test_resolve_term():
    assert terms.resolve_term(2267) == 2267
    assert terms.resolve_term("2267") == 2267
    assert terms.resolve_term("Fall 2026") == 2267
    assert terms.resolve_term(None, default=2267) == 2267
    assert terms.resolve_term("current", default=2267) == 2267


def test_resolve_session_pair():
    assert terms.resolve_session_pair("2267:REG") == (2267, "REG")
    assert terms.resolve_session_pair(2267, "cel") == (2267, "CEL")
    assert terms.resolve_session_pair("2265:R2") == (2265, "R2")
    assert terms.resolve_session_pair(None) == (None, "REG")


def test_normalize_category():
    assert terms.normalize_category(None) == "REG"
    assert terms.normalize_category("cel") == "CEL"
    assert terms.normalize_category("2265:r3") == "R3"
