import sqlite3

import pytest

from python_capstone.db.sqldb import (
    ColumnInfo,
    TableInfo,
    execute_query,
    format_results,
    format_schema,
    introspect_schema,
)


@pytest.fixture
def memory_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE products (product_id INTEGER, name TEXT, unit_price REAL)")
    conn.execute("INSERT INTO products VALUES (1, 'Mug', 16.99)")
    conn.execute("INSERT INTO products VALUES (2, 'Wallet', 49.99)")
    conn.commit()
    yield conn
    conn.close()


def test_introspect_schema_finds_table_and_columns(memory_conn):
    tables = introspect_schema(memory_conn)

    assert len(tables) == 1
    assert tables[0].name == "products"

    column_names = [c.name for c in tables[0].columns]
    assert column_names == ["product_id", "name", "unit_price"]


def test_format_schema_produces_expected_string():
    tables = [
        TableInfo(
            name="products",
            columns=[
                ColumnInfo(name="product_id", type="INTEGER"),
                ColumnInfo(name="name", type="TEXT"),
            ],
        )
    ]

    expected = "Table: products\n  - product_id: INTEGER\n  - name: TEXT"
    assert format_schema(tables) == expected


def test_format_schema_separates_multiple_tables_with_blank_line():
    tables = [
        TableInfo(name="regions", columns=[ColumnInfo(name="region_id", type="INTEGER")]),
        TableInfo(name="products", columns=[ColumnInfo(name="product_id", type="INTEGER")]),
    ]

    result = format_schema(tables)
    assert "Table: regions" in result
    assert "Table: products" in result
    assert "\n\n" in result


def test_execute_query_returns_columns_and_rows(memory_conn):
    columns, rows = execute_query(memory_conn, "SELECT product_id, name FROM products ORDER BY product_id")

    assert columns == ["product_id", "name"]
    assert rows == [(1, "Mug"), (2, "Wallet")]


def test_format_results_aligns_columns():
    columns = ["id", "name"]
    rows = [(1, "Mug"), (2, "Wallet")]

    result = format_results(columns, rows)
    lines = result.splitlines()

    assert lines[0] == "id | name  "
    assert lines[1] == "---+-------"
    assert lines[2] == "1  | Mug   "
    assert lines[3] == "2  | Wallet"


def test_format_results_with_no_rows_returns_header_only():
    result = format_results(["id", "name"], [])
    assert result == "id | name"
