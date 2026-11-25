"""MySQL 数据库连接与只读 SQL 查询。

使用 SQLAlchemy + PyMySQL 连接 MySQL：
- build_mysql_url / create_mysql_engine：根据连接参数创建引擎
- test_connection：测试连接是否可用
- list_tables：列出当前数据库中的表
- load_table：把整张表（或前 N 行）读成 DataFrame
- run_query：执行只读 SQL 查询并返回 DataFrame

安全约定：
- 只允许 SELECT / WITH 开头的单条查询，拒绝增删改、建表、多语句等操作，
  避免在分析页面里误改数据库。
- 查询结果默认最多返回 1000 行，防止一次拉太多数据。
"""

import re

import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL

# 禁止出现的写操作关键字（整词匹配，不区分大小写）
_FORBIDDEN_KEYWORDS = (
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "replace", "grant", "revoke", "rename", "call",
)

DEFAULT_LIMIT = 1000


def build_mysql_url(host, port, user, password, database):
    """根据连接参数构建 MySQL 连接 URL（密码会被正确转义）。"""
    return URL.create(
        drivername="mysql+pymysql",
        username=user,
        password=password,
        host=host,
        port=int(port),
        database=database,
        query={"charset": "utf8mb4"},
    )


def create_mysql_engine(host, port, user, password, database):
    """创建 SQLAlchemy 引擎。调用方负责在用完后 engine.dispose()。"""
    url = build_mysql_url(host, port, user, password, database)
    return create_engine(url, pool_pre_ping=True)


def test_connection(engine):
    """测试连接：执行 SELECT 1，成功返回 True，失败会抛出异常。"""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True


def list_tables(engine):
    """列出当前数据库中的全部表名。"""
    return inspect(engine).get_table_names()


def load_table(engine, table_name, limit=DEFAULT_LIMIT):
    """把一张表读成 DataFrame，最多返回 limit 行。"""
    if not re.fullmatch(r"[A-Za-z0-9_]+", table_name or ""):
        raise ValueError("表名不合法，只能包含字母、数字和下划线。")
    query = f"SELECT * FROM `{table_name}` LIMIT {int(limit)}"
    return pd.read_sql(text(query), engine)


def validate_readonly_query(query):
    """校验 SQL 是否为安全的只读查询，返回去掉末尾分号的查询字符串。

    规则：
    - 不能为空
    - 只能有一条语句（不允许用分号拼接多条）
    - 必须以 SELECT 或 WITH 开头
    - 不能包含 insert/update/delete/drop 等写操作关键字
    """
    if query is None or not str(query).strip():
        raise ValueError("SQL 查询不能为空。")

    cleaned = str(query).strip()
    # 去掉末尾单个分号；中间还有分号说明是多条语句
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()
    if ";" in cleaned:
        raise ValueError("只允许执行一条 SQL 语句。")

    first_word = re.match(r"[A-Za-z]+", cleaned)
    if not first_word or first_word.group(0).lower() not in ("select", "with"):
        raise ValueError("只允许执行 SELECT 查询。")

    lowered = cleaned.lower()
    for keyword in _FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            raise ValueError(f"查询中包含不允许的关键字：{keyword}")

    return cleaned


def run_query(engine, query, limit=DEFAULT_LIMIT):
    """执行只读 SQL 查询，返回 DataFrame，结果最多 limit 行。

    通过把原查询包一层子查询来强制行数上限。
    """
    cleaned = validate_readonly_query(query)
    wrapped = f"SELECT * FROM ({cleaned}) AS _ai_data_analyst_q LIMIT {int(limit)}"
    return pd.read_sql(text(wrapped), engine)
