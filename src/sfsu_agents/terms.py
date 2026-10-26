"""SFSU/PeopleSoft term-code helpers.

Term codes are 4 digits: ``2`` + two-digit year + term digit.
Term digits: 1=Winter, 3=Spring, 5=Summer, 7=Fall.  Example: ``2267`` = Fall 2026.

Session categories (the second half of ``term:category`` pairs used by the
class-search form): ``REG`` academic regular session, ``CEL`` College of
Professional & Global Education (CPaGE), and ``R1``-``R4`` summer sub-sessions.
"""

from __future__ import annotations

import re

TERM_SEASON = {1: "Winter", 3: "Spring", 5: "Summer", 7: "Fall"}
SEASON_DIGIT = {v: k for k, v in TERM_SEASON.items()}

SESSION_LABELS = {
    "REG": "Academic Regular Session",
    "CEL": "College of Professional & Global Education (CPaGE)",
    "R1": "Summer Regular Session 1",
    "R2": "Summer Regular Session 2",
    "R3": "Summer Regular Session 3",
    "R4": "Summer Regular Session 4",
}

_CODE_RE = re.compile(r"^(\d)(\d\d)(\d)$")


def code_to_name(code: int | str) -> str | None:
    """2267 -> 'Fall 2026'. Returns None for unrecognized codes."""
    m = _CODE_RE.match(str(code))
    if not m or m.group(1) != "2":
        return None
    year = 2000 + int(m.group(2))
    season = TERM_SEASON.get(int(m.group(3)))
    return f"{season} {year}" if season else None


def name_to_code(name: str) -> int | None:
    """'Fall 2026' / 'fall 2026' -> 2267. Returns None if unparseable."""
    m = re.match(r"^\s*(winter|spring|summer|fall)\s+(\d{4})\s*$", name, re.I)
    if not m:
        return None
    season, year = m.group(1).capitalize(), int(m.group(2))
    return int(f"2{year % 100:02d}{SEASON_DIGIT[season]}")


def resolve_term(term: int | str | None, default: int | None = None) -> int | None:
    """Accept a code (``2267`` or ``'2267'``) or a name (``'Fall 2026'``)."""
    if term is None or str(term).strip().lower() in ("", "current", "default"):
        return default
    s = str(term).strip()
    if s.isdigit():
        return int(s)
    return name_to_code(s)


def normalize_category(category: str | None) -> str:
    """Normalize a session category: REG/CEL/R1..R4. Default REG."""
    if not category:
        return "REG"
    c = str(category).strip().upper()
    if ":" in c:  # allow '2267:REG' style pairs too
        c = c.split(":", 1)[1] or "REG"
    if c in SESSION_LABELS:
        return c
    return c


def resolve_session_pair(term: int | str | None, category: str | None = None,
                         default: int | None = None) -> tuple[int | None, str]:
    """Handle combined ``'2267:REG'`` input or separate term/category args."""
    if term is not None and ":" in str(term):
        t, c = str(term).split(":", 1)
        return resolve_term(t, default), normalize_category(c)
    return resolve_term(term, default), normalize_category(category)
