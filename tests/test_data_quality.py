"""core/data_quality.py 和 core/data_analyzer.py 的 pytest 测试。"""

import pandas as pd

from core.data_analyzer import analyze_by_major
from core.data_quality import (
    check_data_types,
    check_duplicate_rows,
    check_missing_values,
    check_outliers_iqr,
)


def test_check_missing_values(sample_df):
    result = check_missing_values(sample_df)
    assert result.loc["成绩", "缺失数量"] == 1
    assert result.loc["姓名", "缺失数量"] == 0


def test_check_duplicate_rows(sample_df):
    result = check_duplicate_rows(sample_df)
    assert result["重复行数量"] == 1


def test_check_duplicate_rows_empty_df():
    result = check_duplicate_rows(pd.DataFrame({"成绩": pd.Series(dtype="float64")}))
    assert result["重复行数量"] == 0
    assert result["重复行比例(%)"] == 0


def test_check_outliers_iqr():
    df = pd.DataFrame({"成绩": [10, 11, 12, 13, 14, 15, 1000]})
    result = check_outliers_iqr(df)
    assert result["成绩"]["异常值数量"] == 1
    assert result["成绩"]["异常值"] == [1000]


def test_check_outliers_none():
    df = pd.DataFrame({"成绩": [80, 82, 84, 86, 88]})
    result = check_outliers_iqr(df)
    assert result["成绩"]["异常值数量"] == 0


def test_check_data_types(sample_df):
    result = check_data_types(sample_df)
    assert result.loc["姓名", "非空数量"] == 5
    assert result.loc["成绩", "缺失数量"] == 1


def test_analyze_by_major(sample_df):
    result = analyze_by_major(sample_df.dropna())
    assert set(result.index) == {"计算机科学", "数据科学"}
    assert result.loc["计算机科学", "平均成绩"] == 87.5
    assert result.loc["数据科学", "学生人数"] == 2
