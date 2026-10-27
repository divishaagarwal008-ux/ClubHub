"""
Comprehensive API & Backend Route Test Suite for ClubHub
Tests all CRUD operations, searches, filters, capacity logic, and error handling.
"""

import json
import os
import sqlite3
import sys

# Ensure parent directory is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app

# Temporary test database
TEST_DB_PATH = os.path.join(BASE_DIR, "database", "test_clubhub.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "database", "seed.sql")


def setup_test_db():
    """Initializes a dedicated test database from schema and seed files."""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    with open(SEED_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def run_api_tests():
    print(f"[+] Initializing fresh test database at: {TEST_DB_PATH}")
    setup_test_db()

    app = create_app({"DATABASE": TEST_DB_PATH, "TESTING": True})
    client = app.test_client()

    passed = 0
    total = 0

    def assert_eq(actual, expected, desc):
        nonlocal passed, total
        total += 1
        if actual == expected:
            passed += 1
            print(f"  [PASS] {desc}")
        else:
            print(f"  [FAIL] {desc} (Expected: {expected}, Got: {actual})")

    # =========================================================================
    # 1. System & Dashboard
    # =========================================================================
    print("\n--- 1. Testing System & Dashboard Routes ---")
    res = client.get("/")
    assert_eq(res.status_code, 200, "GET / -> 200 OK")
    data = res.get_json()
    assert_eq(data["status"], "online", "Root status is 'online'")

    res = client.get("/api/dashboard")
    assert_eq(res.status_code, 200, "GET /api/dashboard -> 200 OK")
    dash = res.get_json()
    assert_eq(dash["metrics"]["total_students"], 6, "Dashboard total_students == 6")
    assert_eq(dash["metrics"]["total_clubs"], 5, "Dashboard total_clubs == 5")
    assert_eq(dash["metrics"]["total_events"], 5, "Dashboard total_events == 5")
    assert_eq(len(dash["club_membership_counts"]) > 0, True, "Dashboard has club membership counts")

    # =========================================================================
    # 2. Student CRUD & Search
    # =========================================================================
    print("\n--- 2. Testing Student Routes ---")
    # List all
    res = client.get("/api/students")
    assert_eq(res.status_code, 200, "GET /api/students -> 200 OK")
    assert_eq(res.get_json()["count"], 6, "Initial students count == 6")

    # Search
    res = client.get("/api/students?q=Aarav")
    assert_eq(res.status_code, 200, "GET /api/students?q=Aarav -> 200 OK")
    assert_eq(len(res.get_json()["students"]), 1, "Search returns 1 student for 'Aarav'")

    # Get Single
    res = client.get("/api/students/1")
    assert_eq(res.status_code, 200, "GET /api/students/1 -> 200 OK")
    assert_eq(res.get_json()["student"]["email"], "aarav.sharma@college.edu", "Student 1 email matches")

    # Get Missing
    res = client.get("/api/students/999")
    assert_eq(res.status_code, 404, "GET /api/students/999 -> 404 Not Found")

    # Create Student (Valid)
    new_student = {
        "name": "Pooja Hegde",
        "email": "pooja.h@college.edu",
        "roll_no": "2026CSE099",
        "branch": "CSE",
        "year": 1,
        "phone": "9811223344"
    }
    res = client.post("/api/students", json=new_student)
    assert_eq(res.status_code, 201, "POST /api/students -> 201 Created")
    new_s_id = res.get_json()["student"]["student_id"]

    # Create Student (Duplicate Email)
    res = client.post("/api/students", json=new_student)
    assert_eq(res.status_code, 409, "POST /api/students (duplicate email) -> 409 Conflict")

    # Create Student (Invalid Year > 4)
    bad_student = dict(new_student, email="different@c.edu", roll_no="DIFF123", year=5)
    res = client.post("/api/students", json=bad_student)
    assert_eq(res.status_code, 400, "POST /api/students (year=5) -> 400 Bad Request")

    # Update Student
    res = client.put(f"/api/students/{new_s_id}", json={"name": "Pooja R. Hegde", "branch": "IT"})
    assert_eq(res.status_code, 200, f"PUT /api/students/{new_s_id} -> 200 OK")
    assert_eq(res.get_json()["student"]["name"], "Pooja R. Hegde", "Updated student name matches")

    # List Student's Clubs
    res = client.get("/api/students/1/clubs")
    assert_eq(res.status_code, 200, "GET /api/students/1/clubs -> 200 OK")
    assert_eq(len(res.get_json()["clubs"]) > 0, True, "Student 1 is enrolled in at least 1 club")

    # Delete Student
    res = client.delete(f"/api/students/{new_s_id}")
    assert_eq(res.status_code, 200, f"DELETE /api/students/{new_s_id} -> 200 OK")

    # =========================================================================
    # 3. Club CRUD, Members & Events
    # =========================================================================
    print("\n--- 3. Testing Club Routes ---")
    res = client.get("/api/clubs?category=Technical")
    assert_eq(res.status_code, 200, "GET /api/clubs?category=Technical -> 200 OK")
    assert_eq(all(c["category"] == "Technical" for c in res.get_json()["clubs"]), True, "All filtered clubs are Technical")

    # Get Single Club with Advisors
    res = client.get("/api/clubs/2")
    assert_eq(res.status_code, 200, "GET /api/clubs/2 -> 200 OK")
    c_data = res.get_json()["club"]
    assert_eq(c_data["name"], "RoboTech Club", "Club 2 is RoboTech Club")
    assert_eq(len(c_data["advisors"]) >= 2, True, "RoboTech has at least 2 co-advisors")

    # Create Club (Valid)
    new_club = {
        "name": "Astronomy Guild",
        "category": "Academic",
        "description": "Stargazing and space sciences.",
        "room_no": "Obs-01",
        "status": "Active"
    }
    res = client.post("/api/clubs", json=new_club)
    assert_eq(res.status_code, 201, "POST /api/clubs -> 201 Created")
    new_c_id = res.get_json()["club"]["club_id"]

    # Create Club (Duplicate Name)
    res = client.post("/api/clubs", json=new_club)
    assert_eq(res.status_code, 409, "POST /api/clubs (duplicate name) -> 409 Conflict")

    # Create Club (Invalid Category)
    res = client.post("/api/clubs", json=dict(new_club, name="Other", category="NotACat"))
    assert_eq(res.status_code, 400, "POST /api/clubs (invalid category) -> 400 Bad Request")

    # Club Members
    res = client.get("/api/clubs/1/members")
    assert_eq(res.status_code, 200, "GET /api/clubs/1/members -> 200 OK")
    assert_eq(len(res.get_json()["members"]) >= 3, True, "Club 1 has at least 3 members")

    # Club Events
    res = client.get("/api/clubs/1/events")
    assert_eq(res.status_code, 200, "GET /api/clubs/1/events -> 200 OK")
    assert_eq(len(res.get_json()["events"]) >= 2, True, "Club 1 has at least 2 events")

    # Delete Club
    res = client.delete(f"/api/clubs/{new_c_id}")
    assert_eq(res.status_code, 200, f"DELETE /api/clubs/{new_c_id} -> 200 OK")

    # =========================================================================
    # 4. Faculty Advisor CRUD & Assignment
    # =========================================================================
    print("\n--- 4. Testing Faculty Advisor Routes ---")
    res = client.get("/api/advisors")
    assert_eq(res.status_code, 200, "GET /api/advisors -> 200 OK")
    assert_eq(res.get_json()["count"], 4, "Initial faculty advisors count == 4")

    # Create Advisor (Valid)
    new_adv = {
        "name": "Dr. Kavita Krishnan",
        "email": "kavita.k@college.edu",
        "department": "Mathematics",
        "phone": "9876500000"
    }
    res = client.post("/api/advisors", json=new_adv)
    assert_eq(res.status_code, 201, "POST /api/advisors -> 201 Created")
    new_adv_id = res.get_json()["advisor"]["advisor_id"]

    # Assign Advisor to Club (M:N)
    res = client.post("/api/club-advisors", json={"club_id": 1, "advisor_id": new_adv_id})
    assert_eq(res.status_code, 201, "POST /api/club-advisors -> 201 Created")

    # Assign Duplicate
    res = client.post("/api/club-advisors", json={"club_id": 1, "advisor_id": new_adv_id})
    assert_eq(res.status_code, 409, "POST /api/club-advisors (duplicate) -> 409 Conflict")

    # Remove Assignment
    res = client.delete(f"/api/club-advisors/1/{new_adv_id}")
    assert_eq(res.status_code, 200, "DELETE /api/club-advisors -> 200 OK")

    # Delete Advisor (Leaves clubs intact)
    res = client.delete(f"/api/advisors/{new_adv_id}")
    assert_eq(res.status_code, 200, f"DELETE /api/advisors/{new_adv_id} -> 200 OK")

    # =========================================================================
    # 5. Membership CRUD
    # =========================================================================
    print("\n--- 5. Testing Membership Routes ---")
    res = client.get("/api/memberships?club_id=1")
    assert_eq(res.status_code, 200, "GET /api/memberships?club_id=1 -> 200 OK")

    # Create Membership (Valid)
    res = client.post("/api/memberships", json={"student_id": 5, "club_id": 1, "role": "Member"})
    assert_eq(res.status_code, 201, "POST /api/memberships (student 5 to club 1) -> 201 Created")

    # Duplicate Membership
    res = client.post("/api/memberships", json={"student_id": 5, "club_id": 1, "role": "Member"})
    assert_eq(res.status_code, 409, "POST /api/memberships (duplicate) -> 409 Conflict")

    # Update Membership Role
    res = client.put("/api/memberships/5/1", json={"role": "Treasurer"})
    assert_eq(res.status_code, 200, "PUT /api/memberships/5/1 -> 200 OK")
    assert_eq(res.get_json()["membership"]["role"], "Treasurer", "Role updated to Treasurer")

    # Delete Membership
    res = client.delete("/api/memberships/5/1")
    assert_eq(res.status_code, 200, "DELETE /api/memberships/5/1 -> 200 OK")

    # =========================================================================
    # 6. Event CRUD
    # =========================================================================
    print("\n--- 6. Testing Event Routes ---")
    res = client.get("/api/events")
    assert_eq(res.status_code, 200, "GET /api/events -> 200 OK")

    # Create Event (Valid)
    new_evt = {
        "club_id": 1,
        "title": "Algorithm Arena",
        "event_date": "2026-12-10 10:00:00",
        "venue": "Lab 301",
        "capacity": 50,
        "status": "Upcoming"
    }
    res = client.post("/api/events", json=new_evt)
    assert_eq(res.status_code, 201, "POST /api/events -> 201 Created")
    new_evt_id = res.get_json()["event"]["event_id"]

    # Create Event with Zero Capacity
    res = client.post("/api/events", json=dict(new_evt, capacity=0))
    assert_eq(res.status_code, 400, "POST /api/events (capacity=0) -> 400 Bad Request")

    # View Event Details with Available Seats
    res = client.get(f"/api/events/{new_evt_id}")
    assert_eq(res.status_code, 200, f"GET /api/events/{new_evt_id} -> 200 OK")
    assert_eq(res.get_json()["event"]["available_seats"], 50, "Initially 50 available seats")

    # =========================================================================
    # 7. Event Registration & Atomic Capacity Enforcement
    # =========================================================================
    print("\n--- 7. Testing Event Registration & Capacity Logic ---")
    # Create small test event with capacity = 2
    res = client.post("/api/events", json={
        "club_id": 1,
        "title": "VIP Workshop",
        "event_date": "2026-12-12 15:00:00",
        "venue": "Boardroom",
        "capacity": 2,
        "status": "Upcoming"
    })
    vip_evt_id = res.get_json()["event"]["event_id"]

    # Register Student 1 (Capacity 1/2)
    res = client.post("/api/registrations", json={"student_id": 1, "event_id": vip_evt_id})
    assert_eq(res.status_code, 201, "Register Student 1 for VIP event -> 201 Created")

    # Duplicate Registration Check
    res = client.post("/api/registrations", json={"student_id": 1, "event_id": vip_evt_id})
    assert_eq(res.status_code, 409, "Register duplicate Student 1 -> 409 Conflict")

    # Register Student 2 (Capacity 2/2 - Full)
    res = client.post("/api/registrations", json={"student_id": 2, "event_id": vip_evt_id})
    assert_eq(res.status_code, 201, "Register Student 2 for VIP event -> 201 Created")

    # Attempt Register Student 3 (Exceeds Capacity -> Must Fail)
    res = client.post("/api/registrations", json={"student_id": 3, "event_id": vip_evt_id})
    assert_eq(res.status_code, 409, "Register Student 3 (Capacity Full) -> 409 Conflict")
    assert_eq("full capacity" in res.get_json()["error"].lower(), True, "Error mentions 'full capacity'")

    # Cancel Student 2 Registration (Freeing up 1 seat)
    res = client.put(f"/api/registrations/2/{vip_evt_id}", json={"attendance_status": "Cancelled"})
    assert_eq(res.status_code, 200, "Student 2 cancels registration -> 200 OK")

    # Now Student 3 should be able to register successfully!
    res = client.post("/api/registrations", json={"student_id": 3, "event_id": vip_evt_id})
    assert_eq(res.status_code, 201, "Student 3 registers after cancellation -> 201 Created")

    # Student 2 tries to reactivate cancelled registration when full -> Must Fail
    res = client.put(f"/api/registrations/2/{vip_evt_id}", json={"attendance_status": "Registered"})
    assert_eq(res.status_code, 409, "Reactivating cancelled registration when full -> 409 Conflict")

    # View Event Registration List
    res = client.get(f"/api/events/{vip_evt_id}/registrations")
    assert_eq(res.status_code, 200, "GET /api/events/<id>/registrations -> 200 OK")
    reg_list = res.get_json()
    assert_eq(reg_list["active_registrations"], 2, "VIP active registrations == 2")
    assert_eq(len(reg_list["registrations"]), 3, "Total registration history (including Cancelled) == 3")

    # Clean up VIP event (cascades to registrations)
    res = client.delete(f"/api/events/{vip_evt_id}")
    assert_eq(res.status_code, 200, "DELETE VIP event -> 200 OK")

    # Clean up Algorithm Arena event
    client.delete(f"/api/events/{new_evt_id}")

    # Remove temporary test db file
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    print(f"\n==========================================")
    print(f"RESULTS: {passed} / {total} tests passed.")
    print(f"==========================================")
    if passed == total:
        print("[SUCCESS] All API endpoints and business logic verified successfully!")
    else:
        print("[ERROR] Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    run_api_tests()

