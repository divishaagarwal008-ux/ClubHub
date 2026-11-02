"""
ClubHub — Student Club and Organisation Management System
Flask Backend Application (app.py)

Technology: Python 3, Flask, SQLite 3 (sqlite3 module)
"""

import os
import re
import sqlite3
from flask import Flask, jsonify, request, render_template

import db

# Allowed Enumerations matching SQLite schema CHECK constraints
VALID_CLUB_CATEGORIES = ['Technical', 'Cultural', 'Sports', 'Literary', 'Social', 'Academic']
VALID_CLUB_STATUSES = ['Active', 'Inactive']
VALID_MEMBERSHIP_ROLES = ['President', 'Vice President', 'Secretary', 'Treasurer', 'Core Member', 'Member']
VALID_EVENT_STATUSES = ['Upcoming', 'Ongoing', 'Completed', 'Cancelled']
VALID_ATTENDANCE_STATUSES = ['Registered', 'Attended', 'Absent', 'Cancelled']


def create_app(test_config=None):
    """Application Factory Pattern: Creates and configures the Flask application."""
    app = Flask(__name__)

    # Default configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    default_db_path = os.path.join(base_dir, "database", "clubhub.db")
    app.config.from_mapping(
        DATABASE=default_db_path,
        SECRET_KEY='clubhub-dev-key'
    )

    if test_config:
        app.config.update(test_config)

    # Register teardown helper to close database connections
    db.init_app(app)

    # -------------------------------------------------------------------------
    # Helper Utilities
    # -------------------------------------------------------------------------
    def get_payload():
        """Extracts JSON body or Form data gracefully."""
        if request.is_json:
            return request.get_json(silent=True) or {}
        return request.form.to_dict() if request.form else {}

    def is_valid_email(email):
        """Simple RFC-compliant-enough regex for college/academic email strings."""
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip()))

    # Global Error Handlers for graceful API responses
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"success": False, "error": "Requested resource was not found."}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"success": False, "error": "HTTP method not allowed on this route."}), 405

    @app.errorhandler(500)
    def handle_server_error(e):
        return jsonify({"success": False, "error": "Internal server error occurred."}), 500

    # -------------------------------------------------------------------------
    # System Root & Dashboard Analytics
    # -------------------------------------------------------------------------
    @app.route("/", methods=["GET"])
    def index():
        # If accessed from a web browser (Accept header includes text/html), render the web frontend
        if 'text/html' in request.headers.get('Accept', '') and not request.is_json:
            return render_template("index.html")
        # Otherwise return API status JSON (for curl, test_client, API tools)
        return jsonify({
            "project": "ClubHub — Student Club and Organisation Management System",
            "status": "online",
            "version": "1.0",
            "endpoints": {
                "dashboard": "/api/dashboard",
                "students": "/api/students",
                "clubs": "/api/clubs",
                "faculty_advisors": "/api/advisors",
                "club_advisors": "/api/club-advisors",
                "memberships": "/api/memberships",
                "events": "/api/events",
                "event_registrations": "/api/registrations"
            }
        })

    # Direct Web UI routes so clicking / reloading works directly
    @app.route("/dashboard", methods=["GET"])
    @app.route("/students", methods=["GET"])
    @app.route("/clubs", methods=["GET"])
    @app.route("/memberships", methods=["GET"])
    @app.route("/events", methods=["GET"])
    @app.route("/registrations", methods=["GET"])
    @app.route("/advisors", methods=["GET"])
    def ui_routes():
        return render_template("index.html")

    @app.route("/api/dashboard", methods=["GET"])
    def get_dashboard():
        """
        Dashboard Aggregation Endpoint:
        Computes summary statistics and lists upcoming events and membership counts.
        """
        conn = db.get_db()

        # 1. Metric Counts
        total_students = conn.execute("SELECT COUNT(*) FROM Student;").fetchone()[0]
        total_clubs = conn.execute("SELECT COUNT(*) FROM Club;").fetchone()[0]
        total_events = conn.execute("SELECT COUNT(*) FROM Event;").fetchone()[0]
        total_advisors = conn.execute("SELECT COUNT(*) FROM Faculty_Advisor;").fetchone()[0]
        total_registrations = conn.execute("SELECT COUNT(*) FROM Event_Registration WHERE attendance_status != 'Cancelled';").fetchone()[0]

        # 2. Upcoming Events (ordered by earliest date)
        upcoming_events = db.query_db("""
            SELECT e.event_id, e.title, e.event_date, e.venue, e.capacity, e.status,
                   c.name AS club_name,
                   (SELECT COUNT(*) FROM Event_Registration er 
                    WHERE er.event_id = e.event_id AND er.attendance_status != 'Cancelled') AS active_registrations
            FROM Event e
            JOIN Club c ON e.club_id = c.club_id
            WHERE e.status = 'Upcoming'
            ORDER BY e.event_date ASC
            LIMIT 5;
        """)

        # 3. Club Membership Counts
        club_membership_counts = db.query_db("""
            SELECT c.club_id, c.name, c.category, c.status,
                   COUNT(m.student_id) AS member_count
            FROM Club c
            LEFT JOIN Membership m ON c.club_id = m.club_id
            GROUP BY c.club_id, c.name, c.category, c.status
            ORDER BY member_count DESC, c.name ASC;
        """)

        return jsonify({
            "success": True,
            "metrics": {
                "total_students": total_students,
                "total_clubs": total_clubs,
                "total_events": total_events,
                "total_faculty_advisors": total_advisors,
                "total_active_registrations": total_registrations
            },
            "upcoming_events": upcoming_events,
            "club_membership_counts": club_membership_counts
        })

    # =========================================================================
    # 1. STUDENT ROUTES (CRUD + Search + Club Enrolments)
    # =========================================================================
    @app.route("/api/students", methods=["GET"])
    def list_students():
        """Lists students with optional keyword search across name, roll_no, email, and branch."""
        query = request.args.get('q', '').strip()
        if query:
            wildcard = f"%{query}%"
            students = db.query_db("""
                SELECT student_id, name, email, roll_no, branch, year, phone 
                FROM Student 
                WHERE name LIKE ? OR roll_no LIKE ? OR email LIKE ? OR branch LIKE ?
                ORDER BY roll_no ASC;
            """, (wildcard, wildcard, wildcard, wildcard))
        else:
            students = db.query_db("""
                SELECT student_id, name, email, roll_no, branch, year, phone 
                FROM Student 
                ORDER BY roll_no ASC;
            """)
        return jsonify({"success": True, "count": len(students), "students": students})

    @app.route("/api/students/<int:student_id>", methods=["GET"])
    def get_student(student_id):
        student = db.query_db(
            "SELECT student_id, name, email, roll_no, branch, year, phone FROM Student WHERE student_id = ?;",
            (student_id,), one=True
        )
        if not student:
            return jsonify({"success": False, "error": f"Student with ID {student_id} not found."}), 404
        return jsonify({"success": True, "student": student})

    @app.route("/api/students", methods=["POST"])
    def create_student():
        data = get_payload()
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        roll_no = (data.get("roll_no") or "").strip()
        branch = (data.get("branch") or "").strip()
        year = data.get("year")
        phone = data.get("phone")
        if phone:
            phone = str(phone).strip()

        # Validation
        if not name or not email or not roll_no or not branch or year is None:
            return jsonify({"success": False, "error": "Required fields: name, email, roll_no, branch, year."}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "error": "Invalid email address format."}), 400

        try:
            year = int(year)
            if year not in [1, 2, 3, 4]:
                return jsonify({"success": False, "error": "Year of study must be an integer between 1 and 4."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Year of study must be a valid integer."}), 400

        if phone and len(phone) < 10:
            return jsonify({"success": False, "error": "Phone number must be at least 10 digits if provided."}), 400

        try:
            conn = db.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Student (name, email, roll_no, branch, year, phone)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (name, email, roll_no, branch, year, phone or None))
            conn.commit()
            new_id = cursor.lastrowid
            created = db.query_db("SELECT * FROM Student WHERE student_id = ?;", (new_id,), one=True)
            return jsonify({"success": True, "message": "Student created successfully.", "student": created}), 201
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Student.email" in err:
                return jsonify({"success": False, "error": f"A student with email '{email}' already exists."}), 409
            if "UNIQUE constraint failed: Student.roll_no" in err:
                return jsonify({"success": False, "error": f"A student with roll number '{roll_no}' already exists."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/students/<int:student_id>", methods=["PUT"])
    def update_student(student_id):
        existing = db.query_db("SELECT * FROM Student WHERE student_id = ?;", (student_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Student with ID {student_id} not found."}), 404

        data = get_payload()
        name = data.get("name", existing["name"]).strip()
        email = data.get("email", existing["email"]).strip()
        roll_no = data.get("roll_no", existing["roll_no"]).strip()
        branch = data.get("branch", existing["branch"]).strip()
        year = data.get("year", existing["year"])
        phone = data.get("phone", existing["phone"])
        if phone:
            phone = str(phone).strip()

        if not name or not email or not roll_no or not branch or year is None:
            return jsonify({"success": False, "error": "Fields cannot be blank."}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "error": "Invalid email address format."}), 400

        try:
            year = int(year)
            if year not in [1, 2, 3, 4]:
                return jsonify({"success": False, "error": "Year must be between 1 and 4."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Year must be an integer."}), 400

        if phone and len(phone) < 10:
            return jsonify({"success": False, "error": "Phone number must be at least 10 digits."}), 400

        try:
            conn = db.get_db()
            conn.execute("""
                UPDATE Student 
                SET name = ?, email = ?, roll_no = ?, branch = ?, year = ?, phone = ?
                WHERE student_id = ?;
            """, (name, email, roll_no, branch, year, phone or None, student_id))
            conn.commit()
            updated = db.query_db("SELECT * FROM Student WHERE student_id = ?;", (student_id,), one=True)
            return jsonify({"success": True, "message": "Student updated successfully.", "student": updated})
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Student.email" in err:
                return jsonify({"success": False, "error": f"Email '{email}' is already in use."}), 409
            if "UNIQUE constraint failed: Student.roll_no" in err:
                return jsonify({"success": False, "error": f"Roll number '{roll_no}' is already in use."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/students/<int:student_id>", methods=["DELETE"])
    def delete_student(student_id):
        existing = db.query_db("SELECT * FROM Student WHERE student_id = ?;", (student_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Student with ID {student_id} not found."}), 404

        conn = db.get_db()
        conn.execute("DELETE FROM Student WHERE student_id = ?;", (student_id,))
        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Student '{existing['name']}' (ID: {student_id}) and all associated memberships and event registrations have been deleted."
        })

    @app.route("/api/students/<int:student_id>/clubs", methods=["GET"])
    def list_student_clubs(student_id):
        student = db.query_db("SELECT name FROM Student WHERE student_id = ?;", (student_id,), one=True)
        if not student:
            return jsonify({"success": False, "error": f"Student with ID {student_id} not found."}), 404

        clubs = db.query_db("""
            SELECT c.club_id, c.name, c.category, c.room_no, c.status, m.role, m.joined_at
            FROM Membership m
            JOIN Club c ON m.club_id = c.club_id
            WHERE m.student_id = ?
            ORDER BY m.joined_at DESC;
        """, (student_id,))
        return jsonify({"success": True, "student_id": student_id, "student_name": student["name"], "clubs": clubs})

    # =========================================================================
    # 2. CLUB ROUTES (CRUD + Members + Events + Advisors)
    # =========================================================================
    @app.route("/api/clubs", methods=["GET"])
    def list_clubs():
        category = request.args.get('category')
        status = request.args.get('status')
        query = "SELECT club_id, name, category, description, room_no, status FROM Club WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY name ASC;"
        clubs = db.query_db(query, tuple(params))
        return jsonify({"success": True, "count": len(clubs), "clubs": clubs})

    @app.route("/api/clubs/<int:club_id>", methods=["GET"])
    def get_club(club_id):
        club = db.query_db("SELECT * FROM Club WHERE club_id = ?;", (club_id,), one=True)
        if not club:
            return jsonify({"success": False, "error": f"Club with ID {club_id} not found."}), 404

        # Include member count & assigned advisors
        member_count = db.query_db("SELECT COUNT(*) AS count FROM Membership WHERE club_id = ?;", (club_id,), one=True)["count"]
        advisors = db.query_db("""
            SELECT fa.advisor_id, fa.name, fa.email, fa.department, fa.phone
            FROM Club_Advisor ca
            JOIN Faculty_Advisor fa ON ca.advisor_id = fa.advisor_id
            WHERE ca.club_id = ?;
        """, (club_id,))

        club_dict = dict(club)
        club_dict["member_count"] = member_count
        club_dict["advisors"] = advisors
        return jsonify({"success": True, "club": club_dict})

    @app.route("/api/clubs", methods=["POST"])
    def create_club():
        data = get_payload()
        name = (data.get("name") or "").strip()
        category = (data.get("category") or "").strip()
        description = (data.get("description") or "").strip()
        room_no = (data.get("room_no") or "").strip()
        status = (data.get("status") or "Active").strip()

        if not name or not category:
            return jsonify({"success": False, "error": "Required fields: name, category."}), 400

        if category not in VALID_CLUB_CATEGORIES:
            return jsonify({"success": False, "error": f"Invalid category. Allowed: {VALID_CLUB_CATEGORIES}"}), 400

        if status not in VALID_CLUB_STATUSES:
            return jsonify({"success": False, "error": f"Invalid status. Allowed: {VALID_CLUB_STATUSES}"}), 400

        try:
            conn = db.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Club (name, category, description, room_no, status)
                VALUES (?, ?, ?, ?, ?);
            """, (name, category, description or None, room_no or None, status))
            conn.commit()
            new_id = cursor.lastrowid
            created = db.query_db("SELECT * FROM Club WHERE club_id = ?;", (new_id,), one=True)
            return jsonify({"success": True, "message": "Club created successfully.", "club": created}), 201
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Club.name" in err:
                return jsonify({"success": False, "error": f"A club named '{name}' already exists."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/clubs/<int:club_id>", methods=["PUT"])
    def update_club(club_id):
        existing = db.query_db("SELECT * FROM Club WHERE club_id = ?;", (club_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Club with ID {club_id} not found."}), 404

        data = get_payload()
        name = data.get("name", existing["name"]).strip()
        category = data.get("category", existing["category"]).strip()
        description = data.get("description", existing["description"])
        room_no = data.get("room_no", existing["room_no"])
        status = data.get("status", existing["status"]).strip()

        if not name or not category:
            return jsonify({"success": False, "error": "Club name and category cannot be empty."}), 400

        if category not in VALID_CLUB_CATEGORIES:
            return jsonify({"success": False, "error": f"Category must be one of: {VALID_CLUB_CATEGORIES}"}), 400

        if status not in VALID_CLUB_STATUSES:
            return jsonify({"success": False, "error": f"Status must be one of: {VALID_CLUB_STATUSES}"}), 400

        try:
            conn = db.get_db()
            conn.execute("""
                UPDATE Club 
                SET name = ?, category = ?, description = ?, room_no = ?, status = ?
                WHERE club_id = ?;
            """, (name, category, description, room_no, status, club_id))
            conn.commit()
            updated = db.query_db("SELECT * FROM Club WHERE club_id = ?;", (club_id,), one=True)
            return jsonify({"success": True, "message": "Club updated successfully.", "club": updated})
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Club.name" in err:
                return jsonify({"success": False, "error": f"Club name '{name}' already exists."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/clubs/<int:club_id>", methods=["DELETE"])
    def delete_club(club_id):
        existing = db.query_db("SELECT * FROM Club WHERE club_id = ?;", (club_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Club with ID {club_id} not found."}), 404

        conn = db.get_db()
        conn.execute("DELETE FROM Club WHERE club_id = ?;", (club_id,))
        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Club '{existing['name']}' (ID: {club_id}) and its events, memberships, and advisor mappings have been deleted."
        })

    @app.route("/api/clubs/<int:club_id>/members", methods=["GET"])
    def list_club_members(club_id):
        club = db.query_db("SELECT name FROM Club WHERE club_id = ?;", (club_id,), one=True)
        if not club:
            return jsonify({"success": False, "error": f"Club with ID {club_id} not found."}), 404

        members = db.query_db("""
            SELECT s.student_id, s.name, s.email, s.roll_no, s.branch, s.year,
                   m.role, m.joined_at
            FROM Membership m
            JOIN Student s ON m.student_id = s.student_id
            WHERE m.club_id = ?
            ORDER BY 
                CASE m.role 
                    WHEN 'President' THEN 1 
                    WHEN 'Vice President' THEN 2 
                    WHEN 'Secretary' THEN 3 
                    WHEN 'Treasurer' THEN 4 
                    WHEN 'Core Member' THEN 5 
                    ELSE 6 
                END, s.name ASC;
        """, (club_id,))
        return jsonify({"success": True, "club_id": club_id, "club_name": club["name"], "members": members})

    @app.route("/api/clubs/<int:club_id>/events", methods=["GET"])
    def list_club_events(club_id):
        club = db.query_db("SELECT name FROM Club WHERE club_id = ?;", (club_id,), one=True)
        if not club:
            return jsonify({"success": False, "error": f"Club with ID {club_id} not found."}), 404

        events = db.query_db("""
            SELECT event_id, title, event_date, venue, capacity, status,
                   (SELECT COUNT(*) FROM Event_Registration er 
                    WHERE er.event_id = e.event_id AND er.attendance_status != 'Cancelled') AS active_registrations
            FROM Event e
            WHERE club_id = ?
            ORDER BY event_date DESC;
        """, (club_id,))
        return jsonify({"success": True, "club_id": club_id, "club_name": club["name"], "events": events})

    # =========================================================================
    # 3. FACULTY ADVISOR ROUTES (CRUD)
    # =========================================================================
    @app.route("/api/advisors", methods=["GET"])
    def list_advisors():
        advisors = db.query_db("SELECT advisor_id, name, email, department, phone FROM Faculty_Advisor ORDER BY name ASC;")
        return jsonify({"success": True, "count": len(advisors), "advisors": advisors})

    @app.route("/api/advisors/<int:advisor_id>", methods=["GET"])
    def get_advisor(advisor_id):
        advisor = db.query_db("SELECT * FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,), one=True)
        if not advisor:
            return jsonify({"success": False, "error": f"Faculty Advisor with ID {advisor_id} not found."}), 404

        clubs = db.query_db("""
            SELECT c.club_id, c.name, c.category, c.status
            FROM Club_Advisor ca
            JOIN Club c ON ca.club_id = c.club_id
            WHERE ca.advisor_id = ?;
        """, (advisor_id,))
        advisor_dict = dict(advisor)
        advisor_dict["advised_clubs"] = clubs
        return jsonify({"success": True, "advisor": advisor_dict})

    @app.route("/api/advisors", methods=["POST"])
    def create_advisor():
        data = get_payload()
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        department = (data.get("department") or "").strip()
        phone = data.get("phone")
        if phone:
            phone = str(phone).strip()

        if not name or not email or not department:
            return jsonify({"success": False, "error": "Required fields: name, email, department."}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "error": "Invalid email address format."}), 400

        if phone and len(phone) < 10:
            return jsonify({"success": False, "error": "Phone number must be at least 10 digits."}), 400

        try:
            conn = db.get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Faculty_Advisor (name, email, department, phone)
                VALUES (?, ?, ?, ?);
            """, (name, email, department, phone or None))
            conn.commit()
            new_id = cursor.lastrowid
            created = db.query_db("SELECT * FROM Faculty_Advisor WHERE advisor_id = ?;", (new_id,), one=True)
            return jsonify({"success": True, "message": "Faculty Advisor created successfully.", "advisor": created}), 201
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Faculty_Advisor.email" in err:
                return jsonify({"success": False, "error": f"Faculty advisor email '{email}' already exists."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/advisors/<int:advisor_id>", methods=["PUT"])
    def update_advisor(advisor_id):
        existing = db.query_db("SELECT * FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Faculty Advisor with ID {advisor_id} not found."}), 404

        data = get_payload()
        name = data.get("name", existing["name"]).strip()
        email = data.get("email", existing["email"]).strip()
        department = data.get("department", existing["department"]).strip()
        phone = data.get("phone", existing["phone"])
        if phone:
            phone = str(phone).strip()

        if not name or not email or not department:
            return jsonify({"success": False, "error": "Fields cannot be blank."}), 400

        if not is_valid_email(email):
            return jsonify({"success": False, "error": "Invalid email address format."}), 400

        if phone and len(phone) < 10:
            return jsonify({"success": False, "error": "Phone must be at least 10 digits."}), 400

        try:
            conn = db.get_db()
            conn.execute("""
                UPDATE Faculty_Advisor 
                SET name = ?, email = ?, department = ?, phone = ?
                WHERE advisor_id = ?;
            """, (name, email, department, phone or None, advisor_id))
            conn.commit()
            updated = db.query_db("SELECT * FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,), one=True)
            return jsonify({"success": True, "message": "Faculty Advisor updated successfully.", "advisor": updated})
        except sqlite3.IntegrityError as e:
            err = str(e)
            if "UNIQUE constraint failed: Faculty_Advisor.email" in err:
                return jsonify({"success": False, "error": f"Email '{email}' is already in use."}), 409
            return jsonify({"success": False, "error": f"Database integrity error: {err}"}), 400

    @app.route("/api/advisors/<int:advisor_id>", methods=["DELETE"])
    def delete_advisor(advisor_id):
        existing = db.query_db("SELECT * FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Faculty Advisor with ID {advisor_id} not found."}), 404

        conn = db.get_db()
        # Deleting advisor removes Club_Advisor mappings (ON DELETE CASCADE), leaving Club records intact!
        conn.execute("DELETE FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,))
        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Faculty Advisor '{existing['name']}' deleted. Club advisory mappings were removed while clubs remain intact."
        })

    # =========================================================================
    # 4. CLUB_ADVISOR ROUTES (Bridge Table M:N)
    # =========================================================================
    @app.route("/api/club-advisors", methods=["GET"])
    def list_club_advisors():
        mappings = db.query_db("""
            SELECT ca.club_id, c.name AS club_name, ca.advisor_id, fa.name AS advisor_name, fa.department
            FROM Club_Advisor ca
            JOIN Club c ON ca.club_id = c.club_id
            JOIN Faculty_Advisor fa ON ca.advisor_id = fa.advisor_id
            ORDER BY c.name ASC, fa.name ASC;
        """)
        return jsonify({"success": True, "count": len(mappings), "club_advisors": mappings})

    @app.route("/api/club-advisors", methods=["POST"])
    def assign_club_advisor():
        data = get_payload()
        club_id = data.get("club_id")
        advisor_id = data.get("advisor_id")

        if club_id is None or advisor_id is None:
            return jsonify({"success": False, "error": "Required fields: club_id, advisor_id."}), 400

        try:
            club_id = int(club_id)
            advisor_id = int(advisor_id)
        except ValueError:
            return jsonify({"success": False, "error": "club_id and advisor_id must be integers."}), 400

        # Validate existence
        if not db.query_db("SELECT 1 FROM Club WHERE club_id = ?;", (club_id,), one=True):
            return jsonify({"success": False, "error": f"Club with ID {club_id} does not exist."}), 404

        if not db.query_db("SELECT 1 FROM Faculty_Advisor WHERE advisor_id = ?;", (advisor_id,), one=True):
            return jsonify({"success": False, "error": f"Faculty Advisor with ID {advisor_id} does not exist."}), 404

        try:
            conn = db.get_db()
            conn.execute("INSERT INTO Club_Advisor (club_id, advisor_id) VALUES (?, ?);", (club_id, advisor_id))
            conn.commit()
            return jsonify({"success": True, "message": "Faculty advisor successfully assigned to club."}), 201
        except sqlite3.IntegrityError as e:
            return jsonify({"success": False, "error": "This faculty advisor is already assigned to this club."}), 409

    @app.route("/api/club-advisors/<int:club_id>/<int:advisor_id>", methods=["DELETE"])
    def remove_club_advisor(club_id, advisor_id):
        conn = db.get_db()
        cursor = conn.execute("DELETE FROM Club_Advisor WHERE club_id = ? AND advisor_id = ?;", (club_id, advisor_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "No advisory mapping found for the specified club and advisor."}), 404
        return jsonify({"success": True, "message": "Faculty advisor unassigned from club."})

    # =========================================================================
    # 5. MEMBERSHIP ROUTES (Bridge Table M:N)
    # =========================================================================
    @app.route("/api/memberships", methods=["GET"])
    def list_memberships():
        student_id = request.args.get('student_id')
        club_id = request.args.get('club_id')

        query = """
            SELECT m.student_id, s.name AS student_name, s.roll_no,
                   m.club_id, c.name AS club_name, m.role, m.joined_at
            FROM Membership m
            JOIN Student s ON m.student_id = s.student_id
            JOIN Club c ON m.club_id = c.club_id
            WHERE 1=1
        """
        params = []
        if student_id:
            query += " AND m.student_id = ?"
            params.append(student_id)
        if club_id:
            query += " AND m.club_id = ?"
            params.append(club_id)

        query += " ORDER BY m.joined_at DESC;"
        memberships = db.query_db(query, tuple(params))
        return jsonify({"success": True, "count": len(memberships), "memberships": memberships})

    @app.route("/api/memberships/<int:student_id>/<int:club_id>", methods=["GET"])
    def get_membership(student_id, club_id):
        membership = db.query_db("""
            SELECT m.student_id, s.name AS student_name, s.roll_no,
                   m.club_id, c.name AS club_name, m.role, m.joined_at
            FROM Membership m
            JOIN Student s ON m.student_id = s.student_id
            JOIN Club c ON m.club_id = c.club_id
            WHERE m.student_id = ? AND m.club_id = ?;
        """, (student_id, club_id), one=True)
        if not membership:
            return jsonify({"success": False, "error": "Membership record not found."}), 404
        return jsonify({"success": True, "membership": membership})

    @app.route("/api/memberships", methods=["POST"])
    def create_membership():
        data = get_payload()
        student_id = data.get("student_id")
        club_id = data.get("club_id")
        role = (data.get("role") or "Member").strip()

        if student_id is None or club_id is None:
            return jsonify({"success": False, "error": "Required fields: student_id, club_id."}), 400

        try:
            student_id = int(student_id)
            club_id = int(club_id)
        except ValueError:
            return jsonify({"success": False, "error": "student_id and club_id must be integers."}), 400

        if role not in VALID_MEMBERSHIP_ROLES:
            return jsonify({"success": False, "error": f"Invalid role. Allowed roles: {VALID_MEMBERSHIP_ROLES}"}), 400

        # Foreign Key Reference Checks
        if not db.query_db("SELECT 1 FROM Student WHERE student_id = ?;", (student_id,), one=True):
            return jsonify({"success": False, "error": f"Student with ID {student_id} does not exist."}), 404

        if not db.query_db("SELECT 1 FROM Club WHERE club_id = ?;", (club_id,), one=True):
            return jsonify({"success": False, "error": f"Club with ID {club_id} does not exist."}), 404

        try:
            conn = db.get_db()
            conn.execute("""
                INSERT INTO Membership (student_id, club_id, role)
                VALUES (?, ?, ?);
            """, (student_id, club_id, role))
            conn.commit()
            created = db.query_db("""
                SELECT m.student_id, s.name AS student_name, m.club_id, c.name AS club_name, m.role, m.joined_at
                FROM Membership m
                JOIN Student s ON m.student_id = s.student_id
                JOIN Club c ON m.club_id = c.club_id
                WHERE m.student_id = ? AND m.club_id = ?;
            """, (student_id, club_id), one=True)
            return jsonify({"success": True, "message": "Membership created successfully.", "membership": created}), 201
        except sqlite3.IntegrityError as e:
            return jsonify({"success": False, "error": "Student is already a member of this club (Duplicate membership prevented)."}), 409

    @app.route("/api/memberships/<int:student_id>/<int:club_id>", methods=["PUT"])
    def update_membership(student_id, club_id):
        existing = db.query_db("SELECT * FROM Membership WHERE student_id = ? AND club_id = ?;", (student_id, club_id), one=True)
        if not existing:
            return jsonify({"success": False, "error": "Membership record not found."}), 404

        data = get_payload()
        role = (data.get("role") or existing["role"]).strip()
        if role not in VALID_MEMBERSHIP_ROLES:
            return jsonify({"success": False, "error": f"Invalid role. Allowed: {VALID_MEMBERSHIP_ROLES}"}), 400

        conn = db.get_db()
        conn.execute("UPDATE Membership SET role = ? WHERE student_id = ? AND club_id = ?;", (role, student_id, club_id))
        conn.commit()
        updated = db.query_db("""
            SELECT m.student_id, s.name AS student_name, m.club_id, c.name AS club_name, m.role, m.joined_at
            FROM Membership m
            JOIN Student s ON m.student_id = s.student_id
            JOIN Club c ON m.club_id = c.club_id
            WHERE m.student_id = ? AND m.club_id = ?;
        """, (student_id, club_id), one=True)
        return jsonify({"success": True, "message": "Membership updated successfully.", "membership": updated})

    @app.route("/api/memberships/<int:student_id>/<int:club_id>", methods=["DELETE"])
    def delete_membership(student_id, club_id):
        conn = db.get_db()
        cursor = conn.execute("DELETE FROM Membership WHERE student_id = ? AND club_id = ?;", (student_id, club_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Membership record not found."}), 404
        return jsonify({"success": True, "message": "Membership successfully removed."})

    # =========================================================================
    # 6. EVENT ROUTES (CRUD + Registrations Listing)
    # =========================================================================
    @app.route("/api/events", methods=["GET"])
    def list_events():
        club_id = request.args.get('club_id')
        status = request.args.get('status')

        query = """
            SELECT e.event_id, e.club_id, c.name AS club_name, e.title, e.event_date,
                   e.venue, e.capacity, e.status,
                   (SELECT COUNT(*) FROM Event_Registration er 
                    WHERE er.event_id = e.event_id AND er.attendance_status != 'Cancelled') AS active_registrations
            FROM Event e
            JOIN Club c ON e.club_id = c.club_id
            WHERE 1=1
        """
        params = []
        if club_id:
            query += " AND e.club_id = ?"
            params.append(club_id)
        if status:
            query += " AND e.status = ?"
            params.append(status)

        query += " ORDER BY e.event_date ASC;"
        events = db.query_db(query, tuple(params))
        return jsonify({"success": True, "count": len(events), "events": events})

    @app.route("/api/events/<int:event_id>", methods=["GET"])
    def get_event(event_id):
        event = db.query_db("""
            SELECT e.event_id, e.club_id, c.name AS club_name, e.title, e.event_date,
                   e.venue, e.capacity, e.status,
                   (SELECT COUNT(*) FROM Event_Registration er 
                    WHERE er.event_id = e.event_id AND er.attendance_status != 'Cancelled') AS active_registrations
            FROM Event e
            JOIN Club c ON e.club_id = c.club_id
            WHERE e.event_id = ?;
        """, (event_id,), one=True)
        if not event:
            return jsonify({"success": False, "error": f"Event with ID {event_id} not found."}), 404

        event_dict = dict(event)
        event_dict["available_seats"] = max(0, event_dict["capacity"] - event_dict["active_registrations"])
        return jsonify({"success": True, "event": event_dict})

    @app.route("/api/events", methods=["POST"])
    def create_event():
        data = get_payload()
        club_id = data.get("club_id")
        title = (data.get("title") or "").strip()
        event_date = (data.get("event_date") or "").strip()
        venue = (data.get("venue") or "").strip()
        capacity = data.get("capacity")
        status = (data.get("status") or "Upcoming").strip()

        if club_id is None or not title or not event_date or not venue or capacity is None:
            return jsonify({"success": False, "error": "Required fields: club_id, title, event_date, venue, capacity."}), 400

        try:
            club_id = int(club_id)
        except ValueError:
            return jsonify({"success": False, "error": "club_id must be an integer."}), 400

        try:
            capacity = int(capacity)
            if capacity <= 0:
                return jsonify({"success": False, "error": "Capacity must be a positive integer (> 0)."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Capacity must be a valid integer."}), 400

        if status not in VALID_EVENT_STATUSES:
            return jsonify({"success": False, "error": f"Invalid status. Allowed: {VALID_EVENT_STATUSES}"}), 400

        # Validate Club existence
        if not db.query_db("SELECT 1 FROM Club WHERE club_id = ?;", (club_id,), one=True):
            return jsonify({"success": False, "error": f"Club with ID {club_id} does not exist."}), 404

        conn = db.get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Event (club_id, title, event_date, venue, capacity, status)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (club_id, title, event_date, venue, capacity, status))
        conn.commit()
        new_id = cursor.lastrowid
        created = db.query_db("SELECT * FROM Event WHERE event_id = ?;", (new_id,), one=True)
        return jsonify({"success": True, "message": "Event created successfully.", "event": created}), 201

    @app.route("/api/events/<int:event_id>", methods=["PUT"])
    def update_event(event_id):
        existing = db.query_db("SELECT * FROM Event WHERE event_id = ?;", (event_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Event with ID {event_id} not found."}), 404

        data = get_payload()
        club_id = data.get("club_id", existing["club_id"])
        title = data.get("title", existing["title"]).strip()
        event_date = data.get("event_date", existing["event_date"]).strip()
        venue = data.get("venue", existing["venue"]).strip()
        capacity = data.get("capacity", existing["capacity"])
        status = data.get("status", existing["status"]).strip()

        if not title or not event_date or not venue:
            return jsonify({"success": False, "error": "Title, event_date, and venue cannot be empty."}), 400

        try:
            club_id = int(club_id)
            if not db.query_db("SELECT 1 FROM Club WHERE club_id = ?;", (club_id,), one=True):
                return jsonify({"success": False, "error": f"Club with ID {club_id} does not exist."}), 404
        except ValueError:
            return jsonify({"success": False, "error": "club_id must be an integer."}), 400

        try:
            capacity = int(capacity)
            if capacity <= 0:
                return jsonify({"success": False, "error": "Capacity must be greater than zero."}), 400
        except ValueError:
            return jsonify({"success": False, "error": "Capacity must be an integer."}), 400

        if status not in VALID_EVENT_STATUSES:
            return jsonify({"success": False, "error": f"Invalid status. Allowed: {VALID_EVENT_STATUSES}"}), 400

        conn = db.get_db()
        conn.execute("""
            UPDATE Event
            SET club_id = ?, title = ?, event_date = ?, venue = ?, capacity = ?, status = ?
            WHERE event_id = ?;
        """, (club_id, title, event_date, venue, capacity, status, event_id))
        conn.commit()
        updated = db.query_db("SELECT * FROM Event WHERE event_id = ?;", (event_id,), one=True)
        return jsonify({"success": True, "message": "Event updated successfully.", "event": updated})

    @app.route("/api/events/<int:event_id>", methods=["DELETE"])
    def delete_event(event_id):
        existing = db.query_db("SELECT * FROM Event WHERE event_id = ?;", (event_id,), one=True)
        if not existing:
            return jsonify({"success": False, "error": f"Event with ID {event_id} not found."}), 404

        conn = db.get_db()
        conn.execute("DELETE FROM Event WHERE event_id = ?;", (event_id,))
        conn.commit()
        return jsonify({
            "success": True,
            "message": f"Event '{existing['title']}' (ID: {event_id}) and its registrations have been deleted."
        })

    @app.route("/api/events/<int:event_id>/registrations", methods=["GET"])
    def list_event_registrations(event_id):
        event = db.query_db("SELECT title, capacity FROM Event WHERE event_id = ?;", (event_id,), one=True)
        if not event:
            return jsonify({"success": False, "error": f"Event with ID {event_id} not found."}), 404

        registrations = db.query_db("""
            SELECT er.student_id, s.name AS student_name, s.roll_no, s.email, s.branch,
                   er.registered_at, er.attendance_status
            FROM Event_Registration er
            JOIN Student s ON er.student_id = s.student_id
            WHERE er.event_id = ?
            ORDER BY er.registered_at ASC;
        """, (event_id,))

        active_count = sum(1 for r in registrations if r["attendance_status"] != "Cancelled")
        return jsonify({
            "success": True,
            "event_id": event_id,
            "event_title": event["title"],
            "capacity": event["capacity"],
            "active_registrations": active_count,
            "registrations": registrations
        })

    # =========================================================================
    # 7. EVENT_REGISTRATION ROUTES (Bridge Table M:N with Capacity Safety)
    # =========================================================================
    @app.route("/api/registrations", methods=["GET"])
    def list_all_registrations():
        student_id = request.args.get('student_id')
        event_id = request.args.get('event_id')

        query = """
            SELECT er.student_id, s.name AS student_name, s.roll_no,
                   er.event_id, e.title AS event_title, e.event_date,
                   er.registered_at, er.attendance_status
            FROM Event_Registration er
            JOIN Student s ON er.student_id = s.student_id
            JOIN Event e ON er.event_id = e.event_id
            WHERE 1=1
        """
        params = []
        if student_id:
            query += " AND er.student_id = ?"
            params.append(student_id)
        if event_id:
            query += " AND er.event_id = ?"
            params.append(event_id)

        query += " ORDER BY er.registered_at DESC;"
        registrations = db.query_db(query, tuple(params))
        return jsonify({"success": True, "count": len(registrations), "registrations": registrations})

    @app.route("/api/registrations/<int:student_id>/<int:event_id>", methods=["GET"])
    def get_registration(student_id, event_id):
        registration = db.query_db("""
            SELECT er.student_id, s.name AS student_name, s.roll_no,
                   er.event_id, e.title AS event_title, e.event_date, e.capacity,
                   er.registered_at, er.attendance_status
            FROM Event_Registration er
            JOIN Student s ON er.student_id = s.student_id
            JOIN Event e ON er.event_id = e.event_id
            WHERE er.student_id = ? AND er.event_id = ?;
        """, (student_id, event_id), one=True)
        if not registration:
            return jsonify({"success": False, "error": "Event registration record not found."}), 404
        return jsonify({"success": True, "registration": registration})

    @app.route("/api/registrations", methods=["POST"])
    def register_for_event():
        """
        Registers a student for an event with atomic capacity check and transaction protection.
        Cancels are safely excluded from capacity.
        """
        data = get_payload()
        student_id = data.get("student_id")
        event_id = data.get("event_id")
        attendance_status = (data.get("attendance_status") or "Registered").strip()

        if student_id is None or event_id is None:
            return jsonify({"success": False, "error": "Required fields: student_id, event_id."}), 400

        try:
            student_id = int(student_id)
            event_id = int(event_id)
        except ValueError:
            return jsonify({"success": False, "error": "student_id and event_id must be integers."}), 400

        if attendance_status not in VALID_ATTENDANCE_STATUSES:
            return jsonify({"success": False, "error": f"Invalid attendance status. Allowed: {VALID_ATTENDANCE_STATUSES}"}), 400

        conn = db.get_db()

        # ATOMIC TRANSACTION: Check capacity + Check prior registration + Insert/Update
        try:
            with conn: # Begins transaction context; auto-commits on success, rolls back on error
                # 1. Verify Student Existence
                student = conn.execute("SELECT student_id, name FROM Student WHERE student_id = ?;", (student_id,)).fetchone()
                if not student:
                    return jsonify({"success": False, "error": f"Student with ID {student_id} does not exist."}), 404

                # 2. Verify Event Existence & Status
                event = conn.execute("SELECT event_id, title, capacity, status FROM Event WHERE event_id = ?;", (event_id,)).fetchone()
                if not event:
                    return jsonify({"success": False, "error": f"Event with ID {event_id} does not exist."}), 404

                if event["status"] == "Cancelled":
                    return jsonify({"success": False, "error": "Cannot register for a cancelled event."}), 400

                # 3. Check if student already has a registration record
                existing = conn.execute(
                    "SELECT attendance_status FROM Event_Registration WHERE student_id = ? AND event_id = ?;",
                    (student_id, event_id)
                ).fetchone()

                if existing and existing["attendance_status"] != "Cancelled":
                    return jsonify({
                        "success": False,
                        "error": f"Student '{student['name']}' is already registered for this event (Status: {existing['attendance_status']})."
                    }), 409

                # 4. CAPACITY CEILING ENFORCEMENT:
                # Count only active attendees (Registered, Attended, Absent). Exclude Cancelled.
                active_count = conn.execute("""
                    SELECT COUNT(*) FROM Event_Registration 
                    WHERE event_id = ? AND attendance_status != 'Cancelled';
                """, (event_id,)).fetchone()[0]

                if active_count >= event["capacity"]:
                    return jsonify({
                        "success": False,
                        "error": f"Event '{event['title']}' is at full capacity ({event['capacity']}/{event['capacity']}). Registration closed."
                    }), 409

                # 5. Insert new registration or reactivate previously cancelled registration
                if existing and existing["attendance_status"] == "Cancelled":
                    conn.execute("""
                        UPDATE Event_Registration
                        SET attendance_status = ?, registered_at = CURRENT_TIMESTAMP
                        WHERE student_id = ? AND event_id = ?;
                    """, (attendance_status, student_id, event_id))
                    msg = f"Re-activated registration for '{student['name']}' in event '{event['title']}'."
                else:
                    conn.execute("""
                        INSERT INTO Event_Registration (student_id, event_id, attendance_status)
                        VALUES (?, ?, ?);
                    """, (student_id, event_id, attendance_status))
                    msg = f"Student '{student['name']}' successfully registered for event '{event['title']}'."

            created = db.query_db("""
                SELECT er.student_id, s.name AS student_name, er.event_id, e.title AS event_title,
                       er.registered_at, er.attendance_status
                FROM Event_Registration er
                JOIN Student s ON er.student_id = s.student_id
                JOIN Event e ON er.event_id = e.event_id
                WHERE er.student_id = ? AND er.event_id = ?;
            """, (student_id, event_id), one=True)
            return jsonify({"success": True, "message": msg, "registration": created}), 201

        except sqlite3.IntegrityError as e:
            return jsonify({"success": False, "error": f"Database integrity error: {e}"}), 400

    @app.route("/api/registrations/<int:student_id>/<int:event_id>", methods=["PUT"])
    def update_registration(student_id, event_id):
        data = get_payload()
        attendance_status = (data.get("attendance_status") or "").strip()

        if not attendance_status:
            return jsonify({"success": False, "error": "Required field: attendance_status."}), 400

        if attendance_status not in VALID_ATTENDANCE_STATUSES:
            return jsonify({"success": False, "error": f"Invalid status. Allowed: {VALID_ATTENDANCE_STATUSES}"}), 400

        conn = db.get_db()
        with conn:
            existing = conn.execute(
                "SELECT attendance_status FROM Event_Registration WHERE student_id = ? AND event_id = ?;",
                (student_id, event_id)
            ).fetchone()

            if not existing:
                return jsonify({"success": False, "error": "Registration record not found."}), 404

            # If switching from Cancelled -> Active, ensure capacity has not filled up in the meantime
            if existing["attendance_status"] == "Cancelled" and attendance_status != "Cancelled":
                event = conn.execute("SELECT title, capacity FROM Event WHERE event_id = ?;", (event_id,)).fetchone()
                active_count = conn.execute("""
                    SELECT COUNT(*) FROM Event_Registration 
                    WHERE event_id = ? AND attendance_status != 'Cancelled';
                """, (event_id,)).fetchone()[0]

                if active_count >= event["capacity"]:
                    return jsonify({
                        "success": False,
                        "error": f"Cannot reactivate registration: Event is at full capacity ({event['capacity']})."
                    }), 409

            conn.execute("""
                UPDATE Event_Registration
                SET attendance_status = ?
                WHERE student_id = ? AND event_id = ?;
            """, (attendance_status, student_id, event_id))

        updated = db.query_db("""
            SELECT er.student_id, s.name AS student_name, er.event_id, e.title AS event_title,
                   er.registered_at, er.attendance_status
            FROM Event_Registration er
            JOIN Student s ON er.student_id = s.student_id
            JOIN Event e ON er.event_id = e.event_id
            WHERE er.student_id = ? AND er.event_id = ?;
        """, (student_id, event_id), one=True)
        return jsonify({"success": True, "message": "Attendance status updated.", "registration": updated})

    @app.route("/api/registrations/<int:student_id>/<int:event_id>", methods=["DELETE"])
    def delete_registration(student_id, event_id):
        conn = db.get_db()
        cursor = conn.execute("DELETE FROM Event_Registration WHERE student_id = ? AND event_id = ?;", (student_id, event_id))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({"success": False, "error": "Registration record not found."}), 404
        return jsonify({"success": True, "message": "Event registration deleted successfully."})

    return app


# Application entry point when run directly
app = create_app()

if __name__ == "__main__":
    # Running on localhost:5000 in debug mode for development
    print("[+] Starting ClubHub Flask server at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)

