# .out Output Viewer — v26 Consolidated Cockpit

v26 is a consolidation release. v19→v25 added a lot of genuinely useful
analysis features, but also nearly doubled `app.py` (918 → 1,562 lines) and
the tab count (17 → 31), with real overlap between tabs (risk ranking shown
in two places, PCA-based multivariate outliers in three, three independent
HTML report generators with three near-identical stylesheets, three
inconsistent "save your session" formats, and the same `INDEX_NAMES`
constant copy-pasted into ~12 places).

v26 keeps every analysis capability from v25 but reorganizes them into
**11 top-level tabs (12 with Admin/QA)**, each composed from small,
single-purpose modules under `out_viewer/tabs/`.

## Single BAT

```text
OutViewer_Install_Update_Run.bat
```

## What changed in v26

### Consolidated navigation (31 tabs → 11, +1 optional)

| New tab | Replaces / merges (v25) |
| --- | --- |
| Cockpit | Cockpit + Findings |
| Data | Summary + Tables + PDF + Manual Table |
| Analysis | Statistics + Distribution + Insights + Advanced Insights + Analytics + Charts |
| Derived & Units | Derived + Units |
| Compliance | Compliance + Expression Rules |
| Compare | Compare + Baseline |
| Filter & Search | Filter + Adv Filter + Search All |
| Notes | Notes |
| Reports | Report + Report Builder + Batch |
| Project | Workspace + Templates (profiles) + Export Bundle |
| Raw & Diagnostics | Raw + Diag |
| Admin (sidebar toggle, off by default) | Admin QA |

Each merged tab keeps the union of the underlying functionality (e.g.
Compliance now offers both threshold rules *and* custom expression rules on
the same table, with one combined violations export; Compare offers both
overlay/delta and baseline-verdict modes via a mode toggle).

### New shared modules

- `out_viewer/constants.py` -- `INDEX_NAMES` and related sets, previously
  redefined independently in 5 modules plus inlined ~7 more times.
- `out_viewer/html_report.py` -- one stylesheet and table/card/list/figure
  renderers, used by the Quick Report, Report Builder, and Batch report
  (previously three separate inline `<style>` blocks).
- `out_viewer/context.py` -- `AppContext`, the per-request bundle of
  `current_name`, `tables`, `unit_map`, etc. passed to every tab's
  `render(ctx)`.
- `out_viewer/session_data.py` -- session-state helpers (parsing cache,
  derived-column storage, comparisons, global search) used consistently by
  *full filename* (`current_name`), not file stem.
- `out_viewer/sample_data.py` -- the "Load sample demo file" dataset, split
  out of `app.py`.

### Bug fixes

- **Derived columns now show up everywhere.** v25's Distribution and
  Insights tabs looked up per-table session data using the file *stem*
  (`source_stem(current_name)`), while Derived Columns wrote it under the
  full filename. A derived column added on one tab silently failed to
  appear on those tabs. All tabs now consistently use `current_name`.
- **Manual table extraction now supports multiple promoted tables per
  file** and is keyed consistently with what the Report Builder's "Manual
  Tables" section reads.
- **`self_audit.source_metrics_text` now actually returns `bytes`**
  (matching its use in `st.download_button`) instead of being typed `-> str`
  while returning `.encode("utf-8")`.
- **Architecture audit findings are separated from general reminders.**
  v25's `architecture_recommendations` always appended two boilerplate
  reminders, so the Admin tab could never show "no issues" even when the
  codebase was healthy. `architecture_issues()` now reflects the actual
  audit; `general_reminders()` is shown separately.

### One canonical "Project file"

v25 had three overlapping save formats. v26 makes the **Export Bundle ZIP**
the canonical, fully round-trippable "Project file" --
`out_viewer.export_bundle.read_export_bundle` restores files, unit tags,
notes, and saved expression rules from a bundle previously produced by
`build_export_bundle`. The lighter Workspace JSON (files + units) and
Project Profile JSON (settings only) formats remain available under
"Advanced / partial exports" in the Project tab for the cases they're
genuinely better at -- sharing just a rules/units profile, for example.
Restoring a project no longer silently overwrites existing unit
tags/notes/rules unless you opt in.

### Admin/QA tools are now opt-in

Session inventory, source audit (which exports the running app's own file
paths and line counts), and reset controls now live behind a "Show admin /
QA tools" sidebar checkbox, off by default. This is maintainer tooling, not
part of the engineering analysis workflow.

## Tests

The test suite has been split from a single 336-line `tests/test_parser.py`
(which tested far more than the parser, with version-numbered test names
like `test_v24_...`/`test_v25_...`) into one file per area, named for what
they test: `test_parser.py`, `test_rules_and_filters.py`,
`test_derived_and_units.py`, `test_cockpit_and_reports.py`,
`test_advanced_insights_and_baseline.py`, `test_batch_and_manual_table.py`,
`test_diagnostics_profiles_notes.py`, `test_export_and_admin.py`, and a new
`test_session_data.py` covering the `current_name`-vs-stem fix and the
export-bundle round trip.

## Expected title

```text
.out Output Viewer — v26 Consolidated Cockpit
```


## v26d local launcher behavior

This local package changes the Windows launcher behavior:

- The installer CMD can be closed after the browser opens.
- Streamlit runs in a separate minimized `Out Viewer Server` window.
- Closing that server window stops `http://localhost:8600`.
- A cleaner desktop `.url` shortcut is created:
  - `Out Viewer Stable.url`
  - It opens `http://localhost:8600`
- Logs are written to:
  - `%LOCALAPPDATA%\OutViewerStable\out_viewer_server.log`

To stop the app, close the minimized `Out Viewer Server` window, or run the installer BAT again; it will close the old server on port 8600 first.
