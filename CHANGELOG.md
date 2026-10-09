# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-10-09

### Added

- Optional offline agent skill and `install`/`update`/`delete`/`status` commands for consuming FastAPI projects.
- Project maintainer guidance and English/Russian skill installation documentation.
- Installer ownership, rollback, recovery-backup, and symlink protection tests, plus a release wheel lifecycle check.

### Fixed

- Use core metadata 2.4 for distributions to remain compatible with the locked release validation tools.

## [0.1.0] - 2026-07-19

### Added

- Application-scoped `CabinetSite` and deterministic admin registry.
- Generic list, detail, form, and operation page contracts.
- Metric, table, list, and chart widget contracts.
- Permission port for modules, pages, widgets, navigation, and actions.
- Explicit module loading through `register_cabinet` or `CABINET_ADMINS`.
- Overridable Jinja templates, responsive static assets, examples, and EN/RU documentation.
