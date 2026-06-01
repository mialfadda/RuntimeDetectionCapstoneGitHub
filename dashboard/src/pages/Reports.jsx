import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api, apiFetchBlob } from '../api/client';

export default function Reports() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [predictionId, setPredictionId] = useState('');
  const [format, setFormat] = useState('pdf');
  const [genMsg, setGenMsg] = useState('');
  const [genLoading, setGenLoading] = useState(false);

  function loadReports() {
    setLoading(true);
    setError('');
    api('/dashboard/reports')
      .then(d => setReports(d.reports || []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }

  useEffect(() => { loadReports(); }, []);

  async function handleGenerate(e) {
    e.preventDefault();
    setGenMsg('');
    setGenLoading(true);
    try {
      const data = await api('/dashboard/reports/generate', {
        method: 'POST',
        body: JSON.stringify({ prediction_id: parseInt(predictionId), format }),
      });
      setGenMsg(`Report #${data.report_id} queued`);
      setPredictionId('');
      loadReports();
    } catch (err) {
      setGenMsg(err.message);
    } finally {
      setGenLoading(false);
    }
  }

  async function handleDownload(reportId, fmt) {
    try {
      const blob = await apiFetchBlob(`/dashboard/reports/${reportId}/download`);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report_${reportId}.${fmt || 'pdf'}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(err.message);
    }
  }

  if (loading) return <div className="p-8 text-gray-500">Loading...</div>;

  return (
    <div className="flex-1 p-8">
      <Link to="/app" className="text-[#2D5FA6] hover:underline text-sm mb-4 inline-block">&larr; Back to Dashboard</Link>
      <h2 className="text-xl font-bold text-[#1A3A6B] mb-6">Reports</h2>

      {/* Generate */}
      <div className="bg-white rounded-xl shadow p-6 mb-6">
        <h3 className="text-base font-semibold text-[#1A3A6B] mb-3">Generate Report</h3>
        <form onSubmit={handleGenerate} className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Prediction ID</label>
            <input type="number" required value={predictionId} onChange={e => setPredictionId(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 w-36 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D5FA6]" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Format</label>
            <select value={format} onChange={e => setFormat(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#2D5FA6]">
              <option value="pdf">PDF</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <button type="submit" disabled={genLoading}
            className="bg-[#2D5FA6] text-white px-5 py-2 rounded-lg font-semibold text-sm hover:bg-[#1A3A6B] disabled:opacity-50 transition-colors">
            {genLoading ? 'Generating...' : 'Generate'}
          </button>
        </form>
        {genMsg && <p className="mt-2 text-sm text-gray-600">{genMsg}</p>}
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-3">
          <div className="text-[#ef4444] text-sm">{error}</div>
          <button onClick={loadReports} className="text-[#2D5FA6] hover:underline text-sm font-medium">Retry</button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-xl shadow overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-[#dde6f5] text-[#1A3A6B]">
            <tr>
              <th className="py-3 px-5 font-semibold">ID</th>
              <th className="py-3 px-5 font-semibold">Threat Level</th>
              <th className="py-3 px-5 font-semibold">Format</th>
              <th className="py-3 px-5 font-semibold">Status</th>
              <th className="py-3 px-5 font-semibold">Generated</th>
              <th className="py-3 px-5 font-semibold"></th>
            </tr>
          </thead>
          <tbody>
            {reports.length === 0 ? (
              <tr><td colSpan={6} className="py-8 text-center text-gray-400">No reports yet</td></tr>
            ) : reports.map(r => (
              <tr key={r.report_id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-5 text-gray-800">{r.report_id}</td>
                <td className="py-3 px-5 capitalize text-gray-700">{r.threat_level}</td>
                <td className="py-3 px-5 uppercase text-xs text-gray-600">{r.format}</td>
                <td className="py-3 px-5">
                  <span className={`px-3 py-1 rounded-full text-white text-xs font-semibold ${
                    r.status === 'complete' ? 'bg-[#22c55e]' : 'bg-[#f59e0b]'
                  }`}>{r.status}</span>
                </td>
                <td className="py-3 px-5 text-gray-500 text-xs">
                  {r.generated_at ? new Date(r.generated_at).toLocaleString() : '-'}
                </td>
                <td className="py-3 px-5">
                  <button onClick={() => handleDownload(r.report_id, r.format)}
                    className="text-[#2D5FA6] hover:underline text-xs font-medium">Download</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
