-- =====================================================================
-- ClubHub — Student Club and Organisation Management System
-- Database Schema (SQLite 3)
-- =====================================================================

-- Enforce Foreign Key Constraints
PRAGMA foreign_keys = ON;

-- 1. Student Table
-- Represents individual college students enrolled in the institution.
CREATE TABLE IF NOT EXISTS Student (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    roll_no TEXT NOT NULL UNIQUE,
    branch TEXT NOT NULL,
    year INTEGER NOT NULL CHECK (year BETWEEN 1 AND 4),
    phone TEXT CHECK (phone IS NULL OR length(phone) >= 10)
);

-- 2. Club Table
-- Represents student-run societies, technical clubs, and cultural clubs.
CREATE TABLE IF NOT EXISTS Club (
    club_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('Technical', 'Cultural', 'Sports', 'Literary', 'Social', 'Academic')),
    description TEXT,
    room_no TEXT,
    status TEXT NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive'))
);

-- 3. Faculty_Advisor Table
-- Represents college professors or faculty members who guide clubs.
CREATE TABLE IF NOT EXISTS Faculty_Advisor (
    advisor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    phone TEXT CHECK (phone IS NULL OR length(phone) >= 10)
);

-- 4. Club_Advisor Table (Bridge / Junction Table)
-- Resolves the M:N relationship between Club and Faculty_Advisor.
CREATE TABLE IF NOT EXISTS Club_Advisor (
    club_id INTEGER NOT NULL,
    advisor_id INTEGER NOT NULL,
    PRIMARY KEY (club_id, advisor_id),
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE,
    FOREIGN KEY (advisor_id) REFERENCES Faculty_Advisor(advisor_id) ON DELETE CASCADE
);

-- 5. Membership Table (Bridge / Junction Table)
-- Resolves the M:N relationship between Student and Club.
CREATE TABLE IF NOT EXISTS Membership (
    student_id INTEGER NOT NULL,
    club_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'Member' CHECK (role IN ('President', 'Vice President', 'Secretary', 'Treasurer', 'Core Member', 'Member')),
    joined_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    PRIMARY KEY (student_id, club_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE
);

-- 6. Event Table
-- Represents events organised by clubs. (1:N from Club to Event).
CREATE TABLE IF NOT EXISTS Event (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    club_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    event_date TEXT NOT NULL,
    venue TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    status TEXT NOT NULL DEFAULT 'Upcoming' CHECK (status IN ('Upcoming', 'Ongoing', 'Completed', 'Cancelled')),
    FOREIGN KEY (club_id) REFERENCES Club(club_id) ON DELETE CASCADE
);

-- 7. Event_Registration Table (Bridge / Junction Table)
-- Resolves the M:N relationship between Student and Event.
CREATE TABLE IF NOT EXISTS Event_Registration (
    student_id INTEGER NOT NULL,
    event_id INTEGER NOT NULL,
    registered_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
    attendance_status TEXT NOT NULL DEFAULT 'Registered' CHECK (attendance_status IN ('Registered', 'Attended', 'Absent', 'Cancelled')),
    PRIMARY KEY (student_id, event_id),
    FOREIGN KEY (student_id) REFERENCES Student(student_id) ON DELETE CASCADE,
    FOREIGN KEY (event_id) REFERENCES Event(event_id) ON DELETE CASCADE
);

-- 8. Capacity Enforcement Triggers
-- A CHECK constraint cannot count rows in another table, so the event capacity
-- ceiling is enforced with triggers. Cancelled registrations do not occupy a seat.

-- Block a new active registration when the event is already full.
CREATE TRIGGER IF NOT EXISTS trg_registration_capacity_insert
BEFORE INSERT ON Event_Registration
WHEN NEW.attendance_status != 'Cancelled'
 AND (SELECT COUNT(*) FROM Event_Registration
      WHERE event_id = NEW.event_id AND attendance_status != 'Cancelled')
     >= (SELECT capacity FROM Event WHERE event_id = NEW.event_id)
BEGIN
    SELECT RAISE(ABORT, 'Event is at full capacity');
END;

-- Block reactivating a cancelled registration (or moving it to another event) when the event is full.
CREATE TRIGGER IF NOT EXISTS trg_registration_capacity_update
BEFORE UPDATE OF attendance_status, event_id ON Event_Registration
WHEN NEW.attendance_status != 'Cancelled'
 AND (OLD.attendance_status = 'Cancelled' OR OLD.event_id != NEW.event_id)
 AND (SELECT COUNT(*) FROM Event_Registration
      WHERE event_id = NEW.event_id AND attendance_status != 'Cancelled')
     >= (SELECT capacity FROM Event WHERE event_id = NEW.event_id)
BEGIN
    SELECT RAISE(ABORT, 'Event is at full capacity');
END;

-- Block lowering an event's capacity below its current number of active registrations.
CREATE TRIGGER IF NOT EXISTS trg_event_capacity_update
BEFORE UPDATE OF capacity ON Event
WHEN NEW.capacity < (SELECT COUNT(*) FROM Event_Registration
                     WHERE event_id = NEW.event_id AND attendance_status != 'Cancelled')
BEGIN
    SELECT RAISE(ABORT, 'Capacity cannot be lower than the number of active registrations');
END;

