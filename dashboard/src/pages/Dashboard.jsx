import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

const CATEGORY_STYLE = {
  benign:     { label: 'Benign',     color: 'bg-[#22c55e]' },
  defacement: { label: 'Defacement', color: 'bg-[#f59e0b]' },
  phishing:   { label: 'Phishing',   color: 'bg-[#ef4444]' },
  malware:    { label: 'Malware',    color: 'bg-[#7c3aed]' },
};

function categoryBadge(threat_category) {
  return CATEGORY_STYLE[(threat_category || '').toLowerCase()] || {
    label: '—',
    color: 'bg-gray-400',
  };
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [scans, setScans] = useState([]);
  const [error, setError] = useState('');

  function load() {
    setError('');
    setMetrics(null);
    Promise.all([
      api('/dashboard/metrics'),
      api('/detections?limit=50'),
    ])
      .then(([m, d]) => {
        setMetrics(m);
        setScans(d.detections || []);
      })
      .catch(e => setError(e.message));
  }

  useEffect(() => { load(); }, []);

  if (error) return (
    <div className="p-8">
      <div className="text-[#ef4444] mb-3">{error}</div>
      <button onClick={load} className="bg-[#2D5FA6] text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#1A3A6B]">Retry</button>
    </div>
  );
  if (!metrics) return <div className="p-8 text-gray-500">Loading dashboard...</div>;

  return (
    <div className="flex-1 p-8">
      {/* Metric cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
        <MetricCard label="Total Scans" value={metrics.total_scans} color="bg-[#2D5FA6]" />
        <MetricCard label="Completed" value={metrics.completed_scans} color="bg-[#22c55e]" />
        <MetricCard label="Pending" value={metrics.pending_scans} color="bg-[#f59e0b]" />
      </div>

      {/* Header row */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-[#1A3A6B]">Recent Scans</h2>
        <Link
          to="/app/scans"
          className="px-5 py-2 bg-[#2D5FA6] text-white rounded-lg font-semibold text-sm hover:bg-[#1A3A6B] transition-colors"
        >
          New Scan
        </Link>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-[#dde6f5] text-[#1A3A6B]">
            <tr>
              <th className="py-3 px-5 font-semibold">URL</th>
              <th className="py-3 px-5 font-semibold">Date</th>
              <th className="py-3 px-5 font-semibold">Category</th>
              <th className="py-3 px-5 font-semibold">Risk</th>
              <th className="py-3 px-5 font-semibold">Confidence %</th>
            </tr>
          </thead>
          <tbody>
            {scans.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-gray-400">No scans yet</td></tr>
            ) : scans.map((s) => {
              const rl = (s.risk_level || '').toLowerCase();
              const risk = {
                safe:     { label: 'Safe',       color: 'bg-[#22c55e]' },
                low:      { label: 'Low',        color: 'bg-[#22c55e]' },
                medium:   { label: 'Medium',     color: 'bg-[#f59e0b]' },
                high:     { label: 'High',       color: 'bg-[#ef4444]' },
                critical: { label: 'Critical',   color: 'bg-[#7c3aed]' },
              }[rl] || { label: s.status || '\u2014', color: 'bg-gray-400' };
              const cat = categoryBadge(s.threat_category);
              return (
                <tr key={s.scan_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-5 font-mono text-xs max-w-xs truncate text-gray-800">{s.url}</td>
                  <td className="py-3 px-5 text-gray-500 text-xs">
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="py-3 px-5">
                    <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${cat.color}`}>
                      {cat.label}
                    </span>
                  </td>
                  <td className="py-3 px-5">
                    <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${risk.color}`}>
                      {risk.label}
                    </span>
                  </td>
                  <td className="py-3 px-5 text-gray-700 font-medium text-xs">
                    {s.confidence != null ? Math.round(s.confidence * 100) + '%' : '\u2014'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function MetricCard({ label, value, color }) {
  return (
    <div className={`${color} rounded-xl p-5 text-white shadow`}>
      <div className="text-sm font-medium opacity-90">{label}</div>
      <div className="text-3xl font-bold mt-1">{value}</div>
    </div>
  );
}
