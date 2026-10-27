"""
Comprehensive Verification and Constraint Integrity Test Suite for ClubHub Database
Tests:
1. Foreign key enforcement (invalid references fail)
2. UNIQUE constraints (duplicate student email/roll_no, club name, faculty email)
3. CHECK constraints (year, capacity, statuses, categories, roles, phone length)
4. Composite Primary Key integrity (duplicate junction records fail)
5. Cascade Deletion & Isolation (Student, Club, Event, and Faculty Advisor deletion behaviors)
6. Capacity Behavior (Confirms that SQLite schema alone does not enforce registration limit,
   proving application logic is responsible for capacity ceiling)
"""

import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "clubhub.db")


def run_tests():
    print(f"[+] Connecting to SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    passed = 0
    total = 0

    def assert_fails(sql_stmt, params, expected_desc):
        nonlocal passed, total
        total += 1
        try:
            cursor.execute(sql_stmt, params)
            conn.commit()
            print(f"  [FAIL] {expected_desc} - Query succeeded unexpectedly!")
        except sqlite3.IntegrityError as e:
            passed += 1
            print(f"  [PASS] {expected_desc} -> Caught IntegrityError: {e}")
        except Exception as e:
            print(f"  [FAIL] {expected_desc} -> Unexpected error: {e}")

    # =========================================================================
    # 1. Foreign Key Enforcement
    # =========================================================================
    print("\n--- 1. Testing Foreign Key Enforcement ---")
    assert_fails(
        "INSERT INTO Membership (student_id, club_id, role) VALUES (?, ?, ?);",
        (9999, 1, "Member"),
        "Inserting Membership with non-existent student_id (9999)"
    )
    assert_fails(
        "INSERT INTO Event (club_id, title, event_date, venue, capacity) VALUES (?, ?, ?, ?, ?);",
        (9999, "Fake Event", "2026-11-01", "Hall", 50),
        "Inserting Event with non-existent club_id (9999)"
    )
    assert_fails(
        "INSERT INTO Club_Advisor (club_id, advisor_id) VALUES (?, ?);",
        (1, 9999),
        "Inserting Club_Advisor with non-existent advisor_id (9999)"
    )

    # =========================================================================
    # 2. UNIQUE Constraints
    # =========================================================================
    print("\n--- 2. Testing UNIQUE Constraints ---")
    assert_fails(
        "INSERT INTO Student (name, email, roll_no, branch, year) VALUES (?, ?, ?, ?, ?);",
        ("Duplicate Student", "aarav.sharma@college.edu", "2026NEW001", "CSE", 1),
        "Inserting duplicate email 'aarav.sharma@college.edu'"
    )
    assert_fails(
        "INSERT INTO Student (name, email, roll_no, branch, year) VALUES (?, ?, ?, ?, ?);",
        ("Duplicate Roll", "unique.email@college.edu", "2024CSE001", "CSE", 1),
        "Inserting duplicate roll_no '2024CSE001'"
    )
    assert_fails(
        "INSERT INTO Club (name, category) VALUES (?, ?);",
        ("CodeForge", "Technical"),
        "Inserting duplicate club name 'CodeForge'"
    )
    assert_fails(
        "INSERT INTO Faculty_Advisor (name, email, department) VALUES (?, ?, ?);",
        ("Duplicate Advisor", "rajesh.rao@college.edu", "CSE"),
        "Inserting duplicate faculty advisor email 'rajesh.rao@college.edu'"
    )

    # =========================================================================
    # 3. CHECK Constraints
    # =========================================================================
    print("\n--- 3. Testing CHECK Constraints ---")
    assert_fails(
        "INSERT INTO Student (name, email, roll_no, branch, year) VALUES (?, ?, ?, ?, ?);",
        ("Invalid Year", "year5@college.edu", "2026CHK01", "CSE", 5),
        "Inserting Student with invalid year (5 > 4)"
    )
    assert_fails(
        "INSERT INTO Student (name, email, roll_no, branch, year, phone) VALUES (?, ?, ?, ?, ?, ?);",
        ("Short Phone", "phone_short@college.edu", "2026CHK02", "CSE", 1, "12345"),
        "Inserting Student with short phone number (< 10 digits)"
    )
    assert_fails(
        "INSERT INTO Club (name, category) VALUES (?, ?);",
        ("Invalid Cat Club", "NonExistentCategory"),
        "Inserting Club with invalid category"
    )
    assert_fails(
        "INSERT INTO Club (name, category, status) VALUES (?, ?, ?);",
        ("Bad Status Club", "Technical", "Pending"),
        "Inserting Club with invalid status"
    )
    assert_fails(
        "INSERT INTO Membership (student_id, club_id, role) VALUES (?, ?, ?);",
        (1, 4, "Grandmaster"),
        "Inserting Membership with invalid role"
    )
    assert_fails(
        "INSERT INTO Event (club_id, title, event_date, venue, capacity) VALUES (?, ?, ?, ?, ?);",
        (1, "Zero Cap Event", "2026-11-01", "Lab", 0),
        "Inserting Event with zero capacity"
    )
    assert_fails(
        "INSERT INTO Event (club_id, title, event_date, venue, capacity, status) VALUES (?, ?, ?, ?, ?, ?);",
        (1, "Bad Status Event", "2026-11-01", "Lab", 50, "InvalidStatus"),
        "Inserting Event with invalid status string"
    )
    assert_fails(
        "INSERT INTO Event_Registration (student_id, event_id, attendance_status) VALUES (?, ?, ?);",
        (5, 1, "UnknownStatus"),
        "Inserting Event_Registration with invalid attendance_status"
    )

    # =========================================================================
    # 4. Composite Primary Key Constraints
    # =========================================================================
    print("\n--- 4. Testing Composite Primary Key Constraints ---")
    assert_fails(
        "INSERT INTO Membership (student_id, club_id, role) VALUES (?, ?, ?);",
        (1, 1, "Core Member"),
        "Inserting duplicate Membership for student_id=1, club_id=1"
    )
    assert_fails(
        "INSERT INTO Event_Registration (student_id, event_id) VALUES (?, ?);",
        (1, 1),
        "Inserting duplicate Event_Registration for student_id=1, event_id=1"
    )
    assert_fails(
        "INSERT INTO Club_Advisor (club_id, advisor_id) VALUES (?, ?);",
        (1, 1),
        "Inserting duplicate Club_Advisor for club_id=1, advisor_id=1"
    )

    # =========================================================================
    # 5. Cascade Deletions & Isolation Behaviors
    # =========================================================================
    print("\n--- 5. Testing Cascade Deletions & Isolation Behaviors ---")
    cursor.execute("SAVEPOINT test_cascades;")

    # 5A. Student Deletion Cascade
    total += 1
    cursor.execute("INSERT INTO Student (student_id, name, email, roll_no, branch, year) VALUES (901, 'Temp Student', 'temp.s@college.edu', '901TMP', 'CSE', 1);")
    cursor.execute("INSERT INTO Membership (student_id, club_id) VALUES (901, 1);")
    cursor.execute("INSERT INTO Event_Registration (student_id, event_id) VALUES (901, 1);")
    cursor.execute("DELETE FROM Student WHERE student_id = 901;")
    mem_c = cursor.execute("SELECT COUNT(*) FROM Membership WHERE student_id = 901;").fetchone()[0]
    reg_c = cursor.execute("SELECT COUNT(*) FROM Event_Registration WHERE student_id = 901;").fetchone()[0]
    if mem_c == 0 and reg_c == 0:
        passed += 1
        print("  [PASS] Student deletion correctly cascaded to Membership and Event_Registration.")
    else:
        print(f"  [FAIL] Student cascade failed: mem={mem_c}, reg={reg_c}")

    # 5B. Club Deletion Cascade (Cascades to Event, Membership, Club_Advisor, and transitively Event_Registration)
    total += 1
    cursor.execute("INSERT INTO Club (club_id, name, category) VALUES (902, 'Temp Club', 'Technical');")
    cursor.execute("INSERT INTO Membership (student_id, club_id) VALUES (1, 902);")
    cursor.execute("INSERT INTO Club_Advisor (club_id, advisor_id) VALUES (902, 1);")
    cursor.execute("INSERT INTO Event (event_id, club_id, title, event_date, venue, capacity) VALUES (902, 902, 'Temp Evt', '2026-12-01', 'Hall', 50);")
    cursor.execute("INSERT INTO Event_Registration (student_id, event_id) VALUES (1, 902);")

    cursor.execute("DELETE FROM Club WHERE club_id = 902;")
    c_mem = cursor.execute("SELECT COUNT(*) FROM Membership WHERE club_id = 902;").fetchone()[0]
    c_adv = cursor.execute("SELECT COUNT(*) FROM Club_Advisor WHERE club_id = 902;").fetchone()[0]
    c_evt = cursor.execute("SELECT COUNT(*) FROM Event WHERE club_id = 902;").fetchone()[0]
    c_reg = cursor.execute("SELECT COUNT(*) FROM Event_Registration WHERE event_id = 902;").fetchone()[0]

    if c_mem == 0 and c_adv == 0 and c_evt == 0 and c_reg == 0:
        passed += 1
        print("  [PASS] Club deletion correctly cascaded to Event, Membership, Club_Advisor, and transitively Event_Registration.")
    else:
        print(f"  [FAIL] Club cascade failed: mem={c_mem}, adv={c_adv}, evt={c_evt}, reg={c_reg}")

    # 5C. Faculty Advisor Deletion Isolation (Deleting Advisor deletes Club_Advisor, but Club remains)
    total += 1
    cursor.execute("INSERT INTO Faculty_Advisor (advisor_id, name, email, department) VALUES (903, 'Temp Prof', 'temp.prof@college.edu', 'CSE');")
    cursor.execute("INSERT INTO Club (club_id, name, category) VALUES (903, 'Club Survived', 'Literary');")
    cursor.execute("INSERT INTO Club_Advisor (club_id, advisor_id) VALUES (903, 903);")

    cursor.execute("DELETE FROM Faculty_Advisor WHERE advisor_id = 903;")
    ca_count = cursor.execute("SELECT COUNT(*) FROM Club_Advisor WHERE advisor_id = 903;").fetchone()[0]
    club_exists = cursor.execute("SELECT COUNT(*) FROM Club WHERE club_id = 903;").fetchone()[0]

    if ca_count == 0 and club_exists == 1:
        passed += 1
        print("  [PASS] Faculty_Advisor deletion removed Club_Advisor mapping while preserving Club intact.")
    else:
        print(f"  [FAIL] Faculty deletion isolation failed: ca_count={ca_count}, club_exists={club_exists}")

    cursor.execute("ROLLBACK TO test_cascades;")

    # =========================================================================
    # 6. Capacity Enforcement Verification (Database vs Application)
    # =========================================================================
    print("\n--- 6. Verifying Event Capacity Behavior ---")
    total += 1
    cursor.execute("SAVEPOINT test_cap;")
    # Create event with capacity 1
    cursor.execute("INSERT INTO Event (event_id, club_id, title, event_date, venue, capacity) VALUES (905, 1, 'Micro Event', '2026-11-30', 'Room 1', 1);")
    cursor.execute("INSERT INTO Event_Registration (student_id, event_id) VALUES (1, 905);")
    
    # SQLite schema allows second insert because capacity check requires application logic or trigger
    cursor.execute("INSERT INTO Event_Registration (student_id, event_id) VALUES (2, 905);")
    reg_count = cursor.execute("SELECT COUNT(*) FROM Event_Registration WHERE event_id = 905;").fetchone()[0]
    
    if reg_count == 2:
        passed += 1
        print("  [PASS] Confirmed: Database schema does NOT block over-capacity registrations.")
        print("         -> Proves event capacity ceiling MUST be enforced by Application Logic in Flask.")
    else:
        print("  [FAIL] Unexpected capacity behavior.")
    cursor.execute("ROLLBACK TO test_cap;")

    conn.close()

    print(f"\n==========================================")
    print(f"RESULTS: {passed} / {total} tests passed.")
    print(f"==========================================")
    if passed == total:
        print("[SUCCESS] All schema constraints, cascade behaviors, and edge cases verified!")
    else:
        print("[ERROR] Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()
