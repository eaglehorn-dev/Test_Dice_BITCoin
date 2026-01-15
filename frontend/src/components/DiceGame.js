import React, { useState, useEffect, useRef } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import MultiplierSlider from './MultiplierSlider';
import { getAllWallets, getCurrentSeedHash } from '../utils/api';
import './DiceGame.css';

function DiceGame() {
  const [copied, setCopied] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [wallets, setWallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [serverSeedHash, setServerSeedHash] = useState(null);
  const [seedHashCopied, setSeedHashCopied] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    loadWallets();
    loadSeedHash();
    setupWebSocket();
    
    return () => {
      // Cleanup WebSocket on unmount
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);
  
  const loadSeedHash = async () => {
    try {
      const seedData = await getCurrentSeedHash();
      if (seedData && seedData.server_seed_hash) {
        setServerSeedHash(seedData.server_seed_hash);
      }
    } catch (err) {
      console.error('Failed to load seed hash:', err);
    }
  };
  
  const setupWebSocket = () => {
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Don't reconnect if already connecting or connected
    if (wsRef.current && (wsRef.current.readyState === WebSocket.CONNECTING || wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    try {
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = process.env.REACT_APP_API_URL 
        ? process.env.REACT_APP_API_URL.replace('http://', '').replace('https://', '')
        : window.location.host.replace(':3000', ':8000');
      
      const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/bets`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('WebSocket connected for seed hash updates');
        setWsConnected(true);
        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle seed hash updates
          if (data.type === 'seed_hash_update' && data.server_seed_hash) {
            setServerSeedHash(data.server_seed_hash);
            console.log('Server seed hash updated:', data.server_seed_hash);
          }
          
          // Handle new bet (which might include seed hash)
          if (data.type === 'new_bet' && data.bet && data.bet.server_seed_hash) {
            setServerSeedHash(prevHash => {
              if (data.bet.server_seed_hash !== prevHash) {
                return data.bet.server_seed_hash;
              }
              return prevHash;
            });
          }
        } catch (error) {
          console.error('WebSocket message error:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.warn('WebSocket error:', error);
        setWsConnected(false);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected, will reconnect...', event.code, event.reason);
        setWsConnected(false);
        wsRef.current = null;
        
        // Only reconnect if it wasn't a manual close (code 1000)
        if (event.code !== 1000) {
          // Exponential backoff: 1s, 2s, 4s, max 10s
          const delay = Math.min(10000, 1000 * Math.pow(2, 0));
          reconnectTimeoutRef.current = setTimeout(() => {
            setupWebSocket();
          }, delay);
        }
      };
    } catch (error) {
      console.warn('WebSocket connection failed:', error);
      setWsConnected(false);
      // Retry connection after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        setupWebSocket();
      }, 3000);
    }
  };

  const loadWallets = async () => {
    try {
      setLoading(true);
      const walletsData = await getAllWallets();
      setWallets(walletsData);
      
      // Default to first wallet if available
      if (walletsData.length > 0) {
        const defaultWallet = walletsData.sort((a, b) => a.multiplier - b.multiplier)[0];
        setSelectedWallet(defaultWallet);
        setWalletAddress(defaultWallet.address);
      }
      
      setLoading(false);
    } catch (err) {
      console.error('Failed to fetch wallets:', err);
      setError('Failed to load wallet addresses. Please refresh.');
      setLoading(false);
    }
  };

  const handleMultiplierChange = (wallet) => {
    setSelectedWallet(wallet);
    setWalletAddress(wallet.address);
    console.log(`Switched to ${wallet.multiplier}x wallet:`, wallet.address);
  };

  const copyToClipboard = (text) => {
    // Try modern clipboard API first (requires HTTPS or localhost)
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => {
          showCopiedMessage();
        })
        .catch(err => {
          console.error('Clipboard API failed:', err);
          fallbackCopy(text);
        });
    } else {
      // Fallback for HTTP or older browsers
      fallbackCopy(text);
    }
  };

  const fallbackCopy = (text) => {
    // Create temporary textarea
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    
    // Select and copy
    textarea.select();
    textarea.setSelectionRange(0, 99999); // For mobile
    
    try {
      const successful = document.execCommand('copy');
      if (successful) {
        showCopiedMessage();
      }
    } catch (err) {
      console.error('Fallback copy failed:', err);
    }
    
    document.body.removeChild(textarea);
  };

  const showCopiedMessage = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const copySeedHash = () => {
    if (serverSeedHash) {
      copyToClipboard(serverSeedHash);
      setSeedHashCopied(true);
      setTimeout(() => setSeedHashCopied(false), 2000);
    }
  };
  
  const truncateHash = (hash) => {
    if (!hash) return 'N/A';
    if (hash.length <= 16) return hash;
    return `${hash.slice(0, 8)}...${hash.slice(-8)}`;
  };

  if (loading) {
    return (
      <div className="dice-game">
        <div className="game-card">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading wallet vault...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dice-game">
        <div className="game-card">
          <div className="error-message">
            <h3>⚠️ Error</h3>
            <p>{error}</p>
            <button onClick={loadWallets} className="btn-retry">🔄 Retry</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dice-game">
      <div className="game-card satoshi-style-simple">
        <div className="game-header">
          <h2>🎲 Provably Fair Dice</h2>
          <p className="subtitle">Choose Your Multiplier, Send Bitcoin, Win Instantly</p>
        </div>

        <div className="satoshi-container">
          {/* Main Row: QR and Address */}
          <div className="game-main-row">
            {/* QR Code Section */}
            <div className="qr-section-main">
              <h3>📲 Scan to Play</h3>
              {selectedWallet && (
                <div className="selected-wallet-info">
                  <span className="wallet-badge">{selectedWallet.multiplier}x Multiplier</span>
                  <span className="network-badge">{selectedWallet.network}</span>
                </div>
              )}
              <div className="qr-container-large">
                <QRCodeSVG 
                  value={`bitcoin:${walletAddress}`}
                  size={200}
                  level="H"
                  includeMargin={true}
                  bgColor="#ffffff"
                  fgColor="#000000"
                />
              </div>
            </div>

            {/* Address Section */}
            <div className="address-section-main">
              <h3>💰 Send Bitcoin</h3>
              <div className="address-display-box">
                <code className="address-text">{walletAddress}</code>
                <button 
                  className={`btn-copy-large ${copied ? 'copied' : ''}`}
                  onClick={() => copyToClipboard(walletAddress)}
                >
                  {copied ? '✅ Copied!' : '📋 Copy Address'}
                </button>
                {copied && <div className="copied-message">Address copied to clipboard!</div>}
                
                {/* Server Seed Hash Display */}
                {serverSeedHash && (
                  <div className="seed-hash-display-section">
                    <div className="seed-hash-label">Server Seed Hash:</div>
                    <div className="seed-hash-value-container">
                      <code 
                        className="seed-hash-value-text" 
                        onClick={() => {
                          copyToClipboard(serverSeedHash);
                          setSeedHashCopied(true);
                          setTimeout(() => setSeedHashCopied(false), 2000);
                        }}
                        title="Click to copy full hash"
                      >
                        {serverSeedHash.slice(0, 16)}...{serverSeedHash.slice(-8)}
                      </code>
                      <span className={`seed-hash-status ${wsConnected ? 'connected' : 'disconnected'}`} title={wsConnected ? 'WebSocket connected' : 'WebSocket disconnected'}>
                        {wsConnected ? '🟢' : '🔴'}
                      </span>
                    </div>
                    {seedHashCopied && <div className="copied-message">Seed hash copied!</div>}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Multiplier Slider (below the row) */}
          {wallets.length > 0 && (
            <div className="slider-section">
              <MultiplierSlider 
                wallets={wallets} 
                onMultiplierChange={handleMultiplierChange}
                selectedWallet={selectedWallet}
              />
              
              {/* Multiplier Badges - Landscape: one row below slider, Portrait: separate section */}
              <div className="multiplier-badges-container">
                <div className="multiplier-badges-grid">
                  {wallets
                    .sort((a, b) => a.multiplier - b.multiplier)
                    .map((wallet) => (
                      <button
                        key={wallet.multiplier}
                        className={`multiplier-badge ${selectedWallet && selectedWallet.multiplier === wallet.multiplier ? 'active' : ''}`}
                        onClick={() => handleMultiplierChange(wallet)}
                      >
                        <div className="badge-multiplier">{wallet.multiplier}x</div>
                        <div className="badge-chance">
                          {wallet.chance ? wallet.chance.toFixed(2) : 'N/A'}%
                        </div>
                      </button>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DiceGame;
