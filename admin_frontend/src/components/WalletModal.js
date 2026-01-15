import React, { useState } from 'react';
import { generateWallet, updateWallet } from '../services/api';

function WalletModal({ wallet, onClose }) {
  const isEdit = !!wallet;
  const [formData, setFormData] = useState({
    multiplier: wallet?.multiplier || '',
    chance: wallet?.chance || '',
    addressType: wallet?.address_type || 'segwit',
    label: wallet?.label || '',
    isActive: wallet?.is_active ?? true
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validation
    if (!isEdit && (!formData.multiplier || parseInt(formData.multiplier) < 1)) {
      alert('Please enter a valid multiplier (minimum 1)');
      return;
    }

    try {
      setLoading(true);

      if (isEdit) {
        // Update existing wallet
        await updateWallet(wallet.wallet_id, {
          multiplier: parseInt(formData.multiplier),
          chance: parseFloat(formData.chance),
          label: formData.label || null,
          is_active: formData.isActive
        });
        alert('✅ Wallet updated successfully!');
      } else {
        // Create new wallet
        await generateWallet(
          parseInt(formData.multiplier),
          formData.addressType,
          parseFloat(formData.chance)
        );
        alert(`✅ Successfully generated ${formData.multiplier}x ${formData.addressType} wallet!`);
      }

      onClose(true); // Close modal and trigger refresh
    } catch (error) {
      alert(`❌ Failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-4 rounded-t-lg">
          <h3 className="text-xl font-bold">
            {isEdit ? '✏️ Edit Wallet' : '➕ Create New Wallet'}
          </h3>
          <p className="text-sm text-blue-100 mt-1">
            {isEdit ? 'Update wallet properties' : 'Generate a new Bitcoin wallet for your vault'}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Multiplier */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Multiplier *
            </label>
            <input
              type="number"
              min="1"
              max="1000"
              value={formData.multiplier}
              onChange={(e) => handleChange('multiplier', e.target.value)}
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="e.g., 2, 5, 10, 100"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              The bet multiplier for this wallet (e.g., 2 for 2x, 100 for 100x)
            </p>
          </div>

          {/* Chance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Win Chance (%) *
            </label>
            <input
              type="number"
              min="0.01"
              max="99.99"
              step="0.01"
              value={formData.chance}
              onChange={(e) => handleChange('chance', e.target.value)}
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="e.g., 49.5"
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Win chance percentage (0.01-99.99). Bet wins if random number &lt; chance
            </p>
          </div>

          {/* Address Type (only for new wallets) */}
          {!isEdit && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Address Type *
              </label>
              <select
                value={formData.addressType}
                onChange={(e) => handleChange('addressType', e.target.value)}
                className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-blue-500 focus:outline-none"
              >
                <option value="legacy">Legacy (P2PKH) - 1... / m/n...</option>
                <option value="segwit">SegWit (P2WPKH) - bc1q... / tb1q... ⭐ Recommended</option>
                <option value="taproot">Taproot (P2TR) - bc1p... / tb1p...</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                ⭐ SegWit recommended: Lower fees, modern standard
              </p>
            </div>
          )}

          {/* Label (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Label (Optional)
            </label>
            <input
              type="text"
              value={formData.label}
              onChange={(e) => handleChange('label', e.target.value)}
              className="w-full border-2 border-gray-300 rounded-lg px-4 py-2 focus:border-blue-500 focus:outline-none"
              placeholder="e.g., High roller wallet"
            />
            <p className="text-xs text-gray-500 mt-1">
              A custom label to identify this wallet
            </p>
          </div>

          {/* Active Status (edit only) */}
          {isEdit && (
            <div className="flex items-center">
              <input
                type="checkbox"
                id="isActive"
                checked={formData.isActive}
                onChange={(e) => handleChange('isActive', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <label htmlFor="isActive" className="ml-2 text-sm text-gray-700">
                Wallet is active (accepts new bets)
              </label>
            </div>
          )}

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={() => onClose(false)}
              disabled={loading}
              className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 disabled:opacity-50 font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {loading ? '⏳ Processing...' : isEdit ? '💾 Save Changes' : '🔑 Generate Wallet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default WalletModal;
