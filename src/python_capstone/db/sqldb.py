import sqlite3
from python_capstone.config import settings
from dataclasses import dataclass

@dataclass
class ColumnInfo:
    name: str
    type: str

@dataclass
class TableInfo:
    name: str
    columns: list[ColumnInfo]


def open_connection() -> sqlite3.Connection:
    return sqlite3.connect(settings.sqlite_db_path)

def introspect_schema(dbconn: sqlite3.Connection) -> list[TableInfo]:
    tables: list[TableInfo] = []
    select_tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
    
    rows = dbconn.execute(select_tables_query).fetchall()
    table_names = [row[0] for row in rows]

    for table in table_names:
        get_columns_query = f"PRAGMA table_info({table})"
        table_columns = dbconn.execute(get_columns_query).fetchall()

        columns: list[ColumnInfo] = []
        for col in table_columns:
            column_info = ColumnInfo(name=col[1], type=col[2])
            columns.append(column_info)

        table_info = TableInfo(name=table, columns=columns)

        tables.append(table_info)

    return tables

def format_schema(tables: list[TableInfo]) -> str:
    table_blocks: list[str] = []

    for table in tables:
        lines = [f"Table: {table.name}"]
        for column in table.columns:
            lines.append(f"  - {column.name}: {column.type}")
        table_blocks.append("\n".join(lines))

    return "\n\n".join(table_blocks)


def execute_query(dbconn: sqlite3.Connection, sql: str) -> tuple[list[str], list[tuple]]:
    cursor = dbconn.execute(sql)
    column_names = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    return column_names, rows


def format_results(columns: list[str], rows: list[tuple]) -> str:
    if not rows:
        return " | ".join(columns)

    str_rows = [[str(value) for value in row] for row in rows]

    widths = [
        max(len(columns[i]), max(len(row[i]) for row in str_rows))
        for i in range(len(columns))
    ]

    header = " | ".join(columns[i].ljust(widths[i]) for i in range(len(columns)))
    separator = "-+-".join("-" * widths[i] for i in range(len(columns)))
    body_lines = [
        " | ".join(row[i].ljust(widths[i]) for i in range(len(columns)))
        for row in str_rows
    ]

    return "\n".join([header, separator, *body_lines])

