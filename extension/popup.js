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
  const lastScanDiv = document.getElementById('last-scan');
  const lastScanInfo = document.getElementById('last-scan-info');

  function mapVerdict(riskLevel) {
    if (riskLevel === 'safe' || riskLevel === 'low') return { label: 'Safe ✅', cls: 'safe' };
    if (riskLevel === 'medium') return { label: 'Suspicious ⚠️', cls: 'suspicious' };
    return { label: 'Malicious! 💀', cls: 'malicious' };
  }

  function showResult(data) {
    const v = mapVerdict(data.risk_level);
    scanResult.className = `result ${v.cls}`;
    scanResult.innerHTML = `
      ${v.label}
      <div class="detail">Confidence: ${Math.round(data.confidence * 100)}% · ${data.threat_category}</div>
    `;
    scanResult.classList.remove('hidden');
  }

  // Check login status
  chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (res) => {
    if (res && res.loggedIn) {
      loginSection.classList.add('hidden');
      mainSection.classList.remove('hidden');
      userInfo.textContent = res.user ? `Signed in as ${res.user.email}` : 'Signed in';
      if (res.lastScan) {
        showLastScan(res.lastScan);
      }
    } else {
      loginSection.classList.remove('hidden');
      mainSection.classList.add('hidden');
    }
  });

  function showLastScan(data) {
    const v = mapVerdict(data.risk_level);
    lastScanInfo.innerHTML = `
      <span>${data.url}</span><br/>
      <strong class="${v.cls}">${v.label}</strong> (${Math.round(data.confidence * 100)}%)
    `;
    lastScanDiv.classList.remove('hidden');
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
        loginSection.classList.add('hidden');
        mainSection.classList.remove('hidden');
        userInfo.textContent = `Signed in as ${email}`;
      } else {
        loginError.textContent = res?.error || 'Login failed';
        loginError.classList.remove('hidden');
      }
    });
  });

  // Logout
  logoutBtn.addEventListener('click', () => {
    chrome.runtime.sendMessage({ type: 'LOGOUT' }, () => {
      mainSection.classList.add('hidden');
      loginSection.classList.remove('hidden');
      scanResult.classList.add('hidden');
      lastScanDiv.classList.add('hidden');
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
        scanResult.innerHTML = `Error: ${res?.error || 'Scan failed'}`;
        scanResult.classList.remove('hidden');
      }
    });
  });

  // Pre-fill with current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]?.url && tabs[0].url.startsWith('http')) {
      scanUrlInput.value = tabs[0].url;
    }
  });
});
