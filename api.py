"""AI-Data-Analyst 的 FastAPI 后端接口。

把 core/ 里已有的数据处理能力包装成 HTTP 接口，供前端或其他程序调用。
和 Streamlit 页面（app.py）相互独立：app.py 是给人看的页面，
api.py 只返回 JSON 数据，没有页面。

启动：
    uvicorn api:app --reload
启动后打开 http://127.0.0.1:8000/docs 可以在线查看和测试全部接口。
"""

import io

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from core.ai_analyzer import ask_deepseek
from core.data_analyzer import analyze_by_major
from core.data_cleaner import (
    drop_duplicate_rows,
    drop_missing_values,
    fill_missing_with_mean,
    fill_missing_with_median,
    handle_outliers_iqr,
    mark_outliers_iqr,
)
from core.data_quality import (
    check_data_types,
    check_duplicate_rows,
    check_missing_values,
    check_outliers_iqr,
)
from core.database import create_mysql_engine, run_query

# 创建 FastAPI 应用
app = FastAPI(
    title="AI-Data-Analyst API",
    description="AI 数据分析系统后端接口",
    version="1.0.0",
)


# ---------- 通用小工具 ----------

async def read_csv_file(file: UploadFile) -> pd.DataFrame:
    """把上传的文件读成 DataFrame，只接受 CSV。"""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="只支持上传 CSV 文件。")
    content = await file.read()
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV 文件读取失败：{e}")


def to_python(value):
    """把 numpy / pandas 的类型递归转成普通 Python 类型，NaN 转 None，保证能编码成 JSON。"""
    if isinstance(value, dict):
        return {str(k): to_python(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_python(v) for v in value]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return None if pd.isna(value) else float(value)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, float):
        return None if pd.isna(value) else value
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def df_records(df: pd.DataFrame, limit: int | None = None):
    """DataFrame 转成 JSON 友好的记录列表（空值转 None，numpy 类型转普通类型）。"""
    if limit is not None:
        df = df.head(limit)
    # 先转 object 类型，否则 float 列里的 None 会被 pandas 又变回 NaN，JSON 编码会报错
    cleaned = df.astype(object).where(pd.notnull(df), None)
    return to_python(cleaned.to_dict(orient="records"))


# ---------- 基础接口 ----------

@app.get("/")
def root():
    return {
        "service": "AI-Data-Analyst API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# 健康检查接口
@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AI-Data-Analyst API is running",
    }


# ---------- 数据接口（上传 CSV） ----------

@app.post("/data/upload", summary="上传 CSV，返回基本信息和预览")
async def upload_data(file: UploadFile = File(...)):
    df = await read_csv_file(file)
    return {
        "filename": file.filename,
        "rows": len(df),
        "columns": df.columns.tolist(),
        "preview": df_records(df, limit=5),
    }


@app.post("/data/quality", summary="上传 CSV，返回数据质量报告")
async def data_quality(file: UploadFile = File(...)):
    df = await read_csv_file(file)

    missing = check_missing_values(df).reset_index().rename(
        columns={"index": "column"}
    )
    types = check_data_types(df).reset_index().rename(
        columns={"index": "column"}
    )
    return {
        "rows": len(df),
        "missing_values": df_records(missing),
        "duplicates": to_python(check_duplicate_rows(df)),
        "outliers": to_python(check_outliers_iqr(df)),
        "data_types": df_records(types),
    }


# 支持的清洗操作：名字 -> (函数, 说明)
_CLEAN_OPERATIONS = {
    "drop_missing": drop_missing_values,
    "fill_mean": fill_missing_with_mean,
    "fill_median": fill_missing_with_median,
    "drop_duplicates": drop_duplicate_rows,
    "mark_outliers": mark_outliers_iqr,
}


@app.post("/data/clean", summary="上传 CSV 并执行数据清洗")
async def clean_data(
    file: UploadFile = File(...),
    operations: str = Form(
        "drop_duplicates",
        description="逗号分隔的清洗操作，可选：drop_missing、fill_mean、fill_median、drop_duplicates、mark_outliers、cap_outliers",
    ),
):
    df = await read_csv_file(file)
    rows_before = len(df)

    for name in [op.strip() for op in operations.split(",") if op.strip()]:
        if name == "cap_outliers":
            df = handle_outliers_iqr(df, method="cap")
        elif name in _CLEAN_OPERATIONS:
            df = _CLEAN_OPERATIONS[name](df)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的清洗操作：{name}。可选：{', '.join([*_CLEAN_OPERATIONS, 'cap_outliers'])}",
            )

    return {
        "operations": operations,
        "rows_before": rows_before,
        "rows_after": len(df),
        "columns": df.columns.tolist(),
        "preview": df_records(df, limit=5),
    }


@app.post("/data/analyze-by-major", summary="按专业统计成绩（需要 姓名/专业/课程/成绩 列）")
async def analyze_major(file: UploadFile = File(...)):
    df = await read_csv_file(file)
    required = {"姓名", "专业", "课程", "成绩"}
    missing_columns = required - set(df.columns)
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"数据缺少必要的列：{', '.join(sorted(missing_columns))}",
        )
    result = analyze_by_major(df).reset_index()
    return {"result": df_records(result)}


# ---------- AI 分析接口 ----------

@app.post("/ai/ask", summary="上传 CSV 并用自然语言向 AI 提问（需要配置 DeepSeek API Key）")
async def ai_ask(
    file: UploadFile = File(...),
    question: str = Form(..., description="例如：哪个专业的平均成绩最高？"),
):
    df = await read_csv_file(file)

    data_context = f"""
数据行数：{len(df)}
数据列数：{len(df.columns)}
列名：{df.columns.tolist()}

数据统计：
{df.describe(include="all").to_string()}

缺失值数量：
{df.isna().sum().to_string()}

完全重复行数量：{int(df.duplicated().sum())}
"""
    if "专业" in df.columns:
        numeric_columns = df.select_dtypes(include="number").columns.tolist()
        for column in numeric_columns:
            data_context += (
                f"\n各专业的{column}平均值：\n"
                + df.groupby("专业")[column].mean().to_string()
            )

    try:
        answer = ask_deepseek(question, data_context)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 分析失败：{e}")

    return {"question": question, "answer": answer}


# ---------- MySQL 查询接口 ----------

class DatabaseQuery(BaseModel):
    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = Field(..., description="数据库名")
    query: str = Field(..., description="只允许 SELECT / WITH 开头的单条只读查询")
    limit: int = 1000


@app.post("/database/query", summary="连接 MySQL 执行只读 SQL 查询")
def database_query(payload: DatabaseQuery):
    engine = create_mysql_engine(
        host=payload.host,
        port=payload.port,
        user=payload.user,
        password=payload.password,
        database=payload.database,
    )
    try:
        df = run_query(engine, payload.query, limit=payload.limit)
    except ValueError as e:
        # SQL 校验不通过（写操作、多语句等）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"数据库查询失败：{e}")
    finally:
        engine.dispose()

    return {
        "rows": len(df),
        "columns": df.columns.tolist(),
        "result": df_records(df),
    }
