"""api.py 的 pytest 测试（使用 FastAPI TestClient，不用真的启动服务器）。

运行方式（任选其一）：
    python -m pytest test_api.py
    python test_api.py
注意：/ai/ask 需要真实的 DeepSeek API Key，本文件不调用它，tests/ 里
有 monkeypatch 版本；/database/query 只测危险 SQL 被拦截，
不需要真的有 MySQL 服务器。
"""

import io

import pytest
from fastapi.testclient import TestClient

from api import app

# 示例 CSV：含 1 行重复、1 个缺失值
CSV_TEXT = """姓名,专业,课程,成绩
小明,计算机科学,数学,90
小红,计算机科学,数学,85
小刚,数据科学,数学,92
小刚,数据科学,数学,92
小丽,数据科学,英语,
"""


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def upload_csv():
    """每次调用生成一份新的上传文件参数（文件流读完不能复用）。"""
    def make():
        return {"file": ("students.csv", io.BytesIO(CSV_TEXT.encode("utf-8")), "text/csv")}
    return make


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok", r.text


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200 and r.json()["docs"] == "/docs", r.text


def test_upload_csv(client, upload_csv):
    r = client.post("/data/upload", files=upload_csv())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["rows"] == 5 and data["columns"] == ["姓名", "专业", "课程", "成绩"], data


def test_data_quality(client, upload_csv):
    r = client.post("/data/quality", files=upload_csv())
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["duplicates"]["重复行数量"] == 1, data


def test_clean_drop_duplicates_and_missing(client, upload_csv):
    r = client.post(
        "/data/clean",
        files=upload_csv(),
        data={"operations": "drop_duplicates,drop_missing"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["rows_before"] == 5 and data["rows_after"] == 3, data


def test_clean_invalid_operation(client, upload_csv):
    r = client.post("/data/clean", files=upload_csv(), data={"operations": "hack"})
    assert r.status_code == 400, r.text


def test_analyze_by_major(client, upload_csv):
    r = client.post("/data/analyze-by-major", files=upload_csv())
    assert r.status_code == 200, r.text
    majors = {row["专业"] for row in r.json()["result"]}
    assert majors == {"计算机科学", "数据科学"}, majors


def test_upload_rejects_non_csv(client):
    r = client.post(
        "/data/upload",
        files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 400, r.text


def test_database_query_rejects_write_sql(client):
    # 危险 SQL 在连接数据库之前就应被拦截
    r = client.post(
        "/database/query",
        json={
            "host": "localhost", "port": 3306, "user": "root",
            "password": "", "database": "test",
            "query": "DELETE FROM students",
        },
    )
    assert r.status_code == 400, r.text


def test_docs_page(client):
    r = client.get("/docs")
    assert r.status_code == 200, r.text


if __name__ == "__main__":
    # 兼容原来的 python test_api.py 跑法：转交给 pytest 执行本文件
    raise SystemExit(pytest.main([__file__, "-q"]))
