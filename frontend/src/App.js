import React, { useState } from 'react';
import './App.css';
import DiceGame from './components/DiceGame';
import FairnessVerifier from './components/FairnessVerifier';
import Stats from './components/Stats';
import RecentBets from './components/RecentBets';
import AllBetsHistory from './components/AllBetsHistory';

function App() {
  const [activeTab, setActiveTab] = useState('game');

  return (
    <div className="App">
      <header className="app-header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <span className="logo-icon">🎲</span>
              <h1>Bitcoin Dice</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="main-content">
        <div className="container">
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
              📜 All Bets
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
            {activeTab === 'game' && <DiceGame />}
            
            {activeTab === 'history' && <AllBetsHistory />}
            
            {activeTab === 'verify' && <FairnessVerifier />}
            
            {activeTab === 'stats' && (
              <>
                <Stats />
                <RecentBets />
              </>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <div className="container">
          <p>Provably Fair • Non-Custodial • Open Source</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
