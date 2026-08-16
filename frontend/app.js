/* ============================================================
   TASKFLOW — app.js
   Author : Senior Frontend Developer
   Stack  : Vanilla JS (ES2022) · Fetch API · DOM API
   Backend: FastAPI @ http://127.0.0.1:8000

   CHANGES (latest):
   - Landing page is the default unauthenticated view (no auto-open modal)
   - Sign In / Get Started CTAs open respective auth dialogs
   - Public AI Help Desk works without authentication
   - Logout confirm modal now says "Cancel / Logout" not "Delete"
   ============================================================ */

'use strict';

/* ============================================================
   1. CONFIGURATION
   ============================================================ */
const API_BASE = '';

/** Allowed email domains — mirrors backend validation */
const ALLOWED_EMAIL_DOMAINS = ['gmail.com', 'outlook.com', 'yahoo.com', 'yahoomail.com'];

const TASK_PRIORITIES = ['High', 'Medium', 'Low'];
const TASK_STATUSES   = ['Pending', 'In Progress', 'Completed'];


/* ============================================================
   2. STATE
   ============================================================ */
const State = {
  token        : null,
  user         : null,
  projects     : [],
  currentProjectId : null,   // for project-detail view
  tasksPage    : 1,
  tasksLimit   : 10,
  tasksSort    : 'priority',
  tasksStatus  : '',
  confirmCb    : null,       // pending confirm-delete callback
};


/* ============================================================
   3. HELPERS
   ============================================================ */

/** Sanitise a string to prevent XSS when injecting as textContent is preferred,
 *  but we still escape when building HTML strings. */
