import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getStats } from '../utils/api';
import './LandingSection.css';

function LandingSection() {
  const navigate = useNavigate();
  const [isVisible, setIsVisible] = useState(false);
  const [stats, setStats] = useState({
    totalBets: 0,
    totalWagered: 0,
    winRate: 0
  });

  useEffect(() => {
    setIsVisible(true);
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const data = await getStats();
      if (data) {
        setStats({
          totalBets: data.total_bets || 0,
          totalWagered: data.total_wagered || 0,
          winRate: data.win_rate || 0
        });
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
      // Keep default values on error
    }
  };

  return (
    <section className="landing-section">
      <div className="landing-container">
        {/* Main Hero Content */}
        <div className={`hero-content ${isVisible ? 'fade-in' : ''}`}>
          {/* Bitcoin/Dice Graphic */}
          <div className="bitcoin-graphic">
            <div className="bitcoin-icon-wrapper">
              <svg 
                className="bitcoin-symbol" 
                viewBox="0 0 24 24" 
                fill="none" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path 
                  d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1.41 16.09V20h-2.67v-1.93c-1.71-.36-3.16-1.46-3.27-3.4h1.96c.1 1.05.82 1.87 2.65 1.87 1.96 0 2.4-.98 2.4-1.59 0-.83-.44-1.61-2.67-2.14-2.48-.6-4.18-1.62-4.18-3.67 0-1.72 1.39-2.84 3.11-3.21V4h2.67v1.95c1.86.45 2.79 1.86 2.85 3.39H14.3c-.05-1.11-.64-1.87-2.22-1.87-1.5 0-2.4.68-2.4 1.64 0 .84.65 1.39 2.67 1.91s4.18 1.39 4.18 3.91c-.01 1.83-1.38 2.83-3.12 3.16z" 
                  fill="#FFD700"
                />
              </svg>
              <div className="glow-effect"></div>
            </div>
          </div>

          {/* Headline */}
          <h1 className="hero-headline">
            <span className="headline-main">Satoshi Dice</span>
            <span className="headline-sub">Provably Fair Bitcoin Gaming</span>
          </h1>

          {/* Key Stats */}
          <div className="hero-stats">
            <div className="stat-item">
              <div className="stat-value">{stats.totalBets.toLocaleString()}</div>
              <div className="stat-label">Total Bets</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value">{stats.totalWagered.toLocaleString()}</div>
              <div className="stat-label">Wagered (sats)</div>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <div className="stat-value">{stats.winRate}%</div>
              <div className="stat-label">Win Rate</div>
            </div>
          </div>

          {/* CTA Button */}
          <button className="btn-get-started" onClick={() => navigate('/roll')}>
            <span>Roll</span>
            <span className="btn-arrow">→</span>
          </button>
        </div>

        {/* Trust & Transparency Panel */}
        <div className={`trust-panel ${isVisible ? 'fade-in-delay' : ''}`}>
          <div className="trust-item">
            <div className="trust-icon">🔒</div>
            <div className="trust-content">
              <div className="trust-label">Provably Fair</div>
              <div className="trust-desc">Cryptographically verifiable</div>
            </div>
          </div>
          
          <div className="trust-item">
            <div className="trust-icon">#</div>
            <div className="trust-content">
              <div className="trust-label">Hash</div>
              <div className="trust-desc">SHA256 commitment</div>
            </div>
          </div>
          
          <div className="trust-item">
            <div className="trust-icon">🌱</div>
            <div className="trust-content">
              <div className="trust-label">Seed</div>
              <div className="trust-desc">Server seed revealed</div>
            </div>
          </div>
          
          <div className="trust-item">
            <div className="trust-icon">✓</div>
            <div className="trust-content">
              <div className="trust-label">Verify</div>
              <div className="trust-desc">Independent verification</div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className={`action-buttons ${isVisible ? 'fade-in-delay-2' : ''}`}>
          <button className="btn-action" onClick={() => navigate('/roll')}>
            <span className="btn-icon">🎲</span>
            <span>Roll</span>
          </button>
          <button className="btn-action" onClick={() => navigate('/verify')}>
            <span className="btn-icon">✓</span>
            <span>Verify</span>
          </button>
          <button className="btn-action" onClick={() => navigate('/history')}>
            <span className="btn-icon">📜</span>
            <span>History</span>
          </button>
          <button className="btn-action" onClick={() => navigate('/fairness')}>
            <span className="btn-icon">🔐</span>
            <span>Fairness</span>
          </button>
        </div>
      </div>
    </section>
  );
}

export default LandingSection;
