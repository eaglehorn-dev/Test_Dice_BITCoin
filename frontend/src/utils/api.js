import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Methods
export const connectUser = async (address) => {
  const response = await api.post('/api/user/connect', null, {
    params: { user_address: address }
  });
  return response.data;
};

export const createDepositAddress = async (userAddress, multiplier) => {
  const response = await api.post('/api/deposit/create', {
    user_address: userAddress,
    multiplier: multiplier
  });
  return response.data;
};

export const submitTransaction = async (txid, depositAddress) => {
  const response = await api.post('/api/tx/submit', {
    txid: txid,
    deposit_address: depositAddress
  });
  return response.data;
};

export const getUserBets = async (userAddress, limit = 50, offset = 0) => {
  const response = await api.get(`/api/bets/user/${userAddress}`, {
    params: { limit, offset }
  });
  return response.data;
};

export const getBet = async (betId) => {
  const response = await api.get(`/api/bet/${betId}`);
  return response.data;
};

export const verifyBet = async (betId) => {
  const response = await api.post('/api/bet/verify', {
    bet_id: betId
  });
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

export const getRecentBets = async (limit = 20) => {
  const response = await api.get('/api/bets/recent', {
    params: { limit }
  });
  return response.data;
};

export default api;
