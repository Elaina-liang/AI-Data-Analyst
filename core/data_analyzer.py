import pandas as pd


def analyze_by_major(df):
    """按照专业统计成绩"""

    result = df.groupby("专业").agg(
        平均成绩=("成绩", "mean"),
        最高成绩=("成绩", "max"),
        最低成绩=("成绩", "min"),
        学生人数=("姓名", "count"),
        课程数量=("课程", "nunique")
    )

    result["平均成绩"] = result["平均成绩"].round(2)

    return result