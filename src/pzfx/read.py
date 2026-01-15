"""
Read GraphPad Prism .pzfx files
"""

from typing import Union, List, Optional
import warnings
from lxml import etree
import pandas as pd
import numpy as np


def pzfx_tables(path: str) -> List[str]:
    """
    List all tables in a GraphPad Prism .pzfx file.

    Parameters
    ----------
    path : str
        Path to the .pzfx file

    Returns
    -------
    list of str
        Names of all tables in the file

    Examples
    --------
    >>> tables = pzfx_tables("data.pzfx")
    >>> print(tables)
    ['Table 1', 'Table 2']
    """
    tree = etree.parse(path)
    root = tree.getroot()

    # Find all Table and HugeTable elements
    table_nodes = root.xpath(".//*[local-name()='Table' or local-name()='HugeTable']")

    tables = []
    for t in table_nodes:
        # Use xpath for local-name() support
        title_nodes = t.xpath(".//*[local-name()='Title']")
        if title_nodes and title_nodes[0].text:
            tables.append(title_nodes[0].text)
        else:
            tables.append("")

    return tables


def _read_subcol(subcol_elem, strike_action: str = "exclude") -> list:
    """
    Parse one sub-column from a column of a table in a .pzfx file.

    Parameters
    ----------
    subcol_elem : lxml Element
        XML element for the subcolumn
    strike_action : str
        One of "exclude", "keep", "star" (or "e", "k", "s")

    Returns
    -------
    list
        Values in the sub-column
    """
    strike_action = strike_action.lower()
    if strike_action not in ("exclude", "keep", "star", "e", "k", "s"):
        raise ValueError("strike_action must be one of ('exclude', 'keep', 'star', 'e', 'k', 's')")

    vals = []
    for d_elem in subcol_elem.findall("d"):
        # Use itertext() to get text from nested elements like <TextAlign>
        val = "".join(d_elem.itertext()).strip() or None
        excluded = d_elem.get("Excluded") == "1"

        if excluded:
            if strike_action in ("exclude", "e"):
                val = None
            elif strike_action in ("keep", "k"):
                pass  # keep val as is
            elif strike_action in ("star", "s"):
                if val is not None:
                    val = f"{val}*"

        vals.append(val)

    # Convert to numeric if not using star action
    if strike_action not in ("star", "s"):
        numeric_vals = []
        all_convertible = True
        for v in vals:
            if v is None:
                numeric_vals.append(np.nan)
            else:
                # Handle comma as decimal separator
                v_str = str(v).replace(",", ".")
                try:
                    numeric_vals.append(float(v_str))
                except ValueError:
                    all_convertible = False
                    break

        if all_convertible:
            vals = numeric_vals

    return vals


def _read_col(col_elem, strike_action: str = "exclude", format_: str = "", col_name: str = "", target_len: int = 0) -> pd.DataFrame:
    """
    Parse one column from a table in a .pzfx file.

    Parameters
    ----------
    col_elem : lxml Element
        XML element for the column
    strike_action : str
        How to handle excluded values
    format_ : str
        XFormat or YFormat attribute
    col_name : str
        Default base column name

    Returns
    -------
    pd.DataFrame
        Parsed column data
    """
    # Get column title if present
    title_elem = col_elem.find("Title")
    if title_elem is not None:
        # Handle nested text elements
        title_text = "".join(title_elem.itertext())
        if title_text:
            col_name = title_text

    # Read all subcolumns
    subcol_list = []
    for subcol_elem in col_elem.findall("Subcolumn"):
        subcol_data = _read_subcol(subcol_elem, strike_action=strike_action)
        subcol_list.append(subcol_data)

    # Handle case where there are no subcolumns at all
    if not subcol_list:
        return pd.DataFrame()

    # Handle case where all subcolumns are empty (but column exists)
    # Return a DataFrame with NaN values to preserve column structure
    all_empty = all(len(s) == 0 for s in subcol_list)
    if all_empty and target_len > 0:
        # Create NaN-filled columns
        for s in subcol_list:
            for _ in range(target_len):
                s.append(np.nan)

    # Determine column names based on format
    n_subcols = len(subcol_list)
    if n_subcols == 1:
        col_names = [col_name]
    elif format_ == "error":
        col_names = [f"{col_name}_X", f"{col_name}_ERROR"]
    elif format_ == "replicates":
        col_names = [f"{col_name}_{i+1}" for i in range(n_subcols)]
    elif format_ == "SDN":
        col_names = [f"{col_name}_MEAN", f"{col_name}_SD", f"{col_name}_N"]
    elif format_ == "SEN":
        col_names = [f"{col_name}_MEAN", f"{col_name}_SEM", f"{col_name}_N"]
    elif format_ == "CVN":
        col_names = [f"{col_name}_MEAN", f"{col_name}_CV", f"{col_name}_N"]
    elif format_ == "SD":
        col_names = [f"{col_name}_MEAN", f"{col_name}_SD"]
    elif format_ == "SE":
        col_names = [f"{col_name}_MEAN", f"{col_name}_SE"]
    elif format_ == "CV":
        col_names = [f"{col_name}_MEAN", f"{col_name}_CV"]
    elif format_ == "low-high":
        col_names = [f"{col_name}_MEAN", f"{col_name}_PLUSERROR", f"{col_name}_MINUSERROR"]
    elif format_ == "upper-lower-limits":
        col_names = [f"{col_name}_MEAN", f"{col_name}_UPPERLIMIT", f"{col_name}_LOWERLIMIT"]
    else:
        # Default: just number them
        col_names = [f"{col_name}_{i+1}" for i in range(n_subcols)]

    # Pad subcols to same length
    max_len = max(len(s) for s in subcol_list) if subcol_list else 0
    for i, s in enumerate(subcol_list):
        while len(s) < max_len:
            # Use np.nan for numeric columns, None for string columns
            if s and isinstance(s[0], (int, float)):
                s.append(np.nan)
            else:
                s.append(None)

    # Create DataFrame
    data = {col_names[i]: subcol_list[i] for i in range(len(subcol_list))}
    return pd.DataFrame(data)


