-- =====================================================================
-- ClubHub — Extended Sample Seed Data  (Nov 2026)
-- Covers: multi-JOINs, GROUP BY/HAVING, subqueries, NULLs,
--         orphaned rows, clubs with no events, advisors with no clubs,
--         students with no memberships, capacity overflow edge cases.
-- =====================================================================

PRAGMA foreign_keys = ON;

-- Clean in reverse dependency order
DELETE FROM Event_Registration;
DELETE FROM Membership;
DELETE FROM Club_Advisor;
DELETE FROM Event;
DELETE FROM Faculty_Advisor;
DELETE FROM Club;
DELETE FROM Student;

DELETE FROM sqlite_sequence WHERE name IN ('Student','Club','Faculty_Advisor','Event');

-- =====================================================================
-- 1. STUDENTS  (20 total)
-- =====================================================================
INSERT INTO Student (student_id, name, email, roll_no, branch, year, phone) VALUES
-- Original 6
( 1, 'Aarav Sharma',       'aarav.sharma@college.edu',       '2024CSE001', 'CSE', 3, '9876543210'),
( 2, 'Diya Patel',         'diya.patel@college.edu',         '2024IT015',  'IT',  3, '9876543211'),
( 3, 'Rohan Verma',        'rohan.verma@college.edu',        '2025ECE042', 'ECE', 2, '9876543212'),
( 4, 'Ananya Iyer',        'ananya.iyer@college.edu',        '2026CSE108', 'CSE', 1, '9876543213'),
( 5, 'Kabir Mehta',        'kabir.mehta@college.edu',        '2023ME020',  'ME',  4, '9876543214'),
( 6, 'Sneha Mukherjee',    'sneha.m@college.edu',            '2026EE055',  'EE',  1, '9876543215'),
-- New additions
( 7, 'Arjun Nair',         'arjun.nair@college.edu',         '2025CSE078', 'CSE', 2, '9876543216'),
( 8, 'Priya Desai',        'priya.desai@college.edu',        '2024IT032',  'IT',  3, '9876543217'),
( 9, 'Vikram Singh',       'vikram.singh@college.edu',       '2023ECE011', 'ECE', 4, '9876543218'),
(10, 'Meera Pillai',       'meera.pillai@college.edu',       '2026CSE201', 'CSE', 1, '9876543219'),
(11, 'Siddharth Roy',      'siddharth.roy@college.edu',      '2024ME066',  'ME',  3, '9876543220'),
(12, 'Tanvi Kulkarni',     'tanvi.kulkarni@college.edu',     '2025EE037',  'EE',  2, '9876543221'),
(13, 'Harsh Agarwal',      'harsh.agarwal@college.edu',      '2026IT190',  'IT',  1, '9876543222'),
(14, 'Neha Joshi',         'neha.joshi@college.edu',         '2023CSE009', 'CSE', 4, '9876543223'),
(15, 'Rahul Banerjee',     'rahul.banerjee@college.edu',     '2025ME051',  'ME',  2, '9876543224'),
(16, 'Aishwarya Menon',    'aishwarya.menon@college.edu',    '2024ECE088', 'ECE', 3, '9876543225'),
(17, 'Dev Tripathi',       'dev.tripathi@college.edu',       '2026CSE145', 'CSE', 1, '9876543226'),
(18, 'Simran Kaur',        'simran.kaur@college.edu',        '2025IT063',  'IT',  2, '9876543227'),
-- No-membership / edge-case students
(19, 'Yash Goyal',         'yash.goyal@college.edu',         '2024ME099',  'ME',  3, '9876543228'),  -- no memberships
(20, 'Ritika Sinha',       'ritika.sinha@college.edu',       '2026EE210',  'EE',  1, '9876543229');  -- no memberships, no registrations

