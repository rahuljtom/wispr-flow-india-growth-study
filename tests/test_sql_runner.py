import pandas as pd
import pytest

from src.common import sql


@pytest.fixture
def sql_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(sql, "SQL_DIR", tmp_path)
    return tmp_path


def test_parameters_and_views(sql_dir):
    (sql_dir / "q.sql").write_text("SELECT name, v * $k AS scaled FROM src ORDER BY name")
    src = pd.DataFrame({"name": ["b", "a"], "v": [2.0, 1.5]})
    out = sql.run_sql("q.sql", {"k": 10}, {"src": src})
    assert out.to_dict("list") == {"name": ["a", "b"], "scaled": [15.0, 20.0]}


def test_null_round_trip_not_zero(sql_dir):
    (sql_dir / "q.sql").write_text("SELECT TRY_CAST(x AS DOUBLE) AS n FROM src ORDER BY x")
    out = sql.run_sql("q.sql", tables={"src": pd.DataFrame({"x": ["1.5", "unknown"]})})
    assert out["n"].tolist()[0] == 1.5 and pd.isna(out["n"].tolist()[1])


def test_data_values_cannot_alter_the_query(sql_dir):
    (sql_dir / "q.sql").write_text("SELECT count(*) AS n FROM src WHERE label = $label")
    src = pd.DataFrame({"label": ["x'; DROP TABLE src; --", "ok"]})
    out = sql.run_sql("q.sql", {"label": "x'; DROP TABLE src; --"}, {"src": src})
    assert int(out["n"][0]) == 1


def test_missing_file_raises(sql_dir):
    with pytest.raises(FileNotFoundError):
        sql.run_sql("nope.sql")
