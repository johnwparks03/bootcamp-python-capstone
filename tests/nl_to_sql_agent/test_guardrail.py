import pytest

from python_capstone.quantitative_agent.guardrail import UnsafeSqlError, validate_select_only


def test_allows_simple_select():
    sql = "SELECT * FROM products"
    assert validate_select_only(sql) == sql


def test_allows_select_case_insensitive():
    sql = "select * from products"
    assert validate_select_only(sql) == sql


def test_strips_trailing_semicolon():
    assert validate_select_only("SELECT * FROM products;") == "SELECT * FROM products"


def test_allows_cte_with_select():
    sql = (
        "WITH regional_totals AS (SELECT region_id, SUM(revenue) AS total FROM sales "
        "GROUP BY region_id) SELECT * FROM regional_totals"
    )
    assert validate_select_only(sql) == sql


def test_rejects_chained_statements():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("SELECT 1; DROP TABLE sales;")


def test_rejects_non_select_statement():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("DELETE FROM sales")


def test_rejects_insert():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("INSERT INTO sales (sale_id) VALUES (1)")


def test_rejects_pragma():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("PRAGMA table_info(sales)")


def test_rejects_empty_string():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("")


def test_rejects_only_whitespace():
    with pytest.raises(UnsafeSqlError):
        validate_select_only("   ")


def test_does_not_false_positive_on_column_named_like_keyword():
    sql = "SELECT update_date FROM sales"
    assert validate_select_only(sql) == sql


def test_does_not_false_positive_on_table_named_like_keyword():
    sql = "SELECT * FROM deletion_log"
    assert validate_select_only(sql) == sql