def read_pzfx(
    path: str,
    table: Union[int, str] = 1,
    strike_action: str = "exclude",
    date_x: str = "character"
) -> pd.DataFrame:
    """
    Read one table from a GraphPad Prism .pzfx file.

    Parameters
    ----------
    path : str
        Path to the .pzfx file
    table : int or str
        Table to read. Either a string (name of table) or integer (1-based position).
        Defaults to 1 (first table).
    strike_action : str
        One of "exclude", "keep", "star" (or "e", "k", "s").
        How to handle excluded/stricken values:
        - "exclude": replace with NaN
        - "keep": keep the value
        - "star": append "*" to the value (column becomes string type)
    date_x : str
        One of "numeric", "character", "both" (or "n", "c", "b").
        How to handle Date-formatted X columns.

    Returns
    -------
    pd.DataFrame
        The table data

    Examples
    --------
    >>> df = read_pzfx("data.pzfx", table=1)
    >>> df = read_pzfx("data.pzfx", table="My Table", strike_action="star")
    """
    # Validate date_x
    date_x = date_x.lower()
    if date_x not in ("numeric", "character", "both", "n", "c", "b"):
        raise ValueError("date_x must be one of ('numeric', 'character', 'both', 'n', 'c', 'b')")

    # Get table names
    table_names = pzfx_tables(path)

    # Determine table index
    if isinstance(table, int):
        if table < 1 or table > len(table_names):
            raise IndexError("Table index out of range")
        this_idx = table - 1  # Convert to 0-based
    else:
        table = str(table)
        if table not in table_names:
            raise ValueError(f"Can't find {table} in prism file")
        indices = [i for i, name in enumerate(table_names) if name == table]
        if len(indices) > 1:
            warnings.warn(f"Multiple tables named {table}, returning the first one only")
        this_idx = indices[0]

    # Parse XML
    tree = etree.parse(path)
    root = tree.getroot()

    # Find all tables
    table_nodes = root.xpath(".//*[local-name()='Table' or local-name()='HugeTable']")
    this_table = table_nodes[this_idx]

    # Check for Title
    title_elem = this_table.find("Title")
    if title_elem is None:
        raise ValueError("Can't work with this pzfx file, is it later than v6.0?")

    # Get format attributes
    x_format = this_table.get("XFormat", "")
    y_format = this_table.get("YFormat", "")

    # Check if XAdvancedColumn exists (for date handling)
    has_x_advanced = this_table.find("XAdvancedColumn") is not None

    # First pass: collect all columns to determine max length
    col_dfs = []
    col_info = []  # Store (elem, tag, kwargs) for second pass if needed

    for elem in this_table:
        tag = etree.QName(elem).localname if isinstance(elem.tag, str) else elem.tag

        if tag == "XColumn":
            # Read normally unless it's date and we want character only
            if x_format == "date" and (date_x in ("numeric", "n", "both", "b") or not has_x_advanced):
                col_df = _read_col(elem, strike_action=strike_action, col_name="X", format_="")
                if date_x in ("both", "b") and not col_df.empty:
                    col_df.columns = [f"{c}_1" for c in col_df.columns]
                col_dfs.append(col_df)
            elif x_format == "date":
                continue  # Skip XColumn for date when we only want character
            else:
                col_df = _read_col(elem, strike_action=strike_action, col_name="X", format_=x_format)
                col_dfs.append(col_df)

        elif tag == "XAdvancedColumn":
            # Only read if it's date and we want character or both
            if x_format == "date" and date_x in ("character", "c", "both", "b"):
                col_df = _read_col(elem, strike_action=strike_action, col_name="X", format_="")
                if date_x in ("both", "b") and not col_df.empty:
                    col_df.columns = [f"{c}_2" for c in col_df.columns]
                col_dfs.append(col_df)

        elif tag == "RowTitlesColumn":
            col_df = _read_col(elem, strike_action=strike_action, col_name="ROWTITLE", format_="")
            # Only include ROWTITLE if it has actual data (not all empty/NaN)
            if not col_df.empty:
                col_dfs.append(col_df)

        elif tag == "YColumn":
            col_df = _read_col(elem, strike_action=strike_action, format_=y_format)
            col_dfs.append(col_df)

    # Filter out truly empty dataframes (no columns at all)
    col_dfs = [df for df in col_dfs if len(df.columns) > 0]

    if not col_dfs:
        return pd.DataFrame()

    # Find max length from non-empty columns
    max_len = max((len(df) for df in col_dfs if not df.empty), default=0)

    # Pad all DataFrames to same length and concatenate
    padded_dfs = []
    for df in col_dfs:
        if df.empty and max_len > 0:
            # Empty column - fill with NaN
            df = pd.DataFrame({col: [np.nan] * max_len for col in df.columns})
        elif len(df) < max_len:
            padding = pd.DataFrame(
                {col: [np.nan] * (max_len - len(df)) for col in df.columns}
            )
            df = pd.concat([df, padding], ignore_index=True)
        padded_dfs.append(df)

    result = pd.concat(padded_dfs, axis=1)
    return result
