/**
 * Civic Sense — Central Authentication State Manager
 *
 * Manages Supabase Auth session across all pages:
 * - Checks existing session on page load
 * - Listens for auth state changes (login/logout)
 * - Provides token helpers for API calls
 * - Updates nav bar with login/logout button
 * - Handles logout
 */

/* ── Auth State ── */
let _authState = {
  loading: true,
  session: null,
  user: null,
  reporterId: null
};

/* ── Auth Callbacks ── */
const _authListeners = [];

function onAuthChange(callback) {
  _authListeners.push(callback);
}

function _notifyListeners() {
  _authListeners.forEach(fn => {
    try { fn(_authState); } catch (e) { console.error("Auth listener error:", e); }
  });
}

/* ── Public API ── */

function isAuthenticated() {
  return !_authState.loading && _authState.session !== null;
}

function isAuthLoading() {
  return _authState.loading;
}

function getAuthUser() {
  return _authState.user;
}

function getReporterId() {
  return _authState.reporterId;
}

async function getAccessToken() {
  const sb = getSupabase();
  if (!sb) return null;

  try {
    const { data } = await sb.auth.getSession();
    return data?.session?.access_token || null;
  } catch (e) {
    console.error("Failed to get access token:", e);
    return null;
  }
}

async function logout() {
  const sb = getSupabase();
  if (!sb) return;

  try {
    await sb.auth.signOut();
  } catch (e) {
    console.error("Logout error:", e);
  }

  _authState = { loading: false, session: null, user: null, reporterId: null };
  _notifyListeners();
  _updateNavAuth();
  toast("Logged out successfully.");
}

/* ── Fetch Reporter ID from Backend ── */

async function _fetchReporterId(token) {
  try {
    const res = await fetch("/api/auth/me", {
      headers: { "Authorization": "Bearer " + token }
    });
    const data = await res.json();
    if (data.success && data.reporter_id) {
      return data.reporter_id;
    }
  } catch (e) {
    console.error("Failed to fetch reporter ID:", e);
  }
  return null;
}

/* ── Nav Bar Auth UI ── */

function _updateNavAuth() {
  const actionsDiv = document.querySelector(".nav .actions");
  if (!actionsDiv) return;

  // Remove existing auth button if any
  const existing = document.getElementById("authNavBtn");
  if (existing) existing.remove();

  const btn = document.createElement("button");
  btn.id = "authNavBtn";
  btn.className = "theme"; // reuse existing nav button style
  btn.style.cssText = "width:auto;padding:0 12px;font-size:12px;font-weight:600;letter-spacing:.5px;";

  if (_authState.loading) {
    btn.textContent = "…";
    btn.disabled = true;
  } else if (isAuthenticated()) {
    btn.textContent = _authState.reporterId ? `${_authState.reporterId} (Logout)` : "Logout";
    btn.title = _authState.reporterId ? `Signed in as ${_authState.reporterId}. Click to logout.` : "Click to logout";
    btn.addEventListener("click", logout);
  } else {
    btn.textContent = "Login";
    btn.addEventListener("click", () => {
      window.location.href = "login.html";
    });
  }

  actionsDiv.appendChild(btn);
}

/* ── Initialization ── */

async function initAuth() {
  const sb = getSupabase();
  if (!sb) {
    _authState.loading = false;
    _updateNavAuth();
    _notifyListeners();
    return;
  }

  // Check existing session
  try {
    const { data } = await sb.auth.getSession();
    if (data?.session) {
      _authState.session = data.session;
      _authState.user = data.session.user;
      _authState.reporterId = await _fetchReporterId(data.session.access_token);
    }
  } catch (e) {
    console.error("Session check error:", e);
  }

  _authState.loading = false;
  _updateNavAuth();
  _notifyListeners();

  // Listen for auth state changes (login, logout, token refresh)
  sb.auth.onAuthStateChange(async (event, session) => {
    if (event === "SIGNED_IN" && session) {
      _authState.session = session;
      _authState.user = session.user;
      _authState.reporterId = await _fetchReporterId(session.access_token);
      _authState.loading = false;
    } else if (event === "SIGNED_OUT") {
      _authState.session = null;
      _authState.user = null;
      _authState.reporterId = null;
      _authState.loading = false;
    } else if (event === "TOKEN_REFRESHED" && session) {
      _authState.session = session;
    }
    _updateNavAuth();
    _notifyListeners();
  });
}

/* ── Auto-init on DOMContentLoaded ── */
document.addEventListener("DOMContentLoaded", () => {
  // Small delay to ensure supabase-config.js has run
  setTimeout(initAuth, 50);
});
