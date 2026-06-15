"""Admin/QA tab: release verification, session inventory, source audit,
and reset controls.

In v25 this was a regular tab any user could click, mixed in with the
engineering workflow tabs. It's developer/maintainer tooling (it literally
exports the running app's own source file paths and line counts), so v26
only mounts it when "Show admin / QA tools" is enabled in the sidebar --
off by default.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..self_audit import architecture_issues, audit_project, general_reminders, source_metrics_text
from ..session_tools import reset_analysis_state, session_inventory
from ..ui_helpers import build_download_button, dataframe_view


def render(ctx) -> None:
    st.subheader("Admin / QA Tools")
    st.write("Use these tools to inspect session state and export maintainability diagnostics.")

    st.markdown("#### Session Inventory")
    inventory = session_inventory(st.session_state)
    dataframe_view(inventory)
    build_download_button("Download session inventory", inventory, "session_inventory.csv")

    st.markdown("#### Source Audit")
    root = Path(__file__).resolve().parents[2]
    audit_df = audit_project(root)
    dataframe_view(audit_df)
    build_download_button("Download source audit CSV", audit_df, "source_audit.csv")
    st.download_button(
        "Download source audit markdown",
        data=source_metrics_text(root),
        file_name="source_audit.md",
        mime="text/markdown",
    )

    st.markdown("#### Architecture Findings")
    issues = architecture_issues(audit_df)
    if not issues:
        st.success("No architecture issues -- all files are within the configured size thresholds.")
    else:
        for issue in issues:
            st.warning(issue)

    st.markdown("#### General Reminders")
    for reminder in general_reminders():
        st.caption(f"• {reminder}")

    st.markdown("#### Reset Controls")
    c1, c2 = st.columns(2)
    if c1.button("Reset analysis state, keep loaded files"):
        reset_analysis_state(st.session_state, keep_files=True)
        st.success("Analysis state reset. Loaded files kept.")
        st.rerun()
    if c2.button("Reset everything"):
        reset_analysis_state(st.session_state, keep_files=False)
        st.success("Everything reset.")
        st.rerun()
