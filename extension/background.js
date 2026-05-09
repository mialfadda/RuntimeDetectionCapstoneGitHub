const API_BASE = 'http://localhost:5000';

// --- Token helpers ---
async function getTokens() {
  const data = await chrome.storage.local.get(['access_token', 'refresh_token']);
  return data;
}

async function setTokens(access, refresh) {
  await chrome.storage.local.set({ access_token: access, refresh_token: refresh });
}

async function clearTokens() {
  await chrome.storage.local.remove(['access_token', 'refresh_token', 'user']);
}

// --- Authenticated fetch with auto-refresh ---
async function apiFetch(path, options = {}) {
  const { access_token, refresh_token } = await getTokens();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (access_token) headers['Authorization'] = `Bearer ${access_token}`;

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401 && refresh_token) {
    // Try refreshing
    const refreshRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${refresh_token}`,
      },
    });
    if (refreshRes.ok) {
      const data = await refreshRes.json();
      await setTokens(data.access_token, refresh_token);
      headers['Authorization'] = `Bearer ${data.access_token}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      await clearTokens();
      throw new Error('Session expired');
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed (${res.status})`);
  }
  return res.json();
}

// --- Login ---
async function login(email, password) {
  const data = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  await setTokens(data.access_token, data.refresh_token);
  await chrome.storage.local.set({
    user: { user_id: data.user_id, email, role: data.role },
  });
  return data;
}

// --- Scan URL ---
async function scanUrl(url) {
  return apiFetch('/scan/analyze', {
    method: 'POST',
    body: JSON.stringify({ url, source: 'extension' }),
  });
}

// --- Navigation listener: scan on every page load ---
chrome.webNavigation.onCompleted.addListener(async (details) => {
  if (details.frameId !== 0) return; // main frame only
  const url = details.url;
  if (!url.startsWith('http://') && !url.startsWith('https://')) return;

  const { access_token } = await getTokens();
  if (!access_token) return; // not logged in

  try {
    const result = await scanUrl(url);
    // If high/critical, notify the content script to show warning
    if (result.risk_level === 'high' || result.risk_level === 'critical') {
      chrome.tabs.sendMessage(details.tabId, {
        type: 'THREAT_DETECTED',
        data: result,
      }).catch(() => {}); // content script may not be ready
    }
    // Store last scan result for popup
    await chrome.storage.local.set({ lastScan: result });
  } catch (e) {
    console.warn('Scan failed:', e.message);
  }
});

// --- Message handler for popup ---
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'LOGIN') {
    login(msg.email, msg.password)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true; // async
  }

  if (msg.type === 'LOGOUT') {
    apiFetch('/auth/logout', { method: 'POST' })
      .catch(() => {})
      .finally(() => clearTokens())
      .then(() => sendResponse({ ok: true }));
    return true;
  }

  if (msg.type === 'SCAN') {
    scanUrl(msg.url)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }

  if (msg.type === 'GET_STATUS') {
    getTokens().then(async (tokens) => {
      const user = (await chrome.storage.local.get('user')).user || null;
      const lastScan = (await chrome.storage.local.get('lastScan')).lastScan || null;
      sendResponse({
        loggedIn: !!tokens.access_token,
        user,
        lastScan,
      });
    });
    return true;
  }
});
