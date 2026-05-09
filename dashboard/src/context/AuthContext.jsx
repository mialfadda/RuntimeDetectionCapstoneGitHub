import { createContext, useContext, useState, useEffect } from 'react';
import { api, setTokens, clearTokens } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const s = sessionStorage.getItem('user');
    return s ? JSON.parse(s) : null;
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      api('/auth/me')
        .then((u) => { setUser(u); sessionStorage.setItem('user', JSON.stringify(u)); })
        .catch(() => { clearTokens(); setUser(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  async function login(email, password) {
    const data = await api('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    setTokens(data.access_token, data.refresh_token);
    const u = { user_id: data.user_id, email, role: data.role };
    setUser(u);
    sessionStorage.setItem('user', JSON.stringify(u));
    return data;
  }

  async function register(name, email, password) {
    const data = await api('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    setTokens(data.access_token, data.refresh_token);
    const u = { user_id: data.user_id, email, role: data.role };
    setUser(u);
    sessionStorage.setItem('user', JSON.stringify(u));
    return data;
  }

  async function logout() {
    try { await api('/auth/logout', { method: 'POST' }); } catch {}
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
