import { useSearchParams, Link, useNavigate } from 'react-router-dom';

export default function Warning() {
  const [params] = useSearchParams();
  const scanId = params.get('scan_id');
  const url = params.get('url') || '';
  const confidence = params.get('confidence');
  const category = params.get('category') || '';
  const navigate = useNavigate();

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 px-6">
      <div className="w-full max-w-lg border-2 border-[#ef4444] rounded-xl p-10 bg-white text-center shadow-lg">
        <div className="text-6xl mb-4">&#x26A0;</div>
        <h1 className="text-3xl font-extrabold text-[#ef4444] mb-2">WARNING!</h1>
        <p className="text-gray-600 mb-2 text-lg">This site may be malicious</p>
        {url && <p className="text-gray-400 text-xs font-mono break-all mb-1">{url}</p>}
        {confidence && (
          <p className="text-gray-400 text-xs mb-6">
            Threat: <strong className="text-gray-600 capitalize">{category}</strong> &middot; Confidence: <strong className="text-gray-600">{confidence}%</strong>
          </p>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mt-4">
          {scanId && (
            <Link
              to={`/explanation/${scanId}`}
              className="px-6 py-2.5 bg-[#2D5FA6] text-white rounded-lg font-semibold text-sm hover:bg-[#1A3A6B] transition-colors w-full sm:w-auto"
            >
              View Explanation
            </Link>
          )}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-2.5 border border-gray-300 text-gray-600 rounded-lg font-semibold text-sm hover:bg-gray-50 transition-colors w-full sm:w-auto"
          >
            Proceed Anyway
          </a>
          <button
            onClick={() => navigate('/scan')}
            className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-semibold text-sm hover:bg-gray-200 transition-colors w-full sm:w-auto"
          >
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}
