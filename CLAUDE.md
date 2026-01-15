# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Overview

pzfx is a Python library for reading and writing GraphPad Prism `.pzfx` files. It parses XML-based `.pzfx` files and converts them to/from pandas DataFrames. This is a Python port of the [R pzfx package](https://github.com/Yue-Jiang/pzfx).

## Build and Test Commands

```bash
# Install package in development mode
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_read_pzfx.py

# Run a specific test
pytest tests/test_read_pzfx.py::TestReadPzfx::test_column

# Build package for distribution
python3 -m build

# Check package before upload
twine check dist/*
```

## Architecture

### Package Structure

```
pypzfx/
├── src/pzfx/
│   ├── __init__.py      # Exports: read_pzfx, write_pzfx, pzfx_tables
│   ├── read.py          # Reading .pzfx files
│   └── write.py         # Writing .pzfx files
├── tests/
│   ├── testdata/        # Test .pzfx and .tab files (shared with R package)
│   ├── test_read_pzfx.py
│   └── test_write_pzfx.py
├── pyproject.toml       # Package configuration (hatchling build system)
└── dist/                # Built packages (.whl and .tar.gz)
```

### Core Functions (src/pzfx/)

- **read.py**
  - `pzfx_tables(path)` - Lists table names in a `.pzfx` file
  - `read_pzfx(path, table, strike_action, date_x)` - Reads a table as DataFrame
  - `_read_col()` - Internal: parses one column with subcolumn naming
  - `_read_subcol()` - Internal: parses individual subcolumns, handles excluded values

- **write.py**
  - `write_pzfx(x, path, ...)` - Writes DataFrame(s) to `.pzfx` format
  - Supports: multiple tables, X columns, subcolumns, notes, excluded values (marked with `*`)

### Key Implementation Details

- Uses `lxml` for XML parsing with XPath queries
- Must use `xpath()` method (not `find()`) for `local-name()` queries
- Uses `itertext()` to extract text from nested elements (e.g., `<d><TextAlign>value</TextAlign></d>`)
- Supports both `<Table>` and `<HugeTable>` nodes
- Column formats detected via `XFormat`/`YFormat` attributes determine suffix naming (_MEAN, _SD, _N, etc.)
- Stricken/excluded values handled via `strike_action` parameter: "exclude" (NaN), "keep", or "star" (append `*`)

### Data Flow

**Reading:** XML → `lxml.etree.parse()` → XPath to find tables/columns → `_read_col()` → `_read_subcol()` for each subcolumn → assemble DataFrame

**Writing:** DataFrame → build nested dict structure → `lxml.etree.Element` tree → write XML

## Dependencies

- pandas >= 1.0.0
- lxml >= 4.0.0
- pytest >= 7.0.0 (dev)

## PyPI Publishing

Package name: `pzfx` (version 0.3.0)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Test Data

Test data files in `tests/testdata/` are shared with the R package. Each `.pzfx` file has a corresponding `.tab` file with expected output.
