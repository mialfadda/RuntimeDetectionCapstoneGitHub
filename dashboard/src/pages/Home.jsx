import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col items-center justify-center bg-white px-6">
      <div className="text-center max-w-3xl">
        {/* Hero */}
        <div className="mb-6">
          <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-[#dde6f5] flex items-center justify-center">
            <svg className="w-10 h-10 text-[#2D5FA6]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-[#1A3A6B] leading-tight tracking-tight">
            DETECT MALICIOUS<br />WEBSITES INSTANTLY
          </h1>
          <p className="mt-4 text-gray-500 text-lg">
            Protect yourself from phishing, malware, and other online threats with real-time detection.
          </p>
        </div>

        {/* Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-8">
          <Link
            to="/extension"
            className="px-8 py-3 bg-[#2D5FA6] text-white rounded-full font-semibold text-sm hover:bg-[#1A3A6B] transition-colors shadow-md"
          >
            Download Extension
          </Link>
          <Link
            to="/scan"
            className="px-8 py-3 border-2 border-[#2D5FA6] text-[#2D5FA6] rounded-full font-semibold text-sm hover:bg-[#dde6f5] transition-colors"
          >
            Check URL Now
          </Link>
        </div>

        {/* Text links */}
        <div className="flex items-center justify-center gap-6 mt-6 text-sm">
          {user ? (
            <Link to="/app" className="text-[#2D5FA6] hover:underline font-medium">Go to Dashboard</Link>
          ) : (
            <>
              <Link to="/login" className="text-[#2D5FA6] hover:underline font-medium">Log In</Link>
              <Link to="/scan" className="text-gray-500 hover:text-gray-700 font-medium">Continue as Guest</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
