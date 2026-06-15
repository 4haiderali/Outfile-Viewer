# 📋 Outfile Format Specification

This document describes the expected format and structure of `.out`, `.txt`, `.log`, and `.dat` files that Outfile Viewer can parse.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Section Types](#section-types)
4. [Table Format](#table-format)
5. [Examples](#examples)
6. [Troubleshooting](#troubleshooting)

---

## Overview

### Supported File Types

| Extension | Use Case | Parser Support |
|-----------|----------|-----------------|
| `.out` | Primary engineering simulation output | ✅ Full |
| `.txt` | Text export of output | ✅ Full |
| `.log` | Log files with similar structure | ✅ Partial |
| `.dat` | Data export format | ✅ Partial |

### Character Encoding

- **Preferred:** UTF-8
- **Fallback:** ASCII
- **NOT supported:** Binary, EBCDIC

Files with Unicode characters (é, ñ, 中文) are supported if properly encoded as UTF-8.

---

## File Structure

### Basic Organization

A well-formed `.out` file typically has this structure:

```
[HEADER]
(optional metadata about the run)

[SUMMARY/STATISTICS SECTION]
Key metrics and summary data

[TABLE DATA SECTION]
One or more data tables

[PROBABILITY/DISTRIBUTION SECTION]
(optional PDF or distribution data)

[DIAGNOSTICS/WARNINGS SECTION]
(optional debug info, warnings, errors)

[FOOTER]
(optional closing remarks)
```

### Minimal Example

```
RUN SUMMARY
===========
Run ID: SIM-2026-001
Date: 2026-06-15
Time: 14:23:15
Duration: 45.2 seconds

RESULTS
-------
Temperature (°C)    Pressure (Pa)    Status
75.3                101325           PASS
78.9                101500           PASS
82.1                102100           WARN
```

---

## Section Types

### 1. **Header/Metadata Section**

Metadata about the simulation run:

```
RUN PARAMETERS
==============
Simulation ID: TEST-001
Description: Temperature study
Date: 2026-06-15 14:23:15
Version: 1.2.3
Author: John Doe
```

**Expected fields:**
- Simulation/Run ID
- Date/Time (ISO 8601 preferred)
- Duration
- Version info
- Status (PASS, FAIL, WARNING, etc.)

### 2. **Summary/Statistics Section**

High-level statistics:

```
SUMMARY STATISTICS
==================
Total Runs: 100
Passed: 95
Failed: 3
Warnings: 2
Min Value: 45.2
Max Value: 98.7
Mean: 72.4
Std Dev: 12.1
```

**Expected content:**
- Count-based metrics (total, passed, failed)
- Value statistics (min, max, mean, median, stdev)
- Status summaries

### 3. **Table Data Section**

Structured tabular data:

```
RESULTS TABLE
=============
Index  Time(s)  Temp(°C)  Pressure(Pa)  Status
-----  -------  --------  -----------  --------
1      0.0      20.1      101325       PASS
2      1.0      25.3      101400       PASS
3      2.0      30.8      101500       PASS
...
```

**Table Format Guidelines:**

- **Header row:** Column names separated by whitespace or delimiters
- **Separator row:** Line of dashes `-----` (optional but recommended)
- **Data rows:** Values aligned with headers
- **Delimiters:** Spaces, tabs, commas, or pipes (`|`)

**Example table with pipe delimiters:**
```
| Index | Temperature | Pressure | Status |
|-------|-------------|----------|--------|
| 1     | 20.1        | 101325   | PASS   |
| 2     | 25.3        | 101400   | PASS   |
```

### 4. **Probability Distribution Section**

Probability or distribution data (PDF):

```
PROBABILITY DISTRIBUTIONS
==========================
Distribution: Temperature
Percentile  Value
0%          15.2
25%         22.1
50%         30.0
75%         42.3
100%        55.8
```

### 5. **Diagnostics Section**

Warnings, errors, or debug information:

```
DIAGNOSTICS
===========
WARNING: Model updated at iteration 500
ERROR: Convergence not achieved after 1000 iterations
DEBUG: Final residual = 1.2e-5
```

---

## Table Format

### Column Detection Rules

The parser uses these rules to identify table columns:

1. **Header Row:** Line followed by dashes or pipes
   ```
   Col1  Col2  Col3
   ----  ----  ----
   ```

2. **Fixed-width:** Columns aligned with consistent spacing
   ```
   Time    Temp   Pressure
   0.0     20.1   101325
   1.0     25.3   101400
   ```

3. **Delimited:** Columns separated by commas, tabs, or pipes
   ```
   Time,Temp,Pressure
   0.0,20.1,101325
   1.0,25.3,101400
   ```

### Data Types

The parser automatically infers column types:

| Type | Detection | Example |
|------|-----------|---------|
| **Integer** | All digits | `42`, `-5`, `0` |
| **Float** | Digits + decimal | `3.14`, `-2.5e-3`, `1.0` |
| **String** | Text | `PASS`, `ERROR`, `Model_v2` |
| **DateTime** | ISO 8601 or common formats | `2026-06-15`, `2026-06-15T14:23:15` |
| **Boolean** | TRUE/FALSE, Yes/No, 1/0 | `TRUE`, `False`, `yes`, `1` |

### Missing Values

Missing or invalid data is represented as:

- `NaN`, `N/A`, `NA`, `None`
- Empty cell
- `--` or `...`

Example:
```
Index  Value1  Value2  Status
1      10.5    N/A     PASS
2      12.3           PASS
3      15.1    NaN     WARN
```

---

## Examples

### Example 1: Simple Simulation Output

```
SIMULATION RUN v1.0
===================
Run ID: TEST-2026-001
Date: 2026-06-15
Time: 14:23:15

SUMMARY
=======
Total Cases: 3
Passed: 3
Failed: 0

RESULTS
=======
Case  Input   Output  Status
----  -----   ------  ------
1     100.0   205.3   PASS
2     150.0   310.1   PASS
3     200.0   415.8   PASS
```

### Example 2: Complex Multi-Table Output

```
THERMAL ANALYSIS REPORT
=======================
Project: Heat Transfer Study
Date: 2026-06-15 10:30:00
Model Version: 2.1

SUMMARY STATISTICS
==================
Total Nodes: 5000
Total Elements: 8432
Total Load Steps: 100
Convergence Status: SUCCESSFUL

NODAL TEMPERATURES (°C)
======================
NodeID  X(mm)   Y(mm)   Z(mm)   Temp(°C)   Status
------  -----   -----   -----   --------   ------
1       0.0     0.0     0.0     25.1       OK
2       10.0    0.0     0.0     26.3       OK
3       20.0    0.0     0.0     27.8       OK
4       30.0    0.0     0.0     28.9       OK
5       40.0    0.0     0.0     29.2       OK

ELEMENT STRESSES (MPa)
=====================
ElemID  Material  Stress(X)  Stress(Y)  VM_Stress  Factor_of_Safety
------  --------  ---------  ---------  ---------  ----------------
1       Steel     45.2       12.3       50.1       2.1
2       Steel     48.1       14.5       52.8       2.0
3       Steel     52.3       16.7       56.2       1.9

WARNINGS
========
WARNING: Element 47 is distorted (aspect ratio > 10)
WARNING: Node 234 has large displacement (42.3 mm)

COMPLETION
==========
Run completed successfully.
Elapsed Time: 125.3 seconds
```

---

## Troubleshooting

### My file won't parse. What's wrong?

#### Check 1: File Encoding
- Save file as **UTF-8** (not ANSI, UTF-16, etc.)
- In VS Code: Click "UTF-8" in bottom-right → Reopen with encoding → UTF-8
- Command line: `file myfile.out` should show "UTF-8"

#### Check 2: File Format
- File should be **text-based**, not binary
- Open in Notepad/VS Code and verify it's readable text
- Not a PDF, image, or other binary format

#### Check 3: Table Structure
- Table headers should be on **one line**
- Column names should be separated consistently (spaces, tabs, or commas)
- Data rows should have the same number of columns as headers

**Bad:**
```
Name            Age
John Doe        30 50    # Wrong: too many columns
Jane Smith
```

**Good:**
```
Name            Age
John Doe        30
Jane Smith      28
```

#### Check 4: Special Characters
- Unicode characters (é, ñ, 中文) are supported if UTF-8 encoded
- Avoid special shell characters in filenames: `<`, `>`, `|`, `*`, `?`
- Use underscores or hyphens instead: `test_file_2026.out`

### Parser Found Data But It Looks Wrong

#### Issue: Column data is shifted
- **Cause:** Inconsistent column alignment
- **Fix:** Ensure each data row has values aligned with column headers

#### Issue: Numbers are read as text
- **Cause:** Extra spaces or special characters
- **Fix:** Remove leading/trailing spaces, use only digits and decimal points

**Bad:**
```
Value
$ 100.50
```

**Good:**
```
Value
100.50
```

#### Issue: Date/Time not recognized
- **Cause:** Non-standard date format
- **Fix:** Use ISO 8601 format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`

**Bad:**
```
Date
06/15/2026
15-Jun-2026
```

**Good:**
```
Date
2026-06-15
2026-06-15T14:23:15
```

### Still having issues?

1. **Check the error message** displayed in Outfile Viewer
2. **Enable debug mode** (check browser console: F12 → Console)
3. **Report the bug** with:
   - File size and format
   - First 50 lines of the file (sanitized)
   - Error message and screenshot
   - Python version and OS

[Report an issue →](https://github.com/4haiderali/Outfile-Viewer/issues)

---

## Best Practices

### For File Creators

1. **Use consistent formatting:**
   - Align columns neatly
   - Use consistent delimiters
   - Keep column widths reasonable

2. **Include clear headers:**
   - Use descriptive column names
   - Avoid spaces in header names (use underscores: `Temperature_C`)
   - Include units in header: `Temperature(°C)` not just `Temperature`

3. **Add metadata:**
   - Date/time of run
   - Simulation ID or name
   - Version/configuration info
   - Status (passed/failed)

4. **Use UTF-8 encoding** for all files

5. **Document non-obvious sections** with section headers

---

## Contact & Support

For questions about file format:

- [Open a discussion](https://github.com/4haiderali/Outfile-Viewer/discussions)
- [Report an issue](https://github.com/4haiderali/Outfile-Viewer/issues)
- Provide a sanitized sample file for analysis

---

Last updated: 2026-06-15
