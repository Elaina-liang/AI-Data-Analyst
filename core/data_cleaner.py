
import io

import pandas as pd


def drop_missing_values(df):
    """删除包含缺失值的行"""

    cleaned_df = df.dropna()

    return cleaned_df


def fill_missing_with_mean(df, columns=None):
    """使用均值填充缺失值（默认对数值列填充）"""

    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include="number").columns.tolist()

    for column in columns:
        if column in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[column]):
            mean_value = cleaned_df[column].mean()
            if pd.notna(mean_value):
                cleaned_df[column] = cleaned_df[column].fillna(mean_value)

    return cleaned_df


def fill_missing_with_median(df, columns=None):
    """使用中位数填充缺失值（默认对数值列填充）"""

    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include="number").columns.tolist()

    for column in columns:
        if column in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[column]):
            median_value = cleaned_df[column].median()
            if pd.notna(median_value):
                cleaned_df[column] = cleaned_df[column].fillna(median_value)

    return cleaned_df


def drop_duplicate_rows(df, subset=None, keep="first"):
    """删除重复数据"""

    cleaned_df = df.drop_duplicates(subset=subset, keep=keep)

    return cleaned_df


def _get_iqr_bounds(series):
    """计算 IQR 异常值边界"""

    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return lower_bound, upper_bound


def mark_outliers_iqr(df, columns=None):
    """标记异常值（基于 IQR 方法，新增布尔标记列）"""

    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include="number").columns.tolist()

    for column in columns:
        if column not in cleaned_df.columns or not pd.api.types.is_numeric_dtype(cleaned_df[column]):
            continue

        series = cleaned_df[column]
        if series.dropna().empty:
            cleaned_df[f"{column}_异常值"] = False
            continue

        lower_bound, upper_bound = _get_iqr_bounds(series)
        cleaned_df[f"{column}_异常值"] = (series < lower_bound) | (series > upper_bound)

    return cleaned_df


def handle_outliers_iqr(df, columns=None, method="cap"):
    """处理异常值（基于 IQR 方法）

    method:
        - cap: 将异常值截断到上下界
        - remove: 删除包含异常值的行
        - median: 用中位数替换异常值
        - mean: 用均值替换异常值
    """

    cleaned_df = df.copy()
    if columns is None:
        columns = cleaned_df.select_dtypes(include="number").columns.tolist()

    valid_columns = [
        column for column in columns
        if column in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[column])
    ]

    if method == "remove":
        mask = pd.Series(False, index=cleaned_df.index)
        for column in valid_columns:
            series = cleaned_df[column]
            if series.dropna().empty:
                continue
            lower_bound, upper_bound = _get_iqr_bounds(series)
            mask = mask | (series < lower_bound) | (series > upper_bound)
        return cleaned_df.loc[~mask].copy()

    for column in valid_columns:
        series = cleaned_df[column]
        non_null = series.dropna()
        if non_null.empty:
            continue

        lower_bound, upper_bound = _get_iqr_bounds(series)
        outlier_mask = (series < lower_bound) | (series > upper_bound)

        if not outlier_mask.any():
            continue

        if method == "cap":
            cleaned_df[column] = series.clip(lower=lower_bound, upper=upper_bound)
        elif method == "median":
            replacement = series.median()
            cleaned_df.loc[outlier_mask, column] = replacement
        elif method == "mean":
            replacement = series.mean()
            cleaned_df.loc[outlier_mask, column] = replacement
        else:
            raise ValueError(f"不支持的异常值处理方法: {method}")

    return cleaned_df