function sanitize(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/** Format ISO date string → readable label */
function fmtDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

/** Today's date as YYYY-MM-DD for date input min attribute */
function todayISO() {
  return new Date().toISOString().split('T')[0];
}

/** Debounce factory */
function debounce(fn, delay = 320) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

/** Set button to loading state */
function btnLoading(btn, yes) {
  if (!btn) return;
  if (yes) { btn.classList.add('loading'); btn.disabled = true; }
  else     { btn.classList.remove('loading'); btn.disabled = false; }
}


/* ============================================================
   4. TOAST NOTIFICATIONS
   ============================================================ */
let _toastTimer;

function showToast(message, type = 'info', duration = 3500) {
  const el = document.getElementById('toast');
  if (!el) return;
  clearTimeout(_toastTimer);
  el.textContent = sanitize(message);
  el.className = `toast toast--${type} toast--visible`;
  _toastTimer = setTimeout(() => { el.classList.remove('toast--visible'); }, duration);
}


/* ============================================================
   5. FETCH WRAPPER
   ============================================================ */

/**
 * Centralised API call. Automatically injects JWT, returns parsed JSON.
 * Throws an Error with the backend's `detail` on non-2xx status.
 */
async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (State.token) headers['Authorization'] = `Bearer ${State.token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  let data;
  try { data = await res.json(); } catch { data = null; }

  if (!res.ok) {
    const msg = (data && (data.detail || data.message))
      ? (Array.isArray(data.detail) ? data.detail.map(e => e.msg).join(', ') : data.detail)
      : `Request failed (${res.status})`;
    throw new Error(msg);
  }

  return data;
}


/* ============================================================
   6. TOKEN / AUTH PERSISTENCE
   ============================================================ */

function saveToken(token) {
  State.token = token;
  localStorage.setItem('tf_token', token);
}

function loadToken() {
  const t = localStorage.getItem('tf_token');
  if (t) State.token = t;
  return !!t;
}

function clearToken() {
  State.token = null;
  State.user  = null;
  localStorage.removeItem('tf_token');
}


/* ============================================================
   7. AUTH VALIDATION
   ============================================================ */

function validateEmail(email) {
  const trimmed = email.trim().toLowerCase();
  if (!trimmed) return 'Email is required.';
  if (trimmed.split('@').length !== 2) return 'Enter a valid email address.';
  const domain = trimmed.split('@')[1];
  if (!ALLOWED_EMAIL_DOMAINS.includes(domain))
    return `Allowed domains: ${ALLOWED_EMAIL_DOMAINS.join(', ')}.`;
  return '';
}

function validatePassword(password) {
  if (!password) return 'Password is required.';
  if (password.length < 8) return 'Password must be at least 8 characters.';
  return '';
}

function validateName(name) {
  const trimmed = name.trim();
  if (!trimmed) return 'Full name is required.';
  if (trimmed.length < 2) return 'Name must be at least 2 characters.';
  return '';
}

/** Show / clear an error under a field */
function fieldError(errId, message) {
  const el = document.getElementById(errId);
  if (!el) return;
  el.textContent = message;
  const input = el.closest('.field-group')?.querySelector('.field-input, .field-select, .field-textarea');
  if (input) {
    input.classList.toggle('invalid', !!message);
    input.classList.toggle('valid', !message && input.value.trim() !== '');
  }
}

/** Returns true when there are no errors */
function isFormValid(errorIds) {
  return errorIds.every(id => {
    const el = document.getElementById(id);
    return el && el.textContent.trim() === '';
  });
}


/* ============================================================
   8. LOGIN FORM
   ============================================================ */

function initLoginForm() {
  const form    = document.getElementById('login-form');
  const emailEl = document.getElementById('login-email');
  const passEl  = document.getElementById('login-password');
  const submitBtn = document.getElementById('login-btn');

  function validate() {
    const emailErr = validateEmail(emailEl.value);
    const passErr  = validatePassword(passEl.value);
    fieldError('login-email-error', emailErr);
    fieldError('login-password-error', passErr);
    submitBtn.disabled = !!(emailErr || passErr);
  }

  emailEl.addEventListener('input', validate);
  passEl.addEventListener('input', validate);
  // Immediate feedback on blur
  emailEl.addEventListener('blur', validate);
  passEl.addEventListener('blur', validate);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    validate();
    if (submitBtn.disabled) return;

    btnLoading(submitBtn, true);
    try {
      const data = await apiFetch('/login', {
        method: 'POST',
        body: JSON.stringify({
          email   : emailEl.value.trim().toLowerCase(),
          password: passEl.value,
        }),
      });
      saveToken(data.access_token);
      await bootApp();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnLoading(submitBtn, false);
    }
  });
}


/* ============================================================
   9. REGISTER FORM
   ============================================================ */

function initRegisterForm() {
  const form       = document.getElementById('register-form');
  const nameEl     = document.getElementById('reg-name');
  const emailEl    = document.getElementById('reg-email');
  const passEl     = document.getElementById('reg-password');
  const confirmEl  = document.getElementById('reg-confirm-password');
  const submitBtn  = document.getElementById('register-btn');

  function validateConfirm() {
    if (!confirmEl.value) return 'Please confirm your password.';
    if (confirmEl.value !== passEl.value) return 'Passwords do not match.';
    return '';
  }

  function validate() {
    const nameErr    = validateName(nameEl.value);
    const emailErr   = validateEmail(emailEl.value);
    const passErr    = validatePassword(passEl.value);
    const confirmErr = validateConfirm();
    fieldError('reg-name-error', nameErr);
    fieldError('reg-email-error', emailErr);
    fieldError('reg-password-error', passErr);
    fieldError('reg-confirm-password-error', confirmErr);
    submitBtn.disabled = !!(nameErr || emailErr || passErr || confirmErr);
  }

  [nameEl, emailEl, passEl, confirmEl].forEach(el => {
    el.addEventListener('input', validate);
    el.addEventListener('blur', validate);
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    validate();
    if (submitBtn.disabled) return;

    btnLoading(submitBtn, true);
    try {
      await apiFetch('/register', {
        method: 'POST',
        body: JSON.stringify({
          name    : nameEl.value.trim(),
          email   : emailEl.value.trim().toLowerCase(),
          password: passEl.value,
        }),
      });
      showToast('Account created! Please log in.', 'success');
      // Close register modal, open login modal
      closeModal('register-modal');
      openLoginModal();
      form.reset();
      submitBtn.disabled = true;
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btnLoading(submitBtn, false);
    }
  });
}


/* ============================================================
   10. AUTH TABS  (no-op — tabs replaced by separate modals)
   ============================================================ */

function initAuthTabs() {
  // Auth tabs are no longer used — login and register each have their own dialog.
}


/* ============================================================
   11. PASSWORD TOGGLE
   ============================================================ */

function initPasswordToggles() {
  document.querySelectorAll('.password-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.getElementById(btn.dataset.target);
      if (!input) return;
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      btn.querySelector('.eye-icon').textContent = isHidden ? '🙈' : '👁';
      btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Toggle password visibility');
    });
  });
}


/* ============================================================
   12. NAVIGATION
   ============================================================ */

function switchView(viewName) {
  // Hide all views
  document.querySelectorAll('.view').forEach(v => {
    v.classList.remove('active');
    v.classList.add('hidden');
  });

  // Show target
  const target = document.getElementById(`view-${viewName}`);
  if (target) { target.classList.remove('hidden'); target.classList.add('active'); }

  // Update nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    const active = item.dataset.view === viewName;
    item.classList.toggle('active', active);
    item.setAttribute('aria-current', active ? 'page' : 'false');
  });

  // Update topbar title
  const titleMap = {
    dashboard       : 'Dashboard',
    projects        : 'Projects',
    tasks           : 'All Tasks',
    'ai-chat'       : 'AI Assistant',
    'project-detail': State.currentProject?.name || 'Project',
  };
  const topbarTitle = document.getElementById('topbar-title');
  if (topbarTitle) topbarTitle.textContent = titleMap[viewName] ?? viewName;

  // Trigger data loads
  if (viewName === 'dashboard')       loadDashboard();
  if (viewName === 'projects')        loadProjects();
  if (viewName === 'tasks')           { State.tasksPage = 1; loadTasks(); }

  // Close sidebar on mobile
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('menu-toggle')?.setAttribute('aria-expanded', 'false');
}

function initNavigation() {
  // Nav items in sidebar
  document.querySelectorAll('.nav-item[data-view]').forEach(btn => {
    btn.addEventListener('click', () => switchView(btn.dataset.view));
  });

  // "View all" shortcut on dashboard
  document.getElementById('view-all-tasks-btn')?.addEventListener('click', () => switchView('tasks'));

  // Mobile hamburger
  const menuToggle = document.getElementById('menu-toggle');
  const sidebar    = document.getElementById('sidebar');
  menuToggle?.addEventListener('click', () => {
    const open = sidebar.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(open));
  });

  // Sidebar close button
  document.getElementById('sidebar-close')?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    menuToggle?.setAttribute('aria-expanded', 'false');
  });

  // Backdrop click closes sidebar
  document.addEventListener('click', (e) => {
    if (sidebar?.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        e.target !== menuToggle) {
      sidebar.classList.remove('open');
      menuToggle?.setAttribute('aria-expanded', 'false');
    }
  });

  // Back button in project detail
  document.getElementById('back-to-projects-btn')?.addEventListener('click', () => switchView('projects'));
}


/* ============================================================
   13. MODALS
   ============================================================ */

function openModal(id) {
  const modal    = document.getElementById(id);
  const backdrop = document.getElementById('modal-backdrop');
  if (!modal || !backdrop) return;
  backdrop.classList.remove('hidden');
  modal.showModal ? modal.showModal() : modal.setAttribute('open', '');
  // Focus first focusable element
  setTimeout(() => {
    const focusable = modal.querySelector('input, select, textarea, button:not(.modal-close)');
    focusable?.focus();
  }, 50);
}

function closeModal(id) {
  const modal    = document.getElementById(id);
  const backdrop = document.getElementById('modal-backdrop');
  if (!modal) return;
  modal.close ? modal.close() : modal.removeAttribute('open');
  // Only hide backdrop if no other modals are open
  const anyOpen = document.querySelectorAll('dialog[open]').length > 0;
  if (!anyOpen && backdrop) backdrop.classList.add('hidden');
}

function initModals() {
  // Close buttons inside modals
  document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.modal));
  });

  // Backdrop click closes any open modal
  document.getElementById('modal-backdrop')?.addEventListener('click', () => {
    document.querySelectorAll('dialog[open]').forEach(d => closeModal(d.id));
  });

  // ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('dialog[open]').forEach(d => closeModal(d.id));
    }
  });
}


/* ============================================================
   14. CONFIRM DELETE MODAL
   ============================================================ */

function confirmDelete(message, callback, { title = 'Confirm Delete', confirmLabel = 'Delete' } = {}) {
  const msgEl   = document.getElementById('confirm-modal-message');
  const titleEl = document.getElementById('confirm-modal-title');
  const btnEl   = document.getElementById('confirm-delete-btn');
  if (msgEl)   msgEl.textContent = message;
  if (titleEl) titleEl.textContent = title;
  if (btnEl)   btnEl.querySelector('.btn-text').textContent = confirmLabel;
  State.confirmCb = callback;
  openModal('confirm-modal');
}

function initConfirmModal() {
  document.getElementById('confirm-delete-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('confirm-delete-btn');
    if (!State.confirmCb) return;
    btnLoading(btn, true);
    try {
      await State.confirmCb();
    } finally {
      btnLoading(btn, false);
      State.confirmCb = null;
      closeModal('confirm-modal');
    }
  });
}


/* ============================================================
   15. USER PROFILE
   ============================================================ */

async function loadUserProfile() {
  try {
    const user = await apiFetch('/users/me');
    State.user = user;

    // Sidebar
    const nameEl   = document.getElementById('sidebar-user-name');
    const emailEl  = document.getElementById('sidebar-user-email');
    const avatarEl = document.getElementById('user-avatar');
    if (nameEl)  nameEl.textContent  = user.name;
    if (emailEl) emailEl.textContent = user.email;
    if (avatarEl) avatarEl.textContent = user.name.charAt(0).toUpperCase();

    // Topbar greeting
    const hour = new Date().getHours();
    const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
    const greetEl = document.getElementById('topbar-greeting');
    if (greetEl) greetEl.textContent = `${greeting}, ${user.name.split(' ')[0]}`;
  } catch {
    logout();
  }
}


/* ============================================================
   16. LOGOUT
   ============================================================ */

function logout() {
  clearToken();
  document.getElementById('app-shell')?.classList.add('hidden');
  document.getElementById('landing-page')?.classList.remove('hidden');
  // Reset forms
  document.getElementById('login-form')?.reset();
  document.getElementById('register-form')?.reset();
  document.getElementById('login-btn').disabled = true;
  document.getElementById('register-btn').disabled = true;
  showToast('Logged out successfully.', 'info');
}

function initLogout() {
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    confirmDelete(
      'Are you sure you want to log out?',
      async () => { logout(); },
      { title: 'Log Out', confirmLabel: 'Log Out' }
    );
  });
}


/* ============================================================
   17. DASHBOARD
   ============================================================ */

async function loadDashboard() {
  // Stats
  try {
    const stats = await apiFetch('/tasks/statistics');
    document.getElementById('stat-total').textContent       = stats.Total        ?? 0;
    document.getElementById('stat-pending').textContent     = stats.Pending       ?? 0;
    document.getElementById('stat-in-progress').textContent = stats['In Progress'] ?? 0;
    document.getElementById('stat-completed').textContent   = stats.Completed     ?? 0;

    const pct = stats['Completion Percentage'] ?? 0;
    document.getElementById('progress-pct').textContent = `${pct}%`;
    const fill = document.getElementById('progress-fill');
    if (fill) {
      fill.style.width = `${pct}%`;
      fill.closest('[role="progressbar"]')?.setAttribute('aria-valuenow', pct);
    }
  } catch {
    /* stats optional — don't crash */
  }

  // Recent tasks (first page, priority sorted)
  try {
    const tasks = await apiFetch('/tasks?page=1&limit=5&sort=priority');
    renderRecentTasks(tasks);
  } catch {
    renderRecentTasks([]);
  }
}

function renderRecentTasks(tasks) {
  const container = document.getElementById('recent-tasks-list');
  if (!container) return;

  if (!tasks.length) {
    container.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon" aria-hidden="true">📭</span>
        <p>No tasks yet. Create a project and add your first task.</p>
      </div>`;
    return;
  }

  container.innerHTML = tasks.map(t => `
    <div class="task-list-mini-item">
      <span class="task-list-mini-title" title="${sanitize(t.title)}">${sanitize(t.title)}</span>
      <div class="task-list-mini-meta">
        ${priorityBadge(t.priority)}
        ${statusBadge(t.status)}
      </div>
    </div>`).join('');
}


