/**
 * ClubHub — Student Club and Organisation Management System
 * Frontend Application Controller (app.js)
 * Clean, lightweight, modular vanilla JavaScript for easy viva explanation.
 */

// =============================================================================
// GLOBAL STATE & INITIALIZATION
// =============================================================================
let currentSection = 'dashboard';
let cachedStudents = [];
let cachedClubs = [];
let cachedEvents = [];
let cachedAdvisors = [];

// Bootstrap Modal Instances
let modals = {};

document.addEventListener('DOMContentLoaded', () => {
    initModals();
    initNavigation();
    initEventListeners();

    // Initial load: parse URL hash or default to dashboard
    const initialHash = window.location.hash.replace('#', '') || 'dashboard';
    navigateSection(initialHash);
});

function initModals() {
    const modalIds = [
        'studentModal', 'studentDetailModal',
        'clubModal', 'clubDetailModal',
        'membershipModal', 'eventModal',
        'registrationModal', 'advisorModal',
        'assignAdvisorModal', 'deleteConfirmModal'
    ];
    modalIds.forEach(id => {
        const el = document.getElementById(id);
        if (el && window.bootstrap) {
            modals[id] = new bootstrap.Modal(el);
        }
    });
}

function initNavigation() {
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.getAttribute('data-section');
            navigateSection(section);
            // On mobile devices, close the sidebar after navigation
            const sidebar = document.getElementById('sidebar');
            if (sidebar.classList.contains('show')) {
                sidebar.classList.remove('show');
            }
        });
    });

    // Mobile sidebar toggle
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('show');
        });
    }

    // Refresh button
    const refreshBtn = document.getElementById('btn-refresh-data');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            loadSectionData(currentSection);
            showAlert('Data refreshed successfully.', 'info');
        });
    }
}

function initEventListeners() {
    // Student Search with debouncing
    const searchInput = document.getElementById('student-search-input');
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                loadStudents(searchInput.value.trim());
            }, 300);
        });

        document.getElementById('btn-clear-student-search').addEventListener('click', () => {
            searchInput.value = '';
            loadStudents();
        });
    }

    // Club Filters
    const clubCatFilter = document.getElementById('club-filter-category');
    const clubStatusFilter = document.getElementById('club-filter-status');
    if (clubCatFilter && clubStatusFilter) {
        clubCatFilter.addEventListener('change', () => loadClubs());
        clubStatusFilter.addEventListener('change', () => loadClubs());
    }

    // Membership Club Filter
    const memClubFilter = document.getElementById('membership-filter-club');
    if (memClubFilter) {
        memClubFilter.addEventListener('change', () => loadMemberships());
    }

    // Event Filters
    const evtClubFilter = document.getElementById('event-filter-club');
    const evtStatusFilter = document.getElementById('event-filter-status');
    if (evtClubFilter && evtStatusFilter) {
        evtClubFilter.addEventListener('change', () => loadEvents());
        evtStatusFilter.addEventListener('change', () => loadEvents());
    }

    // Registration Event Filter
    const regEvtFilter = document.getElementById('registration-filter-event');
    if (regEvtFilter) {
        regEvtFilter.addEventListener('change', () => loadRegistrations());
    }
}

// =============================================================================
// NAVIGATION & VIEW SWITCHING
// =============================================================================
function navigateSection(sectionName) {
    const validSections = ['dashboard', 'students', 'clubs', 'memberships', 'events', 'registrations', 'advisors'];
    if (!validSections.includes(sectionName)) {
        sectionName = 'dashboard';
    }

    currentSection = sectionName;
    window.location.hash = sectionName;

    // Update Sidebar active state
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        if (link.getAttribute('data-section') === sectionName) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Update Page Header Title
    const titleMap = {
        'dashboard': 'Dashboard & Overview',
        'students': 'Student Directory',
        'clubs': 'Clubs & Societies',
        'memberships': 'Club Memberships (M:N)',
        'events': 'Event Management',
        'registrations': 'Event Registrations & Attendance',
        'advisors': 'Faculty Advisors & Mentorship'
    };
    document.getElementById('page-title').textContent = titleMap[sectionName] || 'Dashboard';

    // Toggle Content Sections
    document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.add('d-none');
    });
    const targetSection = document.getElementById(`section-${sectionName}`);
    if (targetSection) {
        targetSection.classList.remove('d-none');
    }

    // Load data for the selected section
    loadSectionData(sectionName);
}

function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'students':
            loadStudents();
            break;
        case 'clubs':
            loadClubs();
            break;
        case 'memberships':
            populateClubFilterDropdown('membership-filter-club');
            loadMemberships();
            break;
        case 'events':
            populateClubFilterDropdown('event-filter-club');
            loadEvents();
            break;
        case 'registrations':
            populateEventFilterDropdown('registration-filter-event');
            loadRegistrations();
            break;
        case 'advisors':
            loadAdvisors();
            break;
    }
}

