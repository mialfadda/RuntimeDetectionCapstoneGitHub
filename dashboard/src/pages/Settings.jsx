import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user } = useAuth();

  return (
    <div className="flex-1 p-8">
      <h2 className="text-xl font-bold text-[#1A3A6B] mb-6">Settings</h2>

      <div className="bg-white rounded-xl shadow p-6 max-w-lg">
        <h3 className="text-base font-semibold text-[#1A3A6B] mb-4">Account</h3>
        <dl className="space-y-3 text-sm">
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Name</dt>
            <dd className="text-gray-800">{user?.name || user?.email?.split('@')[0] || '-'}</dd>
          </div>
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Email</dt>
            <dd className="text-gray-800">{user?.email || '-'}</dd>
          </div>
          <div className="flex">
            <dt className="w-28 text-gray-500 font-medium">Role</dt>
            <dd>
              <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                user?.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-[#dde6f5] text-[#1A3A6B]'
              }`}>{user?.role || 'user'}</span>
            </dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
