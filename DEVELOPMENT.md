# 🛠️ Development Guide

Welcome to the Outfile Viewer development guide! This document explains the architecture, how to set up your dev environment, and how to contribute.

---

## Table of Contents

1. [Architecture Overview](#-architecture-overview)
2. [Development Setup](#-development-setup)
3. [Project Structure](#-project-structure)
4. [Adding a New Tab](#-adding-a-new-tab)
5. [Extending the Parser](#-extending-the-parser)
6. [Testing](#-testing)
7. [Building & Releasing](#-building--releasing)

---

## 🏗️ Architecture Overview

### High-Level Flow

```
User Upload
    ↓
session_data.register_file()
    ↓
Parser (extracts tables, metadata, stats)
    ↓
AppContext (shared state container)
    ↓
Tab Modules (cockpit, data, analysis, etc.)
    ↓
Streamlit Renders UI
```

### Key Components

#### **app.py** (Main Entry Point)
- Configures Streamlit page
- Manages file upload & session history
- Builds `AppContext` from parsed data
- Dispatches to tab modules

```python
ctx = AppContext(
    current_name=...,
    parsed=parsed_data,
    tables=tables,
    # ... more state
)

for label, module in TAB_MODULES:
    with tab:
        module.render(ctx)  # Each tab calls render(ctx)
```

#### **out_viewer/context.py** (AppContext)
Central data container shared across all tabs. Contains:
- `parsed` — Raw parsed file data
- `tables` — Extracted data tables
- `metadata_df` — File metadata (version, date, etc.)
- `stats_df` — Statistics summary
- `unit_map` — Unit definitions for columns
- `file_history` — All uploaded files this session

**Never modify directly!** Use `st.session_state` for mutable state.

#### **out_viewer/session_data.py** (File Parsing)
Parses raw `.out` / `.txt` / `.log` / `.dat` files:

```python
def register_file(uploaded_file):
    """Parse file and store in session_state['file_history']"""
    content = uploaded_file.read().decode('utf-8')
    parsed = parse_outfile(content)  # <-- Main parser
    st.session_state['file_history'][uploaded_file.name] = {
        'parsed': parsed,
        'file_bytes': len(uploaded_file.getbuffer()),
    }
```

#### **out_viewer/tabs/** (Analysis Modules)
Each tab is a module with a `render(ctx)` function:

```python
# out_viewer/tabs/data_tab.py
def render(ctx: AppContext) -> None:
    """Render the Data tab"""
    st.subheader("Data Tables")
    for table in ctx.main_table_list:
        st.dataframe(table.data)
```

---

## 💻 Development Setup

### Prerequisites

- **Python 3.8+** (test with `python --version`)
- **pip** or **conda**
- **Git**

### Step 1: Clone & Create Virtual Environment

```bash
git clone https://github.com/4haiderali/Outfile-Viewer.git
cd Outfile-Viewer

# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt

# For development (linting, testing):
pip install black flake8 pytest pytest-cov
```

### Step 3: Run the App

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`

### Step 4: (Optional) Run Tests

```bash
pytest tests/
```

---

## 📁 Project Structure

```
Outfile-Viewer/
│
├── app.py                      # Main Streamlit app (orchestration)
├── launcher.py                 # Windows desktop launcher
├── requirements.txt            # Python dependencies
├── VERSION.txt                 # Version number (v1.26)
│
├── out_viewer/                 # Core application package
│   ├── __init__.py
│   │
│   ├── constants.py            # APP_TITLE, APP_VERSION, PORT, etc.
│   ├── context.py              # AppContext class (shared state)
│   ├── session_data.py         # File parsing & registration
│   ├── navigation.py           # TAB_DESCRIPTIONS, routing
│   │
│   ├── tabs/                   # Tab render modules
│   │   ├── __init__.py
│   │   ├── cockpit_tab.py      # Risk summary, key metrics
│   │   ├── data_tab.py         # Browse tables
│   │   ├── analysis_tab.py     # Trends, aggregations
│   │   ├── derived_tab.py      # Create derived columns
│   │   ├── compliance_tab.py   # Compliance checks
│   │   ├── compare_tab.py      # Multi-file comparison
│   │   ├── filter_tab.py       # Search & filter
│   │   ├── notes_tab.py        # Annotations
│   │   ├── reports_tab.py      # Excel export
│   │   ├── project_tab.py      # Save/load projects
│   │   ├── raw_diag_tab.py     # Raw data & diagnostics
│   │   └── admin_tab.py        # Admin tools (debug, reset)
│   │
│   ├── columns.py              # Column detection (main_table, numeric_columns)
│   ├── export.py               # Excel export logic
│   ├── ui_helpers.py           # Streamlit UI utilities
│   ├── ui_theme.py             # Theming & styling
│   ├── units.py                # Unit management
│   ├── visuals.py              # Charts & visualizations
│   │
│   ├── sample_data.py          # Sample .out file for demo
│   ├── workspace.py            # Project save/load
│   │
│   └── Icon.ico                # Windows tray icon
│
├── docs/
│   └── file_format.md          # Input file specification
│
├── examples/                   # Sample .out files (for testing/demo)
│   ├── example_1.out
│   ├── example_2.out
│   └── README.md               # How to use examples
│
├── tests/                      # Pytest tests
│   ├── __init__.py
│   ├── test_parser.py          # File parsing tests
│   ├── test_columns.py         # Column detection tests
│   └── conftest.py             # Pytest configuration
│
├── .github/
│   └── workflows/
│       ├── test.yml            # Run tests on push/PR
│       └── lint.yml            # Run linting on push/PR
│
├── .gitignore
├── OutfileViewerInstaller.iss  # Inno Setup config (Windows installer)
├── Setup.bat                   # Windows setup script
├── LICENSE
├── README.md
└── DEVELOPMENT.md              # <-- You are here
```

---

## ➕ Adding a New Tab

### Step 1: Create the Tab Module

Create `out_viewer/tabs/my_feature_tab.py`:

```python
"""MyFeature tab implementation."""

from out_viewer.context import AppContext
import streamlit as st


def render(ctx: AppContext) -> None:
    """Render the MyFeature tab.
    
    Args:
        ctx: Application context containing parsed data and session state.
    """
    st.subheader("My Feature")
    st.write("Insert your feature here!")
    
    # Access shared data
    st.write(f"Current file: {ctx.current_name}")
    st.write(f"Rows: {len(ctx.primary_table.data)}")
    
    # Use the tables
    for table in ctx.main_table_list:
        st.dataframe(table.data)
```

### Step 2: Register in app.py

Update `app.py` to include your tab:

```python
from out_viewer.tabs import (
    # ... existing imports ...
    my_feature_tab,  # <-- Add here
)

TAB_MODULES = [
    # ... existing tabs ...
    ("My Feature", my_feature_tab),  # <-- Add here
]
```

### Step 3: Add to Navigation Docs

Update `out_viewer/navigation.py`:

```python
TAB_DESCRIPTIONS = {
    # ... existing tabs ...
    "My Feature": "Describe what your tab does here.",
}
```

---

## 🔧 Extending the Parser

The parser lives in `out_viewer/session_data.py`. To handle new file formats or extract additional data:

### Step 1: Understand Current Parser

```python
def parse_outfile(content: str) -> dict:
    """Parse .out file content.
    
    Returns:
        {
            'lines': [...],           # Raw lines
            'tables': [...],          # Extracted tables
            'metadata': {...},        # File metadata
            'stats': {...},           # Statistics
            'diagnostics': {...},     # Errors/warnings
        }
    """
```

### Step 2: Add Custom Parsing Logic

```python
def parse_outfile(content: str) -> dict:
    lines = content.split('\n')
    
    # YOUR CUSTOM LOGIC HERE
    tables = extract_tables(lines)
    metadata = extract_metadata(lines)
    
    return {
        'lines': lines,
        'tables': tables,
        'metadata': metadata,
        'stats': extract_stats(tables),
        'diagnostics': extract_diagnostics(lines),
    }
```

### Step 3: Test It

Create `tests/test_parser.py`:

```python
from out_viewer.session_data import parse_outfile

def test_parse_sample_file():
    with open('examples/example_1.out', 'r') as f:
        content = f.read()
    
    result = parse_outfile(content)
    
    assert 'tables' in result
    assert len(result['tables']) > 0
    assert 'metadata' in result
```

Run tests:
```bash
pytest tests/test_parser.py -v
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=out_viewer

# Run specific test
pytest tests/test_parser.py::test_parse_sample_file
```

### Writing Tests

Create `tests/test_my_feature.py`:

```python
"""Tests for my_feature_tab.py"""

import pytest
from out_viewer.context import AppContext
from out_viewer.tabs import my_feature_tab


@pytest.fixture
def mock_ctx():
    """Create a mock AppContext for testing."""
    return AppContext(
        current_name="test.out",
        parsed={},
        tables=[],
        # ... other fields
    )


def test_render_displays_subheader(mock_ctx):
    """Test that render() displays the subheader."""
    # Note: Testing Streamlit apps is tricky; focus on logic, not UI
    assert mock_ctx.current_name == "test.out"
```

---

## 📦 Building & Releasing

### Version Bumping

1. Update `VERSION.txt`:
```
v1.27  # Increment version
```

2. Update version marker in `app.py`:
```python
# OUT_VIEWER_VERSION_MARKER=v1.27_FEATURE_NAME
```

3. Create a changelog entry in `CHANGELOG.md`

### Building Windows Installer

Requires **Inno Setup** (free, Windows-only):

1. Install [Inno Setup](https://jrsoftware.org/isdl.php)
2. Open `OutfileViewerInstaller.iss` in Inno Setup
3. Click **Build** → generates `.exe` in `installer_output/`

### Creating a Release

1. Commit & push all changes
2. Create a Git tag:
   ```bash
   git tag v1.27
   git push origin v1.27
   ```
3. [Create a GitHub Release](https://github.com/4haiderali/Outfile-Viewer/releases):
   - Tag: `v1.27`
   - Title: `Outfile Viewer v1.27`
   - Description: Copy from `CHANGELOG.md`
   - Upload `.exe` binary

---

## 🐛 Debugging Tips

### Enable Streamlit Debug Mode

```bash
streamlit run app.py --logger.level=debug
```

### Check Session State

Add to any tab:
```python
st.write("Session state:", st.session_state)
```

### Inspect Parsed Data

```python
st.write("Parsed tables:", ctx.parsed['tables'])
st.write("Metadata:", ctx.metadata_df)
```

### View Launcher Logs (Windows)

Windows launcher logs to:
```
%LOCALAPPDATA%\OutfileViewer\OutfileViewer.log
```

---

## ✅ Before Submitting a PR

- [ ] Code follows [PEP 8](https://pep8.org/) (run `black` and `flake8`)
- [ ] All tests pass (`pytest`)
- [ ] Added tests for new features
- [ ] Updated `CHANGELOG.md`
- [ ] Updated `README.md` or `DEVELOPMENT.md` if needed
- [ ] Commits have clear messages

```bash
# Auto-format code
black out_viewer/ tests/

# Check for linting errors
flake8 out_viewer/ tests/

# Run all tests
pytest

# Commit & push
git add .
git commit -m "feat: Add new tab for X"
git push origin feature/my-feature
```

---

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pandas API Reference](https://pandas.pydata.org/docs/)
- [Plotly Documentation](https://plotly.com/python/)
- [PEP 8 Style Guide](https://pep8.org/)

---

## ❓ Questions?

Open an issue or discussion: https://github.com/4haiderali/Outfile-Viewer/issues

Happy coding! 🚀
