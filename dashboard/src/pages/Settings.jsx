import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();
  const [apiBase, setApiBase] = useState(
    () => localStorage.getItem('api_base') || ''
  );
  const [saved, setSaved] = useState(false);

  function handleSave(e) {
    e.preventDefault();
    localStorage.setItem('api_base', apiBase.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  return (
    <div className="flex-1 p-8">
      <Link to="/app" className="text-[#2D5FA6] hover:underline text-sm mb-4 inline-block">&larr; Back to Dashboard</Link>
      <h2 className="text-xl font-bold text-[#1A3A6B] mb-6">Settings</h2>

      {/* Account */}
      <div className="bg-white rounded-xl shadow p-6 max-w-lg mb-6">
        <h3 className="text-base font-semibold text-[#1A3A6B] mb-4">Account</h3>
        <dl className="space-y-3 text-sm">
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Name</dt>
            <dd className="text-gray-800">{user?.name || user?.email?.split('@')[0] || '-'}</dd>
          </div>
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Email</dt>
            <dd className="text-gray-800">{user?.email || '-'}</dd>
          </div>
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Role</dt>
            <dd>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                user?.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-[#dde6f5] text-[#1A3A6B]'
              }`}>{user?.role || 'user'}</span>
            </dd>
          </div>
        </dl>
      </div>

      {/* API */}
      <div className="bg-white rounded-xl shadow p-6 max-w-lg">
        <h3 className="text-base font-semibold text-[#1A3A6B] mb-4">API</h3>
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">API base URL</label>
            <input
              type="text"
              value={apiBase}
              onChange={e => setApiBase(e.target.value)}
              placeholder="(empty = same origin / Vite proxy)"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D5FA6]"
            />
            <p className="text-xs text-gray-400 mt-1">
              Leave empty for the default (dev: Vite proxy, prod: same origin). Example: <code className="bg-gray-100 px-1 rounded">http://localhost:5000</code>
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button type="submit" className="bg-[#2D5FA6] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:bg-[#1A3A6B] transition-colors">
              Save
            </button>
            {saved && <span className="text-[#22c55e] text-sm">Saved &#x2705;</span>}
          </div>
        </form>
      </div>
    </div>
  );
}
