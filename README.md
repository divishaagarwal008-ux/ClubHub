# ClubHub — Student Club and Organisation Management System

A beginner-friendly College DBMS Mini-Project built with **Python Flask**, **SQLite 3**, **Bootstrap 5**, and **Vanilla JavaScript**.

---

## 1. Project Overview & Architecture

ClubHub streamlines the administration of student clubs, faculty advisors, memberships, events, and registrations in an academic institution.

### Tech Stack
- **Frontend**: HTML5, Bootstrap 5 (CSS & JS), Bootstrap Icons, Custom CSS (`style.css`), Vanilla JavaScript (`app.js`)
- **Backend**: Python 3, Flask 3 (RESTful API & Web Application)
- **Database**: SQLite 3 (using standard `sqlite3` module)
- **Relational Integrity**: Complete Third Normal Form (3NF) relational design with composite primary keys, `ON DELETE CASCADE`, and strict `PRAGMA foreign_keys = ON;` on every database connection.

```text
ClubHub/
├── database/
│   ├── schema.sql          # DDL: Table creation with constraints & checks
│   ├── seed.sql            # DML: Coherent sample college data
│   ├── init_db.py          # Script to create and populate clubhub.db
│   └── clubhub.db          # Generated SQLite database file
├── docs/
│   ├── DATABASE_DESIGN.md  # Detailed schema, FDs, and 1NF/2NF/3NF proofs
│   └── erd.mmd             # Mermaid ER diagram source
├── static/
│   ├── css/
│   │   └── style.css       # Custom university theme styling
│   └── js/
│       └── app.js          # Modular vanilla JS frontend application controller
├── templates/
│   └── index.html          # Responsive Bootstrap 5 SPA dashboard layout
├── tests/
│   ├── verify_db.py        # Schema constraint & cascade test suite (22 tests)
│   ├── test_api.py         # Flask API route & capacity logic test suite (65 tests)
│   └── test_ui_flows.py    # End-to-end user journey test suite (22 tests)
├── app.py                  # Flask web server & REST API application entrypoint
├── db.py                   # Reusable SQLite connection helper with FK enforcement
├── requirements.txt        # Python dependencies (Flask>=3.0.0)
└── README.md               # Setup and execution guide
```

---

## 2. Windows PowerShell Setup & Run Instructions

### Step 1: Open PowerShell and Navigate to the Project
```powershell
cd c:\DivishaData22Dec23\nsut\codes\projects\ClubHub
```

### Step 2: (Optional) Create & Activate Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Initialize and Seed the Database
```powershell
python database/init_db.py
```

### Step 5: Run the Automated Test Suites
ClubHub includes 3 comprehensive automated test suites covering all schema constraints, API endpoints, and complete end-to-end user journeys:
```powershell
# 1. Test database schema constraints & cascades (22 tests)
python tests/verify_db.py

# 2. Test Flask REST API routes & capacity safety (65 tests)
python tests/test_api.py

# 3. Test end-to-end user workflows (22 tests)
python tests/test_ui_flows.py
```

### Step 6: Start the Application
```powershell
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 3. Web UI Screens & Features

1. **Dashboard (`#dashboard`)**:
   - Real-time metric cards: Total Students, Active Clubs, Total Events, Faculty Advisors, and Active Registrations.
   - Upcoming Events table with real-time capacity occupancy progress bars.
   - Club Membership Breakdown table.
2. **Student Directory (`#students`)**:
   - Search bar filtering by Name, Roll Number, Branch, or Email.
   - Add & Edit Student forms with client & server-side validation.
   - Student Profile view displaying their enrolled clubs and roles.
   - Delete confirmation with cascading deletion warnings.
3. **Clubs & Societies (`#clubs`)**:
   - Filter by Category (`Technical`, `Cultural`, `Sports`, etc.) and Status (`Active`, `Inactive`).
   - Add & Edit Club forms.
   - Club Overview view showing assigned faculty mentors, active members, and organized events.
4. **Club Memberships (`#memberships` — M:N)**:
   - Filter memberships by club.
   - Enroll student in a club with assigned role (`President`, `Vice President`, `Secretary`, `Treasurer`, `Core Member`, `Member`).
   - Prevents duplicate memberships at both form and database level.
   - Update role or remove membership.
5. **Event Management (`#events`)**:
   - Filter by organizing club and event status.
   - Schedule Event form with positive capacity validation and venue booking.
   - Real-time seat occupancy badges.
6. **Registrations & Attendance (`#registrations` — M:N)**:
   - Filter registrations by event.
   - Register Student form showing remaining seat count in real-time.
   - **Capacity Protection**: Atomically rejects registrations when an event reaches maximum capacity.
   - **Seat Release**: Marking a student's status as `Cancelled` automatically frees up a seat.
   - Quick attendance status updater (`Registered`, `Attended`, `Absent`, `Cancelled`).
7. **Faculty Advisors & Mentorship (`#advisors`)**:
   - Faculty Advisors directory with Add, Edit, and Delete actions.
   - Mentorship Assignment panel to assign or remove professors from clubs.

---

## 4. Key DBMS Viva Talking Points

1. **Why SQLite & Foreign Key Enforcement**:
   - SQLite disables foreign keys by default for backwards compatibility. ClubHub explicitly executes `PRAGMA foreign_keys = ON;` in `db.py` on **every single connection**, guaranteeing referential integrity.
2. **Third Normal Form (3NF) & BCNF**:
   - All relations are free from partial dependencies (single-attribute primary keys or verified full composite dependencies) and transitive dependencies.
   - For every non-trivial functional dependency $X \to Y$, $X$ is a superkey, satisfying Boyce-Codd Normal Form (BCNF).
3. **Capacity Ceiling Enforcement**:
   - SQLite table constraints cannot execute subqueries across tables. Therefore, `CHECK (capacity > 0)` guarantees validity in `Event`, while the upper bound ($\le \text{capacity}$) is safely enforced in an atomic Python transaction inside `app.py`.
4. **Parameterized SQL Queries**:
   - Every single SQL statement uses `?` parameter placeholders (`db.query_db("SELECT ... WHERE id = ?", (id,))`), completely eliminating SQL Injection vulnerabilities.
5. **Referential Actions**:
   - Deleting a Student cleanly cascades to their memberships and registrations
   - Deleting a Club cascades to its memberships and events
   - Deleting a Faculty Advisor unassigns them from the club while leaving the Club itself intact
