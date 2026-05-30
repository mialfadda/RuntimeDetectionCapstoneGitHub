import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';

const CATEGORY_STYLE = {
  benign:     { label: 'Benign',     color: 'bg-[#22c55e]' },
  defacement: { label: 'Defacement', color: 'bg-[#f59e0b]' },
  phishing:   { label: 'Phishing',   color: 'bg-[#ef4444]' },
  malware:    { label: 'Malware',    color: 'bg-[#7c3aed]' },
};

const RISK_STYLE = {
  safe:     { label: 'Safe',     color: 'bg-[#22c55e]' },
  low:      { label: 'Low',      color: 'bg-[#22c55e]' },
  medium:   { label: 'Medium',   color: 'bg-[#f59e0b]' },
  high:     { label: 'High',     color: 'bg-[#ef4444]' },
  critical: { label: 'Critical', color: 'bg-[#7c3aed]' },
};

function categoryBadge(threat_category) {
  return CATEGORY_STYLE[(threat_category || '').toLowerCase()] || {
    label: '—',
    color: 'bg-gray-400',
  };
}

function riskBadge(risk_level) {
  return RISK_STYLE[(risk_level || '').toLowerCase()] || {
    label: '—',
    color: 'bg-gray-400',
  };
}

export default function Scans() {
  const [url, setUrl] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleScan(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await api('/scan/analyze', {
        method: 'POST',
        body: JSON.stringify({ url, source: 'dashboard' }),
      });
      setResults(prev => [{ ...data, scannedAt: new Date().toISOString() }, ...prev]);
      setUrl('');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex-1 p-8">
      <h2 className="text-xl font-bold text-[#1A3A6B] mb-6">Scan URLs</h2>

      <form onSubmit={handleScan} className="flex items-center gap-0 mb-6 max-w-2xl">
        <input
          type="url" required value={url} onChange={e => setUrl(e.target.value)}
          placeholder="Enter URL to scan..."
          className="flex-1 border-2 border-r-0 border-[#2D5FA6] rounded-l-full px-6 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D5FA6]"
        />
        <button type="submit" disabled={loading}
          className="bg-[#2D5FA6] text-white px-8 py-3 rounded-r-full font-semibold text-sm hover:bg-[#1A3A6B] disabled:opacity-50 border-2 border-[#2D5FA6] transition-colors">
          {loading ? 'Scanning...' : 'Scan'}
        </button>
      </form>

      {error && <div className="mb-4 text-[#ef4444] text-sm">{error}</div>}

      {results.length > 0 && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <table className="w-full text-sm text-left">
            <thead className="bg-[#dde6f5] text-[#1A3A6B]">
              <tr>
                <th className="py-3 px-5 font-semibold">URL</th>
                <th className="py-3 px-5 font-semibold">Date</th>
                <th className="py-3 px-5 font-semibold">Category</th>
                <th className="py-3 px-5 font-semibold">Risk</th>
                <th className="py-3 px-5 font-semibold">Confidence %</th>
                <th className="py-3 px-5 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => {
                const cat = categoryBadge(r.threat_category);
                const risk = riskBadge(r.risk_level);
                const isThreat = (r.threat_category || 'benign').toLowerCase() !== 'benign';
                return (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-5 font-mono text-xs max-w-xs truncate text-gray-800">{r.url}</td>
                    <td className="py-3 px-5 text-gray-500 text-xs">{new Date(r.scannedAt).toLocaleDateString()}</td>
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
                    <td className="py-3 px-5 text-gray-700 font-medium">{(r.confidence * 100).toFixed(1)}%</td>
                    <td className="py-3 px-5">
                      {isThreat && r.scan_id && (
                        <Link to={`/explanation/${r.scan_id}`} className="text-[#2D5FA6] hover:underline text-xs font-medium">
                          View Explanation..
                        </Link>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
