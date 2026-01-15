import React, { useState, useEffect } from 'react';
import './MultiplierSlider.css';

function MultiplierSlider({ onMultiplierChange, wallets, selectedWallet }) {
  const [selectedMultiplier, setSelectedMultiplier] = useState(null);
  const [sliderValue, setSliderValue] = useState(0);

  // Sort wallets by multiplier
  const sortedWallets = [...wallets].sort((a, b) => a.multiplier - b.multiplier);

  useEffect(() => {
    if (sortedWallets.length > 0) {
      // Use selectedWallet if provided, otherwise default to first wallet
      if (selectedWallet) {
        const index = sortedWallets.findIndex(w => w.multiplier === selectedWallet.multiplier);
        if (index !== -1) {
          setSelectedMultiplier(selectedWallet);
          setSliderValue(index);
        } else {
          const defaultWallet = sortedWallets[0];
          setSelectedMultiplier(defaultWallet);
          setSliderValue(0);
          onMultiplierChange(defaultWallet);
        }
      } else {
        // Default to first wallet (usually 2x)
        const defaultWallet = sortedWallets[0];
        setSelectedMultiplier(defaultWallet);
        setSliderValue(0);
        onMultiplierChange(defaultWallet);
      }
    }
  }, [wallets, selectedWallet]);

  const handleSliderChange = (e) => {
    const index = parseInt(e.target.value);
    setSliderValue(index);
    const wallet = sortedWallets[index];
    setSelectedMultiplier(wallet);
    onMultiplierChange(wallet);
  };

  if (wallets.length === 0) {
    return <div className="multiplier-slider">Loading multipliers...</div>;
  }

  return (
    <div className="multiplier-slider">
      {/* Win Chance Display (above slider) */}
      {selectedMultiplier && (
        <div className="win-chance-display">
          <span className="win-chance-label">Win Chance:</span>
          <span className="win-chance-value">
            {selectedMultiplier.chance ? selectedMultiplier.chance.toFixed(2) : 'N/A'}%
          </span>
        </div>
      )}

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
    </div>
  );
}

export default MultiplierSlider;
