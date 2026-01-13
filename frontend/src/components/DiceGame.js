import React, { useState, useEffect } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import './DiceGame.css';

function DiceGame() {
  const [copied, setCopied] = useState(false);
  const [houseAddress, setHouseAddress] = useState('');
  const [loading, setLoading] = useState(true);
  const [multipliers] = useState([
    { value: 1.5, chance: 65.33 },
    { value: 2.0, chance: 49.0 },
    { value: 3.0, chance: 32.67 },
    { value: 5.0, chance: 19.6 },
    { value: 10.0, chance: 9.8 },
    { value: 98.0, chance: 1.0 }
  ]);

  useEffect(() => {
    // Fetch house address from backend on load
    fetch('/api/config/house-address')
      .then(res => res.json())
      .then(data => {
        setHouseAddress(data.address);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch house address:', err);
        // Fallback to hardcoded address if API fails
        setHouseAddress('bc1qq5tdg4c736l6vmqy6farsmv56texph7gv7h2ks');
        setLoading(false);
      });
  }, []);

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
            <p>Loading...</p>
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
          <p className="subtitle">Send Bitcoin, Win Instantly</p>
        </div>

        <div className="satoshi-container">
          {/* QR Code Section */}
          <div className="qr-section-main">
            <h3>📲 Scan to Play</h3>
            <div className="qr-container-large">
              <QRCodeSVG 
                value={`bitcoin:${houseAddress}`}
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
            <h3>💰 Send Bitcoin to This Address</h3>
            <div className="address-display-box">
              <code className="address-text">{houseAddress}</code>
              <button 
                className={`btn-copy-large ${copied ? 'copied' : ''}`}
                onClick={() => copyToClipboard(houseAddress)}
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
                  <strong>Send Bitcoin</strong>
                  <p>Send any amount (min 600 sats ~$0.30) to the address above</p>
                </div>
              </div>
              <div className="step">
                <div className="step-number">2</div>
                <div className="step-content">
                  <strong>Auto-Detect</strong>
                  <p>Transaction detected automatically in 5-30 seconds</p>
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
                  <p>If you win, payout sent to your address instantly!</p>
                </div>
              </div>
            </div>
          </div>

          {/* Multiplier Options */}
          <div className="multiplier-options">
            <h3>🎯 Multiplier Options</h3>
            <p className="multiplier-note">Your payout depends on the last digit of your transaction ID!</p>
            <div className="multiplier-grid">
              {multipliers.map((m) => (
                <div key={m.value} className="multiplier-card">
                  <div className="multiplier-value">{m.value}x</div>
                  <div className="multiplier-chance">{m.chance.toFixed(2)}% chance</div>
                  <div className="multiplier-example">
                    1,000 sats → {(1000 * m.value).toLocaleString()} sats
                  </div>
                </div>
              ))}
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
