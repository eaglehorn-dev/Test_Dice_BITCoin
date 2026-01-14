import React, { useState, useEffect } from 'react';
import { getDashboard } from '../services/api';
import StatsCards from '../components/StatsCards';
import WalletGrid from '../components/WalletGrid';
import VolumeChart from '../components/VolumeChart';
import { formatUSD, formatBTC } from '../utils/format';

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await getDashboard();
      setDashboard(data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !dashboard) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <h3 className="text-red-800 font-bold text-lg mb-2">Error</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadDashboard}
            className="mt-4 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🔐 Admin Dashboard</h1>
              <p className="text-gray-600 mt-1">Bitcoin Dice Game Management</p>
            </div>
            <button
              onClick={loadDashboard}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <span>🔄</span> Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Treasury Balance */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg p-8 text-white mb-8">
          <h2 className="text-xl font-semibold mb-4">💰 Total Treasury Balance</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-blue-100 text-sm">Bitcoin</p>
              <p className="text-4xl font-bold">{formatBTC(dashboard.treasury_balance_btc)} BTC</p>
            </div>
            <div>
              <p className="text-blue-100 text-sm">USD Value</p>
              <p className="text-4xl font-bold">{formatUSD(dashboard.treasury_balance_usd)}</p>
            </div>
            <div>
              <p className="text-blue-100 text-sm">BTC Price</p>
              <p className="text-2xl font-semibold">{formatUSD(dashboard.btc_price_usd)}</p>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <StatsCards dashboard={dashboard} />

        {/* Wallets Grid */}
        <WalletGrid wallets={dashboard.wallets} onUpdate={loadDashboard} />

        {/* Volume Chart */}
        <VolumeChart data={dashboard.volume_by_multiplier} />
      </div>
    </div>
  );
}

export default Dashboard;
