import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

function mapVerdict(risk_level) {
  if (risk_level === 'safe' || risk_level === 'low') return 'Safe';
  if (risk_level === 'medium') return 'Suspicious';
  return 'Malicious';
}

function verdictColor(v) {
  if (v === 'Safe') return 'bg-[#22c55e]';
  if (v === 'Suspicious') return 'bg-[#f59e0b]';
  return 'bg-[#ef4444]';
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [scans, setScans] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      api('/dashboard/metrics'),
      api('/detections?limit=50'),
    ])
      .then(([m, d]) => {
        setMetrics(m);
        setScans(d.detections || []);
      })
      .catch(e => setError(e.message));
  }, []);

  if (error) return <div className="p-8 text-[#ef4444]">{error}</div>;
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
              <th className="py-3 px-5 font-semibold">Verdict</th>
              <th className="py-3 px-5 font-semibold">Confidence %</th>
            </tr>
          </thead>
          <tbody>
            {scans.length === 0 ? (
              <tr><td colSpan={4} className="py-8 text-center text-gray-400">No scans yet</td></tr>
            ) : scans.map((s) => {
              // detections endpoint doesn't return verdict/confidence,
              // so we show status and N/A for confidence
              const verdict = s.status === 'completed' ? 'Completed' : 'Pending';
              return (
                <tr key={s.scan_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-5 font-mono text-xs max-w-xs truncate text-gray-800">{s.url}</td>
                  <td className="py-3 px-5 text-gray-500 text-xs">
                    {s.created_at ? new Date(s.created_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="py-3 px-5">
                    <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${
                      s.status === 'completed' ? 'bg-[#22c55e]' : 'bg-[#f59e0b]'
                    }`}>
                      {verdict}
                    </span>
                  </td>
                  <td className="py-3 px-5 text-gray-500 text-xs">-</td>
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
