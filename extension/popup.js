document.addEventListener('DOMContentLoaded', () => {
  const loginSection = document.getElementById('login-section');
  const mainSection = document.getElementById('main-section');
  const loginBtn = document.getElementById('login-btn');
  const logoutBtn = document.getElementById('logout-btn');
  const scanBtn = document.getElementById('scan-btn');
  const scanUrlInput = document.getElementById('scan-url');
  const scanResult = document.getElementById('scan-result');
  const loginError = document.getElementById('login-error');
  const userInfo = document.getElementById('user-info');
  const lastScanSection = document.getElementById('last-scan-section');
  const lastScanInfo = document.getElementById('last-scan-info');
  const statusDot = document.getElementById('status-dot');
  const alertsList = document.getElementById('alerts-list');

  // Tab switching
  function switchTab(name) {
    document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === 'tab-' + name));
  }
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => switchTab(tab.dataset.tab));
  });

  // Back-to-tab buttons inside content panes
  document.querySelectorAll('.back-btn[data-back-to]').forEach(b => {
    b.addEventListener('click', () => switchTab(b.dataset.backTo));
  });

  // Alert detail back button
  const alertDetail = document.getElementById('alert-detail');
  const alertDetailBody = document.getElementById('alert-detail-body');
  document.getElementById('alert-detail-back').addEventListener('click', () => {
    alertDetail.classList.add('hidden');
  });

  function mapVerdict(riskLevel) {
    if (riskLevel === 'safe' || riskLevel === 'low') return { label: 'Safe \u2705', cls: 'safe' };
    if (riskLevel === 'medium') return { label: 'Suspicious \u26A0\uFE0F', cls: 'suspicious' };
    return { label: 'Malicious! \uD83D\uDC80', cls: 'malicious' };
  }

  function showResult(data) {
    const v = mapVerdict(data.risk_level);
    scanResult.className = 'result ' + v.cls;
    scanResult.innerHTML =
      v.label +
      '<div class="detail">Confidence: ' + Math.round(data.confidence * 100) + '% \u00B7 ' + data.threat_category + '</div>';
    scanResult.classList.remove('hidden');

    // Add to alerts tab
    addAlert(data);
  }

  function addAlert(data) {
    const v = mapVerdict(data.risk_level);
    const dotCls = v.cls === 'safe' ? 'safe' : v.cls === 'suspicious' ? 'warning' : 'danger';
    // Remove empty message
    const empty = alertsList.querySelector('.empty');
    if (empty) empty.remove();

    const item = document.createElement('div');
    item.className = 'alert-item clickable';
    item.title = 'View explanation';
    item.innerHTML =
      '<div class="alert-dot ' + dotCls + '"></div>' +
      '<div class="alert-url">' + escapeHtml(data.url) + '</div>' +
      '<div class="alert-time">' + Math.round(data.confidence * 100) + '%</div>';
    item.addEventListener('click', () => openExplanation(data));
    alertsList.prepend(item);
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  async function openExplanation(scanData) {
    switchTab('alerts');
    alertDetail.classList.remove('hidden');
    alertDetailBody.innerHTML = '<div class="alert-detail-card">Loading explanation...</div>';
    try {
      const exp = await new Promise((resolve, reject) => {
        chrome.runtime.sendMessage(
          { type: 'GET_EXPLANATION', scan_id: scanData.scan_id },
          (res) => res && res.ok ? resolve(res.data) : reject(new Error((res && res.error) || 'Load failed'))
        );
      });
      const features = exp.top_features || [];
      alertDetailBody.innerHTML =
        '<div class="alert-detail-card">' +
        '<div class="label">URL</div>' +
        '<div style="word-break:break-all;margin-bottom:8px;">' + escapeHtml(scanData.url) + '</div>' +
        '<div class="label">Verdict</div>' +
        '<div style="margin-bottom:8px;">' + mapVerdict(scanData.risk_level).label +
        ' &middot; ' + Math.round(scanData.confidence * 100) + '%</div>' +
        '<div class="label">Summary</div>' +
        '<div style="margin-bottom:8px;">' + escapeHtml(exp.summary_text || 'No summary available.') + '</div>' +
        (features.length ? (
          '<div class="label">Top indicators (' + (exp.method || 'shap').toUpperCase() + ')</div>' +
          features.map(([name, score]) =>
            '<div class="feature"><span>' + escapeHtml(name) + '</span>' +
            '<span style="font-weight:600;">' + Math.round(score * 100) + '%</span></div>'
          ).join('')
        ) : '') +
        '</div>';
    } catch (e) {
      alertDetailBody.innerHTML = '<div class="alert-detail-card" style="color:var(--danger)">' + escapeHtml(e.message) + '</div>';
    }
  }

  // Check login status
  chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (res) => {
    if (res && res.loggedIn) {
      showLoggedIn(res.user, res.lastScan);
    } else {
      loginSection.classList.remove('hidden');
      mainSection.style.display = 'none';
      statusDot.style.background = 'var(--text-muted)';
    }
  });

  function showLoggedIn(user, lastScan) {
    loginSection.classList.add('hidden');
    mainSection.style.display = 'flex';
    mainSection.classList.remove('hidden');
    userInfo.textContent = user ? 'Signed in as ' + user.email : 'Signed in';
    statusDot.style.background = 'var(--safe)';
    if (lastScan) showLastScan(lastScan);
  }

  function showLastScan(data) {
    const v = mapVerdict(data.risk_level);
    lastScanInfo.innerHTML =
      '<span style="word-break:break-all;">' + data.url + '</span><br/>' +
      '<strong style="color:var(--' + (v.cls === 'safe' ? 'safe' : v.cls === 'suspicious' ? 'warning' : 'danger') + ')">' + v.label + '</strong>' +
      ' (' + Math.round(data.confidence * 100) + '%)';
    lastScanSection.style.display = 'block';
  }

  // Login
  loginBtn.addEventListener('click', () => {
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    if (!email || !password) return;

    loginBtn.disabled = true;
    loginBtn.textContent = 'Signing in...';
    loginError.classList.add('hidden');

    chrome.runtime.sendMessage({ type: 'LOGIN', email, password }, (res) => {
      loginBtn.disabled = false;
      loginBtn.textContent = 'Sign In';
      if (res && res.ok) {
        showLoggedIn({ email }, null);
      } else {
        loginError.textContent = (res && res.error) || 'Login failed';
        loginError.classList.remove('hidden');
      }
    });
  });

  // Logout
  logoutBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'LOGOUT' }, () => {
      mainSection.style.display = 'none';
      loginSection.classList.remove('hidden');
      scanResult.classList.add('hidden');
      lastScanSection.style.display = 'none';
      statusDot.style.background = 'var(--text-muted)';
    });
  });

  // Manual scan
  scanBtn.addEventListener('click', () => {
    const url = scanUrlInput.value.trim();
    if (!url) return;

    scanBtn.disabled = true;
    scanBtn.textContent = 'Scanning...';
    scanResult.classList.add('hidden');

    chrome.runtime.sendMessage({ type: 'SCAN', url }, (res) => {
      scanBtn.disabled = false;
      scanBtn.textContent = 'Scan';
      if (res && res.ok) {
        showResult(res.data);
      } else {
        scanResult.className = 'result malicious';
        scanResult.innerHTML = 'Error: ' + ((res && res.error) || 'Scan failed');
        scanResult.classList.remove('hidden');
      }
    });
  });

  // Pre-fill with current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0] && tabs[0].url && tabs[0].url.startsWith('http')) {
      scanUrlInput.value = tabs[0].url;
    }
  });

  // API Base URL setting
  const apiBaseInput = document.getElementById('setting-api-base');
  const apiBaseSave = document.getElementById('setting-api-save');
  const apiBaseMsg = document.getElementById('setting-api-msg');
  if (apiBaseInput && apiBaseSave) {
    chrome.runtime.sendMessage({ type: 'GET_API_BASE' }, (res) => {
      if (res && res.ok) {
        apiBaseInput.value = res.url || '';
        apiBaseMsg.textContent = 'Default: ' + (res.default || 'http://localhost:5000');
      }
    });
    apiBaseSave.addEventListener('click', () => {
      chrome.runtime.sendMessage(
        { type: 'SET_API_BASE', url: apiBaseInput.value },
        (res) => {
          apiBaseMsg.textContent = res && res.ok ? 'Saved ✅' : 'Save failed';
        }
      );
    });
  }
});
