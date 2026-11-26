"""api.py 的冒烟测试（使用 FastAPI TestClient，不用真的启动服务器）。

运行前先安装依赖：pip install -r requirements.txt httpx
运行：python test_api.py
注意：/ai/ask 需要真实的 DeepSeek API Key，本测试不调用它；
/database/query 只测危险 SQL 被拦截，不需要真的有 MySQL 服务器。
"""

import io

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)

# 示例 CSV：含 1 行重复、1 个缺失值
CSV_TEXT = """姓名,专业,课程,成绩
小明,计算机科学,数学,90
小红,计算机科学,数学,85
小刚,数据科学,数学,92
小刚,数据科学,数学,92
小丽,数据科学,英语,
"""


def upload_csv():
    return {"file": ("students.csv", io.BytesIO(CSV_TEXT.encode("utf-8")), "text/csv")}


# 1. 健康检查和首页
r = client.get("/health")
assert r.status_code == 200 and r.json()["status"] == "ok", r.text
r = client.get("/")
assert r.status_code == 200 and r.json()["docs"] == "/docs", r.text

# 2. 上传预览
r = client.post("/data/upload", files=upload_csv())
assert r.status_code == 200, r.text
data = r.json()
assert data["rows"] == 5 and data["columns"] == ["姓名", "专业", "课程", "成绩"], data

# 3. 数据质量报告
r = client.post("/data/quality", files=upload_csv())
assert r.status_code == 200, r.text
data = r.json()
assert data["duplicates"]["重复行数量"] == 1, data

# 4. 数据清洗：去重 + 删缺失
r = client.post(
    "/data/clean",
    files=upload_csv(),
    data={"operations": "drop_duplicates,drop_missing"},
)
assert r.status_code == 200, r.text
data = r.json()
assert data["rows_before"] == 5 and data["rows_after"] == 3, data

# 5. 不支持的清洗操作应报错
r = client.post("/data/clean", files=upload_csv(), data={"operations": "hack"})
assert r.status_code == 400, r.text

# 6. 按专业分析
r = client.post("/data/analyze-by-major", files=upload_csv())
assert r.status_code == 200, r.text
majors = {row["专业"] for row in r.json()["result"]}
assert majors == {"计算机科学", "数据科学"}, majors

# 7. 非 CSV 文件应报错
r = client.post(
    "/data/upload",
    files={"file": ("a.txt", io.BytesIO(b"hello"), "text/plain")},
)
assert r.status_code == 400, r.text

# 8. MySQL 接口：危险 SQL 在连接数据库之前就应被拦截
r = client.post(
    "/database/query",
    json={
        "host": "localhost", "port": 3306, "user": "root",
        "password": "", "database": "test",
        "query": "DELETE FROM students",
    },
)
assert r.status_code == 400, r.text

# 9. /docs 页面可打开
r = client.get("/docs")
assert r.status_code == 200, r.text

print("全部测试通过：/health、/、/data/upload、/data/quality、/data/clean、/data/analyze-by-major、/database/query 校验、/docs 都正常。")
