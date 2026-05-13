import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register(name, email, password);
      navigate('/app');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 px-6">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <Link to="/" className="text-[#2D5FA6] hover:underline text-sm mb-4 inline-block">&larr; Back to Home</Link>
        <h2 className="text-2xl font-bold text-[#1A3A6B] text-center mb-6">Create Account</h2>
        {error && <div className="bg-red-50 border border-red-200 text-[#ef4444] rounded-lg p-3 mb-4 text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} placeholder="Optional"
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2D5FA6] focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2D5FA6] focus:border-transparent" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-[#2D5FA6] focus:border-transparent" />
            <p className="text-xs text-gray-400 mt-1">At least 8 characters</p>
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-[#2D5FA6] text-white py-2.5 rounded-lg hover:bg-[#1A3A6B] disabled:opacity-50 font-semibold transition-colors">
            {loading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>
        <p className="mt-5 text-center text-sm text-gray-500">
          Already have an account? <Link to="/login" className="text-[#2D5FA6] hover:underline font-medium">Sign In</Link>
        </p>
      </div>
    </div>
  );
}
