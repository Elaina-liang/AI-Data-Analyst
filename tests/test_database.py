"""core/database.py 的 pytest 测试（用 SQLite 内存库代替 MySQL）。"""

import pytest

from core.database import (
    build_mysql_url,
    list_tables,
    load_table,
    run_query,
    test_connection as db_test_connection,
    validate_readonly_query,
)


def test_connection_ok(sqlite_engine):
    assert db_test_connection(sqlite_engine) is True


def test_list_tables(sqlite_engine):
    assert list_tables(sqlite_engine) == ["students"]


def test_load_table(sqlite_engine):
    df = load_table(sqlite_engine, "students")
    assert len(df) == 3
    assert list(df.columns) == ["id", "name", "score"]


def test_load_table_limit(sqlite_engine):
    df = load_table(sqlite_engine, "students", limit=2)
    assert len(df) == 2


def test_load_table_invalid_name(sqlite_engine):
    with pytest.raises(ValueError):
        load_table(sqlite_engine, "students; DROP TABLE students")


def test_run_query(sqlite_engine):
    df = run_query(sqlite_engine, "SELECT name, score FROM students WHERE score >= 90")
    assert len(df) == 2
    assert set(df["name"]) == {"小明", "小刚"}


def test_run_query_limit(sqlite_engine):
    df = run_query(sqlite_engine, "SELECT * FROM students", limit=1)
    assert len(df) == 1


def test_validate_readonly_query_ok():
    assert validate_readonly_query("SELECT * FROM students;") == "SELECT * FROM students"
    assert validate_readonly_query("  select id from students ").startswith("select")


@pytest.mark.parametrize("bad_sql", [
    "DELETE FROM students",
    "UPDATE students SET score = 0",
    "DROP TABLE students",
    "INSERT INTO students VALUES (4, 'x', 1)",
    "SELECT * FROM students; DELETE FROM students",
    "",
    "   ",
    None,
])
def test_validate_readonly_query_rejects(bad_sql):
    with pytest.raises(ValueError):
        validate_readonly_query(bad_sql)


def test_build_mysql_url_escapes_password():
    url = build_mysql_url("localhost", 3306, "root", "p@ss:word", "school")
    assert url.drivername == "mysql+pymysql"
    assert url.host == "localhost"
    assert url.port == 3306
    assert url.database == "school"
    assert url.password == "p@ss:word"
