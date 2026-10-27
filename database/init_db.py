"""
ClubHub Database Initialization Script
Executes schema.sql and seed.sql to create and populate clubhub.db.
"""

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clubhub.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "seed.sql")


def init_database():
    print(f"[+] Initializing database at: {DB_PATH}")

    # Remove existing DB file for a clean rebuild if desired
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # 1. Apply Schema
    print(f"[+] Applying schema from: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cursor.executescript(schema_sql)
    print("    -> Schema created successfully.")

    # 2. Apply Seed Data
    print(f"[+] Seeding data from: {SEED_PATH}")
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        seed_sql = f.read()
    cursor.executescript(seed_sql)
    print("    -> Seed data inserted successfully.")

    conn.commit()

    # 3. Verification & Summary
    print("\n[+] Verification & Row Counts:")
    tables = [
        "Student",
        "Club",
        "Faculty_Advisor",
        "Club_Advisor",
        "Membership",
        "Event",
        "Event_Registration"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"    - Table '{table}': {count} records")

    # Check foreign keys pragma
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]
    print(f"\n[+] Foreign key enforcement enabled: {'YES (1)' if fk_status == 1 else 'NO (0)'}")

    conn.close()
    print("[+] Database initialization complete!")


if __name__ == "__main__":
    init_database()

