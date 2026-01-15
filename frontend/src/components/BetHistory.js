import React, { useState, useEffect } from 'react';
import { getBetHistory } from '../utils/api';
import './BetHistory.css';

function BetHistory({ userAddress }) {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMultiplier, setSelectedMultiplier] = useState('');

  useEffect(() => {
    loadBets();
    // eslint-disable-next-line
  }, [userAddress, selectedMultiplier]);

  const loadBets = async () => {
    try {
      setLoading(true);
      setError('');
      
      const options = { limit: 50 };
      if (selectedMultiplier) options.multiplier = parseInt(selectedMultiplier);
      if (searchTerm) options.search = searchTerm;
      
      const response = await getBetHistory(userAddress, options);
      setBets(response.bets || []);
    } catch (err) {
      setError(err.message || 'Failed to load bet history');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    loadBets();
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const formatSats = (sats) => {
    return new Intl.NumberFormat().format(sats);
  };

  if (loading) {
    return (
      <div className="bet-history">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading bet history...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bet-history">
        <div className="error-message">⚠️ {error}</div>
      </div>
    );
  }

  if (bets.length === 0) {
    return (
      <div className="bet-history">
        <div className="empty-state">
          <span className="empty-icon">📜</span>
          <h3>No Bets Yet</h3>
          <p>Your bet history will appear here</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bet-history slide-in">
      <div className="history-header">
        <h2>📜 Your Bet History</h2>
      </div>

      {/* Search and Filter Controls */}
      <div className="bet-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="🔍 Search by wallet address or transaction ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="search-input"
          />
          <button onClick={handleSearch} className="btn-search">Search</button>
        </div>

        <div className="filter-box">
          <label htmlFor="multiplier-filter">Filter by Multiplier:</label>
          <select
            id="multiplier-filter"
            value={selectedMultiplier}
            onChange={(e) => setSelectedMultiplier(e.target.value)}
            className="multiplier-filter"
          >
            <option value="">All Multipliers</option>
            <option value="2">2x</option>
            <option value="3">3x</option>
            <option value="5">5x</option>
            <option value="10">10x</option>
            <option value="100">100x</option>
          </select>
        </div>

        <button className="btn btn-secondary" onClick={loadBets}>
          🔄 Refresh
        </button>
      </div>

      <div className="bets-table">
        <div className="table-header">
          <div>Date</div>
          <div>Bet Amount</div>
          <div>Wallet</div>
          <div>Multiplier</div>
          <div>Roll</div>
          <div>Result</div>
          <div>Profit</div>
          <div>TxID</div>
        </div>

        {bets.map((bet) => (
          <div 
            key={bet.bet_id} 
            className={`table-row ${bet.is_win ? 'win-row' : bet.roll_result !== null ? 'lose-row' : ''}`}
          >
            <div className="cell-date">
              {formatDate(bet.created_at)}
            </div>
            <div className="cell-amount">
              {formatSats(bet.bet_amount)} sats
            </div>
            <div className="cell-wallet" title={bet.target_address}>
              {bet.target_address ? `${bet.target_address.substring(0, 10)}...` : 'N/A'}
            </div>
            <div className="cell-multiplier multiplier-badge">
              {bet.multiplier}x
            </div>
            <div className="cell-multiplier">
              {bet.target_multiplier.toFixed(2)}x
            </div>
            <div className="cell-roll">
              {bet.roll_result !== null ? (
                <span className="roll-value">{bet.roll_result.toFixed(2)}</span>
              ) : (
                <span className="pending-text">-</span>
              )}
            </div>
            <div className="cell-result">
              {bet.is_win === true && <span className="win-badge">WIN 🎉</span>}
              {bet.is_win === false && <span className="lose-badge">LOSE</span>}
              {bet.is_win === null && <span className="pending-badge">PENDING</span>}
            </div>
            <div className="cell-profit">
              {bet.profit !== null ? (
                <span className={bet.profit >= 0 ? 'profit-positive' : 'profit-negative'}>
                  {bet.profit >= 0 ? '+' : ''}{formatSats(bet.profit)}
                </span>
              ) : (
                <span className="pending-text">-</span>
              )}
            </div>
            <div className="cell-status">
              <span className={`status-badge status-${bet.status}`}>
                {bet.status.toUpperCase()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default BetHistory;
