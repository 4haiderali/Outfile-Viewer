"""Project tab: save/restore a full session.

v25 had three independent, partially-overlapping save formats:
  - Workspace JSON (files + unit maps, restorable from the sidebar)
  - Project Profile JSON (units + expression rules + notes, no files)
  - Export Bundle ZIP (everything, but write-only -- no restore)

For v26 the Export Bundle ZIP is the canonical, fully round-trippable
"Project file" (see ``out_viewer.export_bundle.read_export_bundle``). The
lighter JSON formats remain available under "Advanced / partial exports"
for the cases they're genuinely good at: sharing just a rules/units profile,
or a smaller files+units workspace, without the full bundle (reports, CSVs).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ..export import source_stem
from ..export_bundle import build_export_bundle, read_export_bundle
from ..profiles import build_profile_payload, read_profile_payload
from ..session_data import register_raw_file
from ..ui_helpers import dataframe_view
from ..visuals import memory_summary_table
from ..workspace import build_workspace_payload


def _collect_unit_maps() -> dict:
    return {k: v for k, v in st.session_state.items() if str(k).startswith("unit_map_") and isinstance(v, dict)}


def _collect_note_maps() -> dict:
    return {k: v for k, v in st.session_state.items() if str(k).startswith("notes_") and isinstance(v, list)}


def render(ctx) -> None:
    st.subheader("Project File (recommended)")
    st.write(
        "Download one ZIP containing your source files, unit tags, notes, saved expression "
        "rules, and a batch report. Restoring this ZIP brings everything back."
    )

    bundle = build_export_bundle(
        st.session_state.get("file_history", {}),
        unit_maps=_collect_unit_maps(),
        notes=_collect_note_maps(),
        rules=st.session_state.get("saved_expression_rules", []),
    )
    st.download_button(
        "Download project (.zip)",
        data=bundle,
        file_name="out_viewer_project.zip",
        mime="application/zip",
    )

    st.markdown("#### Restore Project")
    overwrite = st.checkbox(
        "Overwrite existing unit tags / notes / expression rules for files already loaded",
        value=False,
        help="Off by default so restoring a project never silently replaces work you've already done this session.",
    )
    project_upload = st.file_uploader("Restore project (.zip)", type=["zip"], key="project_restore")
    if project_upload is not None:
        try:
            payload = read_export_bundle(project_upload.getvalue())
            for item in payload["files"]:
                register_raw_file(item["name"], item["bytes"])
            for key, value in payload["unit_maps"].items():
                if overwrite or key not in st.session_state:
                    st.session_state[key] = value
            for key, value in payload["notes"].items():
                if overwrite or key not in st.session_state:
                    st.session_state[key] = value
            if payload["expression_rules"]:
                if overwrite or not st.session_state.get("saved_expression_rules"):
                    st.session_state["saved_expression_rules"] = payload["expression_rules"]
            st.success(f"Restored project with {len(payload['files'])} file(s).")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not restore project: {exc}")

    st.markdown("#### Workspace Contents")
    dataframe_view(memory_summary_table(st.session_state.get("file_history", {})))

    with st.expander("Advanced / partial exports", expanded=False):
        st.caption(
            "These smaller formats are useful for sharing just settings (a rules/units profile) "
            "or just files+units, without the reports and CSVs in the full project ZIP."
        )

        st.markdown("##### Workspace JSON (files + unit tags)")
        workspace_bytes = build_workspace_payload(st.session_state.get("file_history", {}), _collect_unit_maps())
        st.download_button(
            "Download workspace JSON",
            data=workspace_bytes,
            file_name="out_viewer_workspace.json",
            mime="application/json",
        )
        st.caption("Restore a workspace JSON from the file uploader in the sidebar.")

        st.markdown("##### Project Profile JSON (settings only, no files)")
        profile_name = st.text_input("Profile name", value=f"{source_stem(ctx.current_name)} profile")
        profile_bytes = build_profile_payload(
            name=profile_name,
            unit_maps=_collect_unit_maps(),
            expression_rules=st.session_state.get("saved_expression_rules", []),
            notes=_collect_note_maps(),
            chart_defaults={},
        )
        st.download_button(
            "Download project profile JSON",
            data=profile_bytes,
            file_name=f"{ctx.stem}_out_viewer_profile.json",
            mime="application/json",
        )

        uploaded_profile = st.file_uploader("Apply project profile (.json)", type=["json"], key="profile_apply")
        if uploaded_profile is not None:
            try:
                profile = read_profile_payload(uploaded_profile.getvalue())
                for key, value in profile.get("unit_maps", {}).items():
                    st.session_state[key] = value
                st.session_state["saved_expression_rules"] = profile.get("expression_rules", [])
                for key, value in profile.get("notes", {}).items():
                    st.session_state[key] = value
                st.success(f"Applied profile: {profile.get('name', 'Unnamed')}")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not apply profile: {exc}")

        st.markdown("##### Saved Expression Rules")
        rules_df = pd.DataFrame(st.session_state.get("saved_expression_rules", []))
        if rules_df.empty:
            st.info("No saved expression rules yet.")
        else:
            dataframe_view(rules_df)