/* ============================================================
   18. PROJECTS
   ============================================================ */

async function loadProjects() {
  const grid = document.getElementById('projects-grid');
  if (!grid) return;

  grid.innerHTML = skeletonCards(3);
  try {
    const projects = await apiFetch('/projects');
    State.projects = projects;
    renderProjectsGrid(projects);
    refreshProjectSelects();
  } catch (err) {
    showToast(err.message, 'error');
    grid.innerHTML = '<div class="empty-state"><span class="empty-icon">⚠️</span><p>Failed to load projects.</p></div>';
  }
}

function renderProjectsGrid(projects) {
  const grid = document.getElementById('projects-grid');
  if (!grid) return;

  if (!projects.length) {
    grid.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon" aria-hidden="true">◫</span>
        <p>No projects yet. Create your first one!</p>
      </div>`;
    return;
  }

  grid.innerHTML = projects.map(p => `
    <article class="project-card" data-id="${p.id}" role="button" tabindex="0" aria-label="Open project ${sanitize(p.name)}">
      <div class="project-card-header">
        <div class="project-card-icon" aria-hidden="true">◫</div>
        <div class="project-card-actions">
          <button class="btn btn-ghost btn-sm btn-edit-project"  data-id="${p.id}" aria-label="Edit ${sanitize(p.name)}">✏️</button>
          <button class="btn btn-danger btn-sm btn-del-project"  data-id="${p.id}" aria-label="Delete ${sanitize(p.name)}">🗑</button>
        </div>
      </div>
      <h4 class="project-card-name">${sanitize(p.name)}</h4>
      <p class="project-card-desc">${sanitize(p.description || 'No description.')}</p>
      <div class="project-card-footer">
        <span class="project-task-count" id="ptc-${p.id}">— tasks</span>
        <span class="badge badge-pending" style="font-size:0.7rem;">View →</span>
      </div>
    </article>`).join('');

  // Attach click events
  grid.querySelectorAll('.project-card').forEach(card => {
    // Open detail on card click (not on action buttons)
    card.addEventListener('click', (e) => {
      if (e.target.closest('.project-card-actions')) return;
      openProjectDetail(Number(card.dataset.id));
    });
    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') openProjectDetail(Number(card.dataset.id));
    });
  });

  grid.querySelectorAll('.btn-edit-project').forEach(btn => {
    btn.addEventListener('click', (e) => { e.stopPropagation(); openEditProjectModal(Number(btn.dataset.id)); });
  });

  grid.querySelectorAll('.btn-del-project').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const p = State.projects.find(x => x.id === Number(btn.dataset.id));
      confirmDelete(
        `Delete project "${p?.name}"? All its tasks will also be removed.`,
        () => deleteProject(Number(btn.dataset.id))
      );
    });
  });

  // Load task counts async
  projects.forEach(p => loadProjectTaskCount(p.id));
}

async function loadProjectTaskCount(projectId) {
  try {
    const tasks = await apiFetch(`/projects/${projectId}/tasks`);
    const el = document.getElementById(`ptc-${projectId}`);
    if (el) el.textContent = `${tasks.length} task${tasks.length !== 1 ? 's' : ''}`;
  } catch { /* non-critical */ }
}


/* ── Project Modal ─────────────────────────────────────── */

function initProjectModal() {
  document.getElementById('new-project-btn')?.addEventListener('click', openNewProjectModal);
  document.getElementById('project-form')?.addEventListener('submit', handleProjectSubmit);

  // Real-time validation
  const nameInput = document.getElementById('project-name-input');
  nameInput?.addEventListener('input', () => {
    const err = nameInput.value.trim() ? '' : 'Project name is required.';
    fieldError('project-name-error', err);
    document.getElementById('project-submit-btn').disabled = !!err;
  });
}

function openNewProjectModal() {
  const form  = document.getElementById('project-form');
  const title = document.getElementById('project-modal-title');
  const btn   = document.getElementById('project-submit-btn');
  form.reset();
  document.getElementById('project-id-input').value = '';
  if (title) title.textContent = 'New Project';
  if (btn)   { btn.querySelector('.btn-text').textContent = 'Create Project'; btn.disabled = true; }
  fieldError('project-name-error', '');
  openModal('project-modal');
}

function openEditProjectModal(id) {
  const p = State.projects.find(x => x.id === id);
  if (!p) return;
  document.getElementById('project-id-input').value    = id;
  document.getElementById('project-name-input').value  = p.name;
  document.getElementById('project-desc-input').value  = p.description || '';
  document.getElementById('project-modal-title').textContent = 'Edit Project';
  document.getElementById('project-submit-btn').querySelector('.btn-text').textContent = 'Save Changes';
  document.getElementById('project-submit-btn').disabled = false;
  fieldError('project-name-error', '');
  openModal('project-modal');
}

async function handleProjectSubmit(e) {
  e.preventDefault();
  const nameVal = document.getElementById('project-name-input').value.trim();
  if (!nameVal) { fieldError('project-name-error', 'Project name is required.'); return; }

  const btn     = document.getElementById('project-submit-btn');
  const idVal   = document.getElementById('project-id-input').value;
  const payload = {
    name       : nameVal,
    description: document.getElementById('project-desc-input').value.trim() || null,
  };

  btnLoading(btn, true);
  try {
    if (idVal) {
      await apiFetch(`/projects/${idVal}`, { method: 'PUT', body: JSON.stringify(payload) });
      showToast('Project updated.', 'success');
    } else {
      await apiFetch('/projects', { method: 'POST', body: JSON.stringify(payload) });
      showToast('Project created!', 'success');
    }
    closeModal('project-modal');
    await loadProjects();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btnLoading(btn, false);
  }
}

async function deleteProject(id) {
  await apiFetch(`/projects/${id}`, { method: 'DELETE' });
  showToast('Project deleted.', 'success');
  await loadProjects();
  // If we were viewing that project's detail, go back
  if (State.currentProjectId === id) switchView('projects');
}


/* ── Project Detail ────────────────────────────────────── */

async function openProjectDetail(projectId) {
  const project = State.projects.find(p => p.id === projectId);
  if (!project) return;

  State.currentProjectId = projectId;
  State.currentProject   = project;

  document.getElementById('project-detail-title').textContent = project.name;
  document.getElementById('project-detail-desc').textContent  = project.description || '';

  // Bind edit / delete buttons in detail view
  document.getElementById('edit-project-btn').onclick   = () => openEditProjectModal(projectId);
  document.getElementById('delete-project-btn').onclick = () => {
    confirmDelete(
      `Delete project "${project.name}"? All its tasks will also be removed.`,
      () => deleteProject(projectId)
    );
  };
  document.getElementById('new-project-task-btn').onclick = () => {
    openNewTaskModal(projectId);
  };

  switchView('project-detail');
  await loadProjectTasks(projectId);
}

async function loadProjectTasks(projectId, statusFilter = '') {
  const tbody = document.getElementById('project-tasks-tbody');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="5">${skeletonRows(3)}</td></tr>`;
  try {
    const qs    = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : '';
    const tasks = await apiFetch(`/projects/${projectId}/tasks${qs}`);
    renderProjectTasksTable(tasks);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="table-empty"><span class="empty-icon">⚠️</span><p>${sanitize(err.message)}</p></td></tr>`;
  }
}

function renderProjectTasksTable(tasks) {
  const tbody = document.getElementById('project-tasks-tbody');
  if (!tbody) return;

  if (!tasks.length) {
    tbody.innerHTML = `<tr><td colspan="5" class="table-empty"><span class="empty-icon" aria-hidden="true">📭</span><p>No tasks in this project yet.</p></td></tr>`;
    return;
  }

  tbody.innerHTML = tasks.map(t => `
    <tr data-task-id="${t.id}">
      <td class="task-title-cell" title="${sanitize(t.title)}">${sanitize(t.title)}</td>
      <td>${priorityBadge(t.priority)}</td>
      <td>${sanitize(fmtDate(t.due_date))}</td>
      <td>
        <select class="status-select-inline ${statusClass(t.status)}"
                data-task-id="${t.id}" aria-label="Task status">
          ${TASK_STATUSES.map(s => `<option value="${s}" ${s === t.status ? 'selected' : ''}>${s}</option>`).join('')}
        </select>
      </td>
      <td>
        <div class="row-actions">
          <button class="btn-icon btn-edit-task"   data-id="${t.id}" aria-label="Edit task">✏️</button>
          <button class="btn-icon btn-icon-danger btn-del-task" data-id="${t.id}" aria-label="Delete task">🗑</button>
        </div>
      </td>
    </tr>`).join('');

  attachTaskRowEvents(tbody);
}


/* ============================================================
   19. TASKS (All Tasks view)
   ============================================================ */

async function loadTasks() {
  const tbody = document.getElementById('tasks-tbody');
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="6">${skeletonRows(5)}</td></tr>`;

  try {
    const qs    = `?page=${State.tasksPage}&limit=${State.tasksLimit}&sort=${State.tasksSort}`;
    const tasks = await apiFetch(`/tasks${qs}`);

    // Client-side status filter (backend doesn't support on /tasks globally)
    const filtered = State.tasksStatus
      ? tasks.filter(t => t.status === State.tasksStatus)
      : tasks;

    renderTasksTable(filtered);
    renderPagination(tasks.length);
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="table-empty">
      <span class="empty-icon">⚠️</span><p>${sanitize(err.message)}</p></td></tr>`;
  }
}

function renderTasksTable(tasks) {
  const tbody = document.getElementById('tasks-tbody');
  if (!tbody) return;

  if (!tasks.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="table-empty">
      <span class="empty-icon" aria-hidden="true">📭</span>
      <p>No tasks found.</p></td></tr>`;
    return;
  }

  const projectMap = Object.fromEntries(State.projects.map(p => [p.id, p.name]));

  tbody.innerHTML = tasks.map(t => `
    <tr data-task-id="${t.id}">
      <td class="task-title-cell" title="${sanitize(t.title)}">${sanitize(t.title)}</td>
      <td>${sanitize(projectMap[t.project_id] || `#${t.project_id}`)}</td>
      <td>${priorityBadge(t.priority)}</td>
      <td>${sanitize(fmtDate(t.due_date))}</td>
      <td>
        <select class="status-select-inline ${statusClass(t.status)}"
                data-task-id="${t.id}" aria-label="Task status">
          ${TASK_STATUSES.map(s => `<option value="${s}" ${s === t.status ? 'selected' : ''}>${s}</option>`).join('')}
        </select>
      </td>
      <td>
        <div class="row-actions">
          <button class="btn-icon btn-edit-task"   data-id="${t.id}" aria-label="Edit task">✏️</button>
          <button class="btn-icon btn-icon-danger btn-del-task" data-id="${t.id}" aria-label="Delete task">🗑</button>
        </div>
      </td>
    </tr>`).join('');

  attachTaskRowEvents(tbody);
}

/** Attach status-change, edit, delete listeners to task rows */
function attachTaskRowEvents(container) {
  // Inline status change
  container.querySelectorAll('.status-select-inline').forEach(sel => {
    sel.addEventListener('change', async () => {
      const taskId  = Number(sel.dataset.taskId);
      const newStat = sel.value;
      const oldStat = sel.dataset.current || sel.querySelector('[selected]')?.value;
      try {
        await apiFetch(`/tasks/${taskId}/status`, {
          method: 'PATCH',
          body  : JSON.stringify({ status: newStat }),
        });
        // Update class for colour
        sel.className = `status-select-inline ${statusClass(newStat)}`;
        showToast(`Status → ${newStat}`, 'success', 2000);
        // Refresh stats if on dashboard
        if (document.getElementById('view-dashboard')?.classList.contains('active')) {
          loadDashboard();
        }
      } catch (err) {
        showToast(err.message, 'error');
        sel.value = oldStat;
      }
    });
  });

  // Edit
  container.querySelectorAll('.btn-edit-task').forEach(btn => {
    btn.addEventListener('click', () => openEditTaskModal(Number(btn.dataset.id)));
  });

  // Delete
  container.querySelectorAll('.btn-del-task').forEach(btn => {
    btn.addEventListener('click', () => {
      confirmDelete('Delete this task? This action cannot be undone.', () => deleteTask(Number(btn.dataset.id)));
    });
  });
}


/* ── Task Filters & Sort ───────────────────────────────── */

function initTaskControls() {
  // Sort
  document.getElementById('filter-sort')?.addEventListener('change', (e) => {
    State.tasksSort = e.target.value;
    State.tasksPage = 1;
    loadTasks();
  });

  // Status filter
  document.getElementById('filter-status')?.addEventListener('change', (e) => {
    State.tasksStatus = e.target.value;
    State.tasksPage   = 1;
    loadTasks();
  });

  // Search (debounced)
  document.getElementById('task-search-input')?.addEventListener('input',
    debounce(handleTaskSearch, 400)
  );
}

async function handleTaskSearch(e) {
  const query = e.target.value.trim();
  if (!query) { loadTasks(); return; }

  const algo  = document.getElementById('search-algo')?.value || 'linear';
  const tbody = document.getElementById('tasks-tbody');
  if (tbody) tbody.innerHTML = `<tr><td colspan="6">${skeletonRows(3)}</td></tr>`;

  try {
    const results = await apiFetch(`/tasks/search?title=${encodeURIComponent(query)}&algo=${algo}`);
    renderTasksTable(results);
    document.getElementById('tasks-pagination').innerHTML = '';
  } catch (err) {
    showToast(err.message, 'error');
  }
}


/* ── Task Pagination ───────────────────────────────────── */

function renderPagination(currentPageCount) {
  const nav = document.getElementById('tasks-pagination');
  if (!nav) return;

  const hasMore = currentPageCount === State.tasksLimit;
  const page    = State.tasksPage;

  nav.innerHTML = '';

  // Prev
  const prev = pageBtn('← Prev', page === 1);
  prev.addEventListener('click', () => { State.tasksPage--; loadTasks(); });
  nav.appendChild(prev);

  // Current page label
  const label = document.createElement('span');
  label.className = 'page-btn active';
  label.setAttribute('aria-current', 'page');
  label.textContent = page;
  nav.appendChild(label);

  // Next
  const next = pageBtn('Next →', !hasMore);
  next.addEventListener('click', () => { State.tasksPage++; loadTasks(); });
  nav.appendChild(next);
}

function pageBtn(text, disabled) {
  const btn = document.createElement('button');
  btn.className = 'page-btn';
  btn.textContent = text;
  btn.disabled = disabled;
  return btn;
}


/* ── Task Modal ────────────────────────────────────────── */

function initTaskModal() {
  document.getElementById('new-task-btn')?.addEventListener('click', () => openNewTaskModal());
  document.getElementById('task-form')?.addEventListener('submit', handleTaskSubmit);
  initTaskModalValidation();
}

function initTaskModalValidation() {
  const titleInput   = document.getElementById('task-title-input');
  const prioritySel  = document.getElementById('task-priority-input');
  const statusSel    = document.getElementById('task-status-input');
  const projectSel   = document.getElementById('task-project-input');
  const submitBtn    = document.getElementById('task-submit-btn');

  function validateTaskForm() {
    const titleErr   = titleInput?.value.trim()   ? '' : 'Title is required.';
    const priErr     = prioritySel?.value         ? '' : 'Priority is required.';
    const projErr    = projectSel?.value          ? '' : 'Project is required.';
    fieldError('task-title-error', titleErr);
    fieldError('task-priority-error', priErr);
    fieldError('task-project-error', projErr);
    if (submitBtn) submitBtn.disabled = !!(titleErr || priErr || projErr);
  }

  [titleInput, prioritySel, statusSel, projectSel].forEach(el => {
    el?.addEventListener('input',  validateTaskForm);
    el?.addEventListener('change', validateTaskForm);
  });
}

function openNewTaskModal(prefillProjectId = null) {
  const form  = document.getElementById('task-form');
  const title = document.getElementById('task-modal-title');
  const btn   = document.getElementById('task-submit-btn');
  form.reset();
  document.getElementById('task-id-input').value = '';
  if (title) title.textContent = 'New Task';
  if (btn) { btn.querySelector('.btn-text').textContent = 'Create Task'; btn.disabled = true; }

  // Reset errors
  ['task-title-error', 'task-priority-error', 'task-status-error', 'task-project-error'].forEach(id => fieldError(id, ''));

  refreshProjectSelects();

  if (prefillProjectId) {
    const sel = document.getElementById('task-project-input');
    if (sel) { sel.value = prefillProjectId; sel.dispatchEvent(new Event('change')); }
  }

  // Set today as min for due date
  const dueDateEl = document.getElementById('task-duedate-input');
  if (dueDateEl) dueDateEl.min = todayISO();

  openModal('task-modal');
}

async function openEditTaskModal(taskId) {
  try {
    const t = await apiFetch(`/tasks/${taskId}`);
    document.getElementById('task-id-input').value           = t.id;
    document.getElementById('task-title-input').value        = t.title;
    document.getElementById('task-desc-input').value         = t.description || '';
    document.getElementById('task-priority-input').value     = t.priority;
    document.getElementById('task-duedate-input').value      = t.due_date || '';
    document.getElementById('task-status-input').value       = t.status;
    refreshProjectSelects();
    document.getElementById('task-project-input').value      = t.project_id;
    document.getElementById('task-modal-title').textContent  = 'Edit Task';
    document.getElementById('task-submit-btn').querySelector('.btn-text').textContent = 'Save Changes';
    document.getElementById('task-submit-btn').disabled = false;
    ['task-title-error', 'task-priority-error', 'task-status-error', 'task-project-error'].forEach(id => fieldError(id, ''));
    openModal('task-modal');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleTaskSubmit(e) {
  e.preventDefault();

  const titleVal   = document.getElementById('task-title-input').value.trim();
  const priorityVal= document.getElementById('task-priority-input').value;
  const projectVal = document.getElementById('task-project-input').value;

  if (!titleVal || !priorityVal || !projectVal) {
    showToast('Please fill in all required fields.', 'warning');
    return;
  }

  const btn     = document.getElementById('task-submit-btn');
  const idVal   = document.getElementById('task-id-input').value;
  const payload = {
    title      : titleVal,
    description: document.getElementById('task-desc-input').value.trim() || null,
    priority   : priorityVal,
    due_date   : document.getElementById('task-duedate-input').value || null,
    status     : document.getElementById('task-status-input').value,
    project_id : Number(projectVal),
  };

  btnLoading(btn, true);
  try {
    if (idVal) {
      await apiFetch(`/tasks/${idVal}`, { method: 'PUT', body: JSON.stringify(payload) });
      showToast('Task updated.', 'success');
    } else {
      await apiFetch('/tasks', { method: 'POST', body: JSON.stringify(payload) });
      showToast('Task created!', 'success');
    }
    closeModal('task-modal');
    // Refresh the relevant view
    if (State.currentProjectId && document.getElementById('view-project-detail')?.classList.contains('active')) {
      loadProjectTasks(State.currentProjectId);
    } else {
      loadTasks();
    }
    loadDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btnLoading(btn, false);
  }
}

async function deleteTask(taskId) {
  await apiFetch(`/tasks/${taskId}`, { method: 'DELETE' });
  showToast('Task deleted.', 'success');
  if (State.currentProjectId && document.getElementById('view-project-detail')?.classList.contains('active')) {
    loadProjectTasks(State.currentProjectId);
  } else {
    loadTasks();
  }
  loadDashboard();
}


/* ── Refresh project <select> options ──────────────────── */

function refreshProjectSelects() {
  const selects = [
    document.getElementById('task-project-input'),
    document.getElementById('ai-quick-project'),
  ];
  selects.forEach(sel => {
    if (!sel) return;
    const current = sel.value;
    // Keep first placeholder option
    while (sel.options.length > 1) sel.remove(1);
    State.projects.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name;
      sel.appendChild(opt);
    });
    // Restore previous selection if still valid
    if (current) sel.value = current;
  });
}


/* ============================================================
   20. AI QUICK-ADD TASK
   ============================================================ */

function initAIQuickAdd() {
  const btn = document.getElementById('ai-quick-btn');
  btn?.addEventListener('click', handleAIQuickAdd);
}

async function handleAIQuickAdd() {
  const textEl   = document.getElementById('ai-quick-input');
  const projectEl= document.getElementById('ai-quick-project');
  const btn      = document.getElementById('ai-quick-btn');

  const text      = textEl?.value.trim();
  const projectId = projectEl?.value;

  if (!text) {
    showToast('Please describe your task first.', 'warning');
    textEl?.focus();
    return;
  }
  if (!projectId) {
    showToast('Please select a project.', 'warning');
    projectEl?.focus();
    return;
  }

  btnLoading(btn, true);
  try {
    const task = await apiFetch(
      `/tasks/quick-add?text=${encodeURIComponent(text)}&project_id=${projectId}`,
      { method: 'POST' }
    );
    showToast(`Task "${task.title}" created by AI!`, 'success', 4000);
    if (textEl) textEl.value = '';
    loadTasks();
    loadDashboard();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btnLoading(btn, false);
  }
}


/* ============================================================
   21. AI CHAT
   ============================================================ */

function initAIChat() {
  const form   = document.getElementById('chat-form');
  const input  = document.getElementById('chat-input');
  const clearBtn = document.getElementById('clear-chat-btn');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = input?.value.trim();
    if (!msg) return;
    if (input) input.value = '';
    await sendChatMessage(msg);
  });

  // Ctrl/Cmd + Enter to send
  input?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      form?.dispatchEvent(new Event('submit', { cancelable: true }));
    }
  });

  clearBtn?.addEventListener('click', clearChat);
}

function clearChat() {
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  messages.innerHTML = `
    <div class="chat-msg chat-msg-ai">
      <div class="chat-bubble">
        <span class="chat-sender" aria-hidden="true">✦ AI</span>
        <p>Hi! I'm your TaskFlow AI Assistant. Ask me anything — I can help you plan, prioritize, or think through your work.</p>
      </div>
    </div>`;
}

async function sendChatMessage(message) {
  const messages = document.getElementById('chat-messages');
  const sendBtn  = document.getElementById('chat-send-btn');
  if (!messages) return;

  // Append user message
  messages.appendChild(createChatBubble('user', message));
  scrollChatToBottom();

  // Show typing indicator
  const typingEl = createTypingIndicator();
  messages.appendChild(typingEl);
  scrollChatToBottom();

  btnLoading(sendBtn, true);
  try {
    const data = await apiFetch('/ai/chat', {
      method: 'POST',
      body  : JSON.stringify({ message }),
    });
    typingEl.remove();
    messages.appendChild(createChatBubble('ai', data.response));
  } catch (err) {
    typingEl.remove();
    messages.appendChild(createChatBubble('ai', `⚠ Error: ${err.message}`));
  } finally {
    btnLoading(sendBtn, false);
    scrollChatToBottom();
  }
}

function createChatBubble(role, text) {
  const wrapper = document.createElement('div');
  wrapper.className = `chat-msg chat-msg-${role}`;

  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble';

  if (role === 'ai') {
    const sender = document.createElement('span');
    sender.className = 'chat-sender';
    sender.setAttribute('aria-hidden', 'true');
    sender.textContent = '✦ AI';
    bubble.appendChild(sender);
  }

  const p = document.createElement('p');
  // Render newlines as <br> — text is from AI / we trust it was sanitised server-side
  // but we still sanitise before injecting
  p.innerHTML = sanitize(text).replace(/\n/g, '<br>');
  bubble.appendChild(p);
  wrapper.appendChild(bubble);
  return wrapper;
}

function createTypingIndicator() {
  const wrapper = document.createElement('div');
  wrapper.className = 'chat-msg chat-msg-ai';
  wrapper.id = 'typing-indicator';
  wrapper.innerHTML = `
    <div class="chat-bubble">
      <div class="typing-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>`;
  return wrapper;
}

function scrollChatToBottom() {
  scrollEl(document.getElementById('chat-messages'));
}


/* ============================================================
   22. BADGE HELPERS
   ============================================================ */

function priorityBadge(priority) {
  const map = { High: 'badge-high', Medium: 'badge-medium', Low: 'badge-low' };
  const cls = map[priority] || 'badge-pending';
  return `<span class="badge ${cls}">${sanitize(priority)}</span>`;
}

function statusBadge(status) {
  const map = { 'Pending': 'badge-pending', 'In Progress': 'badge-in-progress', 'Completed': 'badge-completed' };
  const cls = map[status] || 'badge-pending';
  return `<span class="badge ${cls}">${sanitize(status)}</span>`;
}

function statusClass(status) {
  const map = { 'Pending': 'status-pending', 'In Progress': 'status-in-progress', 'Completed': 'status-completed' };
  return map[status] || 'status-pending';
}


/* ============================================================
   23. SKELETON LOADERS
   ============================================================ */

function skeletonCards(n) {
  return Array.from({ length: n }).map(() =>
    `<div class="skeleton skeleton-card" aria-hidden="true"></div>`
  ).join('');
}

function skeletonRows(n) {
  return Array.from({ length: n }).map(() =>
    `<div class="skeleton skeleton-row" aria-hidden="true"></div>`
  ).join('');
}


/* ============================================================
   24. BOOT SEQUENCE
   ============================================================ */

async function bootApp() {
  // Hide landing page, show app shell
  document.getElementById('landing-page')?.classList.add('hidden');
  document.getElementById('app-shell')?.classList.remove('hidden');

  // Close any open auth modals
  closeModal('login-modal');
  closeModal('register-modal');

  // Load user profile first (validates token)
  await loadUserProfile();

  // Pre-load projects so selects are ready
  try {
    const projects = await apiFetch('/projects');
    State.projects = projects;
    refreshProjectSelects();
  } catch { /* handled in individual views */ }

  // Show dashboard
  switchView('dashboard');
}


/* ============================================================
   25. APP INIT
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Init all components ── */
  initAuthTabs();
  initPasswordToggles();
  initLoginForm();
  initRegisterForm();
  initNavigation();
  initModals();
  initConfirmModal();
  initLogout();
  initProjectModal();
  initTaskModal();
  initTaskControls();
  initAIQuickAdd();
  initAIChat();
  initLandingCTAs();
  initPublicHelpDesk();

  /* ── Check persisted session ── */
  if (loadToken()) {
    // Valid token found — go straight into the app
    bootApp();
  }
  // Otherwise the landing page is shown by default (visible in HTML)
});


/* ============================================================
   26. LANDING PAGE CTAs
   ============================================================ */

function initLandingCTAs() {
  // All buttons that open the Sign In dialog
  ['landing-signin-btn', 'hero-signin-btn', 'footer-signin-btn'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', () => openLoginModal());
  });

  // All buttons that open the Sign Up dialog
  ['landing-start-btn', 'hero-start-btn', 'footer-start-btn'].forEach(id => {
    document.getElementById(id)?.addEventListener('click', () => openRegisterModal());
  });

  // Cross-modal switch links
  document.getElementById('switch-to-register')?.addEventListener('click', () => {
    closeModal('login-modal');
    openRegisterModal();
  });
  document.getElementById('switch-to-login')?.addEventListener('click', () => {
    closeModal('register-modal');
    openLoginModal();
  });
}

