"""Tests for read_pzfx and pzfx_tables functions."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from pzfx import read_pzfx, pzfx_tables


TESTDATA_DIR = Path(__file__).parent / "testdata"


def read_expected(filename: str, **kwargs) -> pd.DataFrame:
    """Read expected .tab file as DataFrame."""
    path = TESTDATA_DIR / filename
    df = pd.read_csv(path, sep="\t", **kwargs)
    return df


def assert_frame_equal_loose(result: pd.DataFrame, expected: pd.DataFrame):
    """Compare DataFrames with some tolerance for type differences."""
    # Strip whitespace from column names for comparison (some test files have trailing spaces)
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


class TestReadPzfx:
    """Tests for read_pzfx function."""

    def test_column(self):
        pzfx_file = TESTDATA_DIR / "column.pzfx"
        expected = read_expected("column.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_cv(self):
        pzfx_file = TESTDATA_DIR / "column_cv.pzfx"
        expected = read_expected("column_cv.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_cvn(self):
        pzfx_file = TESTDATA_DIR / "column_cvn.pzfx"
        expected = read_expected("column_cvn.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_low_high(self):
        pzfx_file = TESTDATA_DIR / "column_low-high.pzfx"
        expected = read_expected("column_low-high.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_sd(self):
        pzfx_file = TESTDATA_DIR / "column_sd.pzfx"
        expected = read_expected("column_sd.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_sdn(self):
        pzfx_file = TESTDATA_DIR / "column_sdn.pzfx"
        expected = read_expected("column_sdn.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_se(self):
        pzfx_file = TESTDATA_DIR / "column_se.pzfx"
        expected = read_expected("column_se.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_sen(self):
        pzfx_file = TESTDATA_DIR / "column_sen.pzfx"
        expected = read_expected("column_sen.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_column_upper_lower_limits(self):
        pzfx_file = TESTDATA_DIR / "column_upper-lower-limits.pzfx"
        expected = read_expected("column_upper-lower-limits.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_contingency(self):
        pzfx_file = TESTDATA_DIR / "contingency.pzfx"
        expected = read_expected("contingency.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_x_error_y_sdn(self):
        pzfx_file = TESTDATA_DIR / "x_error_y_sdn.pzfx"
        expected = read_expected("x_error_y_sdn.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_x_y_no_rep(self):
        pzfx_file = TESTDATA_DIR / "x_y_no_rep.pzfx"
        expected = read_expected("x_y_no_rep.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_excluded_values_exclude(self):
        pzfx_file = TESTDATA_DIR / "x_y_with_strike.pzfx"
        expected = read_expected("x_y_with_strike_excluded.tab")
        result = read_pzfx(str(pzfx_file), strike_action="exclude")
        assert_frame_equal_loose(result, expected)

    def test_excluded_values_keep(self):
        pzfx_file = TESTDATA_DIR / "x_y_with_strike.pzfx"
        expected = read_expected("x_y_with_strike_kept.tab")
        result = read_pzfx(str(pzfx_file), strike_action="keep")
        assert_frame_equal_loose(result, expected)

    def test_excluded_values_star(self):
        pzfx_file = TESTDATA_DIR / "x_y_with_strike.pzfx"
        expected = read_expected("x_y_with_strike_star.tab", dtype=str)
        result = read_pzfx(str(pzfx_file), strike_action="star")
        # Convert result to string for comparison
        result = result.astype(str)
        expected = expected.astype(str)
        # Handle nan vs 'nan' comparison
        for col in result.columns:
            for i in range(len(result)):
                r_val = result[col].iloc[i]
                e_val = expected[col].iloc[i]
                if r_val == 'nan' and e_val == 'NA':
                    continue
                assert r_val == e_val, f"Mismatch at {col}[{i}]: {r_val} vs {e_val}"

    def test_survival(self):
        pzfx_file = TESTDATA_DIR / "survival.pzfx"
        expected = read_expected("survival.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_parts_of_whole(self):
        pzfx_file = TESTDATA_DIR / "parts_of_whole.pzfx"
        expected = read_expected("parts_of_whole.tab", comment=None)
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_hugetable(self):
        pzfx_file = TESTDATA_DIR / "column_hugetable.pzfx"
        expected = read_expected("column_hugetable.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_date_x_numeric(self):
        pzfx_file = TESTDATA_DIR / "x_date.pzfx"
        expected = read_expected("x_date_numeric.tab")
        result = read_pzfx(str(pzfx_file), date_x="numeric")
        assert_frame_equal_loose(result, expected)

    def test_date_x_character(self):
        pzfx_file = TESTDATA_DIR / "x_date.pzfx"
        expected = read_expected("x_date_character.tab")
        result = read_pzfx(str(pzfx_file), date_x="character")
        assert_frame_equal_loose(result, expected)

    def test_date_x_both(self):
        pzfx_file = TESTDATA_DIR / "x_date.pzfx"
        expected = read_expected("x_date_both.tab")
        result = read_pzfx(str(pzfx_file), date_x="both")
        assert_frame_equal_loose(result, expected)

    def test_column_empty(self):
        pzfx_file = TESTDATA_DIR / "column_empty.pzfx"
        expected = read_expected("column_empty.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_empty_table(self):
        pzfx_file = TESTDATA_DIR / "empty.pzfx"
        result = read_pzfx(str(pzfx_file))
        assert result.empty

    def test_unequal_lengths(self):
        pzfx_file = TESTDATA_DIR / "column_unequal_lengths.pzfx"
        expected = read_expected("column_unequal_lengths.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_comma_decimal(self):
        pzfx_file = TESTDATA_DIR / "comma_decimal.pzfx"
        expected = read_expected("comma_decimal.tab")
        result = read_pzfx(str(pzfx_file))
        assert_frame_equal_loose(result, expected)

    def test_table_not_found(self):
        pzfx_file = TESTDATA_DIR / "parts_of_whole.pzfx"
        with pytest.raises(ValueError, match="Can't find WrongTab in prism file"):
            read_pzfx(str(pzfx_file), table="WrongTab")


class TestPzfxTables:
    """Tests for pzfx_tables function."""

    def test_list_tables(self):
        pzfx_file = TESTDATA_DIR / "column.pzfx"
        tables = pzfx_tables(str(pzfx_file))
        assert isinstance(tables, list)
        assert len(tables) > 0
