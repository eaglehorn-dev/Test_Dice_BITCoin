import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRecentBets } from '../utils/api';
import './AllBetsHistory.css';

function AllBetsHistory() {
  const navigate = useNavigate();
  const [bets, setBets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [betsPerPage] = useState(20);
  const [totalBets, setTotalBets] = useState(0);
  const [filter, setFilter] = useState('all'); // all, wins, losses
  const [wsConnected, setWsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  const setupWebSocket = useCallback(() => {
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
        console.log('WebSocket connected for bet history');
        setWsConnected(true);
        // Clear any pending reconnect
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
          reconnectTimeoutRef.current = null;
        }
        // Send ping every 30 seconds to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send('ping');
          }
        }, 30000);
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
        console.warn('WebSocket connection error (bet history will still work):', error);
        setWsConnected(false);
      };
      
      ws.onclose = (event) => {
        console.log('WebSocket disconnected, will reconnect...', event.code, event.reason);
        setWsConnected(false);
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current);
          pingIntervalRef.current = null;
        }
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
      console.warn('Failed to initialize WebSocket (bet history will still work):', error);
      setWsConnected(false);
      // Retry connection after delay
      reconnectTimeoutRef.current = setTimeout(() => {
        setupWebSocket();
      }, 3000);
    }
  }, []);

  useEffect(() => {
    // Load bets first (don't wait for WebSocket)
    loadBets();
    
    // Setup WebSocket connection (non-blocking, optional for real-time updates)
    setupWebSocket();
    
    // Cleanup on unmount
    return () => {
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current);
        pingIntervalRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        wsRef.current.close(1000); // Manual close
        wsRef.current = null;
      }
    };
  }, [setupWebSocket]);

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
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const truncateAddress = (address) => {
    if (!address || typeof address !== 'string' || address.length < 14) return address || 'N/A';
    return `${address.slice(0, 8)}...${address.slice(-6)}`;
  };

  const truncateTxid = (txid) => {
    if (!txid || typeof txid !== 'string') return 'N/A';
    if (txid.length <= 16) return txid;
    return `${txid.slice(0, 8)}...${txid.slice(-8)}`;
  };

  const getMempoolUrl = (txid) => {
    if (!txid) return null;
    // Check if we're on testnet or mainnet based on API URL or default to testnet
    const apiUrl = process.env.REACT_APP_API_URL || '';
    const isTestnet = apiUrl.includes('testnet') || apiUrl.includes('localhost') || !apiUrl;
    const baseUrl = isTestnet ? 'https://mempool.space/testnet' : 'https://mempool.space';
    return `${baseUrl}/tx/${txid}`;
  };

  const handleTxClick = (txid) => {
    const url = getMempoolUrl(txid);
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
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
      <button className="btn-back" onClick={() => navigate('/')}>
        <span className="back-arrow">←</span>
        <span>Back to Home</span>
      </button>
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
                  <th>Deposit TX</th>
                  <th>Payout TX</th>
                  <th>Server Seed</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {currentBets.map((bet) => (
                  <tr key={bet.bet_id || bet.bet_number || Math.random()} className={bet.is_win ? 'bet-win' : 'bet-loss'}>
                    <td>
                      <span 
                        className="bet-id" 
                        title={`Bet ID: ${bet.bet_id || 'N/A'}`}
                        onClick={() => copyToClipboard(bet.bet_id || '')}
                        style={{ cursor: 'pointer' }}
                      >
                        {bet.bet_id ? bet.bet_id.slice(-12) : 'N/A'}
                      </span>
                    </td>
                    <td>
                      <span 
                        className="address-cell"
                        onClick={() => copyToClipboard(bet.user_address || bet.target_address || 'N/A')}
                        title={`Click to copy: ${bet.user_address || bet.target_address || 'N/A'}`}
                      >
                        {truncateAddress(bet.user_address || bet.target_address)}
                      </span>
                    </td>
                    <td>
                      <span className="amount-cell">
                        {bet.bet_amount?.toLocaleString()} sats
                      </span>
                    </td>
                    <td>
                      <span className="multiplier-cell">
                        {bet.target_multiplier?.toFixed(2)}x
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
                      {bet.deposit_txid ? (
                        <span 
                          className="tx-link"
                          onClick={() => handleTxClick(bet.deposit_txid)}
                          title={`Click to view on mempool.space: ${bet.deposit_txid}`}
                        >
                          🔗 {truncateTxid(bet.deposit_txid)}
                        </span>
                      ) : (
                        <span className="tx-na">N/A</span>
                      )}
                    </td>
                    <td>
                      {bet.payout_txid ? (
                        <span 
                          className="tx-link"
                          onClick={() => handleTxClick(bet.payout_txid)}
                          title={`Click to view on mempool.space: ${bet.payout_txid}`}
                        >
                          🔗 {truncateTxid(bet.payout_txid)}
                        </span>
                      ) : (
                        <span className="tx-na">N/A</span>
                      )}
                    </td>
                    <td>
                      <span 
                        className="seed-cell"
                        onClick={() => copyToClipboard(bet.server_seed || bet.server_seed_hash || 'N/A')}
                        title={bet.server_seed ? `Click to copy server seed: ${bet.server_seed}` : bet.server_seed_hash ? `Server seed hash: ${bet.server_seed_hash}` : 'N/A'}
                      >
                        {bet.server_seed && typeof bet.server_seed === 'string' ? (
                          <span className="seed-revealed" title="Server seed revealed">🔓 {bet.server_seed.slice(0, 12)}...</span>
                        ) : bet.server_seed_hash && typeof bet.server_seed_hash === 'string' ? (
                          <span className="seed-hash" title="Server seed hash (seed not revealed)">🔒 {bet.server_seed_hash.slice(0, 12)}...</span>
                        ) : (
                          'N/A'
                        )}
                      </span>
                    </td>
                    <td>
                      <span className="date-cell">
                        {formatDate(bet.created_at)}
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