function openLoginModal() {
  document.getElementById('login-form')?.reset();
  ['login-email-error', 'login-password-error'].forEach(id => fieldError(id, ''));
  document.getElementById('login-btn').disabled = true;
  openModal('login-modal');
}

function openRegisterModal() {
  document.getElementById('register-form')?.reset();
  ['reg-name-error', 'reg-email-error', 'reg-password-error', 'reg-confirm-password-error']
    .forEach(id => fieldError(id, ''));
  document.getElementById('register-btn').disabled = true;
  openModal('register-modal');
}

/* After successful register, re-open login modal */
// Override the register success handler in initRegisterForm to use modal switch
// We hook into the form submit via a post-success callback stored in State
// — easier: we patch initRegisterForm to call openLoginModal after success.
// This is handled by updating initRegisterForm below.


/* ============================================================
   27. PUBLIC AI HELP DESK  (no auth required)
   ============================================================ */

function initPublicHelpDesk() {
  const form    = document.getElementById('helpdesk-form');
  const input   = document.getElementById('helpdesk-input');

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = input?.value.trim();
    if (!msg) return;
    if (input) input.value = '';
    await sendHelpdeskMessage(msg);
  });

  // Ctrl/Cmd + Enter to send
  input?.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      form?.dispatchEvent(new Event('submit', { cancelable: true }));
    }
  });
}

