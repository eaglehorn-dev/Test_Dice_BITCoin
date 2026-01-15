import React, { useState } from 'react';
import { withdrawToColStorage, deleteWallet } from '../services/api';
import { formatSats, formatUSD, formatDateShort } from '../utils/format';
import WalletModal from './WalletModal';

function WalletGrid({ wallets, onUpdate }) {
  const [showModal, setShowModal] = useState(false);
  const [editingWallet, setEditingWallet] = useState(null);
  const [withdrawing, setWithdrawing] = useState(null);
  const [deleting, setDeleting] = useState(null);

  const handleWithdraw = async (wallet) => {
    if (!window.confirm(`Withdraw entire balance from ${wallet.multiplier}x wallet (${wallet.address})?\n\nThis will send funds to cold storage.`)) {
      return;
    }

    try {
      setWithdrawing(wallet.wallet_id);
      const result = await withdrawToColStorage(wallet.wallet_id);
      alert(`✅ Withdrawal successful!\n\nTXID: ${result.txid}\nAmount: ${formatSats(result.amount_sent)} sats\nFee: ${formatSats(result.fee)} sats`);
      onUpdate();
    } catch (error) {
      alert(`❌ Withdrawal failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setWithdrawing(null);
    }
  };

  const handleEditWallet = (wallet) => {
    setEditingWallet(wallet);
    setShowModal(true);
  };

  const handleDeleteWallet = async (wallet) => {
    const confirmMsg = `⚠️ WARNING: This will permanently delete the wallet!\n\nMultiplier: ${wallet.multiplier}x\nAddress: ${wallet.address}\n\nThis cannot be undone! Continue?`;
    
    if (!window.confirm(confirmMsg)) {
      return;
    }

    try {
      setDeleting(wallet.wallet_id);
      await deleteWallet(wallet.wallet_id);
      alert(`✅ Wallet deleted successfully!`);
      onUpdate();
    } catch (error) {
      alert(`❌ Failed to delete wallet: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeleting(null);
    }
  };

  const handleModalClose = (success) => {
    setShowModal(false);
    setEditingWallet(null);
    if (success) {
      onUpdate();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">🔑 Wallet Vault</h2>
        
        {/* Generate Wallet Button */}
        <button
          onClick={() => setShowModal(true)}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 flex items-center gap-2 font-medium"
        >
          ➕ Create New Wallet
        </button>
      </div>

      {/* Wallets Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Multiplier</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Chance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Balance</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stats</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {wallets.sort((a, b) => a.multiplier - b.multiplier).map((wallet) => (
              <tr key={wallet.wallet_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                    {wallet.multiplier}x
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{wallet.chance?.toFixed(2) || 'N/A'}%</div>
                  <div className="text-xs text-gray-500">Win chance</div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm font-mono text-gray-900">{wallet.address.substring(0, 25)}...</div>
                  <div className="text-xs text-gray-500">{wallet.label || 'No label'}</div>
                  <div className="text-xs text-gray-400">Created: {formatDateShort(wallet.created_at)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{wallet.address_type || 'legacy'}</div>
                  <div className="text-xs text-gray-500">{wallet.address_format || 'P2PKH'}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-gray-900">{formatSats(wallet.balance_sats || 0)} sats</div>
                  <div className="text-xs text-gray-500">{formatUSD(wallet.balance_usd || 0)}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div>Bets: {wallet.bet_count}</div>
                  <div>Received: {formatSats(wallet.total_received)} sats</div>
                  <div>Sent: {formatSats(wallet.total_sent)} sats</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {wallet.is_active && !wallet.is_depleted && (
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      Active
                    </span>
                  )}
                  {wallet.is_depleted && (
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      Depleted
                    </span>
                  )}
                  {!wallet.is_active && (
                    <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                      Inactive
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <div className="flex gap-2 flex-wrap">
                    <button
                      onClick={() => handleEditWallet(wallet)}
                      className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-xs"
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleWithdraw(wallet)}
                      disabled={withdrawing === wallet.wallet_id || (wallet.balance_sats || 0) < 1000}
                      className="bg-orange-600 text-white px-3 py-1 rounded hover:bg-orange-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-xs"
                    >
                      {withdrawing === wallet.wallet_id ? '⏳' : '💸 Withdraw'}
                    </button>
                    <button
                      onClick={() => handleDeleteWallet(wallet)}
                      disabled={deleting === wallet.wallet_id}
                      className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-xs"
                    >
                      {deleting === wallet.wallet_id ? '⏳' : '🗑️ Delete'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {wallets.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          <p className="text-lg">No wallets yet</p>
          <p className="text-sm">Create your first wallet using the button above</p>
        </div>
      )}

      {/* Wallet Modal */}
      {showModal && (
        <WalletModal
          wallet={editingWallet}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}

export default WalletGrid;
