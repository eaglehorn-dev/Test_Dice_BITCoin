import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import LandingSection from './components/LandingSection';
import DiceGame from './components/DiceGame';
import FairnessVerifier from './components/FairnessVerifier';
import AllBetsHistory from './components/AllBetsHistory';
import FairnessPage from './components/FairnessPage';

function App() {
  return (
    <div className="App">
      <Routes>
        <Route path="/" element={<LandingSection />} />
        <Route path="/roll" element={
          <div className="page-container">
            <DiceGame />
          </div>
        } />
        <Route path="/history" element={
          <div className="page-container">
            <AllBetsHistory />
          </div>
        } />
        <Route path="/verify" element={
          <div className="page-container">
            <FairnessVerifier />
          </div>
        } />
        <Route path="/fairness" element={
          <div className="page-container">
            <FairnessPage />
          </div>
        } />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}

export default App;
