import React, { useState, useEffect } from 'react';
import { getAllServerSeeds, createServerSeed, deleteServerSeed } from '../services/api';
import { formatDateShort } from '../utils/format';

function ServerSeeds() {
  const [seeds, setSeeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [seedDate, setSeedDate] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadSeeds();
    const interval = setInterval(loadSeeds, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadSeeds = async () => {
    try {
      const data = await getAllServerSeeds();
      setSeeds(data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load server seeds');
      console.error('Server seeds error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSeed = async (e) => {
    e.preventDefault();
    
    if (!seedDate) {
      alert('Please select a date');
      return;
    }

    try {
      setCreating(true);
      // Send the date directly (YYYY-MM-DD format)
      const result = await createServerSeed(seedDate);
      alert(`✅ ${result.message || 'Server seed created/updated successfully!'}`);
      setShowCreateModal(false);
      setSeedDate('');
      loadSeeds();
    } catch (err) {
      alert(`❌ Failed to create/update server seed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (seedId) => {
    if (!window.confirm('⚠️ Delete this server seed? This action cannot be undone.')) {
      return;
    }

    try {
      await deleteServerSeed(seedId);
      alert('✅ Server seed deleted successfully!');
      loadSeeds();
    } catch (err) {
      alert(`❌ Failed to delete server seed: ${err.response?.data?.detail || err.message}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="text-gray-500">Loading server seeds...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">🔐 Server Seed Management</h2>
              <p className="text-sm text-gray-500 mt-1">
                Manage fixed server seeds for provably fair system
              </p>
            </div>
            
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 font-medium"
            >
              ➕ Generate New Seed
            </button>
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          {/* Seeds Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Seed Hash</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Bet Count</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {seeds.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-6 py-8 text-center text-gray-500">
                      No server seeds found. Generate a new one to get started.
                    </td>
                  </tr>
                ) : (
                  seeds.map((seed) => {
                    const today = new Date().toISOString().split('T')[0];
                    const isToday = seed.seed_date === today;
                    const isPast = seed.seed_date < today;
                    const canDelete = !isPast;
                    
                    return (
                      <tr key={seed.seed_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{seed.seed_date}</div>
                          {isToday && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                              Today
                            </span>
                          )}
                          {isPast && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600 mt-1">
                              Past
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm font-mono text-gray-900">
                            {seed.server_seed_hash.substring(0, 32)}...
                          </div>
                          <div className="text-xs text-gray-500">Click to copy full hash</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDateShort(seed.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {seed.bet_count || 0}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {canDelete ? (
                            <button
                              onClick={() => handleDelete(seed.seed_id)}
                              className="text-red-600 hover:text-red-900 font-medium"
                            >
                              Delete
                            </button>
                          ) : (
                            <span className="text-gray-400 text-xs">Cannot delete past dates</span>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white px-6 py-4 rounded-t-lg">
              <h3 className="text-xl font-bold">🔐 Generate Server Seed</h3>
              <p className="text-sm text-green-100 mt-1">
                Create a server seed for a specific date (one seed per day)
              </p>
            </div>

            <form onSubmit={handleCreateSeed} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date *
                </label>
                <input
                  type="date"
                  value={seedDate}
                  onChange={(e) => setSeedDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-green-500 focus:outline-none"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Select the date for this server seed. One seed per day. Past dates are not allowed.
                </p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setSeedDate('');
                  }}
                  disabled={creating}
                  className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 bg-gradient-to-r from-green-600 to-blue-600 text-white px-4 py-2 rounded-lg hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {creating ? '⏳ Creating...' : '🔐 Create Seed'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ServerSeeds;