def convert_data_types(df, column_types=None, infer_objects=False):
    """数据类型转换

    column_types: {列名: 目标类型}，目标类型支持 int、float、str、bool、datetime、category 等 pandas 可识别类型。
    infer_objects: 为 True 时尝试自动推断 object 列类型。
    """

    cleaned_df = df.copy()

    if column_types:
        for column, target_type in column_types.items():
            if column not in cleaned_df.columns:
                continue

            target = str(target_type).lower()
            try:
                if target in ("datetime", "datetime64", "datetime64[ns]", "date", "time"):
                    cleaned_df[column] = pd.to_datetime(cleaned_df[column], errors="coerce")
                elif target in ("int", "int64", "integer"):
                    numeric_series = pd.to_numeric(cleaned_df[column], errors="coerce")
                    cleaned_df[column] = numeric_series.astype("Int64")
                elif target in ("float", "float64", "number", "numeric"):
                    cleaned_df[column] = pd.to_numeric(cleaned_df[column], errors="coerce")
                elif target in ("bool", "boolean"):
                    cleaned_df[column] = cleaned_df[column].astype("boolean")
                elif target in ("str", "string", "object", "text"):
                    cleaned_df[column] = cleaned_df[column].astype("string")
                elif target == "category":
                    cleaned_df[column] = cleaned_df[column].astype("category")
                else:
                    cleaned_df[column] = cleaned_df[column].astype(target_type)
            except Exception:
                # 转换失败时保留原列，避免中断整体清洗流程
                cleaned_df[column] = df[column]

    if infer_objects:
        cleaned_df = cleaned_df.infer_objects(copy=False)

    return cleaned_df


def compare_dataframes(original_df, cleaned_df):
    """清洗前后数据对比"""

    original_missing = int(original_df.isnull().sum().sum())
    cleaned_missing = int(cleaned_df.isnull().sum().sum())
    original_duplicates = int(original_df.duplicated().sum())
    cleaned_duplicates = int(cleaned_df.duplicated().sum())

    summary = pd.DataFrame([
        {
            "指标": "行数",
            "清洗前": int(len(original_df)),
            "清洗后": int(len(cleaned_df)),
            "变化": int(len(cleaned_df) - len(original_df)),
        },
        {
            "指标": "列数",
            "清洗前": int(len(original_df.columns)),
            "清洗后": int(len(cleaned_df.columns)),
            "变化": int(len(cleaned_df.columns) - len(original_df.columns)),
        },
        {
            "指标": "缺失值总数",
            "清洗前": original_missing,
            "清洗后": cleaned_missing,
            "变化": cleaned_missing - original_missing,
        },
        {
            "指标": "重复行数量",
            "清洗前": original_duplicates,
            "清洗后": cleaned_duplicates,
            "变化": cleaned_duplicates - original_duplicates,
        },
        {
            "指标": "内存占用(bytes)",
            "清洗前": int(original_df.memory_usage(deep=True).sum()),
            "清洗后": int(cleaned_df.memory_usage(deep=True).sum()),
            "变化": int(cleaned_df.memory_usage(deep=True).sum() - original_df.memory_usage(deep=True).sum()),
        },
    ])

    all_columns = sorted(set(original_df.columns) | set(cleaned_df.columns))
    dtype_rows = []
    for column in all_columns:
        before_dtype = str(original_df[column].dtype) if column in original_df.columns else "不存在"
        after_dtype = str(cleaned_df[column].dtype) if column in cleaned_df.columns else "不存在"
        dtype_rows.append({
            "列名": column,
            "清洗前类型": before_dtype,
            "清洗后类型": after_dtype,
            "是否变化": before_dtype != after_dtype,
        })

    missing_rows = []
    for column in all_columns:
        before_missing = int(original_df[column].isnull().sum()) if column in original_df.columns else None
        after_missing = int(cleaned_df[column].isnull().sum()) if column in cleaned_df.columns else None
        change = None
        if before_missing is not None and after_missing is not None:
            change = after_missing - before_missing
        missing_rows.append({
            "列名": column,
            "清洗前缺失值": before_missing,
            "清洗后缺失值": after_missing,
            "变化": change,
        })

    return {
        "summary": summary,
        "dtypes": pd.DataFrame(dtype_rows),
        "missing_values": pd.DataFrame(missing_rows),
    }


def dataframe_to_csv_bytes(df, index=False):
    """将数据框导出为 CSV 字节流（用于下载）"""

    return df.to_csv(index=index).encode("utf-8-sig")


def reset_to_original(original_df):
    """保留原始数据并返回可编辑的清洗副本"""

    return original_df.copy()


