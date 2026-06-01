import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const [moreOpen, setMoreOpen] = useState(false);
  const ref = useRef(null);
  const { user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    function close(e) { if (ref.current && !ref.current.contains(e.target)) setMoreOpen(false); }
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link to="/" className="text-[#2D5FA6] font-bold text-xl tracking-wide">
          RUNTIME MALWEB DETECTOR
        </Link>

        {/* Links */}
        <div className="flex items-center gap-8">
          <Link to="/" className="text-gray-700 hover:text-[#2D5FA6] font-medium text-sm">Home</Link>
          <Link to="/scan" className="text-gray-700 hover:text-[#2D5FA6] font-medium text-sm">Features</Link>

          {/* More dropdown */}
          <div className="relative" ref={ref}>
            <button
              onClick={() => setMoreOpen(!moreOpen)}
              className="text-gray-700 hover:text-[#2D5FA6] font-medium text-sm flex items-center gap-1"
            >
              More
              <svg className={`w-4 h-4 transition-transform ${moreOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {moreOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                {!user && (
                  <>
                    <Link to="/register" onClick={() => setMoreOpen(false)} className="block px-4 py-2 text-sm text-gray-700 hover:bg-[#dde6f5]">Sign Up</Link>
                    <Link to="/login" onClick={() => setMoreOpen(false)} className="block px-4 py-2 text-sm text-gray-700 hover:bg-[#dde6f5]">Log In</Link>
                  </>
                )}
                <Link to="/extension" onClick={() => setMoreOpen(false)} className="block px-4 py-2 text-sm text-gray-700 hover:bg-[#dde6f5]">Download Extension</Link>
                <Link to={user ? '/app' : '/login'} onClick={() => setMoreOpen(false)} className="block px-4 py-2 text-sm text-gray-700 hover:bg-[#dde6f5]">Dashboard</Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
