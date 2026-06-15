"""Short descriptions of each top-level tab, shown in a sidebar "What's in
each tab?" expander.

v19-v25 used a parallel ``WORKFLOW_TABS``/``NAV_DESCRIPTIONS`` structure to
group ~31 tabs into 6 sidebar "navigation modes" -- a second navigation
system layered on top of Streamlit's own tabs. v26 has few enough top-level
tabs (11, or 12 with Admin/QA) that one tab bar is enough; this module now
only provides the one-line descriptions for the optional help expander.
"""

TAB_DESCRIPTIONS = {
    "Cockpit": "Snapshot, plain-English summary, narrative findings, risk ranking, fingerprint, and multivariate outlier snapshot.",
    "Data": "Detected summary, main tables, PDF/probability tables, and manual table extraction.",
    "Analysis": "Statistics, distribution diagnostics, outliers & ranking (incl. PCA), and dynamic charts.",
    "Derived & Units": "Add derived columns from formulas, and tag units for analysis columns.",
    "Compliance": "Threshold (min/max) rules and custom boolean-expression rules, with violating-row exports.",
    "Compare": "Overlay two files and inspect deltas, or get a baseline pass/fail verdict.",
    "Filter & Search": "Quick filters, an AND/OR condition builder, and global search across all tables.",
    "Notes": "Free-text annotations scoped to a file, run, column, chart, or report.",
    "Reports": "Quick HTML report, a customizable report builder, and a multi-file batch report.",
    "Project": "Save/restore a full project (files, units, notes, rules) as one ZIP, plus partial exports.",
    "Raw & Diagnostics": "Browse/search the raw file text and review parser diagnostics.",
    "Admin": "Session inventory, source audit, and reset controls (maintainer tooling).",
}
