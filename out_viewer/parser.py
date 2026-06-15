import re
from dataclasses import dataclass
from typing import Any, List, Optional

import pandas as pd

from .constants import INDEX_NAMES, SUMMARY_ALIGNMENT_INDEX_NAMES


@dataclass(frozen=True)
class DetectedTable:
    name: str
    header_line: int
    columns: List[str]
    data: pd.DataFrame
    kind: str = "table"


def is_number(value: str) -> bool:
    try:
        float(value.replace("D", "E").replace("d", "e"))
        return True
    except Exception:
        return False


def to_number(value: str) -> Any:
    number = float(value.replace("D", "E").replace("d", "e"))
    return int(number) if number.is_integer() else number


def is_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and set(stripped) <= {"-", "=", "_"}


def safe_column_names(columns: List[str]) -> List[str]:
    counts = {}
    output = []

    for raw_col in columns:
        col = str(raw_col).strip() or "Column"
        if col not in counts:
            counts[col] = 0
            output.append(col)
        else:
            counts[col] += 1
            output.append(f"{col}_{counts[col]}")

    return output


def normalize_header(tokens: List[str]) -> List[str]:
    output = []
    index = 0

    while index < len(tokens):
        current = tokens[index]

        if index + 1 < len(tokens) and current.lower() == "run" and tokens[index + 1] == "#":
            output.append("Run")
            index += 2
            continue

        if current == "#":
            if output:
                output[-1] = f"{output[-1]} #"
            else:
                output.append("Index")
            index += 1
            continue

        output.append(current)
        index += 1

    return safe_column_names(output)


def detect_header(line: str) -> Optional[List[str]]:
    if is_separator(line):
        return None

    tokens = line.strip().split()
    if len(tokens) < 2:
        return None

    if any(is_number(token) for token in tokens):
        return None

    joined = " ".join(tokens)
    if ":" in joined or len(tokens) > 12:
        return None

    if "#" in tokens:
        return normalize_header(tokens)

    if any(token.lower() in INDEX_NAMES for token in tokens):
        return normalize_header(tokens)

    if 3 <= len(tokens) <= 12 and all(len(token) <= 20 for token in tokens):
        return normalize_header(tokens)

    return None


def parse_numeric_row_any(line: str) -> Optional[List[Any]]:
    tokens = line.strip().split()
    if not tokens:
        return None

    if not all(is_number(token) for token in tokens):
        return None

    return [to_number(token) for token in tokens]


def parse_numeric_row(line: str, expected_len: int) -> Optional[List[Any]]:
    row = parse_numeric_row_any(line)
    if row is None or len(row) != expected_len:
        return None
    return row


def parse_metric_line(line: str):
    match = re.match(r"^(.+?):\s+(.+)$", line.strip())
    if not match:
        return None

    label = match.group(1).strip()
    values = match.group(2).strip().split()

    if values and all(is_number(value) for value in values):
        return label, [float(to_number(value)) for value in values]

    return None


def is_probability_section_title(line: str) -> bool:
    lowered = line.lower()
    return "probability density function" in lowered or "probability density functions" in lowered


def probability_header_from_line(row_width: int) -> List[str]:
    if row_width == 4:
        return ["Center of Range", "Probability (%)", "Cumulative Prob. (%)", "Cumulative Prob."]
    return [f"Value {index + 1}" for index in range(row_width)]


def parse_info_line(line: str):
    stripped = line.strip()

    if not stripped or is_separator(stripped):
        return None

    if parse_metric_line(stripped):
        return None

    if is_probability_section_title(stripped):
        return "Section", stripped

    if ":" in stripped:
        left, right = stripped.split(":", 1)
        return left.strip(), right.strip()

    if re.search(r"(run\s*#\s*\d+)", stripped, flags=re.IGNORECASE):
        return "Detected run reference", stripped

    return "Info", stripped


def line_is_good_table_title(key: str, value: str) -> bool:
    text = f"{key} {value}".strip().lower()

    if not text or len(text) > 100:
        return False

    title_signals = {
        "case", "study", "scenario", "contingency", "section",
        "output", "table", "report", "results", "summary", "file",
    }

    if any(signal in text for signal in title_signals):
        return True

    letters = [char for char in value if char.isalpha()]
    if letters and len(value) <= 60:
        uppercase_ratio = sum(char.isupper() for char in letters) / len(letters)
        return uppercase_ratio >= 0.65

    return False


def make_stats_dataframe(metric_rows, tables):
    if not metric_rows:
        return pd.DataFrame()

    max_len = max(len(row["Values"]) for row in metric_rows)
    rows = []

    for row in metric_rows:
        values = row["Values"] + [None] * (max_len - len(row["Values"]))
        rows.append([row["Line"], row["Metric"]] + values)

    stats_df = pd.DataFrame(
        rows,
        columns=["Line", "Metric"] + [f"Value {index + 1}" for index in range(max_len)],
    )

    main_tables = [table for table in tables if table.kind == "main"]
    if main_tables:
        main = max(main_tables, key=lambda table: len(table.data))
        non_index_columns = [
            column
            for column in main.columns
            if column.lower() not in SUMMARY_ALIGNMENT_INDEX_NAMES
        ]
        if len(non_index_columns) == max_len:
            stats_df.columns = ["Line", "Metric"] + non_index_columns

    return stats_df


