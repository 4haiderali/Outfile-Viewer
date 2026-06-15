import pandas as pd
import streamlit as st

from .export import table_to_csv_bytes


def _arrow_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Streamlit serializes dataframes through Arrow. Object columns with mixed
    Python types, such as [1, 2, "Yes"], can trigger noisy Arrow conversion
    warnings. Keep numeric columns numeric, but stringify mixed object columns.
    """
    safe = df.copy()

    for column in safe.columns:
        if safe[column].dtype == "object":
            non_null = safe[column].dropna()
            type_names = {type(value).__name__ for value in non_null}

            if len(type_names) > 1:
                safe[column] = safe[column].astype(str)

    return safe


def dataframe_view(df: pd.DataFrame, *, hide_index=True):
    safe_df = _arrow_safe_dataframe(df)
    st.dataframe(safe_df, width="stretch", hide_index=hide_index)


def plotly_view(fig):
    st.plotly_chart(fig, width="stretch")


def build_download_button(label: str, df: pd.DataFrame, filename: str):
    try:
        csv_bytes = table_to_csv_bytes(df)
    except Exception as exc:
        st.error(f"Could not prepare CSV download: {exc}")
        return

    st.download_button(label, data=csv_bytes, file_name=filename, mime="text/csv")


def copy_tsv_button(df: pd.DataFrame, button_text: str = "Download displayed table as TSV"):
    """
    Clean Streamlit-native TSV export.

    Earlier builds used st.components.v1.html for a JavaScript clipboard button,
    but current Streamlit emits repeated deprecation warnings for that API.
    This keeps the workflow quick for Excel without console noise.
    """
    try:
        tsv_bytes = df.to_csv(sep="\t", index=False).encode("utf-8")
    except Exception as exc:
        st.error(f"Could not prepare TSV export: {exc}")
        return

    label = button_text.replace("Copy", "Download").replace("copy", "download")
    st.download_button(
        label,
        data=tsv_bytes,
        file_name="table_export.tsv",
        mime="text/tab-separated-values",
    )



def styled_dataframe_view(df: pd.DataFrame, *, preset: str = "numeric", hide_index=True):
    """
    Styled Streamlit dataframe with a safe fallback.

    Presets:
    - numeric: light numeric heatmap over numeric columns
    - risk: numeric heatmap plus Risk Score bar
    - compliance: bold Status column plus numeric heatmap
    """
    safe_df = _arrow_safe_dataframe(df)

    try:
        styler = safe_df.style

        numeric_cols = [
            col for col in safe_df.columns
            if pd.api.types.is_numeric_dtype(safe_df[col])
        ]

        if numeric_cols:
            styler = styler.background_gradient(subset=numeric_cols)

        if preset == "risk" and "Risk Score" in safe_df.columns:
            styler = styler.bar(subset=["Risk Score"])

        if preset == "compliance" and "Status" in safe_df.columns:
            styler = styler.map(lambda value: "font-weight: 700", subset=["Status"])

        st.dataframe(styler, width="stretch", hide_index=hide_index)
    except Exception:
        dataframe_view(safe_df, hide_index=hide_index)
