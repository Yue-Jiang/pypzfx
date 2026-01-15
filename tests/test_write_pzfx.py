"""Tests for write_pzfx function."""

import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path

from pzfx import read_pzfx, write_pzfx


TESTDATA_DIR = Path(__file__).parent / "testdata"


def read_expected(filename: str, **kwargs) -> pd.DataFrame:
    """Read expected .tab file as DataFrame."""
    path = TESTDATA_DIR / filename
    df = pd.read_csv(path, sep="\t", **kwargs)
    return df


def assert_frame_equal_loose(result: pd.DataFrame, expected: pd.DataFrame):
    """Compare DataFrames with some tolerance for type differences."""
    # Strip whitespace from column names for comparison
    result_cols = [str(c).strip() for c in result.columns]
    expected_cols = [str(c).strip() for c in expected.columns]
    assert result_cols == expected_cols, f"Columns differ: {result.columns} vs {expected.columns}"
    assert len(result) == len(expected), f"Length differs: {len(result)} vs {len(expected)}"

    # Create mapping of result columns to expected columns for iteration
    col_mapping = list(zip(result.columns, expected.columns))
    for r_col, e_col in col_mapping:
        for i in range(len(result)):
            r_val = result[r_col].iloc[i]
            e_val = expected[e_col].iloc[i]

            # Handle NaN
            if pd.isna(r_val) and pd.isna(e_val):
                continue
            if pd.isna(r_val) or pd.isna(e_val):
                raise AssertionError(f"NaN mismatch at column {r_col}, row {i}: {r_val} vs {e_val}")

            # Try numeric comparison first
            try:
                r_num = float(r_val)
                e_num = float(e_val)
                if not np.isclose(r_num, e_num, rtol=1e-9, atol=1e-9):
                    raise AssertionError(f"Value mismatch at column {r_col}, row {i}: {r_val} vs {e_val}")
            except (ValueError, TypeError):
                # Fall back to string comparison
                if str(r_val) != str(e_val):
                    raise AssertionError(f"Value mismatch at column {r_col}, row {i}: {r_val} vs {e_val}")


class TestWritePzfx:
    """Tests for write_pzfx function."""

    def test_write_column_table(self):
        """Test writing 'Column' type table."""
        expected = read_expected("column.tab")
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            write_pzfx(expected, tmp.name, row_names=False)
            result = read_pzfx(tmp.name)
        assert_frame_equal_loose(result, expected)

    def test_write_xy_table(self):
        """Test writing 'XY' type table."""
        expected = read_expected("x_y_no_rep.tab")
        to_write = expected.drop(columns=["ROWTITLE"])
        to_write.index = expected["ROWTITLE"]
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            write_pzfx(to_write, tmp.name, row_names=True, x_col="XX")
            result = read_pzfx(tmp.name)
        assert_frame_equal_loose(result, expected)

    def test_multiple_tables(self):
        """Test multiple input tables work."""
        expected = read_expected("column.tab")
        to_write = {"T1": expected, "T2": expected}
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            write_pzfx(to_write, tmp.name, row_names=False)
            result1 = read_pzfx(tmp.name, table="T1")
            result2 = read_pzfx(tmp.name, table=2)
        assert_frame_equal_loose(result1, expected)
        assert_frame_equal_loose(result2, expected)

    def test_wrong_input_type(self):
        """Should raise when provided with wrong type of input."""
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            with pytest.raises(TypeError, match="Cannot process Data"):
                write_pzfx([1, 2, 3, 4, 5], tmp.name, row_names=False)

            with pytest.raises(TypeError, match="Cannot process Data"):
                write_pzfx("Existence is pain", tmp.name, row_names=False)

            # Non-numeric columns should warn
            with pytest.warns(UserWarning, match="cannot be converted to numbers"):
                df = pd.DataFrame({"X": ["a", "b"], "Y": [1, 2]})
                write_pzfx(df, tmp.name, row_names=False)

            # Dict with non-DataFrame should raise
            with pytest.raises(TypeError, match="not DataFrames"):
                write_pzfx({"a": [1, 2, 3]}, tmp.name, row_names=False)

    def test_wrong_x_col(self):
        """Should raise when provided with wrong 'x_col'."""
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            with pytest.raises(IndexError, match="Not enough columns"):
                write_pzfx(pd.DataFrame({"SingleColumn": [1, 2, 3]}), tmp.name, x_col=2)

            with pytest.raises(ValueError, match="must have length 1 or 2"):
                write_pzfx(
                    {"t1": pd.DataFrame({"A": [1, 2]}), "t2": pd.DataFrame({"B": [3, 4]})},
                    tmp.name,
                    x_col=[1, 1, 1]
                )

    def test_wrong_row_names(self):
        """Should raise when provided with wrong 'row_names'."""
        with tempfile.NamedTemporaryFile(suffix=".pzfx", delete=False) as tmp:
            with pytest.raises(ValueError, match="must have length 1 or 2"):
                write_pzfx(
                    {"t1": pd.DataFrame({"A": [1, 2]}), "t2": pd.DataFrame({"B": [3, 4]})},
                    tmp.name,
                    row_names=[True, False, True]
                )
