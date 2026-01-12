import React, { useState, useEffect } from 'react';
import { getStats } from '../utils/api';
import './Stats.css';

function Stats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
    
    // Refresh stats every 30 seconds
    const interval = setInterval(loadStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      setStats(data);
      setLoading(false);
    } catch (err) {
      console.error('Failed to load stats:', err);
      setLoading(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="stats-container">
        <div className="loading-spinner">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="stats-container slide-in">
      <h2>📊 Platform Statistics</h2>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">👥</div>
          <div className="stat-value">{stats.total_users}</div>
          <div className="stat-label">Total Users</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🎲</div>
          <div className="stat-value">{stats.total_bets}</div>
          <div className="stat-label">Total Bets</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-value">{stats.total_wagered}</div>
          <div className="stat-label">Total Wagered</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">📈</div>
          <div className="stat-value">{stats.win_rate}%</div>
          <div className="stat-label">Win Rate</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🏠</div>
          <div className="stat-value">{stats.house_edge}%</div>
          <div className="stat-label">House Edge</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⬇️</div>
          <div className="stat-value">{(stats.min_bet / 1000).toFixed(0)}k</div>
          <div className="stat-label">Min Bet (sats)</div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⬆️</div>
          <div className="stat-value">{(stats.max_bet / 1000).toFixed(0)}k</div>
          <div className="stat-label">Max Bet (sats)</div>
        </div>

        <div className="stat-card highlight">
          <div className="stat-icon">✅</div>
          <div className="stat-value">100%</div>
          <div className="stat-label">Provably Fair</div>
        </div>
      </div>
    </div>
  );
}

export default Stats;
