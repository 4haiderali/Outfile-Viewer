# OUT_VIEWER_VERSION_MARKER=v1.26_BACKGROUND_LAUNCHER
"""Streamlit entry point for the .out Output Viewer.

v26 consolidates the 31 tabs that had accumulated across v19-v25 into 11
top-level tabs (12 with Admin/QA enabled), each composed from
``out_viewer/tabs/*`` render modules. This file is now orchestration only:
file management, building the shared :class:`AppContext`, and dispatching
to each tab's ``render(ctx)``. See ``out_viewer/context.py`` and
``out_viewer/tabs/__init__.py`` for the structure.
"""

import streamlit as st

from out_viewer.columns import main_table, main_tables, numeric_columns, probability_tables
from out_viewer.constants import APP_TITLE, APP_VERSION, STABLE_PORT
from out_viewer.context import AppContext
from out_viewer.export import source_stem
from out_viewer.sample_data import SAMPLE_OUT_TEXT
from out_viewer.session_data import register_file, register_raw_file
from out_viewer.navigation import TAB_DESCRIPTIONS
from out_viewer.tabs import (
    admin_tab,
    analysis_tab,
    compare_tab,
    compliance_tab,
    cockpit_tab,
    data_tab,
    derived_tab,
    filter_tab,
    notes_tab,
    project_tab,
    raw_diag_tab,
    reports_tab,
)
from out_viewer.ui_helpers import dataframe_view
from out_viewer.ui_theme import inject_theme, render_hero
from out_viewer.units import default_unit_map, unit_state_key
from out_viewer.visuals import memory_summary_table
from out_viewer.workspace import read_workspace_payload


st.set_page_config(page_title=f".out Viewer - {APP_VERSION}", layout="wide")
inject_theme()

st.title(APP_TITLE)
st.caption(f"{APP_VERSION} · stable port {STABLE_PORT}")
render_hero(
    "Analysis Cockpit",
    "Upload one or more .out-style files to get a plain-English summary, risk ranking, "
    "compliance checks, comparisons, and exportable reports.",
)

if "file_history" not in st.session_state:
    st.session_state["file_history"] = {}
if "saved_expression_rules" not in st.session_state:
    st.session_state["saved_expression_rules"] = []
if "manual_tables" not in st.session_state:
    st.session_state["manual_tables"] = {}

with st.sidebar:
    st.subheader("Viewer")
    st.caption(APP_VERSION)

    st.divider()
    show_admin_tools = st.checkbox(
        "Show admin / QA tools",
        value=False,
        help="Session inventory, source audit, and reset controls. Hidden by default -- this is "
             "maintainer tooling, not part of the engineering workflow.",
        key="show_admin_tools",
    )

    st.divider()
    with st.expander("What's in each tab?", expanded=False):
        for tab_name, description in TAB_DESCRIPTIONS.items():
            if tab_name == "Admin" and not show_admin_tools:
                continue
            st.markdown(f"**{tab_name}** — {description}")

    st.divider()
    if st.button("Load sample demo file"):
        register_raw_file("sample_demo.out", SAMPLE_OUT_TEXT.encode("utf-8"))
        st.rerun()

    workspace_upload = st.file_uploader("Restore workspace (.json)", type=["json"], key="workspace_restore")
    if workspace_upload is not None:
        try:
            restored_files, restored_units = read_workspace_payload(workspace_upload.getvalue())
            for item in restored_files:
                register_raw_file(item["name"], item["bytes"])
            for key, value in restored_units.items():
                st.session_state[key] = value
            st.success(f"Restored workspace with {len(restored_files)} file(s).")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not restore workspace: {exc}")
    st.caption("For a full round-trip save (files, units, notes, rules), use the Project tab instead.")

    st.divider()
    st.caption("Upload one or more files. Parsed files stay in session history.")

uploaded_files = st.file_uploader(
    "Choose one or more .out / .txt / .log / .dat files",
    type=["out", "txt", "log", "dat"],
    accept_multiple_files=True,
)

if uploaded_files:
    for item in uploaded_files:
        try:
            register_file(item)
        except Exception as exc:
            st.error(f"Failed to parse {item.name}: {exc}")

if not st.session_state["file_history"]:
    c1, c2, c3 = st.columns(3)
    c1.info("Upload one or more text-based output files.")
    c2.info("Sections such as summary, PDF, statistics, and tables are optional.")
    c3.info("Or click \"Load sample demo file\" in the sidebar to explore with example data.")
    st.stop()

with st.sidebar:
    file_names = list(st.session_state["file_history"].keys())
    current_name = st.selectbox("Session history", file_names, index=len(file_names) - 1, key="session_history_select")
    with st.expander("Files currently in memory", expanded=False):
        dataframe_view(memory_summary_table(st.session_state["file_history"]))
    if st.button("Clear session history"):
        st.session_state["file_history"] = {}
        st.rerun()

record = st.session_state["file_history"][current_name]
parsed = record["parsed"]
tables = parsed["tables"]
primary_table = main_table(tables)

unit_key = unit_state_key(current_name)
if primary_table is not None:
    primary_numeric_columns = numeric_columns(primary_table.data)
    st.session_state.setdefault(unit_key, default_unit_map(primary_numeric_columns))
    # Carry forward inferred units for any columns not present when the unit map was first built
    # (e.g. derived columns added after the unit map was created), without clobbering edits.
    for col, unit in default_unit_map(primary_numeric_columns).items():
        st.session_state[unit_key].setdefault(col, unit)
else:
    st.session_state.setdefault(unit_key, {})

ctx = AppContext(
    current_name=current_name,
    record=record,
    parsed=parsed,
    tables=tables,
    metadata_df=parsed["metadata"],
    stats_df=parsed["stats"],
    main_table_list=main_tables(tables),
    pdf_table_list=probability_tables(tables),
    primary_table=primary_table,
    diagnostics=parsed.get("diagnostics", {}),
    stem=source_stem(current_name),
    unit_key=unit_key,
    unit_map=st.session_state[unit_key],
    file_history=st.session_state["file_history"],
)

st.caption(f"Loaded: `{current_name}` — {len(ctx.file_bytes):,} bytes — {len(parsed['lines']):,} lines")


TAB_MODULES = [
    ("Cockpit", cockpit_tab),
    ("Data", data_tab),
    ("Analysis", analysis_tab),
    ("Derived & Units", derived_tab),
    ("Compliance", compliance_tab),
    ("Compare", compare_tab),
    ("Filter & Search", filter_tab),
    ("Notes", notes_tab),
    ("Reports", reports_tab),
    ("Project", project_tab),
    ("Raw & Diagnostics", raw_diag_tab),
]
if show_admin_tools:
    TAB_MODULES.append(("Admin", admin_tab))

tabs = st.tabs([label for label, _ in TAB_MODULES])
for (label, module), tab in zip(TAB_MODULES, tabs):
    with tab:
        module.render(ctx)
