"""Interactive SQL prompt for the class database.

Usage:
    python explore.py           # read-only session (default)
    python explore.py --write   # allow INSERT/UPDATE/DELETE/DDL

At the prompt, type SQL ending with ';' (it can span lines), or a command:
    \\s         list starter queries
    \\s N       run starter query N
    \\t         list tables and their columns
    \\q         quit
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

from queries import print_table

ROOT = Path(__file__).parent

STARTERS = [
    (
        "Average skill ratings by school year",
        """
        SELECT school_year,
               COUNT(*) AS n,
               ROUND(AVG(skill_programming), 2)     AS programming,
               ROUND(AVG(skill_data_stats), 2)      AS data_stats,
               ROUND(AVG(skill_frontend_design), 2) AS frontend,
               ROUND(AVG(skill_business_pitch), 2)  AS pitch
        FROM students
        GROUP BY school_year
        ORDER BY n DESC;
        """,
    ),
    (
        "Students available on weekend afternoons",
        """
        SELECT s.name, s.school_year
        FROM students s
        JOIN student_availability sa ON sa.student_id = s.student_id
        JOIN availability_slots a    ON a.id = sa.slot_id
        WHERE a.name = 'Weekend afternoons'
        ORDER BY s.name;
        """,
    ),
    (
        "Students who use both SQL and JavaScript",
        """
        SELECT s.name
        FROM students s
        JOIN student_tools st ON st.student_id = s.student_id
        JOIN tools t          ON t.id = st.tool_id
        WHERE t.name IN ('SQL', 'JavaScript')
        GROUP BY s.student_id, s.name
        HAVING COUNT(DISTINCT t.name) = 2
        ORDER BY s.name;
        """,
    ),
    (
        "Each student's tools and availability on one line",
        """
        SELECT s.name,
               (SELECT string_agg(t.name, ', ' ORDER BY t.name)
                FROM student_tools st JOIN tools t ON t.id = st.tool_id
                WHERE st.student_id = s.student_id) AS tools,
               (SELECT string_agg(a.name, ', ' ORDER BY a.name)
                FROM student_availability sa JOIN availability_slots a ON a.id = sa.slot_id
                WHERE sa.student_id = s.student_id) AS availability
        FROM students s
        ORDER BY s.name;
        """,
    ),
    (
        "Strongest programmers (skill 4+) and their other skills",
        """
        SELECT name, school_year, skill_programming, skill_data_stats,
               skill_frontend_design, skill_business_pitch
        FROM students
        WHERE skill_programming >= 4
        ORDER BY skill_programming DESC, name;
        """,
    ),
    (
        "Most popular availability slots",
        """
        SELECT a.name AS slot, COUNT(*) AS n_students
        FROM student_availability sa
        JOIN availability_slots a ON a.id = sa.slot_id
        GROUP BY a.name
        ORDER BY n_students DESC;
        """,
    ),
]

TABLES_SQL = """
    SELECT table_name, string_agg(column_name || ' ' || data_type, ', ' ORDER BY ordinal_position) AS columns
    FROM information_schema.columns
    WHERE table_schema = 'public'
    GROUP BY table_name
    ORDER BY table_name;
"""


def execute(conn, sql):
    """Run one statement and print its result; roll back on error."""
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            if cur.description:
                columns = [col.name for col in cur.description]
                rows = cur.fetchall()
                print_table(columns, rows)
                print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
            else:
                print(cur.statusmessage)
        conn.commit()
    except psycopg2.Error as e:
        conn.rollback()
        print(str(e.pgerror or e).strip())


def list_starters():
    for i, (title, _) in enumerate(STARTERS, 1):
        print(f"  {i}. {title}")


def handle_command(conn, line):
    """Handle a backslash command. Returns False to quit."""
    parts = line.split()
    cmd = parts[0]
    if cmd == "\\q":
        return False
    if cmd == "\\t":
        execute(conn, TABLES_SQL)
    elif cmd == "\\s" and len(parts) == 1:
        list_starters()
    elif cmd == "\\s" and parts[1].isdigit() and 1 <= int(parts[1]) <= len(STARTERS):
        title, sql = STARTERS[int(parts[1]) - 1]
        print(f"-- {title}\n{' '.join(sql.split())}\n")
        execute(conn, sql)
    else:
        print("Unknown command. Use \\s, \\s N, \\t or \\q.")
    return True


def main():
    writable = "--write" in sys.argv[1:]
    load_dotenv(ROOT / ".env")
    conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=10)
    conn.set_session(readonly=not writable)

    print(f"Connected ({'read-write' if writable else 'read-only'}). "
          "End SQL with ';'. \\s = starter queries, \\t = tables, \\q = quit.")
    list_starters()

    buffer = []
    try:
        while True:
            try:
                line = input("sql> " if not buffer else "...> ")
            except EOFError:
                break
            stripped = line.strip()
            if not buffer and stripped.startswith("\\"):
                if not handle_command(conn, stripped):
                    break
                continue
            if stripped:
                buffer.append(line)
            if stripped.endswith(";"):
                execute(conn, "\n".join(buffer))
                buffer = []
    except KeyboardInterrupt:
        print()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
