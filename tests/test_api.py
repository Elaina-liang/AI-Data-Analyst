"""api.py 的 pytest 测试（FastAPI TestClient，不启动真实服务器）。

/ai/ask 用 monkeypatch 替换掉真实的 DeepSeek 调用，不需要 API Key、不联网；
/database/query 只测危险 SQL 在连数据库之前就被拦截，不需要 MySQL 服务器。
"""

import io

import api


def test_health(api_client):
    r = api_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root(api_client):
    r = api_client.get("/")
    assert r.status_code == 200
    assert r.json()["docs"] == "/docs"


def test_docs_page(api_client):
    assert api_client.get("/docs").status_code == 200


def test_upload_csv(api_client, csv_file_factory):
    r = api_client.post("/data/upload", files=csv_file_factory())
    assert r.status_code == 200
    data = r.json()
    assert data["rows"] == 5
    assert data["columns"] == ["姓名", "专业", "课程", "成绩"]


def test_upload_rejects_non_csv(api_client):
    files = {"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")}
    r = api_client.post("/data/upload", files=files)
    assert r.status_code == 400


def test_quality_report(api_client, csv_file_factory):
    r = api_client.post("/data/quality", files=csv_file_factory())
    assert r.status_code == 200
    assert r.json()["duplicates"]["重复行数量"] == 1


def test_clean_drop_duplicates_and_missing(api_client, csv_file_factory):
    r = api_client.post(
        "/data/clean",
        files=csv_file_factory(),
        data={"operations": "drop_duplicates,drop_missing"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["rows_before"] == 5
    assert data["rows_after"] == 3


def test_clean_invalid_operation(api_client, csv_file_factory):
    r = api_client.post(
        "/data/clean", files=csv_file_factory(), data={"operations": "hack"}
    )
    assert r.status_code == 400


def test_analyze_by_major(api_client, csv_file_factory):
    r = api_client.post("/data/analyze-by-major", files=csv_file_factory())
    assert r.status_code == 200
    majors = {row["专业"] for row in r.json()["result"]}
    assert majors == {"计算机科学", "数据科学"}


def test_analyze_by_major_missing_columns(api_client):
    files = {"file": ("a.csv", io.BytesIO("a,b\n1,2".encode()), "text/csv")}
    r = api_client.post("/data/analyze-by-major", files=files)
    assert r.status_code == 400


def test_database_query_rejects_write_sql(api_client):
    r = api_client.post(
        "/database/query",
        json={
            "host": "localhost", "port": 3306, "user": "root",
            "password": "", "database": "test",
            "query": "DELETE FROM students",
        },
    )
    assert r.status_code == 400


def test_ai_ask_success(api_client, csv_file_factory, monkeypatch):
    monkeypatch.setattr(api, "ask_deepseek", lambda q, ctx: "测试回答")
    r = api_client.post(
        "/ai/ask", files=csv_file_factory(), data={"question": "哪个专业平均分最高？"}
    )
    assert r.status_code == 200
    assert r.json()["answer"] == "测试回答"


def test_ai_ask_failure_returns_503(api_client, csv_file_factory, monkeypatch):
    def boom(q, ctx):
        raise RuntimeError("未找到 DeepSeek API Key")

    monkeypatch.setattr(api, "ask_deepseek", boom)
    r = api_client.post(
        "/ai/ask", files=csv_file_factory(), data={"question": "随便问问"}
    )
    assert r.status_code == 503
