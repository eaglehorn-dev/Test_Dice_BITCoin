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
      // Handle empty vault scenario gracefully
      if (err.response?.status === 500 || err.message?.includes('No active vault wallets')) {
        setDashboard({
          treasury_balance_sats: 0,
          treasury_balance_btc: 0,
          treasury_balance_usd: null,
          btc_price_usd: null,
          today_stats: { total_bets: 0, total_income: 0, total_payout: 0, net_profit: 0, total_wins: 0, total_losses: 0, win_rate: 0 },
          week_stats: { total_bets: 0, total_income: 0, total_payout: 0, net_profit: 0, total_wins: 0, total_losses: 0, win_rate: 0 },
          month_stats: { total_bets: 0, total_income: 0, total_payout: 0, net_profit: 0, total_wins: 0, total_losses: 0, win_rate: 0 },
          all_time_stats: { total_bets: 0, total_income: 0, total_payout: 0, net_profit: 0, total_wins: 0, total_losses: 0, win_rate: 0 },
          wallets: [],
          volume_by_multiplier: [],
          is_testnet: true
        });
        setError(null); // Clear error, show empty state instead
      } else {
        setError(err.response?.data?.detail || 'Failed to load dashboard');
        console.error('Dashboard error:', err);
      }
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

  // Check if vault is empty (no wallets)
  const isVaultEmpty = dashboard && dashboard.wallets && dashboard.wallets.length === 0;

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">🔐 Admin Dashboard</h1>
              <p className="text-gray-600 mt-1">
                Bitcoin Dice Game Management
                {dashboard?.is_testnet && <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">TESTNET</span>}
              </p>
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

      {/* Empty Vault Warning */}
      {isVaultEmpty && (
        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="bg-yellow-50 border-2 border-yellow-300 rounded-lg p-8 text-center">
            <div className="text-6xl mb-4">⚠️</div>
            <h2 className="text-2xl font-bold text-yellow-900 mb-2">Vault is Empty</h2>
            <p className="text-yellow-700 mb-6">
              No wallet addresses found. You need to generate vault wallets before the system can operate.
            </p>
            <div className="bg-white rounded-lg p-6 max-w-2xl mx-auto text-left">
              <h3 className="font-semibold text-gray-900 mb-3">Quick Setup:</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                <li>Run the wallet generation script in the backend</li>
                <li>Or use the Wallet Management section below to create wallets manually</li>
                <li>Recommended: Generate wallets for 2x, 3x, 5x, 10x, and 100x multipliers</li>
              </ol>
              <div className="mt-4 p-4 bg-gray-50 rounded border border-gray-200">
                <p className="text-sm font-mono text-gray-800">
                  cd backend<br/>
                  python generate_wallets.py
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      {!isVaultEmpty && (
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
                <p className="text-4xl font-bold">
                  {dashboard.is_testnet ? 'N/A (Testnet)' : formatUSD(dashboard.treasury_balance_usd)}
                </p>
              </div>
              <div>
                <p className="text-blue-100 text-sm">BTC Price</p>
                <p className="text-2xl font-semibold">
                  {dashboard.is_testnet ? 'N/A (Testnet)' : formatUSD(dashboard.btc_price_usd)}
                </p>
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
      )}

      {/* Wallet Management Section (always show) */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <WalletGrid wallets={dashboard?.wallets || []} onUpdate={loadDashboard} />
      </div>
    </div>
  );
}

export default Dashboard;
