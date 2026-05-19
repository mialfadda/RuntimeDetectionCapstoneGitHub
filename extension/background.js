const DEFAULT_API_BASE = 'http://localhost:5000';

// User can override at runtime by saving `api_base` to chrome.storage.local
// from the popup Settings page.
async function getApiBase() {
  const stored = await chrome.storage.local.get('api_base');
  return (stored && stored.api_base) || DEFAULT_API_BASE;
}

// Back-compat shim — older code referenced API_BASE directly.
const API_BASE = DEFAULT_API_BASE;

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
  const base = await getApiBase();
  const { access_token, refresh_token } = await getTokens();
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (access_token) headers['Authorization'] = `Bearer ${access_token}`;

  let res = await fetch(`${base}${path}`, { ...options, headers });

  if (res.status === 401 && refresh_token) {
    // Try refreshing
    const refreshRes = await fetch(`${base}/auth/refresh`, {
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
      res = await fetch(`${base}${path}`, { ...options, headers });
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

// Skip non-web URLs (chrome://, chrome-extension://, about:, moz-extension://, file://, ...)
function isSkippableUrl(url) {
  if (!url) return true;
  return !(url.startsWith('http://') || url.startsWith('https://'));
}

let threatCount = 0;
function updateBadge() {
  if (threatCount > 0) {
    chrome.action.setBadgeText({ text: String(threatCount) });
    chrome.action.setBadgeBackgroundColor({ color: '#ef4444' });
  } else {
    chrome.action.setBadgeText({ text: '' });
  }
}

// Restore threatCount from persisted alerts on service worker startup
chrome.storage.local.get('alerts').then(({ alerts }) => {
  if (Array.isArray(alerts)) {
    threatCount = alerts.filter(a => a.risk_level === 'high' || a.risk_level === 'critical').length;
    updateBadge();
  }
});

async function pushAlert(result) {
  const { alerts } = await chrome.storage.local.get('alerts');
  const list = Array.isArray(alerts) ? alerts : [];
  list.unshift({ ...result, scanned_at: Date.now() });
  if (list.length > 50) list.length = 50; // cap at 50
  await chrome.storage.local.set({ alerts: list });
}

// --- Navigation listener: scan on every page load ---
chrome.webNavigation.onCompleted.addListener(async (details) => {
  if (details.frameId !== 0) return; // main frame only
  if (isSkippableUrl(details.url)) return;

  const { access_token } = await getTokens();
  if (!access_token) return; // not logged in

  try {
    const result = await scanUrl(details.url);

    await pushAlert(result);
    await chrome.storage.local.set({ lastScan: result });

    if (result.risk_level === 'high' || result.risk_level === 'critical') {
      threatCount++;
      updateBadge();
      // Tell the content script to show the overlay. Send under both names
      // (THREAT_DETECTED and SHOW_WARNING) so either listener works.
      const payload = {
        severity: result.risk_level,
        reason: 'This site may be malicious',
        confidence: result.confidence,
        url: result.url,
        threat_category: result.threat_category,
        scan_id: result.scan_id,
        explanation: {},
      };
      chrome.tabs.sendMessage(details.tabId, { type: 'SHOW_WARNING', data: payload }).catch(() => {});
      chrome.tabs.sendMessage(details.tabId, { type: 'THREAT_DETECTED', data: result }).catch(() => {});
    }
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
      .finally(async () => {
        await clearTokens();
        await chrome.storage.local.remove(['alerts', 'lastScan']);
        threatCount = 0;
        updateBadge();
      })
      .then(() => sendResponse({ ok: true }));
    return true;
  }

  if (msg.type === 'SCAN') {
    scanUrl(msg.url)
      .then(async (data) => { await pushAlert(data); sendResponse({ ok: true, data }); })
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }

  if (msg.type === 'GET_EXPLANATION') {
    apiFetch(`/explanations/${msg.scan_id}`)
      .then((data) => sendResponse({ ok: true, data }))
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }

  if (msg.type === 'GET_API_BASE') {
    getApiBase().then((url) => sendResponse({ ok: true, url, default: DEFAULT_API_BASE }));
    return true;
  }

  if (msg.type === 'SET_API_BASE') {
    chrome.storage.local.set({ api_base: (msg.url || '').trim() })
      .then(() => sendResponse({ ok: true }))
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
