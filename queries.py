"""Connect to Postgres at DATABASE_URL and run the deploy lab's base queries."""
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).parent

QUERIES = {
    "Student count (must match the CSV's row count)": """
        SELECT count(*) FROM students
    """,
    "First five students": """
        SELECT name, school_year FROM students LIMIT 5
    """,
    "Students per tool": """
        SELECT t.name, COUNT(*) AS n_students
        FROM student_tools st
        JOIN tools t ON st.tool_id = t.id
        GROUP BY t.name
        ORDER BY n_students DESC
    """,
}


def run(cur, sql):
    """Run a query and return (column names, rows)."""
    cur.execute(sql)
    return [col.name for col in cur.description], cur.fetchall()


def print_table(columns, rows):
    widths = [
        max(len(str(v)) for v in [col, *(row[i] for row in rows)])
        for i, col in enumerate(columns)
    ]
    print("  ".join(col.ljust(w) for col, w in zip(columns, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(row, widths)))


def main():
    load_dotenv(ROOT / ".env")
    conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=10)
    try:
        with conn.cursor() as cur:
            for title, sql in QUERIES.items():
                print(f"\n== {title}")
                print_table(*run(cur, sql))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
