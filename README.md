# 📊 Outfile Viewer

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-red)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-0078d4)](https://github.com/4haiderali/Outfile-Viewer)

> **Transform engineering output files into actionable insights.** Parse `.out`, `.txt`, `.log`, and `.dat` files with one-click analysis, risk ranking, compliance checks, and exportable reports.

## 🎯 What It Does

Outfile Viewer is a **desktop application** that automates the tedious task of parsing and analyzing engineering simulation output files. Instead of manually scrolling through thousands of lines of raw text:

✅ **Automatic Parsing** — Extracts tables, metadata, statistics, and diagnostics  
✅ **Plain-English Summary** — Get instant risk rankings and compliance status  
✅ **Multi-File Comparison** — Compare results across simulations side-by-side  
✅ **Data Exploration** — Filter, search, and derive new columns on the fly  
✅ **Export Reports** — Generate Excel reports with charts and analysis  
✅ **Full Privacy** — Everything runs locally on your machine (no cloud, no telemetry)

---

## 🚀 Getting Started

### Installation (Windows)

1. **Download the installer** from [Releases](https://github.com/4haiderali/Outfile-Viewer/releases)
2. **Run `OutfileViewerSetup.exe`** and follow the installer
3. **Launch from Start Menu** or desktop shortcut
4. The app opens automatically in your browser at `http://localhost:8600`

### First Run

1. Click **"Load sample demo file"** in the sidebar to see sample data
2. Or upload your own `.out`, `.txt`, `.log`, or `.dat` file
3. Explore the tabs:
   - **Cockpit** — Risk summary & key metrics at a glance
   - **Data** — Browse tables and raw data
   - **Analysis** — Derived metrics and trends
   - **Compliance** — Run compliance checks
   - **Reports** — Export to Excel with charts

---

## 📋 Supported File Formats

### `.out` Files (Primary Format)
Standard engineering simulation output files with sections like:
```
SUMMARY STATISTICS
TABLE DATA (optional)
PDF OUTPUT (optional)
DIAGNOSTICS
```

### `.txt`, `.log`, `.dat` Files
Text-based output files with similar structure. The parser attempts to extract:
- **Metadata** — Run parameters, dates, versions
- **Tables** — Structured data (statistics, results)
- **Statistics** — Summary metrics
- **Diagnostics** — Warnings, errors, debug info

**[See File Format Specification →](docs/file_format.md)**

---

## 💻 Features Overview

### 🎛️ Core Tabs

| Tab | What It Does |
|-----|-------------|
| **Cockpit** | Executive summary: risk score, key metrics, status indicators |
| **Data** | Browse parsed tables, view raw data, inspect structure |
| **Analysis** | Trend analysis, statistics, aggregations, derived columns |
| **Derived & Units** | Create calculated columns, override unit definitions |
| **Compliance** | Automated compliance checks against rules |
| **Compare** | Side-by-side comparison of multiple files |
| **Filter & Search** | Advanced filtering, search by keyword or pattern |
| **Notes** | Attach session notes and annotations |
| **Reports** | Export analysis as Excel with charts and summaries |
| **Project** | Save/load full workspaces (files + analysis state) |
| **Raw & Diagnostics** | Inspect raw file contents, parser diagnostics |
| **Admin** (hidden) | Session management, debug tools |

### 🔧 Key Features

- **Multiple File Support** — Analyze 10+ files in one session
- **Session History** — Access previously uploaded files instantly
- **Unit Management** — Override default units for any column
- **Derived Columns** — Create computed columns with expressions
- **Smart Parsing** — Handles irregular formatting and malformed data
- **Export to Excel** — Full reports with pivot tables & charts
- **Workspace Projects** — Save analysis state for later

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.8 or higher
- pip or conda

### Installation (Dev)

```bash
# Clone the repository
git clone https://github.com/4haiderali/Outfile-Viewer.git
cd Outfile-Viewer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will start at `http://localhost:8501` (Streamlit's default dev port).

**[Full Development Guide →](DEVELOPMENT.md)**

---

## 📁 Project Structure

```
Outfile-Viewer/
├── app.py                      # Main Streamlit entry point
├── launcher.py                 # Windows desktop app launcher
├── out_viewer/                 # Core application package
│   ├── tabs/                   # Analysis tabs (cockpit, data, etc.)
│   ├── context.py              # Shared application state (AppContext)
│   ├── constants.py            # App configuration
│   ├── session_data.py         # File parsing & session management
│   ├── export.py               # Export functionality
│   └── ...                     # Other modules
├── requirements.txt            # Python dependencies
├── VERSION.txt                 # Version number
├── OutfileViewerInstaller.iss  # Windows installer config (Inno Setup)
├── Setup.bat                   # Setup script
└── docs/                       # Documentation
    └── file_format.md          # Input file specification

```

---

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature requests, or code:

1. **Read [CONTRIBUTING.md](CONTRIBUTING.md)** for guidelines
2. **Check [DEVELOPMENT.md](DEVELOPMENT.md)** for architecture details
3. **Open an issue** to discuss changes before submitting a PR

---

## ❓ FAQ

### Q: Does it send data to the cloud?
**A:** No. Everything runs locally on your machine. No data leaves your computer.

### Q: Can I use it on Mac/Linux?
**A:** Currently Windows-only (uses Windows-specific tray icon). Mac/Linux support possible with community contribution.

### Q: What if my file doesn't parse?
**A:** Check [docs/file_format.md](docs/file_format.md) for format requirements. Post an issue with a sample file (sanitized) and we'll investigate.

### Q: Can I use this at work?
**A:** Yes! It's MIT licensed. See [LICENSE](LICENSE) for full terms.

### Q: How do I report a bug?
**A:** [Open an issue](https://github.com/4haiderali/Outfile-Viewer/issues) with:
- Your file format (if possible, sanitized sample)
- Steps to reproduce
- Expected vs actual behavior
- Error message from the browser console (F12)

---

## 📝 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 📧 Support

- **Questions?** [Open a discussion](https://github.com/4haiderali/Outfile-Viewer/discussions)
- **Found a bug?** [Report an issue](https://github.com/4haiderali/Outfile-Viewer/issues)
- **Feature request?** [Start a discussion or issue](https://github.com/4haiderali/Outfile-Viewer/issues)

---

## 🎉 Acknowledgments

Built with ❤️ using:
- [Streamlit](https://streamlit.io/) — The fastest way to build data apps
- [Pandas](https://pandas.pydata.org/) — Data analysis library
- [Plotly](https://plotly.com/) — Interactive visualizations
- [openpyxl](https://openpyxl.readthedocs.io/) — Excel file generation

---

**Made by [@4haiderali](https://github.com/4haiderali)**