// =============================================================================
// ALERT NOTIFICATION SYSTEM
// =============================================================================
function showAlert(message, type = 'success') {
    const container = document.getElementById('alert-container');
    if (!container) return;

    const alertId = 'alert-' + Date.now();
    const iconMap = {
        'success': 'bi-check-circle-fill',
        'danger': 'bi-exclamation-triangle-fill',
        'warning': 'bi-exclamation-circle-fill',
        'info': 'bi-info-circle-fill'
    };
    const icon = iconMap[type] || 'bi-info-circle-fill';

    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-toast alert-dismissible fade show d-flex align-items-center gap-2 py-2 px-3" role="alert">
            <i class="bi ${icon} fs-5"></i>
            <div class="flex-grow-1 small">${escapeHtml(message)}</div>
            <button type="button" class="btn-close btn-sm p-2" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', alertHtml);

    // Auto dismiss after 4.5 seconds
    setTimeout(() => {
        const el = document.getElementById(alertId);
        if (el && window.bootstrap) {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
            bsAlert.close();
        }
    }, 4500);
}

function showDeleteConfirm(message, onConfirm) {
    document.getElementById('delete-confirm-message').textContent = message;
    const confirmBtn = document.getElementById('btn-confirm-delete');
    
    // Replace element to clear old event listeners
    const newBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

    newBtn.addEventListener('click', async () => {
        if (modals['deleteConfirmModal']) {
            modals['deleteConfirmModal'].hide();
        }
        await onConfirm();
    });

    if (modals['deleteConfirmModal']) {
        modals['deleteConfirmModal'].show();
    }
}