-- =====================================================================
-- 2. CLUBS  (9 total — Aperture Shutter kept Inactive; MathSoc: new)
-- =====================================================================
INSERT INTO Club (club_id, name, category, description, room_no, status) VALUES
(1, 'CodeForge',         'Technical', 'Competitive programming and software development society.',  'Lab 302',   'Active'),
(2, 'RoboTech Club',     'Technical', 'Robotics, automation, and IoT hardware projects.',           'Mech-105',  'Active'),
(3, 'Natya Manch',       'Cultural',  'Dramatics, street plays (Nukkad Natak), and stage theatre.', 'Audi-02',   'Active'),
(4, 'LitSphere',         'Literary',  'Debating, creative writing, and book discussions.',           'LH-201',    'Active'),
(5, 'Aperture Shutter',  'Cultural',  'Photography, digital art, and cinematography club.',          'Media-1',   'Inactive'),
(6, 'MathSoc',           'Academic',  'Mathematics olympiad prep, puzzles, and research discussions.','LH-301',   'Active'),
(7, 'Enviro Warriors',   'Social',    'Sustainability, eco-drives, and campus green initiatives.',   'Open Lawn', 'Active'),
(8, 'Cybersec Cell',     'Technical', 'CTF competitions, ethical hacking, and security workshops.',  'Lab 210',   'Active'),
(9, 'MusicBox',          'Cultural',  'Western and Hindustani music, bands, and open-mic nights.',   'Audi-01',   'Active');
-- Note: Club 9 (MusicBox) has NO events → tests LEFT JOIN / IS NULL

-- =====================================================================
-- 3. FACULTY ADVISORS  (7 total)
-- =====================================================================
INSERT INTO Faculty_Advisor (advisor_id, name, email, department, phone) VALUES
(1, 'Dr. Rajesh Rao',         'rajesh.rao@college.edu',         'Computer Science & Engineering',  '9123456780'),
(2, 'Dr. Meenakshi Sundar',   'meenakshi.s@college.edu',        'Electronics & Communication',      '9123456781'),
(3, 'Prof. Vikram Malhotra',  'vikram.malhotra@college.edu',    'Humanities & Social Sciences',    '9123456782'),
(4, 'Dr. Sanjay Gupta',       'sanjay.gupta@college.edu',       'Mechanical Engineering',           '9123456783'),
(5, 'Dr. Priti Nanda',        'priti.nanda@college.edu',        'Mathematics',                      '9123456784'),
(6, 'Dr. Anil Khare',         'anil.khare@college.edu',         'Computer Science & Engineering',  '9123456785'),
(7, 'Prof. Sunita Arora',     'sunita.arora@college.edu',       'Environmental Science',            '9123456786');
-- Note: Advisor 7 (Prof. Sunita Arora) is NOT assigned to any club → tests LEFT JOIN / IS NULL

-- =====================================================================
-- 4. CLUB ADVISORS  (M:N)
-- =====================================================================
INSERT INTO Club_Advisor (club_id, advisor_id) VALUES
(1, 1), -- Dr. Rao → CodeForge
(2, 2), -- Dr. Meenakshi → RoboTech
(2, 4), -- Dr. Sanjay co-advises RoboTech
(3, 3), -- Prof. Vikram → Natya Manch
(4, 3), -- Prof. Vikram also → LitSphere (one advisor, two clubs)
(5, 1), -- Dr. Rao → Aperture Shutter (Inactive club, still has advisor)
(6, 5), -- Dr. Priti Nanda → MathSoc
(7, 7), -- Prof. Sunita → Enviro Warriors (she IS assigned here)
(8, 6), -- Dr. Anil Khare → Cybersec Cell
(9, 3); -- Prof. Vikram → MusicBox (he advises 3 clubs total — good for HAVING COUNT)

-- =====================================================================
-- 5. MEMBERSHIPS  (30 total)
-- =====================================================================
INSERT INTO Membership (student_id, club_id, role, joined_at) VALUES
-- CodeForge (club 1)
( 1, 1, 'President',        '2024-08-10 10:00:00'),
( 2, 1, 'Vice President',   '2024-08-12 11:30:00'),
( 7, 1, 'Core Member',      '2025-08-20 09:00:00'),
( 4, 1, 'Member',           '2026-09-01 14:00:00'),
(14, 1, 'Member',           '2023-09-15 10:00:00'),  -- 4th year in club

