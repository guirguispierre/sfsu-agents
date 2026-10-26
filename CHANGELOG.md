# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-10-26

### Added
- CLI (`sfsu-agents`) and MCP stdio server with 13 tools: terms, subjects,
  locations, attributes, class search (quick + advanced filters), section
  detail, catalog subjects/courses/course info, people directory, calendar
  events, event detail, doctor.
- Evidence-envelope result contract (`ok` / `data` / `error` / `evidence`).
- Offline fixture tests and opt-in live smoke tests (`pytest -m live`).
