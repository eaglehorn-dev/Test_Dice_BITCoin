import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API_KEY = process.env.REACT_APP_ADMIN_API_KEY;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'X-Admin-API-Key': API_KEY
  },
});

// Dashboard
export const getDashboard = async () => {
  const response = await api.get('/admin/dashboard');
  return response.data;
};

// Wallets
export const getAllWallets = async (includeBalance = true) => {
  const response = await api.get('/admin/wallets', {
    params: { include_balance: includeBalance }
  });
  return response.data;
};

export const generateWallet = async (multiplier, addressType = 'segwit', chance = null) => {
  const response = await api.post('/admin/wallet/generate', { 
    multiplier, 
    address_type: addressType,
    chance: chance
  });
  return response.data;
};

export const updateWallet = async (walletId, updates) => {
  const response = await api.put(`/admin/wallet/${walletId}`, updates);
  return response.data;
};

export const deleteWallet = async (walletId) => {
  const response = await api.delete(`/admin/wallet/${walletId}`);
  return response.data;
};

// Treasury
export const withdrawToColStorage = async (walletId, amountSats = null) => {
  const response = await api.post('/admin/treasury/withdraw', {
    wallet_id: walletId,
    amount_sats: amountSats
  });
  return response.data;
};

// Analytics
export const getStats = async (period = 'today') => {
  const response = await api.get(`/admin/stats/${period}`);
  return response.data;
};

export const getVolumeByMultiplier = async (period = 'all') => {
  const response = await api.get('/admin/analytics/volume', {
    params: { period }
  });
  return response.data;
};

export const getDailyStats = async (days = 30) => {
  const response = await api.get('/admin/analytics/daily', {
    params: { days }
  });
  return response.data;
};

// Server Seeds
export const getAllServerSeeds = async () => {
  const response = await api.get('/admin/server-seeds');
  return response.data;
};

export const createServerSeed = async (seedDate) => {
  const response = await api.post('/admin/server-seed/create', { seed_date: seedDate });
  return response.data;
};

export const deleteServerSeed = async (seedId) => {
  const response = await api.delete(`/admin/server-seed/${seedId}`);
  return response.data;
};

export default api;
