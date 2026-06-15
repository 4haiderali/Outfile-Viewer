# Changelog

All notable changes to the Outfile Viewer project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Comprehensive documentation (README, DEVELOPMENT.md, CONTRIBUTING.md)
- MIT License file
- CHANGELOG.md for version tracking
- File format specification guide
- GitHub Actions CI/CD pipeline (manual setup guide)

### Changed
- Improved project structure and documentation

---

## [1.26] - 2026-06-15

### Added
- **Background Launcher** — Desktop app now runs in system tray
- **Consolidated Tabs** — Reduced 31 tabs from v19-v25 to 11 core tabs
- **AppContext Architecture** — Centralized shared state for all tabs
- **Session History** — Access previously uploaded files without re-upload
- **Unit Management** — Override default units for any column
- **Derived Columns** — Create calculated columns with expressions
- **Project Workspaces** — Save analysis state and restore later
- **Windows Installer** — OutfileViewerSetup.exe for easy installation
- **Single Instance** — Prevents multiple instances running
- **Logging** — Launcher logs to %LOCALAPPDATA%\OutfileViewer\OutfileViewer.log

### Fixed
- Improved parser robustness for irregular file formats
- Better error handling for malformed files
- Tray icon lifecycle management

### Changed
- Migrated from multiple scattered scripts to modular tab architecture
- Improved UI/UX with consolidated analysis workflows

---

## [1.0] - Initial Release

### Added
- Initial Outfile Viewer release
- Support for .out, .txt, .log, .dat file parsing
- Basic table extraction and display
- Metadata extraction
- Statistics summary
- Simple export functionality

---

## Notes for Maintainers

### Version Bumping

When releasing a new version:

1. Update version in `VERSION.txt`: `vX.Y.Z`
2. Update version marker in `app.py`: `# OUT_VIEWER_VERSION_MARKER=vX.Y.Z_FEATURE_NAME`
3. Update this file with new section
4. Create Git tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
5. Create GitHub Release with binary attachment

---

Last updated: 2026-06-15
