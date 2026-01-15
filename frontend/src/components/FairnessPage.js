import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getFairnessSeeds } from '../utils/api';
import './FairnessPage.css';

function FairnessPage() {
  const navigate = useNavigate();
  const [seeds, setSeeds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSeeds();
    const interval = setInterval(loadSeeds, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const loadSeeds = async () => {
    try {
      const data = await getFairnessSeeds();
      setSeeds(data.seeds || []);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load server seeds');
      console.error('Fairness seeds error:', err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const formatDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
      });
    } catch {
      return dateStr;
    }
  };

  const getDateLabel = (dateStr) => {
    const today = new Date().toISOString().split('T')[0];
    if (dateStr === today) return 'Today';
    
    const date = new Date(dateStr);
    const todayDate = new Date(today);
    const diffTime = date - todayDate;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays > 1 && diffDays <= 3) return `+${diffDays} days`;
    if (diffDays < 0) return 'Past';
    return '';
  };

  if (loading) {
    return (
      <div className="fairness-page">
        <div className="fairness-container">
          <div className="text-center py-12">
            <div className="text-gray-500">Loading server seeds...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fairness-page">
      <div className="fairness-container">
        <button className="btn-back" onClick={() => navigate('/')}>
          <span className="back-arrow">←</span>
          <span>Back to Home</span>
        </button>

        <div className="fairness-header">
          <h1 className="fairness-title">🔐 Provably Fair Transparency</h1>
          <p className="fairness-subtitle">
            Server seed keys for cryptographic verification. Real keys are revealed only for past dates.
          </p>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <div className="seeds-table-container">
          <table className="seeds-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Server Seed Hash</th>
                <th>Server Seed (Real Key)</th>
                <th>Bet Count</th>
              </tr>
            </thead>
            <tbody>
              {seeds.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center py-8 text-gray-500">
                    No server seeds found
                  </td>
                </tr>
              ) : (
                seeds.map((seed) => {
                  const dateLabel = getDateLabel(seed.seed_date);
                  const isPast = seed.server_seed !== null;
                  
                  return (
                    <tr key={seed.seed_id} className="seed-row">
                      <td className="seed-date">
                        <div className="date-value">{formatDate(seed.seed_date)}</div>
                        {dateLabel && (
                          <span className={`date-badge ${isPast ? 'badge-past' : 'badge-future'}`}>
                            {dateLabel}
                          </span>
                        )}
                      </td>
                      <td className="seed-hash">
                        <div className="hash-value" onClick={() => copyToClipboard(seed.server_seed_hash)}>
                          {seed.server_seed_hash.substring(0, 32)}...
                        </div>
                        <div className="hash-hint">Click to copy full hash</div>
                      </td>
                      <td className="seed-key">
                        {isPast ? (
                          <div className="key-value" onClick={() => copyToClipboard(seed.server_seed)}>
                            {seed.server_seed.substring(0, 32)}...
                          </div>
                        ) : (
                          <div className="key-unpublished">Not Published</div>
                        )}
                      </td>
                      <td className="seed-bets">
                        {seed.bet_count || 0}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="fairness-info">
          <p className="info-text">
            <strong>How it works:</strong> Server seed hashes are published in advance. 
            Real keys are revealed only after the date has passed, ensuring provable fairness.
            You can verify any bet using these seeds.
          </p>
        </div>
      </div>
    </div>
  );
}

export default FairnessPage;
