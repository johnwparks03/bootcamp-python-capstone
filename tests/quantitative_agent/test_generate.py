from python_capstone.quantitative_agent.generate import strip_sql_fences


def test_strips_sql_language_fence():
    text = "```sql\nSELECT * FROM products\n```"
    assert strip_sql_fences(text) == "SELECT * FROM products"


def test_strips_plain_fence():
    text = "```\nSELECT * FROM products\n```"
    assert strip_sql_fences(text) == "SELECT * FROM products"


def test_leaves_unfenced_text_unchanged():
    text = "SELECT * FROM products"
    assert strip_sql_fences(text) == text


def test_strips_surrounding_whitespace():
    text = "  \n  SELECT * FROM products  \n  "
    assert strip_sql_fences(text) == "SELECT * FROM products"


def test_fence_case_insensitive():
    text = "```SQL\nSELECT * FROM products\n```"
    assert strip_sql_fences(text) == "SELECT * FROM products"
