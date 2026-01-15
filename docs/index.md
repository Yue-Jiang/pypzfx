# pzfx

A Python library to read and write GraphPad Prism `.pzfx` files.

This is a Python port of the [R pzfx package](https://github.com/yue-jiang/pzfx).

## Features

- **Read** `.pzfx` files into pandas DataFrames
- **Write** pandas DataFrames to `.pzfx` format
- **List** all tables in a `.pzfx` file
- Handle **excluded/stricken values**
- Support for **subcolumns** (replicates) and **SDN format**
- Add **project notes** and metadata

## Quick Example

```python
from pzfx import read_pzfx, write_pzfx, pzfx_tables

# List tables in a file
tables = pzfx_tables("data.pzfx")

# Read a table
df = read_pzfx("data.pzfx", table="My Table")

# Write a DataFrame
write_pzfx(df, "output.pzfx")
```

## Installation

```bash
pip install pzfx
```

## License

MIT License

## See Also

- [R pzfx package](https://github.com/yue-jiang/pzfx) - The original R implementation
