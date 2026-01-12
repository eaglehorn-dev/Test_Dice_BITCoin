import React, { useState } from 'react';
import { connectUser } from '../utils/api';
import './WalletConnect.css';

function WalletConnect({ onConnect, onDisconnect, connected, userAddress }) {
  const [loading, setLoading] = useState(false);
  const [showInput, setShowInput] = useState(false);
  const [inputAddress, setInputAddress] = useState('');
  const [error, setError] = useState('');

  const handleConnect = async () => {
    // Check if Unisat wallet is available (simulated for testnet)
    if (window.unisat) {
      try {
        setLoading(true);
        setError('');
        
        // Request accounts from Unisat
        const accounts = await window.unisat.requestAccounts();
        const address = accounts[0];
        
        // Connect to backend
        const userData = await connectUser(address);
        
        onConnect(address, userData);
      } catch (err) {
        setError(err.message || 'Failed to connect wallet');
      } finally {
        setLoading(false);
      }
    } else {
      // Fallback: Manual address input
      setShowInput(true);
    }
  };

  const handleManualConnect = async () => {
    if (!inputAddress) {
      setError('Please enter a valid Bitcoin address');
      return;
    }

    // Basic validation
    if (inputAddress.length < 26 || inputAddress.length > 35) {
      setError('Invalid Bitcoin address format');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const userData = await connectUser(inputAddress);
      
      onConnect(inputAddress, userData);
      setShowInput(false);
      setInputAddress('');
    } catch (err) {
      setError(err.message || 'Failed to connect');
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = () => {
    onDisconnect();
    setShowInput(false);
    setInputAddress('');
    setError('');
  };

  if (connected) {
    return (
      <div className="wallet-connected">
        <div className="wallet-info">
          <div className="wallet-status">
            <span className="status-dot"></span>
            <span>Connected</span>
          </div>
          <div className="wallet-address">
            {userAddress.slice(0, 6)}...{userAddress.slice(-4)}
          </div>
        </div>
        <button 
          className="btn btn-disconnect"
          onClick={handleDisconnect}
        >
          Disconnect
        </button>
      </div>
    );
  }

  return (
    <div className="wallet-connect">
      {!showInput ? (
        <>
          <button 
            className="btn btn-primary"
            onClick={handleConnect}
            disabled={loading}
          >
            {loading ? '🔄 Connecting...' : '👛 Connect Wallet'}
          </button>
          
          {!window.unisat && (
            <button 
              className="btn btn-secondary"
              onClick={() => setShowInput(true)}
            >
              Enter Address
            </button>
          )}
        </>
      ) : (
        <div className="manual-connect">
          <input
            type="text"
            className="address-input"
            placeholder="Enter your Bitcoin testnet address"
            value={inputAddress}
            onChange={(e) => setInputAddress(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleManualConnect()}
          />
          <button 
            className="btn btn-primary"
            onClick={handleManualConnect}
            disabled={loading}
          >
            {loading ? 'Connecting...' : 'Connect'}
          </button>
          <button 
            className="btn btn-secondary"
            onClick={() => {
              setShowInput(false);
              setInputAddress('');
              setError('');
            }}
          >
            Cancel
          </button>
        </div>
      )}
      
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
}

export default WalletConnect;