-- RoboTech (club 2)
( 5, 2, 'President',        '2023-09-05 16:00:00'),
( 3, 2, 'Core Member',      '2025-08-15 09:00:00'),
(11, 2, 'Secretary',        '2024-09-01 11:00:00'),
(15, 2, 'Member',           '2025-09-10 14:00:00'),
(16, 2, 'Member',           '2024-09-12 13:00:00'),

-- Natya Manch (club 3)
( 2, 3, 'Secretary',        '2024-09-10 12:00:00'),
( 3, 3, 'Member',           '2025-09-12 15:30:00'),
(12, 3, 'Core Member',      '2025-08-22 10:00:00'),
(18, 3, 'Member',           '2025-09-15 16:00:00'),

-- LitSphere (club 4)
( 6, 4, 'Member',           '2026-09-15 17:00:00'),
( 8, 4, 'President',        '2024-08-11 10:00:00'),
(13, 4, 'Member',           '2026-09-20 12:00:00'),
(10, 4, 'Member',           '2026-09-18 11:30:00'),

-- MathSoc (club 6)
( 1, 6, 'Core Member',      '2024-09-01 09:00:00'),  -- Aarav in 2 clubs
( 7, 6, 'Vice President',   '2025-08-25 10:00:00'),
( 9, 6, 'President',        '2023-09-10 08:00:00'),
(17, 6, 'Member',           '2026-09-22 14:00:00'),

-- Enviro Warriors (club 7)
(12, 7, 'President',        '2025-08-20 09:00:00'),  -- Tanvi in 2 clubs
(15, 7, 'Member',           '2025-09-05 11:00:00'),  -- Rahul in 2 clubs
( 6, 7, 'Member',           '2026-09-16 10:00:00'),  -- Sneha in 2 clubs

-- Cybersec Cell (club 8)
(14, 8, 'President',        '2023-08-30 10:00:00'),  -- Neha in 2 clubs
( 7, 8, 'Core Member',      '2025-08-28 09:30:00'),  -- Arjun in 3 clubs!
( 4, 8, 'Member',           '2026-09-05 13:00:00'),  -- Ananya in 3 clubs
(16, 8, 'Member',           '2024-09-08 14:00:00');  -- Aishwarya in 2 clubs
-- MusicBox (club 9) has NO memberships → edge case for aggregation

-- =====================================================================
-- 6. EVENTS  (12 total)
-- =====================================================================
INSERT INTO Event (event_id, club_id, title, event_date, venue, capacity, status) VALUES
-- CodeForge
( 1, 1, 'HackForge 2026',          '2026-11-15 09:00:00', 'Central Computing Center',  100, 'Upcoming'),
( 2, 1, 'Git & GitHub Bootcamp',   '2026-10-10 14:00:00', 'Seminar Hall 1',             80, 'Completed'),
( 3, 1, 'CP Marathon – Round 1',   '2026-09-20 10:00:00', 'Lab 302',                    40, 'Completed'),

-- RoboTech
( 4, 2, 'RoboWars Arena',          '2026-11-20 10:00:00', 'Indoor Sports Complex',     150, 'Upcoming'),
( 5, 2, 'IoT Workshop',            '2026-10-18 13:00:00', 'Mech-105',                   30, 'Completed'),

-- Natya Manch
( 6, 3, 'Nukkad Natak Showcase',   '2026-10-05 16:30:00', 'Open Air Theatre (OAT)',    200, 'Completed'),
( 7, 3, 'Annual Drama Festival',   '2026-12-05 17:00:00', 'Main Auditorium',            500, 'Upcoming'),

-- LitSphere
( 8, 4, 'Parliamentary Debate',    '2026-11-25 11:00:00', 'LH-201',                     50, 'Upcoming'),
( 9, 4, 'Creative Writing Sprint', '2026-10-28 14:00:00', 'LH-201',                     25, 'Completed'),

