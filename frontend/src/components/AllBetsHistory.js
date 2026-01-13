import React, { useState, useEffect } from 'react';
import { getRecentBets } from '../utils/api';
import './AllBetsHistory.css';

function AllBetsHistory() {
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [betsPerPage] = useState(20);
  const [totalBets, setTotalBets] = useState(0);
  const [filter, setFilter] = useState('all'); // all, wins, losses
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    loadBets();
    
    // Setup WebSocket connection
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.REACT_APP_API_URL 
      ? process.env.REACT_APP_API_URL.replace('http://', '').replace('https://', '')
      : window.location.host.replace(':3000', ':8001');
    const ws = new WebSocket(`${wsProtocol}//${wsHost}/ws/bets`);
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setWsConnected(true);
      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);
      ws.pingInterval = pingInterval;
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'new_bet') {
          // Add new bet to the beginning of the list
          setBets(prevBets => [data.bet, ...prevBets]);
          setTotalBets(prev => prev + 1);
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setWsConnected(false);
      if (ws.pingInterval) {
        clearInterval(ws.pingInterval);
      }
    };
    
    // Cleanup on unmount
    return () => {
      if (ws.pingInterval) {
        clearInterval(ws.pingInterval);
      }
      ws.close();
    };
  }, []);

  const loadBets = async () => {
    try {
      setLoading(true);
      const response = await getRecentBets(100); // Get more bets for client-side pagination
      setBets(response.bets || []);
      setTotalBets(response.bets?.length || 0);
    } catch (error) {
      console.error('Error loading bets:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter bets
  const filteredBets = bets.filter(bet => {
    if (filter === 'wins') return bet.is_win;
    if (filter === 'losses') return !bet.is_win;
    return true;
  });

  // Calculate pagination
  const indexOfLastBet = currentPage * betsPerPage;
  const indexOfFirstBet = indexOfLastBet - betsPerPage;
  const currentBets = filteredBets.slice(indexOfFirstBet, indexOfLastBet);
  const totalPages = Math.ceil(filteredBets.length / betsPerPage);

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateAddress = (address) => {
    if (!address) return 'N/A';
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  };

  const copyToClipboard = (text) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
  };

  // Generate page numbers array
  const getPageNumbers = () => {
    const pages = [];
    const maxVisible = 5;
    
    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  return (
    <div className="all-bets-history slide-in">
      <div className="history-header">
        <h2>🎲 All Bets History</h2>
        <p className="history-subtitle">
          Complete history of all bets placed on the platform
        </p>
      </div>

      <div className="history-controls">
        <div className="filter-buttons">
          <button
            className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
            onClick={() => { setFilter('all'); setCurrentPage(1); }}
          >
            All Bets
          </button>
          <button
            className={`filter-btn ${filter === 'wins' ? 'active' : ''}`}
            onClick={() => { setFilter('wins'); setCurrentPage(1); }}
          >
            🎉 Wins Only
          </button>
          <button
            className={`filter-btn ${filter === 'losses' ? 'active' : ''}`}
            onClick={() => { setFilter('losses'); setCurrentPage(1); }}
          >
            😢 Losses Only
          </button>
        </div>

        <div className="stats-summary">
          <span className="stat-item">
            Total: <strong>{filteredBets.length}</strong>
          </span>
          <span className="stat-item">
            Page: <strong>{currentPage} / {totalPages || 1}</strong>
          </span>
          <span className={`ws-status ${wsConnected ? 'connected' : 'disconnected'}`}>
            {wsConnected ? '🟢 Live' : '🔴 Offline'}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading bet history...</p>
        </div>
      ) : currentBets.length === 0 ? (
        <div className="no-bets">
          <p>No bets found</p>
          <p className="small-text">Bets will appear here once users start playing</p>
        </div>
      ) : (
        <>
          <div className="bets-table-container">
            <table className="bets-table">
              <thead>
                <tr>
                  <th>Bet ID</th>
                  <th>Sender Address</th>
                  <th>Amount</th>
                  <th>Multiplier</th>
                  <th>Win Chance</th>
                  <th>Roll</th>
                  <th>Result</th>
                  <th>Profit</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {currentBets.map((bet) => (
                  <tr key={bet.id} className={bet.is_win ? 'bet-win' : 'bet-loss'}>
                    <td>
                      <span className="bet-id">#{bet.id}</span>
                    </td>
                    <td>
                      <span 
                        className="address-cell"
                        onClick={() => copyToClipboard(bet.user_address)}
                        title={`Click to copy: ${bet.user_address}`}
                      >
                        {truncateAddress(bet.user_address)}
                      </span>
                    </td>
                    <td>
                      <span className="amount-cell">
                        {bet.bet_amount?.toLocaleString()} sats
                      </span>
                    </td>
                    <td>
                      <span className="multiplier-cell">
                        {bet.multiplier?.toFixed(2)}x
                      </span>
                    </td>
                    <td>
                      <span className="chance-cell">
                        {bet.win_chance?.toFixed(2)}%
                      </span>
                    </td>
                    <td>
                      <span className={`roll-cell ${bet.is_win ? 'win-roll' : 'loss-roll'}`}>
                        {bet.roll_result?.toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <span className={`result-badge ${bet.is_win ? 'win' : 'loss'}`}>
                        {bet.is_win ? '🎉 WIN' : '😢 LOSS'}
                      </span>
                    </td>
                    <td>
                      <span className={`profit-cell ${bet.profit >= 0 ? 'profit-positive' : 'profit-negative'}`}>
                        {bet.profit >= 0 ? '+' : ''}{bet.profit?.toLocaleString()} sats
                      </span>
                    </td>
                    <td>
                      <span className="date-cell">
                        {formatDate(bet.rolled_at)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
              >
                ← Previous
              </button>

              <div className="pagination-numbers">
                {getPageNumbers().map((page, index) => (
                  page === '...' ? (
                    <span key={`ellipsis-${index}`} className="pagination-ellipsis">
                      ...
                    </span>
                  ) : (
                    <button
                      key={page}
                      className={`pagination-number ${currentPage === page ? 'active' : ''}`}
                      onClick={() => handlePageChange(page)}
                    >
                      {page}
                    </button>
                  )
                ))}
              </div>

              <button
                className="pagination-btn"
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                Next →
              </button>
            </div>
          )}

          <div className="history-footer">
            <p className="small-text">
              Showing {indexOfFirstBet + 1} - {Math.min(indexOfLastBet, filteredBets.length)} of {filteredBets.length} bets
            </p>
            <button className="refresh-btn" onClick={loadBets}>
              🔄 Refresh
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default AllBetsHistory;
