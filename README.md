# sfsu-agents

[![CI](https://github.com/guirguispierre/sfsu-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/guirguispierre/sfsu-agents/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

Unofficial agent-facing toolkit for **San Francisco State University public web services** — class schedule, course catalog, people directory, and events calendar — exposed as a **CLI and an MCP stdio server**, with an evidence envelope on every result.

Inspired by [morluto/rea](https://github.com/morluto/rea) (Reverse Engineer Anything): the same "inspect → contract → evidence" philosophy applied to a university's public web surface. All data is public and unauthenticated; nothing behind the mySFSU login is touched.

> **Unofficial.** Not affiliated with, endorsed by, or supported by San Francisco State University.
> It only reads pages SFSU already publishes to anyone with a browser. Upstream pages can change
> without notice — run `sfsu-agents doctor` if something breaks, and please open an issue.

## Install

```bash
pip install "sfsu-agents[mcp] @ git+https://github.com/guirguispierre/sfsu-agents"   # CLI + MCP server
# or from a clone:
pip install .            # CLI only
pip install '.[mcp]'     # + MCP server
```

Requires Python 3.10+.

## Quick start

```bash
sfsu-agents doctor                    # probe every upstream endpoint
sfsu-agents terms                     # term codes & session categories
sfsu-agents subjects                  # all subject codes (CSC, MATH, ...)

sfsu-agents search CSC                # quick search (current term)
sfsu-agents search --subject MATH --term "Fall 2026" --seats --days m w
sfsu-agents section 7251 --term 2267  # one section's detail page

sfsu-agents course "CSC 413"          # Bulletin description + prereqs
sfsu-agents courses csc               # every CSC catalog course
sfsu-agents directory "smith"         # people directory
sfsu-agents events --calendar all --start 2026-08-01 --end 2026-12-31
```

Every command prints one JSON envelope:

```json
{
  "ok": true,
  "data": { ... },
  "error": null,
  "evidence": { "sources": ["<urls used>"], "limitations": ["..."], "unknowns": [] }
}
```

## MCP

```bash
sfsu-agents setup   # prints config snippets for Claude Code / Cursor / Codex / stdio
sfsu-agents mcp     # run the stdio server
```

Tools: `sfsu_terms`, `sfsu_subjects`, `sfsu_locations`, `sfsu_attributes`,
`sfsu_search_classes`, `sfsu_section_detail`, `sfsu_catalog_subjects`,
`sfsu_catalog_courses`, `sfsu_course_info`, `sfsu_directory_search`,
`sfsu_calendar_events`, `sfsu_event_detail`, `sfsu_doctor`.

## What it wraps (reverse-engineered public endpoints)

| Surface | Endpoint |
|---|---|
| Class search form | `GET webapps.sfsu.edu/public/classservices/classsearch` |
| Results binding (cookie session) | `GET .../classsearch/results?searchFor|subject&term&classCategory&filters` |
| Results JSON | `GET .../classservices/searchresultsjson` → `{"aaData":[rows]}` |
| Section detail | `GET .../classsearch/detail/{term}/{category}/{classNumber}` |
| Bulletin catalog | `GET bulletin.sfsu.edu/courses/{dept}/` (CourseLeaf `courseblock`s) |
| People directory | Algolia `prod_DIRECTORYSEARCH` (search-only key embedded in the site bundle) |
| Events | `GET .../webcalendar/{slug}/listjson?from&to` + `event/{id}.modal` |

See [docs/endpoints.md](docs/endpoints.md) for the full contract notes (term-code scheme, column layout, filter semantics, calendar slugs).

## Scope

- **In:** anything SFSU publishes without a login — class schedule search, section detail, Bulletin catalog, employee directory, campus events.
- **Out:** enrollment, grades, degree progress, anything behind mySFSU/PeopleSoft auth. Not attempted, not proxied.

## Responsible use

- Requests are sequential and identify themselves with a `sfsu-agents/<version>` User-Agent.
  Don't wrap it in tight polling loops or parallel crawlers.
- The people directory returns staff/faculty contact info SFSU publishes publicly; don't use it
  to build bulk contact lists or for spam.
- The Algolia key in the source is SFSU's public **search-only** key from the directory page's JS
  bundle, not a secret (see [SECURITY.md](SECURITY.md)).

## Project layout

```
src/sfsu_agents/
  client.py      HTTP calls only (one method per upstream endpoint)
  parsers.py     pure HTML/JSON -> dict parsers
  tools.py       orchestration; every function returns an evidence envelope
  envelope.py    ok()/err() envelope constructors
  terms.py       term-code helpers ("Fall 2026" <-> 2267)
  cli.py         argparse CLI
  mcp_server.py  MCP stdio server (mcp 1.x and 2.x)
tests/           offline fixture tests + opt-in live tests
docs/endpoints.md  reverse-engineered endpoint contracts
```

## Development

```bash
pip install -e '.[dev]'
ruff check src tests   # lint
pytest                 # offline fixtures + parser contracts
pytest -m live         # live smoke tests against sfsu.edu
```

See [CONTRIBUTING.md](CONTRIBUTING.md). Security issues: [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE). Inspired by [morluto/rea](https://github.com/morluto/rea).
