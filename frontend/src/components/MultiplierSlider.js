import React, { useState, useEffect } from 'react';
import './MultiplierSlider.css';

function MultiplierSlider({ onMultiplierChange, wallets }) {
  const [selectedMultiplier, setSelectedMultiplier] = useState(null);
  const [sliderValue, setSliderValue] = useState(0);

  // Sort wallets by multiplier
  const sortedWallets = [...wallets].sort((a, b) => a.multiplier - b.multiplier);

  useEffect(() => {
    if (sortedWallets.length > 0) {
      // Default to first wallet (usually 2x)
      const defaultWallet = sortedWallets[0];
      setSelectedMultiplier(defaultWallet);
      setSliderValue(0);
      onMultiplierChange(defaultWallet);
    }
  }, [wallets]);

  const handleSliderChange = (e) => {
    const index = parseInt(e.target.value);
    setSliderValue(index);
    const wallet = sortedWallets[index];
    setSelectedMultiplier(wallet);
    onMultiplierChange(wallet);
  };

  const handleMultiplierClick = (wallet, index) => {
    setSliderValue(index);
    setSelectedMultiplier(wallet);
    onMultiplierChange(wallet);
  };

  if (wallets.length === 0) {
    return <div className="multiplier-slider">Loading multipliers...</div>;
  }

  return (
    <div className="multiplier-slider">
      <h3>🎯 Choose Your Multiplier</h3>
      
      {/* Selected Multiplier Display */}
      <div className="selected-multiplier-display">
        <div className="multiplier-big">{selectedMultiplier?.multiplier}x</div>
        <div className="multiplier-label">{selectedMultiplier?.label}</div>
      </div>

      {/* Slider */}
      <div className="slider-container">
        <input
          type="range"
          min="0"
          max={sortedWallets.length - 1}
          value={sliderValue}
          onChange={handleSliderChange}
          className="multiplier-range"
          step="1"
        />
        <div className="slider-markers">
          {sortedWallets.map((wallet, index) => (
            <div
              key={wallet.multiplier}
              className={`slider-marker ${sliderValue === index ? 'active' : ''}`}
              style={{ left: `${(index / (sortedWallets.length - 1)) * 100}%` }}
            >
              {wallet.multiplier}x
            </div>
          ))}
        </div>
      </div>

      {/* Multiplier Buttons */}
      <div className="multiplier-buttons">
        {sortedWallets.map((wallet, index) => (
          <button
            key={wallet.multiplier}
            className={`multiplier-btn ${sliderValue === index ? 'active' : ''}`}
            onClick={() => handleMultiplierClick(wallet, index)}
          >
            <div className="btn-multiplier">{wallet.multiplier}x</div>
            <div className="btn-label">{wallet.label.replace(' Wallet', '')}</div>
          </button>
        ))}
      </div>

      {/* Info Display */}
      {selectedMultiplier && (
        <div className="multiplier-info">
          <div className="info-row">
            <span className="info-label">Win Chance:</span>
            <span className="info-value">{(100 / selectedMultiplier.multiplier).toFixed(2)}%</span>
          </div>
          <div className="info-row">
            <span className="info-label">Example:</span>
            <span className="info-value">
              1,000 sats → {(1000 * selectedMultiplier.multiplier).toLocaleString()} sats
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

export default MultiplierSlider;
