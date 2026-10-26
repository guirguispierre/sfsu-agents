"""sfsu-agents: agent-facing toolkit for San Francisco State University public web services.

Wraps SFSU's public class-schedule search, course catalog (Bulletin),
people directory, and events calendar behind a uniform JSON contract:
every call returns an evidence envelope::

    {"ok": bool, "data": ..., "error": ..., "evidence": {"sources": [...], "limitations": [...], "unknowns": [...]}}

All data is public and unauthenticated. Enrollment, grades, and anything
behind mySFSU login are out of scope by design.
"""

__version__ = "0.1.0"