-- MathSoc
(10, 6, 'Proof-a-thon',            '2026-11-10 10:00:00', 'LH-301',                     60, 'Upcoming'),

-- Enviro Warriors
(11, 7, 'Campus Clean Drive',      '2026-10-22 07:00:00', 'Main Campus',               300, 'Completed'),

-- Cybersec Cell
(12, 8, 'CTF Open 2026',           '2026-11-30 09:00:00', 'Lab 210',                    80, 'Upcoming');
-- Club 9 (MusicBox) intentionally has NO events

-- =====================================================================
-- 7. EVENT REGISTRATIONS  (35 total)
-- Tests: students registering for events outside their own club,
--        near-full events, absent students, cross-club participation
-- =====================================================================
INSERT INTO Event_Registration (student_id, event_id, registered_at, attendance_status) VALUES

-- HackForge 2026 (event 1, cap 100, Upcoming)
( 1, 1, '2026-10-20 09:15:00', 'Registered'),
( 2, 1, '2026-10-20 10:30:00', 'Registered'),
( 3, 1, '2026-10-21 14:00:00', 'Registered'),  -- ECE student in CSE event
( 4, 1, '2026-10-22 18:20:00', 'Registered'),
( 7, 1, '2026-10-23 11:00:00', 'Registered'),
(10, 1, '2026-10-24 12:00:00', 'Registered'),  -- 1st year registered

-- Git & GitHub Bootcamp (event 2, cap 80, Completed)
( 1, 2, '2026-10-01 11:00:00', 'Attended'),
( 4, 2, '2026-10-02 12:45:00', 'Attended'),
( 6, 2, '2026-10-03 16:10:00', 'Absent'),      -- edge: absent
( 8, 2, '2026-10-04 09:00:00', 'Attended'),
(14, 2, '2026-10-04 10:00:00', 'Attended'),

-- CP Marathon – Round 1 (event 3, cap 40, Completed)
( 1, 3, '2026-09-15 08:00:00', 'Attended'),
( 7, 3, '2026-09-15 08:30:00', 'Attended'),
( 9, 3, '2026-09-16 09:00:00', 'Absent'),      -- MathSoc member tried CP
(14, 3, '2026-09-16 09:30:00', 'Attended'),

-- RoboWars Arena (event 4, cap 150, Upcoming)
( 3, 4, '2026-10-25 08:30:00', 'Registered'),
( 5, 4, '2026-10-25 09:00:00', 'Registered'),
(11, 4, '2026-10-26 10:00:00', 'Registered'),
(16, 4, '2026-10-27 11:00:00', 'Registered'),
(15, 4, '2026-10-28 12:00:00', 'Registered'),

-- IoT Workshop (event 5, cap 30, Completed)
( 3, 5, '2026-10-12 09:00:00', 'Attended'),
( 5, 5, '2026-10-12 09:30:00', 'Attended'),
(12, 5, '2026-10-13 10:00:00', 'Attended'),   -- cross-club: EE student

-- Nukkad Natak Showcase (event 6, cap 200, Completed)
( 2, 6, '2026-09-28 10:00:00', 'Attended'),
( 3, 6, '2026-09-29 11:15:00', 'Attended'),
(18, 6, '2026-09-30 12:00:00', 'Attended'),

-- Creative Writing Sprint (event 9, cap 25, Completed)
( 6, 9, '2026-10-20 09:00:00', 'Attended'),
( 8, 9, '2026-10-20 09:30:00', 'Attended'),
(13, 9, '2026-10-21 10:00:00', 'Absent'),     -- registered but absent

-- Parliamentary Debate (event 8, cap 50, Upcoming)
( 6, 8, '2026-10-26 15:00:00', 'Registered'),
( 8, 8, '2026-10-27 16:00:00', 'Registered'),
( 2, 8, '2026-10-28 10:00:00', 'Registered'),  -- Diya: IT, cross-club

