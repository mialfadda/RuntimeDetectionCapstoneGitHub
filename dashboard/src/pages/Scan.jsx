import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../api/client';

function mapVerdict(risk_level) {
  if (risk_level === 'safe' || risk_level === 'low') return 'safe';
  if (risk_level === 'medium') return 'suspicious';
  return 'malicious';
}

export default function Scan() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  async function handleScan(e) {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const data = await api('/scan/analyze', {
        method: 'POST',
        body: JSON.stringify({ url, source: 'dashboard' }),
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const verdict = result ? mapVerdict(result.risk_level) : null;

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center bg-white px-6">
      <div className="w-full max-w-2xl">
        {/* Scan input */}
        <form onSubmit={handleScan} className="flex items-center gap-0">
          <input
            type="url"
            required
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder="Enter URL to scan..."
            className="flex-1 border-2 border-r-0 border-[#2D5FA6] rounded-l-full px-6 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D5FA6]"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-[#2D5FA6] text-white px-8 py-3 rounded-r-full font-semibold text-sm hover:bg-[#1A3A6B] disabled:opacity-50 border-2 border-[#2D5FA6] transition-colors"
          >
            {loading ? 'Scanning...' : 'Scan'}
          </button>
        </form>

        {error && <div className="mt-4 text-[#ef4444] text-sm text-center">{error}</div>}

        {/* Result */}
        {result && (
          <div className="mt-8 text-center">
            {verdict === 'safe' && (
              <div>
                <p className="text-4xl font-bold text-[#22c55e]">Safe! &#x2705;</p>
                <p className="mt-2 text-gray-500 text-sm">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
              </div>
            )}
            {verdict === 'suspicious' && (
              <div>
                <p className="text-4xl font-bold text-[#f59e0b]">Suspicious &#x26A0;&#xFE0F;</p>
                <p className="mt-2 text-gray-500 text-sm">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                <Link to={`/explanation/${result.scan_id}`} className="mt-3 inline-block text-[#2D5FA6] hover:underline text-sm font-medium">
                  View Explanation..
                </Link>
              </div>
            )}
            {verdict === 'malicious' && (
              <div>
                <p className="text-4xl font-bold text-[#ef4444]">Malicious! &#x1F480;</p>
                <p className="mt-2 text-gray-500 text-sm">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                <Link to={`/explanation/${result.scan_id}`} className="mt-3 inline-block text-[#2D5FA6] hover:underline text-sm font-medium">
                  View Explanation..
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Warning interstitial for malicious */}
        {result && verdict === 'malicious' && (
          <div className="mt-8 border-2 border-[#ef4444] rounded-xl p-8 bg-white text-center">
            <div className="text-5xl mb-4">&#x26A0;</div>
            <h2 className="text-2xl font-bold text-[#ef4444] mb-2">WARNING!</h2>
            <p className="text-gray-600 mb-6">This site may be malicious</p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                to={`/explanation/${result.scan_id}`}
                className="px-6 py-2.5 bg-[#2D5FA6] text-white rounded-lg font-semibold text-sm hover:bg-[#1A3A6B] transition-colors"
              >
                View Explanation
              </Link>
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2.5 border border-gray-300 text-gray-600 rounded-lg font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                Proceed Anyway
              </a>
              <button
                onClick={() => { setResult(null); setUrl(''); }}
                className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold text-sm hover:bg-gray-200 transition-colors"
              >
                Go Back
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
