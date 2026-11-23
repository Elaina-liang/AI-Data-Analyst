
import pandas as pd


def check_missing_values(df):
    """检查数据中的缺失值"""

    result = pd.DataFrame({
        "缺失数量": df.isnull().sum(),
        "缺失比例(%)": (df.isnull().mean() * 100).round(2)
    })

    return result

def check_duplicate_rows(df):
    """检查数据中的重复行"""

    duplicate_count = df.duplicated().sum()

    result = {
        "重复行数量": duplicate_count,
        "重复行比例(%)": round(
            duplicate_count / len(df) * 100, 2
        ) if len(df) > 0 else 0
    }

    return result


def check_outliers_iqr(df):
    """使用 IQR 四分位距法检测数值列中的异常值"""

    result = {}

    numeric_columns = df.select_dtypes(
        include="number"
    ).columns

    for column in numeric_columns:
        # 计算第一、第三四分位数
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)

        # 计算四分位距
        iqr = q3 - q1

        # 计算异常值判断边界
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        # 判断异常值
        outliers = df[
            (df[column] < lower_bound) |
            (df[column] > upper_bound)
        ][column]

        result[column] = {
            "异常值数量": len(outliers),
            "异常值": outliers.tolist(),
            "下界": round(lower_bound, 2),
            "上界": round(upper_bound, 2)
        }

    return result


def check_data_types(df):
    """检查每一列的数据类型"""

    result = pd.DataFrame({
        "数据类型": df.dtypes.astype(str),
        "非空数量": df.count(),
        "缺失数量": df.isnull().sum()
    })

    return result