// async function sendHelpdeskMessage(message) {
//   const messages = document.getElementById('helpdesk-messages');
//   const sendBtn  = document.getElementById('helpdesk-send-btn');
//   if (!messages) return;

//   // Append user bubble
//   messages.appendChild(createChatBubble('user', message));
//   scrollEl(messages);

//   // Typing indicator
//   const typingEl = createTypingIndicator();
//   typingEl.id = 'helpdesk-typing';
//   messages.appendChild(typingEl);
//   scrollEl(messages);

//   btnLoading(sendBtn, true);
//   try {
//     // /ai/chat is public — no token needed
//     const savedToken = State.token;
//     State.token = null;                          // temporarily strip auth header
//     const data = await apiFetch('/ai/chat', {
//       method: 'POST',
//       body  : JSON.stringify({ message }),
//     });
//     State.token = savedToken;                    // restore
//     typingEl.remove();
//     messages.appendChild(createChatBubble('ai', data.response));
//   } catch (err) {
//     State.token = null; // already null path, but be safe
//     typingEl.remove();
//     messages.appendChild(createChatBubble('ai', `⚠ Sorry, something went wrong: ${err.message}`));
//   } finally {
//     btnLoading(sendBtn, false);
//     scrollEl(messages);
//   }
// }
async function sendHelpdeskMessage(message) {
  const messages = document.getElementById('helpdesk-messages');
  const sendBtn = document.getElementById('helpdesk-send-btn');

  if (!messages) return;

  messages.appendChild(createChatBubble('user', message));
  scrollEl(messages);

  const typingEl = createTypingIndicator();
  typingEl.id = 'helpdesk-typing';
  messages.appendChild(typingEl);

  scrollEl(messages);
  btnLoading(sendBtn, true);

  const savedToken = State.token;

  try {
    State.token = null;

    const data = await apiFetch('/ai/chat', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });

    typingEl.remove();
    messages.appendChild(
      createChatBubble('ai', data.response)
    );

  } catch (err) {
    typingEl.remove();

    messages.appendChild(
      createChatBubble(
        'ai',
        `⚠ Sorry, something went wrong: ${err.message}`
      )
    );

  } finally {
    // Always restore the logged-in user's token
    State.token = savedToken;

    btnLoading(sendBtn, false);
    scrollEl(messages);
  }
}


/** Generic scroll-to-bottom helper */
function scrollEl(el) {
  if (el) el.scrollTop = el.scrollHeight;
}
