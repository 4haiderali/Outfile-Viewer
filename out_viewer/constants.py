"""Shared constants used across out_viewer modules and the Streamlit app.

Centralizing these avoids the copy/paste drift that built up across the
v19-v25 releases, where the same "this column is a run/case index, not an
analysis variable" set was redefined independently in five different
modules (cockpit, visuals, advanced_insights, baseline, diagnostics) plus
several inline literals in app.py, columns.py, and parser.py. If a future
release needs to recognize another index-like name (for example "scenario"
or "iteration"), it now only needs to change here.

All sets below are matched against ``str(column).strip().lower()`` using
exact membership (``in`` / ``not in`` / ``.isin``) -- that is the convention
every existing call site already used, so these constants intentionally
preserve exact-match semantics rather than switching to substring matching.
"""

from __future__ import annotations

#: Column names (lowercased) that typically identify a run/case/sample
#: index rather than an analysis variable. Used to exclude these columns
#: from risk ranking, PCA / multivariate outliers, distribution
#: diagnostics, convergence checks, and default chart axes/series.
INDEX_NAMES = frozenset({"run", "case", "trial", "index", "sample", "step", "time"})

#: INDEX_NAMES plus "ft", which earlier versions also excluded specifically
#: when choosing default chart Y-series (some fixtures pair a "Run" column
#: with an "Ft" column that is also not a useful default series).
NON_SERIES_NAMES = INDEX_NAMES | {"ft"}

#: A narrower variant (no "time") used only when aligning a detected
#: "Statistics" block's column count against the main table's columns in
#: the parser. Kept separate deliberately -- a stray summary table whose
#: leading column is literally named "Time" should still be considered a
#: real data column for that specific alignment heuristic.
SUMMARY_ALIGNMENT_INDEX_NAMES = INDEX_NAMES - {"time"}

#: App identity, shared by the title, sidebar caption and self-audit.
#: The .bat installer keeps its own explicit marker string as a deliberate,
#: separate safety check -- see OutViewer_Install_Update_Run.bat.
APP_VERSION = "v1.0.1"
APP_RELEASE_NAME = "Desktop"
APP_TITLE = f"Outfile Viewer {APP_VERSION} | {APP_RELEASE_NAME}"
STABLE_PORT = 8600
