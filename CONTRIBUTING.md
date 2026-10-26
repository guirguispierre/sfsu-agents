# Contributing

Thanks for helping! This project wraps SFSU's **public, unauthenticated** web
services for AI agents. Contributions that fix upstream drift, add new public
surfaces, or improve parsing are very welcome.

## Dev setup

```bash
git clone https://github.com/guirguispierre/sfsu-agents
cd sfsu-agents
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'

ruff check src tests     # lint
pytest                   # offline tests (fixtures only, no network)
pytest -m live           # live smoke tests against sfsu.edu
```

## Ground rules

1. **Public data only.** Nothing behind mySFSU, PeopleSoft, iLearn/Canvas, or
   any login. PRs that add credentials, session replay, or scraping of
   auth-gated pages will be closed.
2. **Every tool returns an evidence envelope** (`envelope.ok` / `envelope.err`)
   with real `sources` URLs and honest `limitations` / `unknowns`.
3. **Parsers are pure.** Network lives in `client.py`; HTML/JSON → dict lives in
   `parsers.py`; orchestration + envelopes live in `tools.py`.
4. **Add a fixture + offline test** for any new parser. Save a trimmed real
   response under `tests/fixtures/` and **replace any personal data** (names,
   emails, IDs of real people) with synthetic values. CSRF tokens → `REDACTED`.
5. **Document endpoints** you reverse-engineer in `docs/endpoints.md`.
6. **Be polite to upstream.** No parallel hammering, no tight polling loops.

## Adding a new tool

1. Client method in `client.py` (one HTTP call, `raise_for_status()`).
2. Parser in `parsers.py` + fixture + test in `tests/test_parsers.py`.
3. Tool function in `tools.py` returning an envelope, test in `tests/test_tools.py`.
4. Register it in `mcp_server.py` and add a CLI subcommand in `cli.py`.
5. Mention it in the README tool list and `CHANGELOG.md` under *Unreleased*.

## Releasing (maintainers)

Bump `__version__` in `src/sfsu_agents/__init__.py`, update `CHANGELOG.md`,
tag `vX.Y.Z`, and publish a GitHub release — `.github/workflows/release.yml`
publishes to PyPI via trusted publishing.
