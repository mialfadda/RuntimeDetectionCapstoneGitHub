function getApiBase() {
  return (typeof localStorage !== 'undefined' && localStorage.getItem('api_base')) || '';
}

export function getToken() {
  return sessionStorage.getItem('access_token');
}

function getRefreshToken() {
  return sessionStorage.getItem('refresh_token');
}

export function setTokens(access, refresh) {
  if (access) sessionStorage.setItem('access_token', access);
  else sessionStorage.removeItem('access_token');
  if (refresh) sessionStorage.setItem('refresh_token', refresh);
  else sessionStorage.removeItem('refresh_token');
}

export function clearTokens() {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
  sessionStorage.removeItem('user');
}

async function refreshAccessToken() {
  const rt = getRefreshToken();
  if (!rt) throw new Error('No refresh token');
  const res = await fetch(`${getApiBase()}/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${rt}`,
    },
  });
  if (!res.ok) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  const data = await res.json();
  sessionStorage.setItem('access_token', data.access_token);
  return data.access_token;
}

export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let res = await fetch(`${getApiBase()}${path}`, { ...options, headers });

  if (res.status === 401 && getRefreshToken() && !options._retried) {
    const newToken = await refreshAccessToken();
    headers.Authorization = `Bearer ${newToken}`;
    res = await fetch(`${getApiBase()}${path}`, { ...options, headers, _retried: true });
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const err = new Error(body.error || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function apiFetchBlob(path) {
  const token = getToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(`${getApiBase()}${path}`, { headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || 'Download failed');
  }
  return res.blob();
}
