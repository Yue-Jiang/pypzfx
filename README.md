# pzfx

A Python library to read and write GraphPad Prism `.pzfx` files. This is a vibe coding project that ports the functionality of the [R pzfx package](https://github.com/yue-jiang/pzfx) to Python.

## Installation

```bash
pip install pzfx
```

## Usage

### Reading .pzfx files

```python
from pzfx import read_pzfx, pzfx_tables

# List all tables in a file
tables = pzfx_tables("data.pzfx")
print(tables)  # ['Table 1', 'Table 2']

# Read the first table
df = read_pzfx("data.pzfx")

# Read a specific table by name
df = read_pzfx("data.pzfx", table="My Table")

# Read a specific table by index (1-based)
df = read_pzfx("data.pzfx", table=2)

# Handle excluded/stricken values
df = read_pzfx("data.pzfx", strike_action="exclude")  # Replace with NaN (default)
df = read_pzfx("data.pzfx", strike_action="keep")     # Keep the value
df = read_pzfx("data.pzfx", strike_action="star")     # Append "*" to value
```

### Writing .pzfx files

```python
import pandas as pd
from pzfx import write_pzfx

# Write a single DataFrame
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
write_pzfx(df, "output.pzfx")

# Write multiple tables
tables = {
    'Experiment 1': df1,
    'Experiment 2': df2
}
write_pzfx(tables, "output.pzfx")

# Write with X column
write_pzfx(df, "output.pzfx", x_col="Time")

# Write with row names
write_pzfx(df, "output.pzfx", row_names=True)

# Write with subcolumns (replicates)
write_pzfx(df, "output.pzfx", subcolumns=3, subcolumn_suffix="_[0-9]+$")

# Write excluded values (values ending with "*" are marked as excluded)
df = pd.DataFrame({'A': ['1', '2*', '3']})  # 2 will be excluded in Prism
write_pzfx(df, "output.pzfx")
```

## Parameters

### read_pzfx

- `path`: Path to the .pzfx file
- `table`: Table to read (name or 1-based index). Default: 1
- `strike_action`: How to handle excluded values: "exclude", "keep", or "star"
- `date_x`: How to handle date X columns: "numeric", "character", or "both"

### write_pzfx

- `x`: DataFrame or dict of DataFrames
- `path`: Output file path
- `row_names`: Include row names as row titles (default: True)
- `x_col`: Column for X values (index or name)
- `x_err`: Column for X error values
- `n_digits`: Decimal places for numeric data (default: 2)
- `notes`: Notes table(s) with 'Name' and 'Value' columns
- `subcolumns`: Number of subcolumns, or "SDN" for mean/SD/N format
- `subcolumn_suffix`: Regex to group columns into subcolumns

## License

MIT License

## See Also

- [R pzfx package](https://github.com/yue-jiang/pzfx) - The original R implementation
