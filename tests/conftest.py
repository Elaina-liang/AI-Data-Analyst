"""pytest 共享夹具：示例数据、SQLite 内存库、FastAPI 测试客户端。

这些夹具都不连真实的 MySQL 服务器、不调用 DeepSeek，
保证测试在任何机器上都能离线、重复运行。
"""

import io

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

# 示例成绩数据：含 1 行完全重复、1 个缺失成绩
CSV_TEXT = """姓名,专业,课程,成绩
小明,计算机科学,数学,90
小红,计算机科学,数学,85
小刚,数据科学,数学,92
小刚,数据科学,数学,92
小丽,数据科学,英语,
"""


@pytest.fixture()
def sample_df():
    """从 CSV_TEXT 读出的 DataFrame（成绩列含 1 个 NaN）。"""
    return pd.read_csv(io.StringIO(CSV_TEXT))


@pytest.fixture()
def csv_file_factory():
    """返回一个函数，每次调用生成一份新的上传文件参数（文件读完不能复用）。"""
    def make():
        return {"file": ("students.csv", io.BytesIO(CSV_TEXT.encode("utf-8")), "text/csv")}
    return make


@pytest.fixture()
def sqlite_engine():
    """带 students 表的 SQLite 内存库引擎，代替真实 MySQL 做数据库测试。"""
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE students (id INTEGER, name TEXT, score INTEGER)"
        ))
        conn.execute(text(
            "INSERT INTO students VALUES (1, '小明', 90), (2, '小红', 85), (3, '小刚', 92)"
        ))
    yield engine
    engine.dispose()


@pytest.fixture()
def api_client():
    """FastAPI 的 TestClient，不需要真的启动 uvicorn 服务器。"""
    from fastapi.testclient import TestClient

    from api import app

    return TestClient(app)
