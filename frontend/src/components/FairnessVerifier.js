import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { verifyBet } from '../utils/api';
import './FairnessVerifier.css';

function FairnessVerifier() {
  const navigate = useNavigate();
  const [betId, setBetId] = useState('');
  const [loading, setLoading] = useState(false);
  const [verification, setVerification] = useState(null);
  const [error, setError] = useState('');

  const handleVerify = async () => {
    if (!betId) {
      setError('Please enter a bet ID');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setVerification(null);
      
      const response = await verifyBet(parseInt(betId));
      setVerification(response);
    } catch (err) {
      setError(err.message || 'Failed to verify bet');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fairness-verifier slide-in">
      <button className="btn-back" onClick={() => navigate('/')}>
        <span className="back-arrow">←</span>
        <span>Back to Home</span>
      </button>
      <div className="verifier-card">
        <h2>✅ Verify Bet Fairness</h2>
        <p className="subtitle">
          Verify that any bet was provably fair using cryptographic proof
        </p>

        <div className="verify-input">
          <input
            type="number"
            className="bet-id-input"
            placeholder="Enter Bet ID"
            value={betId}
            onChange={(e) => setBetId(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleVerify()}
          />
          <button
            className="btn btn-primary"
            onClick={handleVerify}
            disabled={loading}
          >
            {loading ? '🔄 Verifying...' : '🔍 Verify'}
          </button>
        </div>

        {error && (
          <div className="error-box">⚠️ {error}</div>
        )}

        {verification && (
          <div className="verification-result">
            <div className={`result-status ${verification.is_valid ? 'valid' : 'invalid'}`}>
              {verification.is_valid ? '✅ VALID - Provably Fair' : '❌ INVALID'}
            </div>

            <div className="verification-details">
              <div className="detail-section">
                <h3>Bet Information</h3>
                <div className="detail-row">
                  <span>Bet ID:</span>
                  <code>{verification.bet_id}</code>
                </div>
                <div className="detail-row">
                  <span>Nonce:</span>
                  <code>{verification.nonce}</code>
                </div>
                <div className="detail-row">
                  <span>Roll Result:</span>
                  <code className="highlight">{verification.roll.toFixed(2)}</code>
                </div>
              </div>

              <div className="detail-section">
                <h3>Seeds</h3>
                <div className="detail-row vertical">
                  <span>Server Seed (Revealed):</span>
                  <code className="long-code">{verification.server_seed}</code>
                </div>
                <div className="detail-row vertical">
                  <span>Server Seed Hash:</span>
                  <code className="long-code">{verification.server_seed_hash}</code>
                </div>
                <div className="detail-row vertical">
                  <span>Client Seed:</span>
                  <code className="long-code">{verification.client_seed}</code>
                </div>
              </div>

              <div className="detail-section">
                <h3>Verification Data</h3>
                <div className="detail-row vertical">
                  <span>HMAC-SHA512:</span>
                  <code className="long-code small-code">
                    {verification.verification_data.hmac_sha512}
                  </code>
                </div>
                <div className="detail-row">
                  <span>First 8 Hex Chars:</span>
                  <code>{verification.verification_data.hmac_first_8_chars}</code>
                </div>
                <div className="detail-row">
                  <span>Decimal Value:</span>
                  <code>{verification.verification_data.hmac_decimal}</code>
                </div>
                <div className="detail-row vertical">
                  <span>Calculation:</span>
                  <code>{verification.verification_data.roll_calculation}</code>
                </div>
                <div className="detail-row">
                  <span>Recalculated Roll:</span>
                  <code className="highlight">{verification.verification_data.recalculated_roll.toFixed(2)}</code>
                </div>
              </div>

              <div className="detail-section">
                <h3>Validation Checks</h3>
                <div className="check-row">
                  <span>Server Seed Hash Valid:</span>
                  <span className={verification.verification_data.server_seed_hash_valid ? 'check-pass' : 'check-fail'}>
                    {verification.verification_data.server_seed_hash_valid ? '✅ PASS' : '❌ FAIL'}
                  </span>
                </div>
                <div className="check-row">
                  <span>Roll Calculation Valid:</span>
                  <span className={verification.verification_data.roll_valid ? 'check-pass' : 'check-fail'}>
                    {verification.verification_data.roll_valid ? '✅ PASS' : '❌ FAIL'}
                  </span>
                </div>
                <div className="check-row overall">
                  <span>Overall Verification:</span>
                  <span className={verification.verification_data.overall_valid ? 'check-pass' : 'check-fail'}>
                    {verification.verification_data.overall_valid ? '✅ VALID' : '❌ INVALID'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="fairness-info">
        <div className="info-card">
          <h3>🔐 How Provably Fair Works</h3>
          <ol>
            <li>
              <strong>Server Seed:</strong> Generated before your bet. Hash is shown to you.
            </li>
            <li>
              <strong>Client Seed:</strong> Your wallet address or custom seed.
            </li>
            <li>
              <strong>Nonce:</strong> Incremental counter for each bet.
            </li>
            <li>
              <strong>HMAC-SHA512:</strong> Cryptographic hash combining all inputs.
            </li>
            <li>
              <strong>Result:</strong> First 8 hex chars converted to 0.00-99.99.
            </li>
          </ol>
        </div>

        <div className="info-card">
          <h3>🧪 Verify Yourself</h3>
          <p>You can independently verify any bet using:</p>
          <ul>
            <li>Any HMAC-SHA512 calculator</li>
            <li>The revealed server seed</li>
            <li>Your client seed</li>
            <li>The bet nonce</li>
          </ul>
          <p className="small-note">
            The server seed is revealed after each bet, proving the house couldn't manipulate the result.
          </p>
        </div>

        <div className="info-card">
          <h3>📊 Transparency</h3>
          <p>Every bet is:</p>
          <ul>
            <li>Cryptographically verifiable</li>
            <li>Independently auditable</li>
            <li>Impossible to manipulate</li>
            <li>100% transparent</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default FairnessVerifier;
