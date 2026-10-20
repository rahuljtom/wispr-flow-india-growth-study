"""Run one .sql file from sql/ in an in-memory DuckDB and return a DataFrame.

Inputs reach the query only as registered DataFrames (views) or named parameters ($name), never as
text spliced into the SQL, so data values cannot change the query.
"""
from pathlib import Path

import duckdb

SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def run_sql(name, params=None, tables=None):
    """Execute sql/<name> (one statement) and return its result as a DataFrame.

    params: values bound to $name placeholders. tables: {view name: DataFrame} the query can read.
    """
    text = (SQL_DIR / name).read_text()
    con = duckdb.connect(":memory:")
    try:
        for view, frame in (tables or {}).items():
            con.register(view, frame)
        return con.execute(text, params or {}).df()
    finally:
        con.close()