class OutputFileParser:
    """
    Dynamic parser.

    Required sections: none.
    Optional sections:
    - metadata / summary text
    - main numeric tables
    - metric/statistical rows
    - probability-density tables
    """

    def __init__(self):
        self.lines = []
        self.metadata = []
        self.metric_rows = []
        self.tables: List[DetectedTable] = []

        self.current_header = None
        self.current_rows = []
        self.current_header_line = None
        self.pending_title = None

        self.probability_title = None
        self.probability_header_seen = False
        self.probability_rows = []
        self.probability_start_line = None

        self.diagnostics = {
            "warnings": [],
            "main_tables_detected": 0,
            "probability_tables_detected": 0,
            "metric_rows_detected": 0,
            "lines_processed": 0,
        }

    def parse(self, text: str):
        self.lines = [line.rstrip("\n\r") for line in text.splitlines()]
        self.diagnostics["lines_processed"] = len(self.lines)

        for line_number, raw_line in enumerate(self.lines, start=1):
            self._process_line(line_number, raw_line)

        self._flush_table()
        self._flush_probability_table()

        metadata_df = pd.DataFrame(self.metadata, columns=["Line", "Item", "Value"])
        stats_df = make_stats_dataframe(self.metric_rows, self.tables)

        return {
            "lines": self.lines,
            "metadata": metadata_df,
            "stats": stats_df,
            "tables": self.tables,
            "diagnostics": self.diagnostics,
        }

    def _process_line(self, line_number: int, raw_line: str):
        line = raw_line.strip()

        if not line or is_separator(line):
            return

        if self.probability_title:
            row_any = parse_numeric_row_any(line)

            if row_any is not None:
                self.probability_rows.append(row_any)
                return

            if not self.probability_header_seen:
                self.probability_header_seen = True
                return

            if self.probability_rows:
                self._flush_probability_table()
            else:
                self.metadata.append({"Line": self.probability_start_line, "Item": "Section", "Value": self.probability_title})
                self.probability_title = None
                self.probability_header_seen = False

        if self.current_header:
            row = parse_numeric_row(line, len(self.current_header))
            if row is not None:
                self.current_rows.append(row)
                return

            if self.current_rows:
                self._flush_table()

        if is_probability_section_title(line):
            self._flush_table()
            self._flush_probability_table()
            self.probability_title = line
            self.probability_header_seen = False
            self.probability_rows = []
            self.probability_start_line = line_number
            self.metadata.append({"Line": line_number, "Item": "Section", "Value": line})
            return

        header = detect_header(line)
        if header:
            self._flush_table()
            self.current_header = header
            self.current_rows = []
            self.current_header_line = line_number
            return

        metric = parse_metric_line(line)
        if metric:
            label, values = metric
            self.metric_rows.append({"Line": line_number, "Metric": label, "Values": values})
            self.diagnostics["metric_rows_detected"] += 1
            return

        info = parse_info_line(line)
        if info:
            key, value = info

            if key == "Info" and parse_numeric_row_any(value) is not None:
                return

            self.metadata.append({"Line": line_number, "Item": key, "Value": value})

            if key not in {"Section"} and line_is_good_table_title(key, value):
                self.pending_title = value if key == "Info" else f"{key}: {value}".strip(": ")

    def _flush_table(self):
        if self.current_header and self.current_rows:
            df = pd.DataFrame(self.current_rows, columns=self.current_header)
            name = self.pending_title or f"Table starting line {self.current_header_line}"

            self.tables.append(
                DetectedTable(
                    name=name,
                    header_line=self.current_header_line or 0,
                    columns=self.current_header,
                    data=df,
                    kind="main",
                )
            )
            self.diagnostics["main_tables_detected"] += 1

        self.current_header = None
        self.current_rows = []
        self.current_header_line = None
        self.pending_title = None

    def _flush_probability_table(self):
        if self.probability_title and self.probability_rows:
            width = len(self.probability_rows[0])
            valid_rows = [row for row in self.probability_rows if len(row) == width]

            if len(valid_rows) != len(self.probability_rows):
                self.diagnostics["warnings"].append(
                    f"Probability table at line {self.probability_start_line} had inconsistent row widths; invalid rows skipped."
                )

            columns = probability_header_from_line(width)
            df = pd.DataFrame(valid_rows, columns=columns)

            self.tables.append(
                DetectedTable(
                    name=self.probability_title,
                    header_line=self.probability_start_line or 0,
                    columns=columns,
                    data=df,
                    kind="probability",
                )
            )
            self.diagnostics["probability_tables_detected"] += 1

        self.probability_title = None
        self.probability_header_seen = False
        self.probability_rows = []
        self.probability_start_line = None


def parse_output(text: str):
    return OutputFileParser().parse(text)
