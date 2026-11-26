"""core/data_cleaner.py 的 pytest 测试。"""

import numpy as np
import pandas as pd
import pytest

from core.data_cleaner import (
    compare_dataframes,
    convert_data_types,
    dataframe_to_csv_bytes,
    drop_duplicate_rows,
    drop_missing_values,
    fill_missing_with_mean,
    fill_missing_with_median,
    handle_outliers_iqr,
    mark_outliers_iqr,
    reset_to_original,
)


def test_drop_missing_values(sample_df):
    cleaned = drop_missing_values(sample_df)
    assert len(cleaned) == 4
    assert cleaned["成绩"].isnull().sum() == 0


def test_drop_missing_values_empty_df():
    empty = pd.DataFrame({"成绩": pd.Series(dtype="float64")})
    assert len(drop_missing_values(empty)) == 0


def test_fill_missing_with_mean(sample_df):
    filled = fill_missing_with_mean(sample_df)
    assert filled["成绩"].isnull().sum() == 0
    # 已有成绩均值：(90+85+92+92) / 4 = 89.75
    assert filled.loc[filled["姓名"] == "小丽", "成绩"].iloc[0] == pytest.approx(89.75)


def test_fill_missing_with_median():
    df = pd.DataFrame({"成绩": [80.0, 90.0, 100.0, np.nan]})
    filled = fill_missing_with_median(df)
    assert filled["成绩"].iloc[3] == pytest.approx(90.0)


def test_fill_mean_does_not_modify_original(sample_df):
    fill_missing_with_mean(sample_df)
    assert sample_df["成绩"].isnull().sum() == 1


def test_drop_duplicate_rows(sample_df):
    cleaned = drop_duplicate_rows(sample_df)
    assert len(cleaned) == 4
    assert cleaned.duplicated().sum() == 0


def test_mark_outliers_iqr():
    df = pd.DataFrame({"成绩": [10, 11, 12, 13, 14, 15, 1000]})
    marked = mark_outliers_iqr(df)
    assert "成绩_异常值" in marked.columns
    assert bool(marked.loc[6, "成绩_异常值"]) is True
    assert marked["成绩_异常值"].sum() == 1


def test_handle_outliers_cap():
    df = pd.DataFrame({"成绩": [10.0, 11, 12, 13, 14, 15, 1000]})
    capped = handle_outliers_iqr(df, method="cap")
    assert capped["成绩"].max() < 1000


def test_handle_outliers_remove():
    df = pd.DataFrame({"成绩": [10.0, 11, 12, 13, 14, 15, 1000]})
    removed = handle_outliers_iqr(df, method="remove")
    assert len(removed) == 6


def test_handle_outliers_invalid_method():
    df = pd.DataFrame({"成绩": [10.0, 11, 12, 13, 14, 15, 1000]})
    with pytest.raises(ValueError):
        handle_outliers_iqr(df, method="hack")


def test_convert_data_types():
    df = pd.DataFrame({"成绩": ["90.5", "85.5"]})
    converted = convert_data_types(df, {"成绩": "float"})
    assert pd.api.types.is_float_dtype(converted["成绩"])


def test_compare_dataframes(sample_df):
    cleaned = drop_duplicate_rows(drop_missing_values(sample_df))
    result = compare_dataframes(sample_df, cleaned)
    summary = result["summary"].set_index("指标")
    assert summary.loc["行数", "清洗前"] == 5
    assert summary.loc["行数", "清洗后"] == 3
    assert summary.loc["重复行数量", "清洗后"] == 0


def test_dataframe_to_csv_bytes(sample_df):
    content = dataframe_to_csv_bytes(sample_df).decode("utf-8-sig")
    assert "姓名" in content.splitlines()[0]


def test_reset_to_original_returns_copy(sample_df):
    copy_df = reset_to_original(sample_df)
    copy_df.loc[0, "成绩"] = 0
    assert sample_df.loc[0, "成绩"] == 90
