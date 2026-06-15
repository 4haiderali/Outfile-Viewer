# 🤝 Contributing to Outfile Viewer

Thank you for your interest in contributing! This document provides guidelines and instructions for getting involved.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Commit Message Guidelines](#commit-message-guidelines)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please:

- Be respectful and professional in all interactions
- Welcome diverse perspectives and experiences
- Focus on what's best for the community
- Show empathy and support for others

---

## How to Contribute

### 1. **Report a Bug** 🐛

Found a problem? [Open an issue](https://github.com/4haiderali/Outfile-Viewer/issues) with:

- **Title:** Clear, concise description of the bug
- **Description:** What happened, what you expected to happen
- **Steps to reproduce:** How to trigger the bug
- **Environment:** OS, Python version, Outfile Viewer version
- **Attachments:** Screenshot, error message, or sanitized sample file

### 2. **Suggest a Feature** ✨

Have an idea? [Start a discussion](https://github.com/4haiderali/Outfile-Viewer/discussions) with:

- **Title:** Clear feature name
- **Description:** What problem does it solve?
- **Use cases:** Real-world examples

### 3. **Submit Code** 💻

Follow the [Pull Request Process](#pull-request-process) below.

---

## Reporting Bugs

### Before You Report

- Check if the bug has already been [reported](https://github.com/4haiderali/Outfile-Viewer/issues)
- Try the latest version from `main` branch
- Check the [FAQ](README.md#-faq)

### Filing a Good Bug Report

Include:

1. **Description** — What's the bug?
2. **Reproduction steps** — How do you trigger it?
3. **Expected behavior** — What should happen?
4. **Actual behavior** — What actually happened?
5. **Environment** — OS, Python version, etc.
6. **Logs/Screenshots** — Error messages, console output, screenshots
7. **Attachments** — Sample file (if possible, sanitized)

---

## Suggesting Features

### Before You Suggest

- Check existing issues/discussions to avoid duplicates
- Consider if it aligns with the project's scope (engineering output analysis)

### Filing a Good Feature Request

Include:

1. **Clear title** — What's the feature?
2. **Problem statement** — Why is this needed?
3. **Proposed solution** — How should it work?
4. **Examples** — Use cases, mockups, screenshots
5. **Alternatives** — Other ways to solve this?

---

## Pull Request Process

### Step 1: Fork & Branch

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Outfile-Viewer.git
cd Outfile-Viewer

# Create a new branch
git checkout -b feature/my-amazing-feature
# or for bugfixes:
git checkout -b fix/bug-description
```

### Step 2: Make Changes

- Follow the [Development Guide](DEVELOPMENT.md)
- Write clear, well-documented code
- Add tests for new features
- Run tests locally: `pytest`

```bash
# Format code
black out_viewer/ tests/

# Check for linting errors
flake8 out_viewer/ tests/

# Run tests
pytest
```

### Step 3: Commit & Push

Follow [Commit Message Guidelines](#commit-message-guidelines):

```bash
git add .
git commit -m "feat: Add dark mode theme toggle"
git push origin feature/my-amazing-feature
```

### Step 4: Create Pull Request

1. Go to https://github.com/4haiderali/Outfile-Viewer
2. Click **"New Pull Request"**
3. Select your branch
4. Fill out the PR template

### Step 5: Review & Iterate

- Address feedback from reviewers
- Push updates to the same branch
- All discussions should happen in the PR

### Step 6: Merge

Once approved, a maintainer will merge your PR. Congratulations! 🎉

---

## Coding Standards

### Python Style

Follow [PEP 8](https://pep8.org/):

```bash
# Auto-format with black
black out_viewer/ tests/

# Check with flake8
flake8 out_viewer/ tests/ --max-line-length=100
```

### Docstrings

Use Google-style docstrings:

```python
def extract_tables(content: str) -> list[dict]:
    """Extract tables from file content.
    
    Parses content for table-like structures.
    
    Args:
        content: Raw file content as string.
        
    Returns:
        List of extracted tables.
        
    Example:
        >>> content = "TABLE NAME\\n...\\nData"
        >>> tables = extract_tables(content)
        >>> len(tables)
        1
    """
```

### Type Hints

Use type hints:

```python
from typing import Optional, List, Dict

def parse_file(filename: str, encoding: str = "utf-8") -> Dict[str, any]:
    """Parse a file."""
    pass
```

---

## Commit Message Guidelines

Use clear, descriptive commit messages:

### Format

```
type(scope): subject

body (optional)

footer (optional)
```

### Types

- **feat** — New feature
- **fix** — Bug fix
- **docs** — Documentation changes
- **style** — Code style (formatting, missing semicolons, etc.)
- **refactor** — Code refactoring without changing functionality
- **test** — Adding or updating tests
- **chore** — Maintenance tasks, dependencies, etc.

### Examples

```
feat(tabs): add dark mode theme toggle
fix(parser): handle unicode characters in .out files
docs: update development guide with testing section
refactor(export): simplify excel generation logic
test(parser): add tests for malformed files
chore(deps): update streamlit to 1.36
```

---

## Getting Help

- **Questions?** [Open a discussion](https://github.com/4haiderali/Outfile-Viewer/discussions)
- **Stuck?** Comment on your PR and ask for guidance
- **Development help?** See [DEVELOPMENT.md](DEVELOPMENT.md)

---

Thank you for contributing! 🙏
