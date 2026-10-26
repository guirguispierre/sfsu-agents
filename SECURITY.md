# Security Policy

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private
[security advisory form](https://github.com/guirguispierre/sfsu-agents/security/advisories/new).
You'll get a response within a few days.

If you've found a vulnerability in **SFSU's own systems** (not this package),
report it to SFSU Information Technology Services instead, not here.

## Scope notes

- The Algolia application ID and API key in `client.py` / `docs/endpoints.md`
  are SFSU's **public, search-only** directory credentials, shipped to every
  browser in the directory page's JavaScript bundle. They are not secrets.
- This package never handles user credentials and does not access any
  authenticated SFSU system.