-- Proof-a-thon (event 10, cap 60, Upcoming)
( 1,10, '2026-10-30 08:00:00', 'Registered'),  -- Aarav joins MathSoc event too
( 7,10, '2026-10-30 08:30:00', 'Registered'),
( 9,10, '2026-10-30 09:00:00', 'Registered'),

-- CTF Open 2026 (event 12, cap 80, Upcoming)
(14,12, '2026-10-31 10:00:00', 'Registered'),
( 4,12, '2026-10-31 11:00:00', 'Registered'),
( 7,12, '2026-10-31 12:00:00', 'Registered');
-- Annual Drama Festival (event 7) has 0 registrations → edge case
-- Campus Clean Drive (event 11) has 0 registrations → edge case

-- =====================================================================
-- QUICK TEST QUERIES (run these to verify the data)
-- =====================================================================

-- Q1: Total students per club (including clubs with 0 members)
-- SELECT c.name, COUNT(m.student_id) AS member_count
-- FROM Club c LEFT JOIN Membership m ON c.club_id = m.club_id
-- GROUP BY c.club_id ORDER BY member_count DESC;

-- Q2: Students who are members of MORE THAN ONE club
-- SELECT s.name, COUNT(m.club_id) AS club_count
-- FROM Student s JOIN Membership m ON s.student_id = m.student_id
-- GROUP BY s.student_id HAVING club_count > 1;

-- Q3: Clubs with no events at all
-- SELECT c.name FROM Club c
-- LEFT JOIN Event e ON c.club_id = e.club_id
-- WHERE e.event_id IS NULL;

-- Q4: Faculty advisors mentoring more than one club
-- SELECT fa.name, COUNT(ca.club_id) AS clubs_advised
-- FROM Faculty_Advisor fa JOIN Club_Advisor ca ON fa.advisor_id = ca.advisor_id
-- GROUP BY fa.advisor_id HAVING clubs_advised > 1;

-- Q5: Students with no club membership
-- SELECT s.name FROM Student s
-- LEFT JOIN Membership m ON s.student_id = m.student_id
-- WHERE m.club_id IS NULL;

-- Q6: Events sorted by registration count DESC
-- SELECT e.title, COUNT(er.student_id) AS registrations
-- FROM Event e LEFT JOIN Event_Registration er ON e.event_id = er.event_id
-- GROUP BY e.event_id ORDER BY registrations DESC;

-- Q7: Attendance rate for completed events
-- SELECT e.title,
--        SUM(CASE WHEN er.attendance_status='Attended' THEN 1 ELSE 0 END) AS attended,
--        COUNT(er.student_id) AS total,
--        ROUND(100.0 * SUM(CASE WHEN er.attendance_status='Attended' THEN 1 ELSE 0 END)
--              / COUNT(er.student_id), 1) AS pct
-- FROM Event e JOIN Event_Registration er ON e.event_id = er.event_id
-- WHERE e.status = 'Completed'
-- GROUP BY e.event_id;

-- Q8: Cross-club participation (student registered for event not of their club)
-- SELECT s.name, c_membership.name AS member_of, c_event.name AS event_club
-- FROM Event_Registration er
-- JOIN Student s ON er.student_id = s.student_id
-- JOIN Event e ON er.event_id = e.event_id
-- JOIN Club c_event ON e.club_id = c_event.club_id
-- LEFT JOIN Membership m ON er.student_id = m.student_id AND m.club_id = e.club_id
-- JOIN Club c_membership ON m.club_id = c_membership.club_id
-- WHERE m.membership_id IS NULL;

-- Q9: Faculty advisor NOT assigned to any club
-- SELECT fa.name FROM Faculty_Advisor fa
-- LEFT JOIN Club_Advisor ca ON fa.advisor_id = ca.advisor_id
-- WHERE ca.club_id IS NULL;

-- Q10: Top 3 most active students (by events registered)
-- SELECT s.name, COUNT(er.event_id) AS events
-- FROM Student s JOIN Event_Registration er ON s.student_id = er.student_id
-- GROUP BY s.student_id ORDER BY events DESC LIMIT 3;
