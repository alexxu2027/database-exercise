"""Create the schema in Postgres and load data/class_dataset.csv into it.

Reads DATABASE_URL from .env. Runs in a single transaction, so a failure
leaves the database untouched.
"""
import csv
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).parent
CSV_PATH = ROOT / "data" / "class_dataset.csv"
SCHEMA_PATH = ROOT / "schema.sql"
TABLES = ["students", "tools", "student_tools", "availability_slots", "student_availability"]


def split_multi(value):
    """Split a semicolon-joined cell into a list of trimmed, non-empty values."""
    return [part.strip() for part in value.split(";") if part.strip()]


def get_or_create(cur, table, name, cache):
    if name not in cache:
        cur.execute(
            f"INSERT INTO {table} (name) VALUES (%s) RETURNING id",
            (name,),
        )
        cache[name] = cur.fetchone()[0]
    return cache[name]


def main():
    load_dotenv(ROOT / ".env")
    conn = psycopg2.connect(os.environ["DATABASE_URL"], connect_timeout=10)
    try:
        with conn, conn.cursor() as cur:
            # Structure first: tables in dependency order (parents before bridges).
            cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))

            tool_ids, slot_ids = {}, {}
            with CSV_PATH.open(newline="", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    cur.execute(
                        """
                        INSERT INTO students (
                            netid, name, school_year, intro_programming,
                            skill_programming, skill_data_stats,
                            skill_frontend_design, skill_business_pitch,
                            working_style, interests, semester_goal, submitted_at
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING student_id
                        """,
                        (
                            row["netid"], row["name"], row["school_year"],
                            row["intro_programming"],
                            int(row["skill_programming"]), int(row["skill_data_stats"]),
                            int(row["skill_frontend_design"]), int(row["skill_business_pitch"]),
                            row["working_style"], row["interests"], row["semester_goal"],
                            row["submitted_at"],
                        ),
                    )
                    student_id = cur.fetchone()[0]

                    for tool in split_multi(row["tools"]):
                        cur.execute(
                            "INSERT INTO student_tools (student_id, tool_id) VALUES (%s, %s)",
                            (student_id, get_or_create(cur, "tools", tool, tool_ids)),
                        )
                    for slot in split_multi(row["availability"]):
                        cur.execute(
                            "INSERT INTO student_availability (student_id, slot_id) VALUES (%s, %s)",
                            (student_id, get_or_create(cur, "availability_slots", slot, slot_ids)),
                        )

            for table in TABLES:
                cur.execute(f"SELECT count(*) FROM {table}")
                print(f"{table:22} {cur.fetchone()[0]}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
