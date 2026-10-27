"""
End-to-End User Flow Verification Suite for ClubHub Frontend Integration
Tests complete user workflows mimicking browser actions and API data exchanges.
"""

import json
import os
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app

TEST_DB_PATH = os.path.join(BASE_DIR, "database", "test_flows.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "database", "seed.sql")


def setup_fresh_db():
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


def run_flow_tests():
    print(f"[+] Initializing user flow test database at: {TEST_DB_PATH}")
    setup_fresh_db()

    app = create_app({"DATABASE": TEST_DB_PATH, "TESTING": True})
    client = app.test_client()

    passed = 0
    total = 0

    def assert_test(condition, desc):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {desc}")
        else:
            print(f"  [FAIL] {desc}")

    # =========================================================================
    # FLOW 1: Complete Student Journey (Onboarding -> Club Join -> Event -> Attendance)
    # =========================================================================
    print("\n--- User Flow 1: Student Onboarding & Event Attendance Lifecycle ---")
    
    # 1. Add student
    student_payload = {
        "name": "Manasvi Joshi",
        "email": "manasvi.j@college.edu",
        "roll_no": "2026ECE088",
        "branch": "ECE",
        "year": 1,
        "phone": "9876543299"
    }
    r = client.post("/api/students", json=student_payload)
    assert_test(r.status_code == 201, "Step 1: Student successfully registered via Add Student form")
    s_id = r.get_json()["student"]["student_id"]

    # 2. Enroll student in CodeForge (Club 1) as Member
    r = client.post("/api/memberships", json={"student_id": s_id, "club_id": 1, "role": "Member"})
    assert_test(r.status_code == 201, "Step 2: Student enrolled into CodeForge society")

    # 3. Promote student to Core Member
    r = client.put(f"/api/memberships/{s_id}/1", json={"role": "Core Member"})
    assert_test(r.status_code == 200 and r.get_json()["membership"]["role"] == "Core Member", "Step 3: Student role updated to Core Member")

    # 4. Student checks their enrolled clubs
    r = client.get(f"/api/students/{s_id}/clubs")
    assert_test(r.status_code == 200 and len(r.get_json()["clubs"]) == 1, "Step 4: Student profile lists CodeForge club membership")

    # 5. Register for Event 1 (HackForge 2026)
    r = client.post("/api/registrations", json={"student_id": s_id, "event_id": 1, "attendance_status": "Registered"})
    assert_test(r.status_code == 201, "Step 5: Student registered for HackForge 2026")

    # 6. Event Organizer marks attendance as 'Attended'
    r = client.put(f"/api/registrations/{s_id}/1", json={"attendance_status": "Attended"})
    assert_test(r.status_code == 200 and r.get_json()["registration"]["attendance_status"] == "Attended", "Step 6: Attendance status updated to 'Attended'")

    # =========================================================================
    # FLOW 2: Club Creation & Faculty Mentorship Assignment
    # =========================================================================
    print("\n--- User Flow 2: Club Creation & Faculty Mentorship Assignment ---")

    # 1. Create new club
    club_payload = {
        "name": "Design & Innovation Cell",
        "category": "Technical",
        "description": "UI/UX, CAD and product prototyping hub.",
        "room_no": "Design-Lab",
        "status": "Active"
    }
    r = client.post("/api/clubs", json=club_payload)
    assert_test(r.status_code == 201, "Step 1: New Club 'Design & Innovation Cell' created")
    c_id = r.get_json()["club"]["club_id"]

    # 2. Add Faculty Advisor
    advisor_payload = {
        "name": "Dr. Sunita Bansal",
        "email": "sunita.bansal@college.edu",
        "department": "Design & Mechanical",
        "phone": "9812345678"
    }
    r = client.post("/api/advisors", json=advisor_payload)
    assert_test(r.status_code == 201, "Step 2: Faculty Advisor Dr. Sunita registered")
    a_id = r.get_json()["advisor"]["advisor_id"]

    # 3. Assign Advisor to Club (M:N)
    r = client.post("/api/club-advisors", json={"club_id": c_id, "advisor_id": a_id})
    assert_test(r.status_code == 201, "Step 3: Dr. Sunita assigned as mentor to Design & Innovation Cell")

    # 4. Schedule Event under new club
    event_payload = {
        "club_id": c_id,
        "title": "Design Sprint 1.0",
        "event_date": "2026-12-05 11:00:00",
        "venue": "Design-Lab",
        "capacity": 30,
        "status": "Upcoming"
    }
    r = client.post("/api/events", json=event_payload)
    assert_test(r.status_code == 201, "Step 4: Event 'Design Sprint 1.0' scheduled under new club")
    e_id = r.get_json()["event"]["event_id"]

    # 5. Verify Club Detail view shows advisor and event
    r = client.get(f"/api/clubs/{c_id}")
    assert_test(r.status_code == 200 and len(r.get_json()["club"]["advisors"]) == 1, "Step 5: Club overview reflects assigned mentor")
    r = client.get(f"/api/clubs/{c_id}/events")
    assert_test(r.status_code == 200 and len(r.get_json()["events"]) == 1, "Step 6: Club overview lists scheduled event")

    # =========================================================================
    # FLOW 3: Capacity Protection & Seat Release on Cancellation
    # =========================================================================
    print("\n--- User Flow 3: Event Capacity Ceiling & Cancellation Slot Release ---")

    # 1. Schedule a micro workshop with capacity = 1
    r = client.post("/api/events", json={
        "club_id": c_id,
        "title": "1-on-1 Mentorship Session",
        "event_date": "2026-12-08 14:00:00",
        "venue": "Conference Room",
        "capacity": 1,
        "status": "Upcoming"
    })
    micro_evt_id = r.get_json()["event"]["event_id"]

    # 2. Student 1 registers (Reaches full capacity 1/1)
    r = client.post("/api/registrations", json={"student_id": 1, "event_id": micro_evt_id})
    assert_test(r.status_code == 201, "Step 1: Student 1 registers, taking the only seat (1/1)")

    # 3. Student 2 tries to register -> MUST BE REJECTED WITH 409
    r = client.post("/api/registrations", json={"student_id": 2, "event_id": micro_evt_id})
    assert_test(r.status_code == 409 and "full capacity" in r.get_json()["error"].lower(), "Step 2: Student 2 registration rejected due to capacity ceiling")

    # 4. Student 1 cancels their registration
    r = client.put(f"/api/registrations/1/{micro_evt_id}", json={"attendance_status": "Cancelled"})
    assert_test(r.status_code == 200, "Step 3: Student 1 cancels registration, freeing up 1 slot")

    # 5. Student 2 now retries registration -> MUST SUCCEED WITH 201
    r = client.post("/api/registrations", json={"student_id": 2, "event_id": micro_evt_id})
    assert_test(r.status_code == 201, "Step 4: Student 2 successfully claims the newly freed slot")

    # =========================================================================
    # FLOW 4: Referential Integrity & Cascade Deletion Checks
    # =========================================================================
    print("\n--- User Flow 4: Referential Actions & Clean Deletions ---")

    # 1. Delete student created in Flow 1
    r = client.delete(f"/api/students/{s_id}")
    assert_test(r.status_code == 200, "Step 1: Student successfully deleted")

    # Verify their membership and event registration disappeared
    r = client.get(f"/api/memberships/{s_id}/1")
    assert_test(r.status_code == 404, "Step 2: Student's membership was cascaded")
    r = client.get(f"/api/registrations/{s_id}/1")
    assert_test(r.status_code == 404, "Step 3: Student's event registration was cascaded")

    # 2. Delete Club created in Flow 2
    r = client.delete(f"/api/clubs/{c_id}")
    assert_test(r.status_code == 200, "Step 4: Club successfully deleted")
    r = client.get(f"/api/events/{e_id}")
    assert_test(r.status_code == 404, "Step 5: Events belonging to deleted club were cascaded")
    r = client.get(f"/api/advisors/{a_id}")
    assert_test(r.status_code == 200, "Step 6: Advisor survives club deletion intact")

    # Cleanup test db
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

    print(f"\n==========================================")
    print(f"USER FLOW RESULTS: {passed} / {total} tests passed.")
    print(f"==========================================")
    if passed == total:
        print("[SUCCESS] All end-to-end user journeys verified!")
    else:
        print("[ERROR] Some user flows failed!")
        sys.exit(1)


if __name__ == "__main__":
    run_flow_tests()

