import React, { useState, useEffect } from 'react';
import './App.css';
import WalletConnect from './components/WalletConnect';
import DiceGame from './components/DiceGame';
import BetHistory from './components/BetHistory';
import FairnessVerifier from './components/FairnessVerifier';
import Stats from './components/Stats';
import RecentBets from './components/RecentBets';

function App() {
  const [connected, setConnected] = useState(false);
  const [userAddress, setUserAddress] = useState(null);
  const [userData, setUserData] = useState(null);
  const [activeTab, setActiveTab] = useState('game');

  const handleConnect = (address, data) => {
    setConnected(true);
    setUserAddress(address);
    setUserData(data);
  };

  const handleDisconnect = () => {
    setConnected(false);
    setUserAddress(null);
    setUserData(null);
  };

  return (
    <div className="App">
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <span className="logo-icon">🎲</span>
              <h1>Bitcoin Dice</h1>
              <span className="beta-badge">TESTNET</span>
            </div>
            
            <WalletConnect 
              onConnect={handleConnect}
              onDisconnect={handleDisconnect}
              connected={connected}
              userAddress={userAddress}
            />
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
          {!connected ? (
            <div className="welcome-section slide-in">
              <div className="welcome-card">
                <h2>🎰 Welcome to Provably Fair Bitcoin Dice</h2>
                <p>The most transparent dice game on Bitcoin Testnet3</p>
                
                <div className="features-grid">
                  <div className="feature">
                    <span className="feature-icon">🔒</span>
                    <h3>Provably Fair</h3>
                    <p>HMAC-SHA512 based rolls, verifiable by anyone</p>
                  </div>
                  
                  <div className="feature">
                    <span className="feature-icon">⚡</span>
                    <h3>Instant Payouts</h3>
                    <p>Automatic payouts to your address</p>
                  </div>
                  
                  <div className="feature">
                    <span className="feature-icon">🛡️</span>
                    <h3>Non-Custodial</h3>
                    <p>Send directly from your wallet</p>
                  </div>
                  
                  <div className="feature">
                    <span className="feature-icon">📊</span>
                    <h3>Transparent</h3>
                    <p>All bets publicly verifiable</p>
                  </div>
                </div>

                <div className="cta">
                  <p className="cta-text">Connect your wallet to start playing</p>
                  <div className="arrow-down">↓</div>
                </div>
              </div>

              <Stats />
              <RecentBets />
            </div>
          ) : (
            <>
              <div className="tabs">
                <button 
                  className={`tab ${activeTab === 'game' ? 'active' : ''}`}
                  onClick={() => setActiveTab('game')}
                >
                  🎲 Play
                </button>
                <button 
                  className={`tab ${activeTab === 'history' ? 'active' : ''}`}
                  onClick={() => setActiveTab('history')}
                >
                  📜 History
                </button>
                <button 
                  className={`tab ${activeTab === 'verify' ? 'active' : ''}`}
                  onClick={() => setActiveTab('verify')}
                >
                  ✅ Verify
                </button>
                <button 
                  className={`tab ${activeTab === 'stats' ? 'active' : ''}`}
                  onClick={() => setActiveTab('stats')}
                >
                  📊 Stats
                </button>
              </div>

              <div className="tab-content">
                {activeTab === 'game' && (
                  <DiceGame 
                    userAddress={userAddress}
                    userData={userData}
                  />
                )}
                
                {activeTab === 'history' && (
                  <BetHistory userAddress={userAddress} />
                )}
                
                {activeTab === 'verify' && (
                  <FairnessVerifier />
                )}
                
                {activeTab === 'stats' && (
                  <>
                    <Stats />
                    <RecentBets />
                  </>
                )}
              </div>
            </>
          )}
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          <p>⚠️ Bitcoin Testnet3 Only - For Educational Purposes</p>
          <p>Provably Fair • Non-Custodial • Open Source</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
