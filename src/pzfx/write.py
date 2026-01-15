"""
Write GraphPad Prism .pzfx files
"""

from typing import Union, List, Optional, Dict, Any
import warnings
import re
from datetime import datetime, timezone
from lxml import etree
import pandas as pd
import numpy as np


def write_pzfx(
    x: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
    path: str,
    row_names: Union[bool, List[bool]] = True,
    x_col: Union[int, str, List[Union[int, str]], None] = None,
    x_err: Union[int, str, List[Union[int, str]], None] = None,
    n_digits: Union[int, List[int]] = 2,
    notes: Union[pd.DataFrame, Dict[str, pd.DataFrame], None] = None,
    subcolumns: Union[int, str, List[Union[int, str]]] = 1,
    subcolumn_suffix: Union[str, List[str]] = ""
) -> None:
    """
    Write one or more tables to a GraphPad Prism .pzfx file.

    Parameters
    ----------
    x : pd.DataFrame or dict of pd.DataFrame
        Data frame or named dict of data frames to include as Prism tables.
    path : str
        Path to output file.
    row_names : bool or list of bool
        Include row names (index) as row titles? Default: True.
    x_col : int, str, or list thereof, optional
        Column index (1-based) or name(s) for X column. 0 or None for none.
    x_err : int, str, or list thereof, optional
        Column index (1-based) or name(s) for X error. 0 or None for none.
    n_digits : int or list of int
        Number of decimal places to display for numeric data. Default: 2.
    notes : pd.DataFrame or dict of pd.DataFrame, optional
        Notes table(s) with columns 'Name' and 'Value'. Default: None (empty notes).
    subcolumns : int, str, or list thereof
        Number of subcolumns for Y data, or "SDN" for mean/SD/N format. Default: 1.
    subcolumn_suffix : str or list of str
        Regex or string identifying grouped subcolumns (e.g., "_[0-9]+$" to group
        A_1, A_2 as column A). Default: "" (no grouping).

    Examples
    --------
    >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    >>> write_pzfx(df, "output.pzfx")

    >>> # Multiple tables
    >>> tables = {'Table1': df1, 'Table2': df2}
    >>> write_pzfx(tables, "output.pzfx")
    """
    # Helper functions
    def utc_iso8601() -> str:
        """Return current UTC time in ISO 8601 format."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    def require_length(arg: Any, n: int, name: str) -> list:
        """Ensure argument has length 1 or n, returning a list of length n."""
        if not isinstance(arg, list):
            arg = [arg]
        if len(arg) == 1:
            arg = arg * n
        if len(arg) != n:
            raise ValueError(f"Argument '{name}' must have length 1 or {n}")
        return arg

    def coerce_to_list_of_dfs(obj: Any, prefix: str) -> Optional[Dict[str, pd.DataFrame]]:
        """Convert input to a dict of DataFrames."""
        if obj is None:
            return None
        if isinstance(obj, pd.DataFrame):
            return {f"{prefix} 1": obj}
        if isinstance(obj, dict):
            # Check all values are DataFrames
            bad = [k for k, v in obj.items() if not isinstance(v, pd.DataFrame)]
            if bad:
                raise TypeError(f"These {prefix} elements are not DataFrames: {', '.join(bad)}")
            # Ensure names
            if not obj:
                return None
            return obj
        raise TypeError(f"Cannot process {prefix} of type {type(obj).__name__}")

    def normalise_col_arg(arg: list, lst: Dict[str, pd.DataFrame], label: str) -> List[int]:
        """Normalize column argument to list of integer indices (1-based, 0 means none)."""
        arg = require_length(arg, len(lst), label)
        result = []
        for i, (name, df) in enumerate(lst.items()):
            a = arg[i]
            if a is None or (isinstance(a, float) and np.isnan(a)):
                result.append(0)
            elif isinstance(a, str):
                if a == "":
                    result.append(0)
                elif a in df.columns:
                    result.append(list(df.columns).index(a) + 1)  # 1-based
                else:
                    warnings.warn(f"Column '{a}' not in table '{name}'; ignored as {label}")
                    result.append(0)
            else:
                result.append(int(a))
        return result

    def subcol_helper(values: pd.Series) -> List[etree._Element]:
        """Create list of 'd' elements for a subcolumn."""
        elements = []
        for v in values:
            d_elem = etree.Element("d")
            if pd.isna(v):
                # Empty element for NA
                pass
            else:
                v_str = str(v)
                if v_str.endswith("*"):
                    # Excluded value
                    d_elem.set("Excluded", "1")
                    d_elem.text = v_str[:-1]  # Remove the *
                else:
                    d_elem.text = v_str
            elements.append(d_elem)
        return elements

    def build_xcol_structure(
        df: pd.DataFrame, x_idx: int, x_err_idx: int, n_dig: int
    ) -> Optional[etree._Element]:
        """Build XColumn element."""
        if x_idx == 0:
            return None

        xcol = etree.Element("XColumn")
        xcol.set("Width", "89" if x_err_idx == 0 else "120")
        xcol.set("Decimals", str(n_dig))
        xcol.set("Subcolumns", "1" if x_err_idx == 0 else "2")

        # Title
        title = etree.SubElement(xcol, "Title")
        title.text = df.columns[x_idx - 1]  # Convert to 0-based

        # Main subcolumn
        subcol = etree.SubElement(xcol, "Subcolumn")
        for d_elem in subcol_helper(df.iloc[:, x_idx - 1]):
            subcol.append(d_elem)

        # Error subcolumn if present
        if x_err_idx != 0:
            subcol_err = etree.SubElement(xcol, "Subcolumn")
            for d_elem in subcol_helper(df.iloc[:, x_err_idx - 1]):
                subcol_err.append(d_elem)

        return xcol

    def generate_subcolumns(
        df: pd.DataFrame, expected_count: int, suffix: str, n_dig: int
    ) -> List[etree._Element]:
        """Generate YColumn elements with subcolumns."""
        col_names = list(df.columns)
        if not col_names:
            col_names = [f"V{i+1}" for i in range(len(df.columns))]

        # Group columns by removing suffix
        if suffix:
            grouping_factor = [re.sub(suffix, "", c) for c in col_names]
        else:
            grouping_factor = col_names

        # Group columns
        groups = {}
        group_order = []
        for i, (col, group) in enumerate(zip(col_names, grouping_factor)):
            if group not in groups:
                groups[group] = []
                group_order.append(group)
            groups[group].append(col)

        y_columns = []
        for group in group_order:
            group_cols = groups[group]
            count_found = len(group_cols)

            if count_found > expected_count:
                raise ValueError(
                    f"Group '{group}' has {count_found} columns, but {expected_count} were expected."
                )

            ycol = etree.Element("YColumn")
            ycol.set("Width", str(89 * expected_count))
            ycol.set("Decimals", str(n_dig))
            ycol.set("Subcolumns", str(expected_count))

            # Title
            title = etree.SubElement(ycol, "Title")
            title.text = group

            # Add subcolumns for existing columns
            for col in group_cols:
                subcol = etree.SubElement(ycol, "Subcolumn")
                for d_elem in subcol_helper(df[col]):
                    subcol.append(d_elem)

            # Pad with empty subcolumns if needed
            for _ in range(expected_count - count_found):
                subcol = etree.SubElement(ycol, "Subcolumn")
                for _ in range(len(df)):
                    d_elem = etree.Element("d")
                    subcol.append(d_elem)

            y_columns.append(ycol)

        return y_columns

    def build_table(
        df: pd.DataFrame,
        table_name: str,
        table_idx: int,
        row_name: bool,
        xi: int,
        xe: int,
        n_dig: int,
        subc: Union[int, str],
        suffix: str
    ) -> etree._Element:
        """Build a Table element."""
        y_format = "replicates"
        table_type = "OneWay"
        x_format = "none"

        if subc == "SDN":
            y_format = "SDN"
            subc = 3
        else:
            subc = int(subc)

        # Build XColumn
        xcol = build_xcol_structure(df, xi, xe, n_dig)
        if xcol is not None:
            x_format = "numbers" if xe == 0 else "error"
            table_type = "XY"

        # Get Y columns (exclude X and X_err columns)
        exclude_cols = set()
        if xi > 0:
            exclude_cols.add(xi - 1)  # Convert to 0-based
        if xe > 0:
            exclude_cols.add(xe - 1)
        y_col_indices = [i for i in range(len(df.columns)) if i not in exclude_cols]
        df_y = df.iloc[:, y_col_indices]

        # Generate YColumns
        ycols = generate_subcolumns(df_y, subc, suffix, n_dig)

        # Build Table element
        table = etree.Element("Table")
        table.set("ID", f"Table{table_idx}")
        table.set("XFormat", x_format)
        table.set("YFormat", y_format)
        table.set("Replicates", str(subc))
        table.set("TableType", table_type)
        table.set("EVFormat", "AsteriskAfterNumber")

        # Title
        title = etree.SubElement(table, "Title")
        title.text = table_name

        # RowTitlesColumn
        if row_name:
            row_titles = etree.SubElement(table, "RowTitlesColumn")
            row_titles.set("Width", "39")
            subcol = etree.SubElement(row_titles, "Subcolumn")
            for idx_val in df_y.index:
                d_elem = etree.Element("d")
                d_elem.text = str(idx_val)
                subcol.append(d_elem)

        # XColumn
        if xcol is not None:
            table.append(xcol)

        # YColumns
        for ycol in ycols:
            table.append(ycol)

        return table

    def build_info(
        df: pd.DataFrame, info_name: str, info_idx: int
    ) -> etree._Element:
        """Build an Info element for notes."""
        info = etree.Element("Info")
        info.set("ID", f"Info{info_idx}")

        # Title
        title = etree.SubElement(info, "Title")
        title.text = info_name

        # Notes section
        notes_elem = etree.SubElement(info, "Notes")
        font = etree.SubElement(notes_elem, "Font")
        font.set("Color", "#000000")
        font.set("Face", "Helvetica")

        # Get Notes rows
        if "Name" in df.columns and "Value" in df.columns:
            notes_rows = df[df["Name"] == "Notes"]
            constants = df[df["Name"] != "Notes"]

            # Add note values
            for _, row in notes_rows.iterrows():
                if pd.notna(row["Value"]):
                    font.text = str(row["Value"])
                    br = etree.SubElement(font, "BR")

            # Add constants
            for _, row in constants.iterrows():
                const = etree.SubElement(info, "Constant")
                name_elem = etree.SubElement(const, "Name")
                name_elem.text = str(row["Name"])
                value_elem = etree.SubElement(const, "Value")
                if pd.notna(row["Value"]):
                    value_elem.text = str(row["Value"])

        return info

    # Main body

    # Default notes
    if notes is None:
        notes = {"Project Info 1": pd.DataFrame({"Name": ["Notes"], "Value": [None]})}

    # Coerce inputs
    n_lst = coerce_to_list_of_dfs(notes, "Project Info")
    x_lst = coerce_to_list_of_dfs(x, "Data")

    if x_lst is None or len(x_lst) == 0:
        raise ValueError("No data tables provided")

    # Warn about non-numeric columns
    for nm, df in x_lst.items():
        bad_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        if bad_cols:
            # Check for values that are neither numeric nor *-suffixed
            problem_values = []
            for col in bad_cols:
                vals = df[col].dropna()
                for v in vals:
                    v_str = str(v)
                    # Skip if it ends with * (exclusion marker)
                    if v_str.endswith("*"):
                        continue
                    # Skip if it can be converted to numeric
                    try:
                        float(v_str)
                        continue
                    except ValueError:
                        pass
                    # This is a problematic value
                    problem_values.append(v_str)

            problem_values = list(set(problem_values))

            if problem_values:
                # Stronger warning for non-numeric, non-exclusion values
                sample_vals = ", ".join(problem_values[:3])
                if len(problem_values) > 3:
                    sample_vals += ", ..."
                warnings.warn(
                    f"Table '{nm}' has non-numeric columns ({', '.join(bad_cols)}) "
                    f"containing text values that cannot be converted to numbers: {sample_vals}. "
                    f"These will be written as literal text in Prism, which may not be what you intended."
                )
            else:
                # Milder warning when all values are either numeric or *-suffixed
                warnings.warn(
                    f"Table '{nm}' has non-numeric columns ({', '.join(bad_cols)}) "
                    f"which will be written as text. Values ending with '*' will be marked as excluded in Prism."
                )

    # Normalize vector arguments
    n_tables = len(x_lst)
    row_names_list = require_length(row_names if isinstance(row_names, list) else [row_names], n_tables, "row_names")
    subcolumns_list = require_length(subcolumns if isinstance(subcolumns, list) else [subcolumns], n_tables, "subcolumns")
    suffix_list = require_length(subcolumn_suffix if isinstance(subcolumn_suffix, list) else [subcolumn_suffix], n_tables, "subcolumn_suffix")
    n_digits_list = require_length(n_digits if isinstance(n_digits, list) else [n_digits], n_tables, "n_digits")

    # Normalize column arguments
    x_col_list = normalise_col_arg(
        x_col if isinstance(x_col, list) else [x_col] if x_col is not None else [None],
        x_lst, "x_col"
    )
    x_err_list = normalise_col_arg(
        x_err if isinstance(x_err, list) else [x_err] if x_err is not None else [None],
        x_lst, "x_err"
    )

    # Validate column indices
    for i, (name, df) in enumerate(x_lst.items()):
        nc = len(df.columns)
        if x_col_list[i] > nc or x_err_list[i] > nc:
            raise IndexError(f"Not enough columns for table {name}")

    # Build XML structure
    root = etree.Element("GraphPadPrismFile")
    root.set("PrismXMLVersion", "5.00")

    # Created element
    created = etree.SubElement(root, "Created")
    orig_version = etree.SubElement(created, "OriginalVersion")
    orig_version.set("CreatedByProgram", "GraphPad Prism")
    orig_version.set("CreatedByVersion", "6.0f.254")
    orig_version.set("Login", "")
    orig_version.set("DateTime", utc_iso8601())

    # InfoSequence
    if n_lst:
        info_seq = etree.SubElement(root, "InfoSequence")
        for i in range(len(n_lst)):
            ref = etree.SubElement(info_seq, "Ref")
            ref.set("ID", f"Info{i}")
            if i == 0:
                ref.set("Selected", "1")

        # Info elements
        for i, (name, df) in enumerate(n_lst.items()):
            info_elem = build_info(df, name, i)
            root.append(info_elem)

    # TableSequence
    table_seq = etree.SubElement(root, "TableSequence")
    for i in range(len(x_lst)):
        ref = etree.SubElement(table_seq, "Ref")
        ref.set("ID", f"Table{i}")
        if i == 0:
            ref.set("Selected", "1")

    # Table elements
    for i, (name, df) in enumerate(x_lst.items()):
        table_elem = build_table(
            df, name, i,
            row_names_list[i],
            x_col_list[i],
            x_err_list[i],
            n_digits_list[i],
            subcolumns_list[i],
            suffix_list[i]
        )
        root.append(table_elem)

    # Write to file
    tree = etree.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True, pretty_print=True)
