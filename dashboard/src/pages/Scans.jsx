import { useState } from 'react';
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
      const verdict = mapVerdict(data.risk_level);
      setResults(prev => [{ ...data, verdict, scannedAt: new Date().toISOString() }, ...prev]);
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
                <th className="py-3 px-5 font-semibold">Verdict</th>
                <th className="py-3 px-5 font-semibold">Confidence %</th>
                <th className="py-3 px-5 font-semibold"></th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-5 font-mono text-xs max-w-xs truncate text-gray-800">{r.url}</td>
                  <td className="py-3 px-5 text-gray-500 text-xs">{new Date(r.scannedAt).toLocaleDateString()}</td>
                  <td className="py-3 px-5">
                    <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${verdictColor(r.verdict)}`}>
                      {r.verdict}
                    </span>
                  </td>
                  <td className="py-3 px-5 text-gray-700 font-medium">{(r.confidence * 100).toFixed(1)}%</td>
                  <td className="py-3 px-5">
                    {r.verdict !== 'Safe' && r.scan_id && (
                      <Link to={`/explanation/${r.scan_id}`} className="text-[#2D5FA6] hover:underline text-xs font-medium">
                        View Explanation..
                      </Link>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
