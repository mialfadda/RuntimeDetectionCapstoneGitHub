import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/client';

export default function Explanation() {
  const { scanId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  function load() {
    setLoading(true);
    setError('');
    api(`/explanations/${scanId}`)
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { load(); }, [scanId]);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh] text-gray-500">Loading explanation...</div>;
  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3">
      <div className="text-[#ef4444]">{error}</div>
      <button onClick={load} className="bg-[#2D5FA6] text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-[#1A3A6B]">Retry</button>
      <Link to="/scan" className="text-[#2D5FA6] hover:underline text-sm">&larr; Back to Scanner</Link>
    </div>
  );

  const features = data?.top_features || [];
  const shapValues = data?.shap_values || {};

  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50 py-10 px-6">
      <div className="max-w-3xl mx-auto">
        <Link to="/scan" className="text-[#2D5FA6] hover:underline text-sm mb-6 inline-block">&larr; Back to Scanner</Link>

        <h1 className="text-2xl font-bold text-[#1A3A6B] mb-6">Why this website was flagged</h1>

        {/* Summary box */}
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-[#1A3A6B] mb-3">Summary</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            {data?.summary_text || 'No summary available.'}
          </p>
        </div>

        {/* Detected Indicators */}
        <div className="bg-white rounded-xl shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-[#1A3A6B] mb-4">Detected Indicators</h2>
          {features.length > 0 ? (
            <div className="space-y-3">
              {features.map(([name, value], i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-40 text-sm text-gray-700 font-medium">{name}</div>
                  <div className="flex-1 bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-[#2D5FA6] h-3 rounded-full transition-all"
                      style={{ width: `${Math.min(value * 100, 100)}%` }}
                    />
                  </div>
                  <div className="w-14 text-right text-sm text-gray-500 font-medium">
                    {(value * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No indicators available.</p>
          )}
        </div>

        {/* Confidence & Recommendation */}
        <div className="bg-white rounded-xl shadow p-6">
          <h2 className="text-lg font-semibold text-[#1A3A6B] mb-3">Confidence & Recommendation</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-[#dde6f5] rounded-lg p-4 text-center">
              <div className="text-sm text-gray-600 mb-1">Method</div>
              <div className="text-lg font-bold text-[#1A3A6B] uppercase">{data?.method || 'N/A'}</div>
            </div>
            <div className="bg-[#dde6f5] rounded-lg p-4 text-center">
              <div className="text-sm text-gray-600 mb-1">Confidence</div>
              <div className="text-lg font-bold text-[#1A3A6B]">
                {data?.confidence != null ? Math.round(data.confidence * 100) + '%' : '—'}
              </div>
            </div>
            <div className="bg-[#dde6f5] rounded-lg p-4 text-center">
              <div className="text-sm text-gray-600 mb-1">Recommendation</div>
              <div className="text-lg font-bold text-[#ef4444]">
                {features.length > 0 ? 'Avoid this site' : 'Likely safe'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
