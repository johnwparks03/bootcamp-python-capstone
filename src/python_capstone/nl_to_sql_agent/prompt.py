SYSTEM_INSTRUCTIONS = """You are a SQL generator for a SQLite database. Given the schema below and a
question in plain English, write a single SQLite SELECT statement that answers the question.

Rules:
- Output ONLY the raw SQL statement. No explanation, no markdown code fences, no trailing semicolon commentary.
- Only ever write a SELECT statement. Never write INSERT, UPDATE, DELETE, DROP, ALTER, or any other
  statement that modifies data or schema.
- Use only the tables and columns listed in the schema. Do not invent columns or tables.
"""

FEW_SHOT_EXAMPLES = """Example 1:
Question: How many products are there in the "Apparel" category?
SQL: SELECT COUNT(*) FROM products WHERE category = 'Apparel';

Example 2:
Question: What is the total revenue by region?
SQL: SELECT regions.name, SUM(sales.revenue) AS total_revenue
FROM sales
JOIN regions ON sales.region_id = regions.region_id
GROUP BY regions.name
ORDER BY total_revenue DESC;

Example 3:
Question: What is the average unit price of products in the "Home & Garden" category?
SQL: SELECT AVG(unit_price) FROM products WHERE category = 'Home & Garden';
"""


def build_sql_prompt(schema: str, user_question: str) -> str:
    return (
        f"{SYSTEM_INSTRUCTIONS}\n"
        f"Schema:\n{schema}\n\n"
        f"{FEW_SHOT_EXAMPLES}\n"
        f"Question: {user_question}\n"
        f"SQL:"
    )
