import React, { useState, useEffect } from 'react';
import { createDepositAddress, submitTransaction, getBet } from '../utils/api';
import './DiceGame.css';

function DiceGame({ userAddress, userData }) {
  const [multiplier, setMultiplier] = useState(2.0);
  const [winChance, setWinChance] = useState(49.0);
  const [betAmount, setBetAmount] = useState(10000);
  const [depositAddress, setDepositAddress] = useState('');
  const [showDeposit, setShowDeposit] = useState(false);
  const [txid, setTxid] = useState('');
  const [loading, setLoading] = useState(false);
  const [betResult, setBetResult] = useState(null);
  const [polling, setPolling] = useState(false);
  const [error, setError] = useState('');

  const HOUSE_EDGE = 2.0;

  useEffect(() => {
    // Calculate win chance from multiplier
    const calculatedWinChance = ((100 - HOUSE_EDGE) / multiplier);
    setWinChance(parseFloat(calculatedWinChance.toFixed(2)));
  }, [multiplier]);

  const handleMultiplierChange = (value) => {
    const newMultiplier = parseFloat(value);
    if (newMultiplier >= 1.1 && newMultiplier <= 98) {
      setMultiplier(newMultiplier);
    }
  };

  const handleCreateBet = async () => {
    try {
      setLoading(true);
      setError('');
      setBetResult(null);
      
      // Create deposit address
      const response = await createDepositAddress(userAddress, multiplier);
      const depositAddr = response.deposit_address;
      
      setDepositAddress(depositAddr);
      
      // If Unisat wallet is available, auto-send Bitcoin
      if (window.unisat) {
        try {
          setError('Please approve the transaction in Unisat wallet...');
          
          // Switch to testnet if needed
          try {
            const network = await window.unisat.getNetwork();
            if (network !== 'testnet') {
              await window.unisat.switchNetwork('testnet');
            }
          } catch (networkErr) {
            console.warn('Could not switch network:', networkErr);
          }
          
          // Send Bitcoin using Unisat wallet
          // Amount is in satoshis
          const txid = await window.unisat.sendBitcoin(depositAddr, betAmount);
          
          setError('Transaction sent! Submitting to backend...');
          setTxid(txid);
          
          // Auto-submit the transaction
          const submitResponse = await submitTransaction(txid, depositAddr);
          
          if (submitResponse.success) {
            setError('Waiting for confirmation and dice roll...');
            // Start polling for bet result
            startPolling(submitResponse.bet_id);
          }
        } catch (walletErr) {
          // If auto-send fails, show manual deposit option
          console.error('Auto-send failed:', walletErr);
          
          // Check if user rejected the transaction
          if (walletErr.message && walletErr.message.includes('User rejected')) {
            setError('Transaction cancelled. Click "Create Bet" again to retry, or send manually.');
          } else {
            setError(`Wallet error: ${walletErr.message || 'Unknown error'}. Please send manually.`);
          }
          
          setShowDeposit(true);
          setLoading(false);
        }
      } else {
        // No wallet, show manual deposit instructions
        setShowDeposit(true);
        setLoading(false);
      }
    } catch (err) {
      setError(err.message || 'Failed to create bet');
      setLoading(false);
    }
  };

  const handleSubmitTx = async () => {
    if (!txid) {
      setError('Please enter transaction ID');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      const response = await submitTransaction(txid, depositAddress);
      
      if (response.success) {
        // Start polling for bet result
        startPolling(response.bet_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit transaction');
      setLoading(false);
    }
  };

  const startPolling = (betId) => {
    setPolling(true);
    
    const pollInterval = setInterval(async () => {
      try {
        const bet = await getBet(betId);
        
        if (bet.roll_result !== null) {
          // Bet has been rolled
          setBetResult(bet);
          setPolling(false);
          setLoading(false);
          clearInterval(pollInterval);
          
          // Reset form
          setShowDeposit(false);
          setTxid('');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (polling) {
        setPolling(false);
        setLoading(false);
        setError('Timeout waiting for bet result. Check your history.');
      }
    }, 300000);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="dice-game slide-in">
      <div className="game-container">
        <div className="game-card">
          <h2>🎲 Roll the Dice</h2>
          
          {!showDeposit ? (
            <>
              <div className="game-settings">
                <div className="setting-group">
                  <label>Multiplier</label>
                  <div className="input-with-slider">
                    <input
                      type="number"
                      className="number-input"
                      value={multiplier}
                      onChange={(e) => handleMultiplierChange(e.target.value)}
                      min="1.1"
                      max="98"
                      step="0.1"
                    />
                    <input
                      type="range"
                      className="slider"
                      value={multiplier}
                      onChange={(e) => handleMultiplierChange(e.target.value)}
                      min="1.1"
                      max="98"
                      step="0.1"
                    />
                  </div>
                  <div className="setting-info">
                    {multiplier.toFixed(2)}x payout
                  </div>
                </div>

                <div className="setting-group">
                  <label>Win Chance</label>
                  <div className="chance-display">
                    <div className="chance-bar">
                      <div 
                        className="chance-fill"
                        style={{ width: `${winChance}%` }}
                      ></div>
                    </div>
                    <div className="chance-text">
                      {winChance.toFixed(2)}%
                    </div>
                  </div>
                  <div className="setting-info">
                    Roll under {winChance.toFixed(2)} to win
                  </div>
                </div>

                <div className="setting-group">
                  <label>Bet Amount (satoshis)</label>
                  <input
                    type="number"
                    className="number-input"
                    value={betAmount}
                    onChange={(e) => setBetAmount(parseInt(e.target.value))}
                    min="10000"
                    max="1000000"
                    step="10000"
                  />
                  <div className="setting-info">
                    {(betAmount / 100000000).toFixed(8)} BTC
                  </div>
                </div>

                <div className="payout-info">
                  <div className="payout-row">
                    <span>Potential Payout:</span>
                    <span className="payout-value">
                      {(betAmount * multiplier).toFixed(0)} sats
                    </span>
                  </div>
                  <div className="payout-row">
                    <span>Potential Profit:</span>
                    <span className="payout-value glow">
                      +{(betAmount * multiplier - betAmount).toFixed(0)} sats
                    </span>
                  </div>
                </div>
              </div>

              <button
                className="btn btn-primary btn-large"
                onClick={handleCreateBet}
                disabled={loading}
              >
                {loading 
                  ? '🔄 Processing...' 
                  : window.unisat 
                    ? '🎲 Bet & Send with Unisat' 
                    : '🎲 Create Bet'}
              </button>
            </>
          ) : (
            <>
              <div className="deposit-instructions">
                <div className="instruction-step">
                  <div className="step-number">1</div>
                  <div className="step-content">
                    <h3>Send Bitcoin</h3>
                    <p>Send <strong>{betAmount} satoshis</strong> to:</p>
                    <div className="address-display">
                      <code>{depositAddress}</code>
                      <button 
                        className="btn-icon"
                        onClick={() => copyToClipboard(depositAddress)}
                        title="Copy address"
                      >
                        📋
                      </button>
                    </div>
                  </div>
                </div>

                <div className="instruction-step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h3>Enter Transaction ID</h3>
                    <p>After sending, paste your transaction ID:</p>
                    <div className="txid-input-group">
                      <input
                        type="text"
                        className="txid-input"
                        placeholder="Transaction ID (txid)"
                        value={txid}
                        onChange={(e) => setTxid(e.target.value)}
                      />
                      <button
                        className="btn btn-primary"
                        onClick={handleSubmitTx}
                        disabled={loading || !txid}
                      >
                        {loading ? '⏳ Processing...' : '✅ Submit'}
                      </button>
                    </div>
                  </div>
                </div>

                {polling && (
                  <div className="polling-status">
                    <div className="spinner"></div>
                    <p>Waiting for transaction confirmation and dice roll...</p>
                    <p className="small-text">This may take a few minutes</p>
                  </div>
                )}

                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowDeposit(false);
                    setTxid('');
                  }}
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </>
          )}

          {error && (
            <div className="error-box">
              ⚠️ {error}
            </div>
          )}
        </div>

        {betResult && (
          <div className="result-card slide-in">
            <div className={`result-header ${betResult.is_win ? 'win' : 'lose'}`}>
              {betResult.is_win ? '🎉 YOU WIN!' : '😢 YOU LOSE'}
            </div>
            
            <div className="result-details">
              <div className="dice-result dice-rolling">
                <div className="roll-number">
                  {betResult.roll_result.toFixed(2)}
                </div>
              </div>

              <div className="result-info">
                <div className="info-row">
                  <span>Target:</span>
                  <span>&lt; {betResult.win_chance.toFixed(2)}</span>
                </div>
                <div className="info-row">
                  <span>Roll:</span>
                  <span className="highlight">{betResult.roll_result.toFixed(2)}</span>
                </div>
                <div className="info-row">
                  <span>Bet Amount:</span>
                  <span>{betResult.bet_amount} sats</span>
                </div>
                <div className="info-row">
                  <span>Payout:</span>
                  <span className={betResult.is_win ? 'win-text' : 'lose-text'}>
                    {betResult.payout_amount} sats
                  </span>
                </div>
                <div className="info-row profit-row">
                  <span>Profit:</span>
                  <span className={betResult.profit >= 0 ? 'win-text' : 'lose-text'}>
                    {betResult.profit >= 0 ? '+' : ''}{betResult.profit} sats
                  </span>
                </div>
              </div>

              {betResult.payout_txid && (
                <div className="payout-txid">
                  <p>Payout Transaction:</p>
                  <code>{betResult.payout_txid}</code>
                </div>
              )}
            </div>

            <button
              className="btn btn-primary"
              onClick={() => setBetResult(null)}
            >
              Place Another Bet
            </button>
          </div>
        )}
      </div>

      <div className="game-info">
        <div className="info-card">
          <h3>🎯 How to Play</h3>
          {window.unisat ? (
            <ol>
              <li>Choose your multiplier (higher = harder to win)</li>
              <li>Set your bet amount</li>
              <li>Click "Bet & Send with Unisat"</li>
              <li>Approve the transaction in your wallet</li>
              <li>Watch the dice roll automatically!</li>
            </ol>
          ) : (
            <ol>
              <li>Choose your multiplier (higher = harder to win)</li>
              <li>Set your bet amount</li>
              <li>Send Bitcoin to the generated address</li>
              <li>Submit your transaction ID</li>
              <li>Watch the dice roll!</li>
            </ol>
          )}
        </div>

        <div className="info-card">
          <h3>📊 Game Info</h3>
          <ul>
            <li>House Edge: {HOUSE_EDGE}%</li>
            <li>Min Bet: 10,000 sats</li>
            <li>Max Bet: 1,000,000 sats</li>
            <li>Provably Fair: ✅</li>
            <li>Instant Payout: ✅</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DiceGame;
