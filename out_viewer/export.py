import io
import re
from pathlib import Path

import pandas as pd


def source_stem(filename: str) -> str:
    return Path(filename).stem or "output"


def table_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def build_excel_workbook(parsed: dict) -> bytes:
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        metadata = parsed["metadata"]
        stats = parsed["stats"]
        tables = parsed["tables"]

        wrote_sheet = False

        if not metadata.empty:
            metadata.to_excel(writer, sheet_name="Summary", index=False)
            wrote_sheet = True

        if not stats.empty:
            stats.to_excel(writer, sheet_name="Statistics", index=False)
            wrote_sheet = True

        used_names = set()
        for index, table in enumerate(tables, start=1):
            base_name = f"{table.kind[:3].upper()}_{index}_{table.name[:18]}"
            sheet_name = re.sub(r"[\[\]\:\*\?\/\\]", "_", base_name)[:31] or f"Table_{index}"

            original = sheet_name
            suffix = 1
            while sheet_name in used_names:
                suffix_text = f"_{suffix}"
                sheet_name = f"{original[:31-len(suffix_text)]}{suffix_text}"
                suffix += 1

            used_names.add(sheet_name)
            table.data.to_excel(writer, sheet_name=sheet_name, index=False)
            wrote_sheet = True

        if not wrote_sheet:
            pd.DataFrame({"Message": ["No tables or summary sections detected."]}).to_excel(
                writer, sheet_name="Empty", index=False
            )

    return buffer.getvalue()
