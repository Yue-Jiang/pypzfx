# Getting Started

## Installation

Install from PyPI:

```bash
pip install pzfx
```

Or install from source:

```bash
git clone https://github.com/Yue-Jiang/pzfx.git
cd pzfx
pip install -e .
```

## Reading .pzfx Files

### List tables in a file

```python
from pzfx import pzfx_tables

tables = pzfx_tables("data.pzfx")
print(tables)  # ['Table 1', 'Table 2']
```

### Read a table

```python
from pzfx import read_pzfx

# Read the first table (default)
df = read_pzfx("data.pzfx")

# Read by table name
df = read_pzfx("data.pzfx", table="My Table")

# Read by index (1-based)
df = read_pzfx("data.pzfx", table=2)
```

### Handle excluded values

GraphPad Prism allows you to "strike" or exclude values from analysis. Control how these are handled:

```python
# Replace with NaN (default)
df = read_pzfx("data.pzfx", strike_action="exclude")

# Keep the original value
df = read_pzfx("data.pzfx", strike_action="keep")

# Append "*" to mark excluded values
df = read_pzfx("data.pzfx", strike_action="star")
```

## Writing .pzfx Files

### Write a DataFrame

```python
import pandas as pd
from pzfx import write_pzfx

df = pd.DataFrame({
    'Control': [1.2, 2.3, 3.1],
    'Treatment': [2.5, 3.8, 4.2]
})

write_pzfx(df, "output.pzfx")
```

### Write multiple tables

```python
tables = {
    'Experiment 1': df1,
    'Experiment 2': df2
}
write_pzfx(tables, "output.pzfx")
```

### Write XY data

```python
df = pd.DataFrame({
    'Time': [0, 1, 2, 3],
    'Response': [0.1, 0.5, 0.9, 0.99]
})

write_pzfx(df, "xy_data.pzfx", x_col="Time")
```

### Add project notes

```python
notes = pd.DataFrame({
    'Name': ['Notes', 'Experiment ID', 'Researcher'],
    'Value': ['My experiment description', 'EXP-001', 'Jane Doe']
})

write_pzfx(df, "output.pzfx", notes=notes)
```

### Write with subcolumns (replicates)

```python
# Columns ending with _1, _2, _3 are grouped together
df = pd.DataFrame({
    'Control_1': [1.1, 2.1],
    'Control_2': [1.2, 2.2],
    'Control_3': [1.3, 2.3],
    'Treatment_1': [2.1, 3.1],
    'Treatment_2': [2.2, 3.2],
    'Treatment_3': [2.3, 3.3]
})

write_pzfx(df, "replicates.pzfx", subcolumns=3, subcolumn_suffix='_[0-9]+$')
```

### Write SDN format (Mean ± SD with N)

```python
df = pd.DataFrame({
    'Control_MEAN': [1.5, 2.5],
    'Control_SD': [0.2, 0.3],
    'Control_N': [5, 5],
    'Treatment_MEAN': [2.5, 3.5],
    'Treatment_SD': [0.3, 0.4],
    'Treatment_N': [5, 5]
})

write_pzfx(df, "summary.pzfx", subcolumns='SDN', subcolumn_suffix='_(MEAN|SD|N)$')
```

### Mark excluded values

Values ending with `*` are marked as excluded in Prism:

```python
df = pd.DataFrame({
    'Control': ['1.2', '2.3*', '3.1'],  # 2.3 will be excluded
    'Treatment': ['2.5', '3.8', '4.2*']  # 4.2 will be excluded
})

write_pzfx(df, "with_exclusions.pzfx")
```
