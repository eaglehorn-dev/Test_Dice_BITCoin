import React, { useState, useEffect } from 'react';
import { getRecentBets } from '../utils/api';
import './RecentBets.css';

function RecentBets() {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentBets();
    
    // Refresh every 15 seconds
    const interval = setInterval(loadRecentBets, 15000);
    return () => clearInterval(interval);
  }, []);

  const loadRecentBets = async () => {
    try {
      const data = await getRecentBets(10);
      setBets(data.bets);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load recent bets:', err);
      setLoading(false);
    }
  };

  const formatSats = (sats) => {
    return new Intl.NumberFormat().format(sats);
  };

  const formatAddress = (address) => {
    if (!address) return 'Unknown';
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  if (loading) {
    return (
      <div className="recent-bets">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="recent-bets slide-in">
      <div className="recent-header">
        <h2>🔥 Recent Bets</h2>
        <div className="live-indicator">
          <span className="live-dot"></span>
          <span>LIVE</span>
        </div>
      </div>

      {bets.length === 0 ? (
        <div className="empty-state">
          <p>No bets yet. Be the first!</p>
        </div>
      ) : (
        <div className="bets-list">
          {bets.map((bet, index) => (
            <div 
              key={bet.id} 
              className={`bet-item ${bet.is_win ? 'win' : 'lose'}`}
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="bet-user">
                <span className="user-icon">👤</span>
                <span className="user-address">{formatAddress(bet.deposit_address)}</span>
              </div>

              <div className="bet-details">
                <div className="bet-amount">
                  {formatSats(bet.bet_amount)} sats
                </div>
                <div className="bet-multiplier">
                  @ {bet.target_multiplier.toFixed(2)}x
                </div>
              </div>

              <div className="bet-roll">
                <div className="roll-label">Roll:</div>
                <div className="roll-value">{bet.roll_result.toFixed(2)}</div>
              </div>

              <div className="bet-result">
                {bet.is_win ? (
                  <div className="win-indicator">
                    <span>WIN</span>
                    <span className="profit">+{formatSats(bet.profit)}</span>
                  </div>
                ) : (
                  <div className="lose-indicator">
                    <span>LOSE</span>
                    <span className="loss">{formatSats(bet.profit)}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RecentBets;
