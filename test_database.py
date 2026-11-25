"""core/database.py 的冒烟测试。

用 SQLite 内存库代替 MySQL 服务器，验证连接、查表、加载表和只读查询逻辑；
另外单独校验 MySQL URL 构建和危险 SQL 拦截，不需要真的连 MySQL。
运行：python test_database.py
"""

import pandas as pd
from sqlalchemy import create_engine, text

from core.database import (
    build_mysql_url,
    list_tables,
    load_table,
    run_query,
    test_connection,
    validate_readonly_query,
)

# 1. 准备一个内存数据库和一张示例表
engine = create_engine("sqlite:///:memory:")
with engine.begin() as conn:
    conn.execute(text(
        "CREATE TABLE students (id INTEGER, name TEXT, score INTEGER)"
    ))
    conn.execute(text(
        "INSERT INTO students VALUES (1, '小明', 90), (2, '小红', 85), (3, '小刚', 92)"
    ))

# 2. 连接 / 查表 / 加载表
assert test_connection(engine) is True
assert list_tables(engine) == ["students"]
df_table = load_table(engine, "students")
assert len(df_table) == 3

# 3. 只读查询
df_query = run_query(engine, "SELECT name, score FROM students WHERE score >= 90")
assert len(df_query) == 2
assert set(df_query["name"]) == {"小明", "小刚"}

# 4. 危险或不合法的 SQL 必须被拦截
for bad_sql in [
    "DELETE FROM students",
    "UPDATE students SET score = 0",
    "DROP TABLE students",
    "SELECT * FROM students; DELETE FROM students",
    "",
]:
    try:
        validate_readonly_query(bad_sql)
    except ValueError:
        pass
    else:
        raise AssertionError(f"危险 SQL 没有被拦截：{bad_sql!r}")

# 5. MySQL URL 构建（密码中的特殊字符应被转义，不连服务器）
url = build_mysql_url("localhost", 3306, "root", "p@ss:word", "school")
assert url.drivername == "mysql+pymysql"
assert url.host == "localhost" and url.port == 3306 and url.database == "school"
assert url.password == "p@ss:word"

engine.dispose()
print("全部测试通过：连接、查表、加载表、只读查询、危险 SQL 拦截、MySQL URL 构建都正常。")
