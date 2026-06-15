"""Notes tab: free-text annotations scoped to a file, run, column, chart,
or report. Unchanged from v25 other than reading values from ``ctx``.
"""

from __future__ import annotations

import streamlit as st

from ..notes import add_note, notes_key, notes_to_dataframe
from ..ui_helpers import build_download_button, dataframe_view


def render(ctx) -> None:
    st.subheader("Notes / Annotations")
    key = notes_key(ctx.current_name)
    st.session_state.setdefault(key, [])

    scope = st.selectbox("Note scope", ["File", "Run", "Column", "Chart", "Report"], key="note_scope")
    target = st.text_input("Target / reference", value=ctx.current_name if scope == "File" else "", key="note_target")
    note_text = st.text_area("Note", key="note_text")
    if st.button("Add note"):
        st.session_state[key] = add_note(st.session_state[key], scope=scope, target=target, note=note_text)
        st.success("Note added.")
        st.rerun()

    notes_df = notes_to_dataframe(st.session_state[key])
    if notes_df.empty:
        st.info("No notes yet.")
    else:
        dataframe_view(notes_df)
        build_download_button("Download notes as CSV", notes_df, f"{ctx.stem}_notes.csv")