// =============================================================================
// 1. DASHBOARD CONTROLLER
// =============================================================================
async function loadDashboard() {
    try {
        const res = await fetch('/api/dashboard');
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        // Metrics
        document.getElementById('dash-students').textContent = data.metrics.total_students;
        document.getElementById('dash-clubs').textContent = data.metrics.total_clubs;
        document.getElementById('dash-events').textContent = data.metrics.total_events;
        document.getElementById('dash-advisors').textContent = data.metrics.total_faculty_advisors;
        document.getElementById('dash-registrations').textContent = data.metrics.total_active_registrations;

        // Upcoming Events Table
        const evtTbody = document.getElementById('dash-upcoming-events-tbody');
        if (data.upcoming_events.length === 0) {
            evtTbody.innerHTML = `<tr><td colspan="5" class="empty-state py-4"><i class="bi bi-calendar-x"></i>No upcoming events scheduled.</td></tr>`;
        } else {
            evtTbody.innerHTML = data.upcoming_events.map(e => {
                const pct = Math.min(100, Math.round((e.active_registrations / e.capacity) * 100));
                const barColor = pct >= 90 ? 'bg-danger' : (pct >= 60 ? 'bg-warning' : 'bg-success');
                return `
                    <tr>
                        <td><span class="fw-bold">${escapeHtml(e.title)}</span></td>
                        <td><span class="badge bg-light text-dark border">${escapeHtml(e.club_name)}</span></td>
                        <td><small class="text-muted"><i class="bi bi-clock me-1"></i>${escapeHtml(e.event_date)}</small></td>
                        <td><small>${escapeHtml(e.venue)}</small></td>
                        <td style="min-width: 150px;">
                            <div class="d-flex justify-content-between small mb-1">
                                <span>${e.active_registrations} / ${e.capacity}</span>
                                <span class="fw-semibold">${pct}%</span>
                            </div>
                            <div class="capacity-bar">
                                <div class="capacity-fill ${barColor}" style="width: ${pct}%;"></div>
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');
        }

        // Clubs Overview Table
        const clubsTbody = document.getElementById('dash-clubs-tbody');
        if (data.club_membership_counts.length === 0) {
            clubsTbody.innerHTML = `<tr><td colspan="4" class="empty-state py-4"><i class="bi bi-building"></i>No clubs registered.</td></tr>`;
        } else {
            clubsTbody.innerHTML = data.club_membership_counts.map(c => `
                <tr>
                    <td><span class="fw-bold">${escapeHtml(c.name)}</span></td>
                    <td><span class="badge bg-secondary-subtle text-secondary border">${escapeHtml(c.category)}</span></td>
                    <td>${getStatusBadge(c.status)}</td>
                    <td><span class="badge bg-primary rounded-pill px-2 py-1">${c.member_count} members</span></td>
                </tr>
            `).join('');
        }
    } catch (err) {
        showAlert('Failed to load dashboard: ' + err.message, 'danger');
    }
}

// =============================================================================
// 2. STUDENTS CONTROLLER
// =============================================================================
async function loadStudents(query = '') {
    const tbody = document.getElementById('students-tbody');
    try {
        const url = query ? `/api/students?q=${encodeURIComponent(query)}` : '/api/students';
        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        cachedStudents = data.students;

        if (data.students.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="empty-state py-4"><i class="bi bi-people"></i>No students found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.students.map(s => `
            <tr>
                <td><small class="text-muted">#${s.student_id}</small></td>
                <td><span class="fw-bold">${escapeHtml(s.name)}</span></td>
                <td><code>${escapeHtml(s.roll_no)}</code></td>
                <td><span class="badge bg-light text-dark border">${escapeHtml(s.branch)}</span></td>
                <td>Year ${s.year}</td>
                <td><small class="text-muted">${escapeHtml(s.email)}</small></td>
                <td><small>${escapeHtml(s.phone || '—')}</small></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-info me-1" onclick="viewStudentDetails(${s.student_id})" title="View Profile">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openStudentModal(${s.student_id})" title="Edit Student">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteStudent(${s.student_id}, '${escapeQuote(s.name)}')" title="Delete Student">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-danger text-center py-3">Error loading students: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function openStudentModal(studentId = null) {
    const form = document.getElementById('studentForm');
    form.reset();
    document.getElementById('student-form-id').value = '';

    if (studentId) {
        const student = cachedStudents.find(s => s.student_id === studentId);
        if (student) {
            document.getElementById('studentModalTitle').textContent = 'Edit Student';
            document.getElementById('student-form-id').value = student.student_id;
            document.getElementById('student-name').value = student.name;
            document.getElementById('student-roll').value = student.roll_no;
            document.getElementById('student-branch').value = student.branch;
            document.getElementById('student-year').value = student.year;
            document.getElementById('student-phone').value = student.phone || '';
            document.getElementById('student-email').value = student.email;
        }
    } else {
        document.getElementById('studentModalTitle').textContent = 'Add Student';
    }

    if (modals['studentModal']) modals['studentModal'].show();
}

async function handleStudentFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('student-form-id').value;
    const payload = {
        name: document.getElementById('student-name').value.trim(),
        roll_no: document.getElementById('student-roll').value.trim(),
        branch: document.getElementById('student-branch').value.trim(),
        year: parseInt(document.getElementById('student-year').value),
        phone: document.getElementById('student-phone').value.trim() || null,
        email: document.getElementById('student-email').value.trim()
    };

    try {
        const url = id ? `/api/students/${id}` : '/api/students';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['studentModal']) modals['studentModal'].hide();
        showAlert(data.message || 'Student saved successfully.', 'success');
        loadStudents();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function deleteStudent(id, name) {
    showDeleteConfirm(
        `Are you sure you want to delete student "${name}"? All associated club memberships and event registrations will also be removed.`,
        async () => {
            try {
                const res = await fetch(`/api/students/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadStudents();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

async function viewStudentDetails(studentId) {
    try {
        const res = await fetch(`/api/students/${studentId}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);
        const s = data.student;

        document.getElementById('sd-name').textContent = s.name;
        document.getElementById('sd-roll').textContent = s.roll_no;
        document.getElementById('sd-branch-year').textContent = `${s.branch} (Year ${s.year})`;
        document.getElementById('sd-email').textContent = s.email;
        document.getElementById('sd-phone').textContent = s.phone || 'Not provided';

        // Load Clubs
        const clubsRes = await fetch(`/api/students/${studentId}/clubs`);
        const clubsData = await clubsRes.json();
        const tbody = document.getElementById('sd-clubs-tbody');

        if (clubsData.clubs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-muted text-center py-3">Student has not joined any clubs.</td></tr>`;
        } else {
            tbody.innerHTML = clubsData.clubs.map(c => `
                <tr>
                    <td class="fw-bold">${escapeHtml(c.name)}</td>
                    <td><span class="badge bg-light text-dark border">${escapeHtml(c.category)}</span></td>
                    <td>${getRoleBadge(c.role)}</td>
                    <td><small class="text-muted">${escapeHtml(c.joined_at)}</small></td>
                </tr>
            `).join('');
        }

        if (modals['studentDetailModal']) modals['studentDetailModal'].show();
    } catch (err) {
        showAlert('Could not load student profile: ' + err.message, 'danger');
    }
}

// =============================================================================
// 3. CLUBS CONTROLLER
// =============================================================================
async function loadClubs() {
    const tbody = document.getElementById('clubs-tbody');
    try {
        const cat = document.getElementById('club-filter-category').value;
        const stat = document.getElementById('club-filter-status').value;
        let url = '/api/clubs?';
        if (cat) url += `category=${encodeURIComponent(cat)}&`;
        if (stat) url += `status=${encodeURIComponent(stat)}&`;

        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        cachedClubs = data.clubs;

        if (data.clubs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="empty-state py-4"><i class="bi bi-building"></i>No clubs found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.clubs.map(c => `
            <tr>
                <td><small class="text-muted">#${c.club_id}</small></td>
                <td><span class="fw-bold">${escapeHtml(c.name)}</span></td>
                <td><span class="badge bg-secondary-subtle text-secondary border">${escapeHtml(c.category)}</span></td>
                <td><small>${escapeHtml(c.room_no || '—')}</small></td>
                <td><small class="text-muted text-truncate d-inline-block" style="max-width: 250px;">${escapeHtml(c.description || '—')}</small></td>
                <td>${getStatusBadge(c.status)}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-info me-1" onclick="viewClubDetails(${c.club_id})" title="View Details">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openClubModal(${c.club_id})" title="Edit Club">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteClub(${c.club_id}, '${escapeQuote(c.name)}')" title="Delete Club">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-danger text-center py-3">Error loading clubs: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function openClubModal(clubId = null) {
    const form = document.getElementById('clubForm');
    form.reset();
    document.getElementById('club-form-id').value = '';

    if (clubId) {
        const club = cachedClubs.find(c => c.club_id === clubId);
        if (club) {
            document.getElementById('clubModalTitle').textContent = 'Edit Club';
            document.getElementById('club-form-id').value = club.club_id;
            document.getElementById('club-name').value = club.name;
            document.getElementById('club-category').value = club.category;
            document.getElementById('club-status').value = club.status;
            document.getElementById('club-room').value = club.room_no || '';
            document.getElementById('club-desc').value = club.description || '';
        }
    } else {
        document.getElementById('clubModalTitle').textContent = 'Add Club';
    }

    if (modals['clubModal']) modals['clubModal'].show();
}

async function handleClubFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('club-form-id').value;
    const payload = {
        name: document.getElementById('club-name').value.trim(),
        category: document.getElementById('club-category').value,
        status: document.getElementById('club-status').value,
        room_no: document.getElementById('club-room').value.trim() || null,
        description: document.getElementById('club-desc').value.trim() || null
    };

    try {
        const url = id ? `/api/clubs/${id}` : '/api/clubs';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['clubModal']) modals['clubModal'].hide();
        showAlert(data.message || 'Club saved successfully.', 'success');
        loadClubs();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function deleteClub(id, name) {
    showDeleteConfirm(
        `Are you sure you want to delete club "${name}"? All internal events, student memberships, and advisor mappings will be permanently removed.`,
        async () => {
            try {
                const res = await fetch(`/api/clubs/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadClubs();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

async function viewClubDetails(clubId) {
    try {
        const res = await fetch(`/api/clubs/${clubId}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);
        const c = data.club;

        document.getElementById('cd-name').textContent = c.name;
        document.getElementById('cd-category').textContent = c.category;
        document.getElementById('cd-room').textContent = c.room_no || 'None allocated';
        document.getElementById('cd-status').innerHTML = getStatusBadge(c.status);
        document.getElementById('cd-desc').textContent = c.description || 'No description provided.';
        document.getElementById('cd-member-count').textContent = c.member_count;

        // Advisors list
        const advList = document.getElementById('cd-advisors-list');
        if (c.advisors.length === 0) {
            advList.innerHTML = `<li class="list-group-item text-muted small">No faculty advisors assigned.</li>`;
        } else {
            advList.innerHTML = c.advisors.map(a => `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    <div>
                        <div class="fw-semibold">${escapeHtml(a.name)}</div>
                        <small class="text-muted">${escapeHtml(a.department)}</small>
                    </div>
                    <small class="text-muted">${escapeHtml(a.email)}</small>
                </li>
            `).join('');
        }

        // Members list
        const mRes = await fetch(`/api/clubs/${clubId}/members`);
        const mData = await mRes.json();
        const memTbody = document.getElementById('cd-members-tbody');
        if (mData.members.length === 0) {
            memTbody.innerHTML = `<tr><td colspan="2" class="text-muted text-center py-2">No active members.</td></tr>`;
        } else {
            memTbody.innerHTML = mData.members.map(m => `
                <tr>
                    <td><strong>${escapeHtml(m.name)}</strong> <small class="text-muted">(${m.roll_no})</small></td>
                    <td>${getRoleBadge(m.role)}</td>
                </tr>
            `).join('');
        }

        // Events list
        const eRes = await fetch(`/api/clubs/${clubId}/events`);
        const eData = await eRes.json();
        const evtTbody = document.getElementById('cd-events-tbody');
        if (eData.events.length === 0) {
            evtTbody.innerHTML = `<tr><td colspan="4" class="text-muted text-center py-2">No events organized.</td></tr>`;
        } else {
            evtTbody.innerHTML = eData.events.map(ev => `
                <tr>
                    <td class="fw-semibold">${escapeHtml(ev.title)}</td>
                    <td><small>${escapeHtml(ev.event_date)}</small></td>
                    <td><small>${escapeHtml(ev.venue)}</small></td>
                    <td><small>${ev.active_registrations} / ${ev.capacity}</small></td>
                </tr>
            `).join('');
        }

        if (modals['clubDetailModal']) modals['clubDetailModal'].show();
    } catch (err) {
        showAlert('Could not load club details: ' + err.message, 'danger');
    }
}

// =============================================================================
// 4. MEMBERSHIPS CONTROLLER (M:N Bridge Table)
// =============================================================================
async function loadMemberships() {
    const tbody = document.getElementById('memberships-tbody');
    try {
        const clubId = document.getElementById('membership-filter-club').value;
        const url = clubId ? `/api/memberships?club_id=${clubId}` : '/api/memberships';
        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (data.memberships.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="empty-state py-4"><i class="bi bi-person-badge"></i>No memberships found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.memberships.map(m => `
            <tr>
                <td><span class="fw-bold">${escapeHtml(m.student_name)}</span></td>
                <td><code>${escapeHtml(m.roll_no)}</code></td>
                <td><span class="badge bg-light text-dark border">${escapeHtml(m.club_name)}</span></td>
                <td>${getRoleBadge(m.role)}</td>
                <td><small class="text-muted">${escapeHtml(m.joined_at)}</small></td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="openMembershipModal(${m.student_id}, ${m.club_id}, '${m.role}', '${escapeQuote(m.student_name)}', '${escapeQuote(m.club_name)}')" title="Change Role">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteMembership(${m.student_id}, ${m.club_id}, '${escapeQuote(m.student_name)}', '${escapeQuote(m.club_name)}')" title="Remove Membership">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center py-3">Error loading memberships: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function openMembershipModal(studentId = null, clubId = null, currentRole = 'Member', studentName = '', clubName = '') {
    const form = document.getElementById('membershipForm');
    form.reset();

    const isEdit = studentId !== null && clubId !== null;
    document.getElementById('membership-is-edit').value = isEdit ? '1' : '0';

    await populateStudentDropdown('membership-student-id');
    await populateClubDropdown('membership-club-id');

    if (isEdit) {
        document.getElementById('membershipModalTitle').textContent = `Update Role: ${studentName} in ${clubName}`;
        document.getElementById('membership-student-id').value = studentId;
        document.getElementById('membership-student-id').disabled = true;
        document.getElementById('membership-club-id').value = clubId;
        document.getElementById('membership-club-id').disabled = true;
        document.getElementById('membership-role').value = currentRole;
    } else {
        document.getElementById('membershipModalTitle').textContent = 'Enroll Student in Club';
        document.getElementById('membership-student-id').disabled = false;
        document.getElementById('membership-club-id').disabled = false;
        document.getElementById('membership-role').value = 'Member';
    }

    if (modals['membershipModal']) modals['membershipModal'].show();
}

async function handleMembershipFormSubmit(e) {
    e.preventDefault();
    const isEdit = document.getElementById('membership-is-edit').value === '1';
    const studentId = parseInt(document.getElementById('membership-student-id').value);
    const clubId = parseInt(document.getElementById('membership-club-id').value);
    const role = document.getElementById('membership-role').value;

    try {
        let url, method, payload;
        if (isEdit) {
            url = `/api/memberships/${studentId}/${clubId}`;
            method = 'PUT';
            payload = { role };
        } else {
            url = '/api/memberships';
            method = 'POST';
            payload = { student_id: studentId, club_id: clubId, role };
        }

        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['membershipModal']) modals['membershipModal'].hide();
        showAlert(data.message || 'Membership saved successfully.', 'success');
        loadMemberships();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function deleteMembership(studentId, clubId, studentName, clubName) {
    showDeleteConfirm(
        `Remove student "${studentName}" from club "${clubName}"?`,
        async () => {
            try {
                const res = await fetch(`/api/memberships/${studentId}/${clubId}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadMemberships();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

// =============================================================================
// 5. EVENTS CONTROLLER
// =============================================================================
async function loadEvents() {
    const tbody = document.getElementById('events-tbody');
    try {
        const clubId = document.getElementById('event-filter-club').value;
        const status = document.getElementById('event-filter-status').value;
        let url = '/api/events?';
        if (clubId) url += `club_id=${clubId}&`;
        if (status) url += `status=${encodeURIComponent(status)}&`;

        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        cachedEvents = data.events;

        if (data.events.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="empty-state py-4"><i class="bi bi-calendar-event"></i>No events found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.events.map(ev => {
            const pct = Math.min(100, Math.round((ev.active_registrations / ev.capacity) * 100));
            const barColor = pct >= 90 ? 'bg-danger' : (pct >= 60 ? 'bg-warning' : 'bg-success');
            return `
                <tr>
                    <td><small class="text-muted">#${ev.event_id}</small></td>
                    <td><span class="fw-bold">${escapeHtml(ev.title)}</span></td>
                    <td><span class="badge bg-light text-dark border">${escapeHtml(ev.club_name)}</span></td>
                    <td><small class="text-muted"><i class="bi bi-clock me-1"></i>${escapeHtml(ev.event_date)}</small></td>
                    <td><small>${escapeHtml(ev.venue)}</small></td>
                    <td style="min-width: 140px;">
                        <div class="d-flex justify-content-between small mb-1">
                            <span>${ev.active_registrations} / ${ev.capacity}</span>
                            <span class="fw-semibold">${pct}%</span>
                        </div>
                        <div class="capacity-bar">
                            <div class="capacity-fill ${barColor}" style="width: ${pct}%;"></div>
                        </div>
                    </td>
                    <td>${getEventStatusBadge(ev.status)}</td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="openEventModal(${ev.event_id})" title="Edit Event">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteEvent(${ev.event_id}, '${escapeQuote(ev.title)}')" title="Delete Event">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-danger text-center py-3">Error loading events: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function openEventModal(eventId = null) {
    const form = document.getElementById('eventForm');
    form.reset();
    document.getElementById('event-form-id').value = '';

    await populateClubDropdown('event-club-id');

    if (eventId) {
        const ev = cachedEvents.find(e => e.event_id === eventId);
        if (ev) {
            document.getElementById('eventModalTitle').textContent = 'Edit Event';
            document.getElementById('event-form-id').value = ev.event_id;
            document.getElementById('event-club-id').value = ev.club_id;
            document.getElementById('event-title').value = ev.title;
            document.getElementById('event-date').value = ev.event_date;
            document.getElementById('event-venue').value = ev.venue;
            document.getElementById('event-capacity').value = ev.capacity;
            document.getElementById('event-status').value = ev.status;
        }
    } else {
        document.getElementById('eventModalTitle').textContent = 'Schedule Event';
        // Set sample default date (tomorrow 10:00:00)
        const d = new Date();
        d.setDate(d.getDate() + 7);
        const dateStr = d.toISOString().split('T')[0] + ' 10:00:00';
        document.getElementById('event-date').value = dateStr;
    }

    if (modals['eventModal']) modals['eventModal'].show();
}

async function handleEventFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('event-form-id').value;
    const payload = {
        club_id: parseInt(document.getElementById('event-club-id').value),
        title: document.getElementById('event-title').value.trim(),
        event_date: document.getElementById('event-date').value.trim(),
        venue: document.getElementById('event-venue').value.trim(),
        capacity: parseInt(document.getElementById('event-capacity').value),
        status: document.getElementById('event-status').value
    };

    try {
        const url = id ? `/api/events/${id}` : '/api/events';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['eventModal']) modals['eventModal'].hide();
        showAlert(data.message || 'Event saved successfully.', 'success');
        loadEvents();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function deleteEvent(id, title) {
    showDeleteConfirm(
        `Are you sure you want to delete event "${title}"? All student registration records for this event will also be deleted.`,
        async () => {
            try {
                const res = await fetch(`/api/events/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadEvents();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

// =============================================================================
// 6. REGISTRATIONS CONTROLLER (M:N with Capacity Safety)
// =============================================================================
async function loadRegistrations() {
    const tbody = document.getElementById('registrations-tbody');
    try {
        const eventId = document.getElementById('registration-filter-event').value;
        const url = eventId ? `/api/registrations?event_id=${eventId}` : '/api/registrations';
        const res = await fetch(url);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (data.registrations.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="empty-state py-4"><i class="bi bi-ticket-perforated"></i>No registrations found.</td></tr>`;
            return;
        }

        tbody.innerHTML = data.registrations.map(r => `
            <tr>
                <td><span class="fw-bold">${escapeHtml(r.student_name)}</span></td>
                <td><code>${escapeHtml(r.roll_no)}</code></td>
                <td><span class="fw-semibold">${escapeHtml(r.event_title)}</span></td>
                <td><small class="text-muted">${escapeHtml(r.event_date)}</small></td>
                <td><small class="text-muted">${escapeHtml(r.registered_at)}</small></td>
                <td>
                    <select class="form-select form-select-sm" style="width: auto; min-width: 120px;" 
                            onchange="quickUpdateAttendance(${r.student_id}, ${r.event_id}, this.value)">
                        <option value="Registered" ${r.attendance_status === 'Registered' ? 'selected' : ''}>Registered</option>
                        <option value="Attended" ${r.attendance_status === 'Attended' ? 'selected' : ''}>Attended</option>
                        <option value="Absent" ${r.attendance_status === 'Absent' ? 'selected' : ''}>Absent</option>
                        <option value="Cancelled" ${r.attendance_status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                    </select>
                </td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteRegistration(${r.student_id}, ${r.event_id}, '${escapeQuote(r.student_name)}', '${escapeQuote(r.event_title)}')" title="Delete Registration">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-danger text-center py-3">Error loading registrations: ${escapeHtml(err.message)}</td></tr>`;
    }
}

async function openRegistrationModal() {
    const form = document.getElementById('registrationForm');
    form.reset();
    document.getElementById('registration-is-edit').value = '0';

    await populateStudentDropdown('reg-student-id');
    await populateEventDropdownWithSeats('reg-event-id');

    if (modals['registrationModal']) modals['registrationModal'].show();
}

async function handleRegistrationFormSubmit(e) {
    e.preventDefault();
    const studentId = parseInt(document.getElementById('reg-student-id').value);
    const eventId = parseInt(document.getElementById('reg-event-id').value);
    const attendanceStatus = document.getElementById('reg-status').value;

    try {
        const res = await fetch('/api/registrations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                student_id: studentId,
                event_id: eventId,
                attendance_status: attendanceStatus
            })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['registrationModal']) modals['registrationModal'].hide();
        showAlert(data.message || 'Registration recorded successfully.', 'success');
        loadRegistrations();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

async function quickUpdateAttendance(studentId, eventId, newStatus) {
    try {
        const res = await fetch(`/api/registrations/${studentId}/${eventId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ attendance_status: newStatus })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);
        showAlert(`Status updated to ${newStatus}.`, 'success');
        loadRegistrations();
    } catch (err) {
        showAlert(err.message, 'danger');
        loadRegistrations(); // Reset select UI to actual state
    }
}

function deleteRegistration(studentId, eventId, studentName, eventTitle) {
    showDeleteConfirm(
        `Remove registration for student "${studentName}" from event "${eventTitle}"?`,
        async () => {
            try {
                const res = await fetch(`/api/registrations/${studentId}/${eventId}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadRegistrations();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

// =============================================================================
// 7. FACULTY ADVISORS & MENTORSHIP CONTROLLER
// =============================================================================
async function loadAdvisors() {
    const advTbody = document.getElementById('advisors-tbody');
    const pairTbody = document.getElementById('club-advisors-tbody');

    // Load Advisors
    try {
        const res = await fetch('/api/advisors');
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        cachedAdvisors = data.advisors;

        if (data.advisors.length === 0) {
            advTbody.innerHTML = `<tr><td colspan="6" class="empty-state py-4"><i class="bi bi-person-workspace"></i>No advisors found.</td></tr>`;
        } else {
            advTbody.innerHTML = data.advisors.map(a => `
                <tr>
                    <td><small class="text-muted">#${a.advisor_id}</small></td>
                    <td><span class="fw-bold">${escapeHtml(a.name)}</span></td>
                    <td><span class="badge bg-light text-dark border">${escapeHtml(a.department)}</span></td>
                    <td><small class="text-muted">${escapeHtml(a.email)}</small></td>
                    <td><small>${escapeHtml(a.phone || '—')}</small></td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-primary me-1" onclick="openAdvisorModal(${a.advisor_id})" title="Edit Advisor">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="deleteAdvisor(${a.advisor_id}, '${escapeQuote(a.name)}')" title="Delete Advisor">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        advTbody.innerHTML = `<tr><td colspan="6" class="text-danger text-center py-3">Error loading advisors: ${escapeHtml(err.message)}</td></tr>`;
    }

    // Load Club-Advisor Assignments (Club_Advisor Bridge Table)
    try {
        const res = await fetch('/api/club-advisors');
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (data.club_advisors.length === 0) {
            pairTbody.innerHTML = `<tr><td colspan="4" class="empty-state py-4">No club mentors assigned.</td></tr>`;
        } else {
            pairTbody.innerHTML = data.club_advisors.map(ca => `
                <tr>
                    <td><span class="fw-bold">${escapeHtml(ca.club_name)}</span></td>
                    <td>${escapeHtml(ca.advisor_name)}</td>
                    <td><small class="text-muted">${escapeHtml(ca.department)}</small></td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-outline-danger" onclick="unassignAdvisor(${ca.club_id}, ${ca.advisor_id}, '${escapeQuote(ca.club_name)}', '${escapeQuote(ca.advisor_name)}')" title="Unassign">
                            <i class="bi bi-x-circle"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        }
    } catch (err) {
        pairTbody.innerHTML = `<tr><td colspan="4" class="text-danger text-center py-3">Error loading assignments: ${escapeHtml(err.message)}</td></tr>`;
    }
}

function openAdvisorModal(advisorId = null) {
    const form = document.getElementById('advisorForm');
    form.reset();
    document.getElementById('advisor-form-id').value = '';

    if (advisorId) {
        const adv = cachedAdvisors.find(a => a.advisor_id === advisorId);
        if (adv) {
            document.getElementById('advisorModalTitle').textContent = 'Edit Faculty Advisor';
            document.getElementById('advisor-form-id').value = adv.advisor_id;
            document.getElementById('advisor-name').value = adv.name;
            document.getElementById('advisor-dept').value = adv.department;
            document.getElementById('advisor-email').value = adv.email;
            document.getElementById('advisor-phone').value = adv.phone || '';
        }
    } else {
        document.getElementById('advisorModalTitle').textContent = 'Add Faculty Advisor';
    }

    if (modals['advisorModal']) modals['advisorModal'].show();
}

async function handleAdvisorFormSubmit(e) {
    e.preventDefault();
    const id = document.getElementById('advisor-form-id').value;
    const payload = {
        name: document.getElementById('advisor-name').value.trim(),
        department: document.getElementById('advisor-dept').value.trim(),
        email: document.getElementById('advisor-email').value.trim(),
        phone: document.getElementById('advisor-phone').value.trim() || null
    };

    try {
        const url = id ? `/api/advisors/${id}` : '/api/advisors';
        const method = id ? 'PUT' : 'POST';
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['advisorModal']) modals['advisorModal'].hide();
        showAlert(data.message || 'Advisor saved successfully.', 'success');
        loadAdvisors();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function deleteAdvisor(id, name) {
    showDeleteConfirm(
        `Are you sure you want to delete advisor "${name}"? Mentorship mappings for this advisor will be removed while clubs remain intact.`,
        async () => {
            try {
                const res = await fetch(`/api/advisors/${id}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadAdvisors();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

async function openAssignAdvisorModal() {
    const form = document.getElementById('assignAdvisorForm');
    form.reset();

    await populateClubDropdown('assign-club-id');
    await populateAdvisorDropdown('assign-advisor-id');

    if (modals['assignAdvisorModal']) modals['assignAdvisorModal'].show();
}

async function handleAssignAdvisorSubmit(e) {
    e.preventDefault();
    const clubId = parseInt(document.getElementById('assign-club-id').value);
    const advisorId = parseInt(document.getElementById('assign-advisor-id').value);

    try {
        const res = await fetch('/api/club-advisors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ club_id: clubId, advisor_id: advisorId })
        });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        if (modals['assignAdvisorModal']) modals['assignAdvisorModal'].hide();
        showAlert(data.message, 'success');
        loadAdvisors();
    } catch (err) {
        showAlert(err.message, 'danger');
    }
}

function unassignAdvisor(clubId, advisorId, clubName, advisorName) {
    showDeleteConfirm(
        `Unassign mentor "${advisorName}" from "${clubName}"?`,
        async () => {
            try {
                const res = await fetch(`/api/club-advisors/${clubId}/${advisorId}`, { method: 'DELETE' });
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                showAlert(data.message, 'success');
                loadAdvisors();
            } catch (err) {
                showAlert(err.message, 'danger');
            }
        }
    );
}

// =============================================================================
// DROPDOWN POPULATION HELPERS
// =============================================================================
async function populateStudentDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/students');
        const data = await res.json();
        if (data.success) {
            el.innerHTML = '<option value="">Select student...</option>' +
                data.students.map(s => `<option value="${s.student_id}">${escapeHtml(s.name)} (${s.roll_no} - ${s.branch})</option>`).join('');
        }
    } catch (err) {
        console.error('Error populating students dropdown:', err);
    }
}

async function populateClubDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/clubs');
        const data = await res.json();
        if (data.success) {
            el.innerHTML = '<option value="">Select club...</option>' +
                data.clubs.map(c => `<option value="${c.club_id}">${escapeHtml(c.name)} (${c.category})</option>`).join('');
        }
    } catch (err) {
        console.error('Error populating clubs dropdown:', err);
    }
}

async function populateClubFilterDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/clubs');
        const data = await res.json();
        if (data.success) {
            const currentVal = el.value;
            el.innerHTML = '<option value="">All Clubs</option>' +
                data.clubs.map(c => `<option value="${c.club_id}">${escapeHtml(c.name)}</option>`).join('');
            el.value = currentVal;
        }
    } catch (err) {
        console.error('Error populating club filter:', err);
    }
}

async function populateEventFilterDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/events');
        const data = await res.json();
        if (data.success) {
            const currentVal = el.value;
            el.innerHTML = '<option value="">All Events</option>' +
                data.events.map(e => `<option value="${e.event_id}">${escapeHtml(e.title)}</option>`).join('');
            el.value = currentVal;
        }
    } catch (err) {
        console.error('Error populating event filter:', err);
    }
}

async function populateEventDropdownWithSeats(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/events');
        const data = await res.json();
        if (data.success) {
            el.innerHTML = '<option value="">Select event...</option>' +
                data.events.map(e => {
                    const available = Math.max(0, e.capacity - e.active_registrations);
                    const label = `${escapeHtml(e.title)} [${available} seats left / cap: ${e.capacity}]`;
                    return `<option value="${e.event_id}" ${available === 0 ? 'disabled' : ''}>${label}</option>`;
                }).join('');
        }
    } catch (err) {
        console.error('Error populating events dropdown:', err);
    }
}

async function populateAdvisorDropdown(selectId) {
    const el = document.getElementById(selectId);
    if (!el) return;
    try {
        const res = await fetch('/api/advisors');
        const data = await res.json();
        if (data.success) {
            el.innerHTML = '<option value="">Select faculty advisor...</option>' +
                data.advisors.map(a => `<option value="${a.advisor_id}">${escapeHtml(a.name)} (${a.department})</option>`).join('');
        }
    } catch (err) {
        console.error('Error populating advisors dropdown:', err);
    }
}

// =============================================================================
// UI BADGE HELPERS & SANITIZERS
// =============================================================================
function getStatusBadge(status) {
    if (status === 'Active') {
        return '<span class="badge bg-success-subtle text-success border border-success-subtle">Active</span>';
    }
    return '<span class="badge bg-secondary-subtle text-secondary border">Inactive</span>';
}

function getEventStatusBadge(status) {
    switch (status) {
        case 'Upcoming':
            return '<span class="badge bg-primary-subtle text-primary border border-primary-subtle">Upcoming</span>';
        case 'Ongoing':
            return '<span class="badge bg-warning-subtle text-warning border border-warning-subtle">Ongoing</span>';
        case 'Completed':
            return '<span class="badge bg-success-subtle text-success border border-success-subtle">Completed</span>';
        case 'Cancelled':
            return '<span class="badge bg-danger-subtle text-danger border border-danger-subtle">Cancelled</span>';
        default:
            return `<span class="badge bg-light text-dark">${escapeHtml(status)}</span>`;
    }
}

function getRoleBadge(role) {
    switch (role) {
        case 'President':
            return '<span class="badge badge-role badge-president">President</span>';
        case 'Vice President':
            return '<span class="badge badge-role badge-vp">Vice President</span>';
        case 'Secretary':
            return '<span class="badge badge-role badge-secretary">Secretary</span>';
        case 'Treasurer':
            return '<span class="badge badge-role badge-treasurer">Treasurer</span>';
        case 'Core Member':
            return '<span class="badge badge-role badge-core">Core Member</span>';
        default:
            return '<span class="badge badge-role badge-member">Member</span>';
    }
}

function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function escapeQuote(text) {
    if (!text) return '';
    return String(text).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

