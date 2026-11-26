"""core/database.py 的 pytest 测试。

用 SQLite 内存库代替 MySQL 服务器，验证连接、查表、加载表和只读查询逻辑；
另外单独校验 MySQL URL 构建和危险 SQL 拦截，不需要真的连 MySQL。

运行方式（任选其一）：
    python -m pytest test_database.py
    python test_database.py
"""

import pytest
from sqlalchemy import create_engine, text

from core.database import (
    build_mysql_url,
    list_tables,
    load_table,
    run_query,
    test_connection as db_test_connection,
    validate_readonly_query,
)


@pytest.fixture()
def engine():
    """带 students 表的 SQLite 内存库，每个用例一份，互不影响。"""
    eng = create_engine("sqlite:///:memory:")
    with eng.begin() as conn:
        conn.execute(text(
            "CREATE TABLE students (id INTEGER, name TEXT, score INTEGER)"
        ))
        conn.execute(text(
            "INSERT INTO students VALUES (1, '小明', 90), (2, '小红', 85), (3, '小刚', 92)"
        ))
    yield eng
    eng.dispose()


def test_connection_ok(engine):
    assert db_test_connection(engine) is True


def test_list_tables(engine):
    assert list_tables(engine) == ["students"]


def test_load_table(engine):
    df_table = load_table(engine, "students")
    assert len(df_table) == 3


def test_run_query(engine):
    df_query = run_query(engine, "SELECT name, score FROM students WHERE score >= 90")
    assert len(df_query) == 2
    assert set(df_query["name"]) == {"小明", "小刚"}


@pytest.mark.parametrize("bad_sql", [
    "DELETE FROM students",
    "UPDATE students SET score = 0",
    "DROP TABLE students",
    "SELECT * FROM students; DELETE FROM students",
    "",
])
def test_validate_readonly_query_rejects(bad_sql):
    with pytest.raises(ValueError):
        validate_readonly_query(bad_sql)


def test_build_mysql_url():
    # 密码中的特殊字符应被转义（只构建 URL，不连服务器）
    url = build_mysql_url("localhost", 3306, "root", "p@ss:word", "school")
    assert url.drivername == "mysql+pymysql"
    assert url.host == "localhost" and url.port == 3306 and url.database == "school"
    assert url.password == "p@ss:word"


if __name__ == "__main__":
    # 兼容原来的 python test_database.py 跑法：转交给 pytest 执行本文件
    raise SystemExit(pytest.main([__file__, "-q"]))
