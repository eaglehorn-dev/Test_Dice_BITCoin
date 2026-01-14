import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import MultiplierSlider from './MultiplierSlider';
import { getAllWallets } from '../utils/api';
import './DiceGame.css';

function DiceGame() {
  const [copied, setCopied] = useState(false);
  const [walletAddress, setWalletAddress] = useState('');
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [wallets, setWallets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadWallets();
  }, []);

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
          {/* Multiplier Slider */}
          {wallets.length > 0 && (
            <MultiplierSlider 
              wallets={wallets} 
              onMultiplierChange={handleMultiplierChange}
            />
          )}

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
                size={280}
                level="H"
                includeMargin={true}
                bgColor="#ffffff"
                fgColor="#000000"
              />
            </div>
          </div>

          {/* Address Section */}
          <div className="address-section-main">
            <h3>💰 Send Bitcoin to {selectedWallet?.multiplier}x Address</h3>
            <div className="address-display-box">
              <code className="address-text">{walletAddress}</code>
              <button 
                className={`btn-copy-large ${copied ? 'copied' : ''}`}
                onClick={() => copyToClipboard(walletAddress)}
              >
                {copied ? '✅ Copied!' : '📋 Copy Address'}
              </button>
              {copied && <div className="copied-message">Address copied to clipboard!</div>}
            </div>
          </div>

          {/* How It Works */}
          <div className="how-it-works">
            <h3>⚡ How It Works</h3>
            <div className="steps">
              <div className="step">
                <div className="step-number">1</div>
                <div className="step-content">
                  <strong>Choose Multiplier</strong>
                  <p>Use the slider to select your desired multiplier (2x to 100x)</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Send Bitcoin</strong>
                  <p>Send any amount (min 600 sats) to the displayed address</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">3</div>
                <div className="step-content">
                  <strong>Auto-Roll</strong>
                  <p>Dice rolls automatically using provably fair algorithm</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">4</div>
                <div className="step-content">
                  <strong>Instant Payout</strong>
                  <p>If you win, get {selectedWallet?.multiplier}x payout to your address!</p>
                </div>
              </div>
            </div>
          </div>

          {/* Important Info */}
          <div className="important-info">
            <div className="info-box">
              <div className="info-icon">💡</div>
              <div className="info-content">
                <strong>Fully Automatic</strong>
                <p>No buttons, no forms. Just send Bitcoin and win!</p>
              </div>
            </div>
            <div className="info-box">
              <div className="info-icon">🔒</div>
              <div className="info-content">
                <strong>Provably Fair</strong>
                <p>Every roll is verifiable using HMAC-SHA512</p>
              </div>
            </div>
            <div className="info-box">
              <div className="info-icon">⚡</div>
              <div className="info-content">
                <strong>Instant Results</strong>
                <p>Winnings sent to your address within seconds</p>
              </div>
            </div>
          </div>

          {/* Bet Limits */}
          <div className="bet-limits">
            <div className="limit-item">
              <span className="limit-label">Min Bet:</span>
              <span className="limit-value">600 sats (~$0.30)</span>
            </div>
            <div className="limit-item">
              <span className="limit-label">Max Bet:</span>
              <span className="limit-value">1,000,000 sats (~$500)</span>
            </div>
            <div className="limit-item">
              <span className="limit-label">House Edge:</span>
              <span className="limit-value">2%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default DiceGame;
