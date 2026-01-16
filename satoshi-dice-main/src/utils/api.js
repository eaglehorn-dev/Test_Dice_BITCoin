import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Fairness Page API
export const getFairnessSeeds = async () => {
  try {
    const response = await api.get('/api/fairness/seeds');
    return response.data;
  } catch (error) {
    console.error('Error fetching fairness seeds:', error);
    throw error;
  }
};

// Wallet API
export const getAllWallets = async () => {
  try {
    const response = await api.get('/api/wallets/all');
    return response.data;
  } catch (error) {
    console.error('Error fetching wallets:', error);
    throw error;
  }
};

export const getWalletAddress = async (multiplier) => {
  try {
    const response = await api.get(`/api/wallets/address/${multiplier}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching wallet address:', error);
    throw error;
  }
};

// House Info API (Bet Limits & Config)
export const getHouseInfo = async () => {
  try {
    const response = await api.get('/api/stats/house');
    return response.data;
  } catch (error) {
    console.error('Error fetching house info:', error);
    throw error;
  }
};

// Stats API
export const getStats = async () => {
  try {
    const response = await api.get('/api/stats/game');
    return response.data;
  } catch (error) {
    console.error('Error fetching stats:', error);
    throw error;
  }
};

// Recent Bets API
export const getRecentBets = async (limit = 3) => {
  try {
    const response = await api.get('/api/bets/recent', { params: { limit } });
    return response.data;
  } catch (error) {
    console.error('Error fetching recent bets:', error);
    throw error;
  }
};

// Bet History API with pagination and filtering
// If address is 'all', uses recent bets endpoint, otherwise uses history endpoint
export const getBetHistory = async (address, options = {}) => {
  try {
    const {
      page = 1,
      page_size = 50,
      multiplier = null,
      search = null,
      filter = 'all',
      sort = 'newest'
    } = options;

    // If address is 'all', use recent bets endpoint (no address filtering)
    if (address === 'all') {
      const limit = page_size * page; // Get enough bets for pagination
      const response = await api.get('/api/bets/recent', { params: { limit } });
      
      // Transform RecentBetsResponse to BetHistoryResponse format
      const allBets = response.data.bets || [];
      
      // Apply client-side filtering and sorting (since recent endpoint doesn't support it)
      let filteredBets = allBets;
      
      if (filter === 'wins') {
        filteredBets = filteredBets.filter(bet => bet.is_win === true);
      } else if (filter === 'big_wins') {
        filteredBets = filteredBets.filter(bet => bet.is_win === true && bet.bet_amount >= 25000000);
      } else if (filter === 'rare_wins') {
        filteredBets = filteredBets.filter(bet => bet.is_win === true && bet.roll_result < 1000);
      }
      
      // Apply sorting
      if (sort === 'newest') {
        filteredBets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      } else if (sort === 'oldest') {
        filteredBets.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
      } else if (sort === 'amount_desc') {
        filteredBets.sort((a, b) => b.bet_amount - a.bet_amount);
      } else if (sort === 'amount_asc') {
        filteredBets.sort((a, b) => a.bet_amount - b.bet_amount);
      }
      
      // Apply search
      if (search) {
        const searchLower = search.toLowerCase();
        filteredBets = filteredBets.filter(bet => 
          (bet.target_address && bet.target_address.toLowerCase().includes(searchLower)) ||
          (bet.deposit_txid && bet.deposit_txid.toLowerCase().includes(searchLower)) ||
          (bet.payout_txid && bet.payout_txid.toLowerCase().includes(searchLower))
        );
      }
      
      // Apply pagination
      const skip = (page - 1) * page_size;
      const paginatedBets = filteredBets.slice(skip, skip + page_size);
      const totalBets = filteredBets.length;
      const totalPages = Math.ceil(totalBets / page_size);
      
      // Calculate stats
      const totalWagered = filteredBets.reduce((sum, bet) => sum + (bet.bet_amount || 0), 0);
      const totalWon = filteredBets.filter(bet => bet.is_win).reduce((sum, bet) => sum + (bet.bet_amount || 0), 0);
      const totalLost = filteredBets.filter(bet => !bet.is_win).reduce((sum, bet) => sum + (bet.bet_amount || 0), 0);
      const totalPayout = filteredBets.filter(bet => bet.is_win).reduce((sum, bet) => sum + (bet.payout_amount || 0), 0);
      
      return {
        bets: paginatedBets,
        pagination: {
          page,
          page_size,
          total_pages: totalPages,
          total_bets: totalBets,
          has_next: page < totalPages,
          has_prev: page > 1
        },
        stats: {
          total_wagered: totalWagered,
          total_won: totalWon,
          total_lost: totalLost,
          total_payout: totalPayout
        }
      };
    }
    
    // Use history endpoint for specific address
    const params = {
      page,
      page_size,
      filter,
      sort
    };

    if (multiplier) params.multiplier = multiplier;
    if (search) params.search = search;

    const response = await api.get(`/api/bets/history/${address}`, { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching bet history:', error);
    throw error;
  }
};

export default api;
