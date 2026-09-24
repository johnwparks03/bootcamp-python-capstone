import re

BLOCKED_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
)

ALLOWED_LEADING_KEYWORDS = ("SELECT", "WITH")


class UnsafeSqlError(ValueError):
    pass


def validate_select_only(sql: str) -> str:
    cleaned = sql.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    if not cleaned:
        raise UnsafeSqlError("SQL statement is empty.")

    if ";" in cleaned:
        raise UnsafeSqlError("Multiple SQL statements are not allowed.")

    first_word_match = re.match(r"[A-Za-z]+", cleaned)
    first_word = first_word_match.group(0).upper() if first_word_match else ""
    if first_word not in ALLOWED_LEADING_KEYWORDS:
        raise UnsafeSqlError(
            f"Only SELECT (or WITH ... SELECT) statements are allowed, got: {first_word!r}"
        )

    for keyword in BLOCKED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", cleaned, re.IGNORECASE):
            raise UnsafeSqlError(f"Disallowed keyword detected in SQL: {keyword}")

    return cleaned
