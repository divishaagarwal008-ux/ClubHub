-- =====================================================================
-- ClubHub — Student Club and Organisation Management System
-- Coherent Sample Seed Data
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Clean existing data in reverse dependency order for safe re-runs
DELETE FROM Event_Registration;
DELETE FROM Membership;
DELETE FROM Club_Advisor;
DELETE FROM Event;
DELETE FROM Faculty_Advisor;
DELETE FROM Club;
DELETE FROM Student;

-- Reset sqlite_sequence to start IDs from 1
DELETE FROM sqlite_sequence WHERE name IN ('Student', 'Club', 'Faculty_Advisor', 'Event');

-- ---------------------------------------------------------------------
-- 1. Insert Students
-- ---------------------------------------------------------------------
INSERT INTO Student (student_id, name, email, roll_no, branch, year, phone) VALUES
(1, 'Aarav Sharma',     'aarav.sharma@college.edu',    '2024CSE001', 'CSE', 3, '9876543210'),
(2, 'Diya Patel',       'diya.patel@college.edu',      '2024IT015',  'IT',  3, '9876543211'),
(3, 'Rohan Verma',      'rohan.verma@college.edu',     '2025ECE042', 'ECE', 2, '9876543212'),
(4, 'Ananya Iyer',      'ananya.iyer@college.edu',     '2026CSE108', 'CSE', 1, '9876543213'),
(5, 'Kabir Mehta',      'kabir.mehta@college.edu',     '2023ME020',  'ME',  4, '9876543214'),
(6, 'Sneha Mukherjee',  'sneha.m@college.edu',         '2026EE055',  'EE',  1, '9876543215');

-- ---------------------------------------------------------------------
-- 2. Insert Clubs
-- ---------------------------------------------------------------------
INSERT INTO Club (club_id, name, category, description, room_no, status) VALUES
(1, 'CodeForge',       'Technical', 'Competitive programming and software development society.', 'Lab 302', 'Active'),
(2, 'RoboTech Club',   'Technical', 'Robotics, automation, and IoT hardware projects.',           'Mech-105', 'Active'),
(3, 'Natya Manch',     'Cultural',  'Dramatics, street plays (Nukkad Natak), and stage theatre.', 'Audi-02', 'Active'),
(4, 'LitSphere',       'Literary',  'Debating, creative writing, and book discussions.',          'LH-201',  'Active'),
(5, 'Aperture Shutter','Cultural',  'Photography, digital art, and cinematography club.',         'Media-1', 'Inactive');

-- ---------------------------------------------------------------------
-- 3. Insert Faculty Advisors
-- ---------------------------------------------------------------------
INSERT INTO Faculty_Advisor (advisor_id, name, email, department, phone) VALUES
(1, 'Dr. Rajesh Rao',      'rajesh.rao@college.edu',      'Computer Science & Engineering', '9123456780'),
(2, 'Dr. Meenakshi Sundar','meenakshi.s@college.edu',     'Electronics & Communication',     '9123456781'),
(3, 'Prof. Vikram Malhotra','vikram.malhotra@college.edu','Humanities & Social Sciences',   '9123456782'),
(4, 'Dr. Sanjay Gupta',    'sanjay.gupta@college.edu',    'Mechanical Engineering',         '9123456783');

-- ---------------------------------------------------------------------
-- 4. Insert Club Advisors (M:N between Club and Faculty_Advisor)
-- ---------------------------------------------------------------------
INSERT INTO Club_Advisor (club_id, advisor_id) VALUES
(1, 1), -- Dr. Rajesh Rao advises CodeForge
(2, 2), -- Dr. Meenakshi Sundar advises RoboTech
(2, 4), -- Dr. Sanjay Gupta co-advises RoboTech (Demonstrating multiple advisors for one club)
(3, 3), -- Prof. Vikram Malhotra advises Natya Manch
(4, 3); -- Prof. Vikram Malhotra also advises LitSphere (Demonstrating one advisor for multiple clubs)

-- ---------------------------------------------------------------------
-- 5. Insert Memberships (M:N between Student and Club)
-- ---------------------------------------------------------------------
INSERT INTO Membership (student_id, club_id, role, joined_at) VALUES
(1, 1, 'President',      '2024-08-10 10:00:00'), -- Aarav leads CodeForge
(2, 1, 'Vice President', '2024-08-12 11:30:00'), -- Diya VP of CodeForge
(4, 1, 'Member',         '2026-09-01 14:00:00'), -- Ananya 1st yr member in CodeForge
(3, 2, 'Core Member',    '2025-08-15 09:00:00'), -- Rohan in RoboTech
(5, 2, 'President',      '2023-09-05 16:00:00'), -- Kabir leads RoboTech
(2, 3, 'Secretary',      '2024-09-10 12:00:00'), -- Diya is also Secretary in Natya Manch
(3, 3, 'Member',         '2025-09-12 15:30:00'), -- Rohan is also Member in Natya Manch
(6, 4, 'Member',         '2026-09-15 17:00:00'); -- Sneha in LitSphere

-- ---------------------------------------------------------------------
-- 6. Insert Events (1:N from Club to Event)
-- ---------------------------------------------------------------------
INSERT INTO Event (event_id, club_id, title, event_date, venue, capacity, status) VALUES
(1, 1, 'HackForge 2026',         '2026-11-15 09:00:00', 'Central Computing Center', 100, 'Upcoming'),
(2, 1, 'Git & GitHub Bootcamp',  '2026-10-10 14:00:00', 'Seminar Hall 1',           80,  'Completed'),
(3, 2, 'RoboWars Arena',         '2026-11-20 10:00:00', 'Indoor Sports Complex',    150, 'Upcoming'),
(4, 3, 'Nukkad Natak Showcase',  '2026-10-05 16:30:00', 'Open Air Theatre (OAT)',   200, 'Completed'),
(5, 4, 'Parliamentary Debate',   '2026-11-25 11:00:00', 'LH-201',                   50,  'Upcoming');

-- ---------------------------------------------------------------------
-- 7. Insert Event Registrations (M:N between Student and Event)
-- ---------------------------------------------------------------------
INSERT INTO Event_Registration (student_id, event_id, registered_at, attendance_status) VALUES
-- HackForge 2026 (Upcoming)
(1, 1, '2026-10-20 09:15:00', 'Registered'),
(2, 1, '2026-10-20 10:30:00', 'Registered'),
(3, 1, '2026-10-21 14:00:00', 'Registered'),
(4, 1, '2026-10-22 18:20:00', 'Registered'),

-- Git & GitHub Bootcamp (Completed)
(1, 2, '2026-10-01 11:00:00', 'Attended'),
(4, 2, '2026-10-02 12:45:00', 'Attended'),
(6, 2, '2026-10-03 16:10:00', 'Absent'),

-- RoboWars Arena (Upcoming)
(3, 3, '2026-10-25 08:30:00', 'Registered'),
(5, 3, '2026-10-25 09:00:00', 'Registered'),

-- Nukkad Natak Showcase (Completed)
(2, 4, '2026-09-28 10:00:00', 'Attended'),
(3, 4, '2026-09-29 11:15:00', 'Attended'),

-- Parliamentary Debate (Upcoming)
(6, 5, '2026-10-26 15:00:00', 'Registered');

