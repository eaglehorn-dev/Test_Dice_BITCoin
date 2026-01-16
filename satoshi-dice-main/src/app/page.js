"use client";
import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  ChevronDown,
  Globe,
  ExternalLink,
  Activity,
  Trophy
} from 'lucide-react';
import Navbar from '@/components/navbar';
import { QRCode } from 'react-qrcode-logo';
import BettingHistory from '@/components/gameHistory';
import Footer from '@/components/footer';
import { getAllWallets, getHouseInfo, getStats, getRecentBets } from '@/utils/api';
import { useWebSocket } from '@/utils/websocket';

export default function App() {
  const SATOSHIS_PER_BTC = 100000000;
  
  // Mounted state to prevent hydration mismatches
  const [mounted, setMounted] = useState(false);
  
  // Logo image state for QR code (converted to data URL for mobile compatibility)
  const [logoDataUrl, setLogoDataUrl] = useState(null);
  
  // API Data State
  const [wallets, setWallets] = useState([]);
  const [houseInfo, setHouseInfo] = useState(null);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [walletAddress, setWalletAddress] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [totalBets, setTotalBets] = useState(null);
  const [recentBets, setRecentBets] = useState([]);
  
  // Multiplier state
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isDraggingMultiplier, setIsDraggingMultiplier] = useState(false);
  const multiplierProgressBarRef = useRef(null);

  // Bet amount state
  const [betAmount, setBetAmount] = useState(0.1);
  const [isDraggingBet, setIsDraggingBet] = useState(false);
  const [currency, setCurrency] = useState('BTC');
  const [betAmountInput, setBetAmountInput] = useState('');
  const betProgressBarRef = useRef(null);

  // Bet limits (will be updated from API and wallet-specific ranges)
  const [minBet, setMinBet] = useState(0.001);
  const [maxBet, setMaxBet] = useState(7.5);
  const [walletBetRanges, setWalletBetRanges] = useState({});
  
  const usdRate = 586.1; // TODO: Remove or fetch from API if needed

  // Transform wallets to match UI structure
  const multipliers = wallets.map(w => ({
    label: `${w.multiplier}x`,
    chance: `${w.chance.toFixed(2)}%`,
    multiplier: w.multiplier,
    address: w.address
  }));

  // Multiplier functions
  const getMultiplierProgressPosition = () => {
    return (selectedIndex / (multipliers.length - 1)) * 100;
  };

  const updateMultiplierPositionFromMouse = (clientX) => {
    if (!multiplierProgressBarRef.current) return;
    const rect = multiplierProgressBarRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    const index = Math.round((percentage / 100) * (multipliers.length - 1));
    setSelectedIndex(index);
  };

  const handleMultiplierMouseDown = (e) => {
    setIsDraggingMultiplier(true);
    updateMultiplierPositionFromMouse(e.clientX);
  };

  const handleMultiplierMouseMove = (e) => {
    if (isDraggingMultiplier) {
      updateMultiplierPositionFromMouse(e.clientX);
    }
  };

  const handleMultiplierMouseUp = () => {
    setIsDraggingMultiplier(false);
  };

  // Bet amount functions
  const formatBTC = (amount) => {
    if (amount >= 1) return amount.toFixed(1);
    if (amount >= 0.01) return amount.toFixed(2);
    return amount.toFixed(6);
  };

  const getBetProgressPosition = () => {
    const minLog = Math.log(minBet);
    const maxLog = Math.log(maxBet);
    const currentLog = Math.log(betAmount);
    return ((currentLog - minLog) / (maxLog - minLog)) * 100;
  };

  const positionToBetAmount = (percentage) => {
    const minLog = Math.log(minBet);
    const maxLog = Math.log(maxBet);
    const currentLog = minLog + (percentage / 100) * (maxLog - minLog);
    return Math.exp(currentLog);
  };

  const handleBetChange = (newAmount) => {
    const clampedAmount = Math.max(minBet, Math.min(maxBet, newAmount));
    setBetAmount(clampedAmount);
  };

  const updateBetPositionFromMouse = (clientX) => {
    if (!betProgressBarRef.current) return;
    const rect = betProgressBarRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
    const newAmount = positionToBetAmount(percentage);
    handleBetChange(newAmount);
  };

  const handleBetMouseDown = (e) => {
    setIsDraggingBet(true);
    updateBetPositionFromMouse(e.clientX);
  };

  const handleBetMouseMove = (e) => {
    if (isDraggingBet) {
      updateBetPositionFromMouse(e.clientX);
    }
  };

  const handleBetMouseUp = () => {
    setIsDraggingBet(false);
  };

  const calculateRollLowerThan = () => {
    const maxRoll = 65535;
    const percentage = getBetProgressPosition();
    return Math.floor((percentage / 100) * maxRoll);
  };

  const getDisplayValue = () => {
    if (currency === 'USD') {
      return (betAmount * usdRate).toFixed(2);
    }
    return formatBTC(betAmount);
  };

  // Handle bet amount input change
  const handleBetAmountInputChange = (e) => {
    const value = e.target.value;
    setBetAmountInput(value);
    
    // Allow empty input for typing
    if (value === '' || value === '.') {
      return;
    }
    
    const numValue = parseFloat(value);
    if (isNaN(numValue) || numValue < 0) {
      return;
    }
    
    let newBetAmount;
    if (currency === 'USD') {
      // Convert USD to BTC
      newBetAmount = numValue / usdRate;
    } else {
      // Already in BTC
      newBetAmount = numValue;
    }
    
    // Clamp to min/max
    const clamped = Math.max(minBet, Math.min(maxBet, newBetAmount));
    setBetAmount(clamped);
    
    // Update input to show clamped value in current currency
    if (currency === 'USD') {
      setBetAmountInput((clamped * usdRate).toFixed(2));
    } else {
      setBetAmountInput(formatBTC(clamped));
    }
  };

  useEffect(() => {
    if (isDraggingMultiplier) {
      document.addEventListener('mousemove', handleMultiplierMouseMove);
      document.addEventListener('mouseup', handleMultiplierMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMultiplierMouseMove);
        document.removeEventListener('mouseup', handleMultiplierMouseUp);
      };
    }
  }, [isDraggingMultiplier, selectedIndex]);

  useEffect(() => {
    if (isDraggingBet) {
      document.addEventListener('mousemove', handleBetMouseMove);
      document.addEventListener('mouseup', handleBetMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleBetMouseMove);
        document.removeEventListener('mouseup', handleBetMouseUp);
      };
    }
  }, [isDraggingBet, betAmount]);

  // Format bet amount from satoshis to BTC
  const formatBetAmount = (satoshis) => {
    const btc = satoshis / SATOSHIS_PER_BTC;
    if (btc >= 1) return btc.toFixed(6);
    if (btc >= 0.01) return btc.toFixed(6);
    return btc.toFixed(8);
  };

  // Transform bet data for display
  const transformBetForDisplay = (bet) => {
    try {
      return {
        result: bet.is_win ? 'win' : 'lose',
        betAmount: formatBetAmount(bet.bet_amount || 0),
        betAmountSat: bet.bet_amount || 0,
        payoutAmount: bet.is_win ? formatBetAmount(bet.payout_amount || 0) : '0.00000000',
        payoutAmountSat: bet.is_win ? (bet.payout_amount || 0) : 0,
        bet: bet.bet_number || (bet.bet_id ? (typeof bet.bet_id === 'string' ? bet.bet_id.slice(-8) : String(bet.bet_id).slice(-8)) : 'N/A'),
        roll: bet.roll_result !== undefined && bet.roll_result !== null ? bet.roll_result : 'N/A'
      };
    } catch (error) {
      console.error('[Main Page] Error transforming bet:', error, bet);
      return null;
    }
  };

  // Set mounted state on client
  useEffect(() => {
    setMounted(true);
  }, []);

  // Fetch data on mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch house info (bet limits)
        const houseData = await getHouseInfo();
        setHouseInfo(houseData);
        
        // Convert satoshis to BTC
        const minBetBTC = houseData.min_bet / SATOSHIS_PER_BTC;
        const maxBetBTC = houseData.max_bet / SATOSHIS_PER_BTC;
        setMinBet(minBetBTC);
        setMaxBet(maxBetBTC);
        
        // Set initial bet amount to middle of range
        const initialBet = (minBetBTC + maxBetBTC) / 2;
        const clampedInitialBet = Math.max(minBetBTC, Math.min(maxBetBTC, initialBet));
        setBetAmount(clampedInitialBet);
        
        // Initialize input value
        if (currency === 'USD') {
          setBetAmountInput((clampedInitialBet * usdRate).toFixed(2));
        } else {
          setBetAmountInput(formatBTC(clampedInitialBet));
        }
        
        // Fetch wallets
        const walletsData = await getAllWallets();
        setWallets(walletsData);
        
        // Store bet ranges per multiplier
        const ranges = {};
        walletsData.forEach(wallet => {
          ranges[wallet.multiplier] = {
            min: wallet.min_bet_sats ? wallet.min_bet_sats / SATOSHIS_PER_BTC : minBetBTC,
            max: wallet.max_bet_sats ? wallet.max_bet_sats / SATOSHIS_PER_BTC : maxBetBTC
          };
        });
        setWalletBetRanges(ranges);
        
        // Set default selected wallet
        if (walletsData.length > 0) {
          const sortedWallets = [...walletsData].sort((a, b) => a.multiplier - b.multiplier);
          const defaultIndex = Math.min(4, sortedWallets.length - 1);
          setSelectedIndex(defaultIndex);
          if (sortedWallets[defaultIndex]) {
            const defaultWallet = sortedWallets[defaultIndex];
            setSelectedWallet(defaultWallet);
            setWalletAddress(defaultWallet.address);
            
            // Set bet limits for default wallet
            const defaultRange = ranges[defaultWallet.multiplier] || { min: minBetBTC, max: maxBetBTC };
            setMinBet(defaultRange.min);
            setMaxBet(defaultRange.max);
            
            // Clamp bet amount to new range
            const clampedBet = Math.max(defaultRange.min, Math.min(defaultRange.max, betAmount));
            setBetAmount(clampedBet);
          }
        }
        
        // Optionally fetch stats and recent bets
        try {
          const statsData = await getStats();
          if (statsData && statsData.total_bets) {
            setTotalBets(statsData.total_bets);
          }
        } catch (err) {
          console.warn('Failed to fetch stats:', err);
        }
        
        // Fetch initial recent bets via REST API for immediate display
        try {
          const recentBetsData = await getRecentBets(3);
          if (recentBetsData && recentBetsData.bets) {
            const formatted = recentBetsData.bets.map(bet => transformBetForDisplay(bet));
            setRecentBets(formatted);
          }
        } catch (err) {
          console.warn('Failed to fetch initial recent bets:', err);
        }
        
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load game data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    
    // Convert SVG logo to data URL for better mobile Safari compatibility
    const convertSvgToDataUrl = async () => {
      try {
        const response = await fetch('/assets/dice-bitcoin.svg');
        if (!response.ok) {
          throw new Error('Failed to fetch SVG');
        }
        const svgText = await response.text();
        
        // Encode SVG to base64 data URL (works better on mobile Safari)
        const base64Svg = btoa(unescape(encodeURIComponent(svgText)));
        const svgDataUrl = `data:image/svg+xml;base64,${base64Svg}`;
        
        // For better mobile Safari support, convert to PNG via canvas
        const img = new Image();
        img.crossOrigin = 'anonymous';
        
        img.onload = () => {
          try {
            const canvas = document.createElement('canvas');
            canvas.width = 200;
            canvas.height = 200;
            const ctx = canvas.getContext('2d');
            
            // Draw white background for better QR code contrast
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Draw the SVG image
            ctx.drawImage(img, 0, 0, 200, 200);
            
            // Convert to PNG data URL
            const pngDataUrl = canvas.toDataURL('image/png');
            setLogoDataUrl(pngDataUrl);
          } catch (canvasError) {
            // Fallback to SVG data URL if canvas fails
            console.warn('Canvas conversion failed, using SVG data URL:', canvasError);
            setLogoDataUrl(svgDataUrl);
          }
        };
        
        img.onerror = () => {
          // Fallback to SVG data URL
          setLogoDataUrl(svgDataUrl);
        };
        
        img.src = svgDataUrl;
      } catch (error) {
        console.error('Error converting SVG to data URL:', error);
        // Fallback to SVG path
        setLogoDataUrl('/assets/dice-bitcoin.svg');
      }
    };
    
    convertSvgToDataUrl();
  }, []);

  // Update input value when betAmount or currency changes
  useEffect(() => {
    if (currency === 'USD') {
      setBetAmountInput((betAmount * usdRate).toFixed(2));
    } else {
      setBetAmountInput(formatBTC(betAmount));
    }
  }, [betAmount, currency]);

  // Update wallet address and bet limits when selected index changes
  useEffect(() => {
    if (wallets.length > 0 && selectedIndex < wallets.length) {
      const sortedWallets = [...wallets].sort((a, b) => a.multiplier - b.multiplier);
      if (selectedIndex < sortedWallets.length) {
        const wallet = sortedWallets[selectedIndex];
        setSelectedWallet(wallet);
        setWalletAddress(wallet.address);
        
        // Update bet limits for selected wallet
        // Use wallet-specific range if available, otherwise calculate from wallet data or use global defaults
        const range = walletBetRanges[wallet.multiplier];
        if (range) {
          setMinBet(range.min);
          setMaxBet(range.max);
          
          // Clamp current bet amount to new range
          setBetAmount(prev => Math.max(range.min, Math.min(range.max, prev)));
        } else if (wallet.min_bet_sats || wallet.max_bet_sats) {
          // Fallback: calculate from wallet data directly
          const minBetBTC = wallet.min_bet_sats ? wallet.min_bet_sats / SATOSHIS_PER_BTC : minBet;
          const maxBetBTC = wallet.max_bet_sats ? wallet.max_bet_sats / SATOSHIS_PER_BTC : maxBet;
          setMinBet(minBetBTC);
          setMaxBet(maxBetBTC);
          setBetAmount(prev => Math.max(minBetBTC, Math.min(maxBetBTC, prev)));
        }
      }
    }
  }, [selectedIndex, wallets, walletBetRanges]);

  const [activeTab, setActiveTab] = useState('all');
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket message handler
  const handleBetMessage = useCallback((message) => {
    console.log('[Main Page] Received WebSocket message:', message);
    if (message.type === 'new_bet' && message.bet) {
      console.log('[Main Page] Processing new bet:', message.bet);
      try {
        const transformed = transformBetForDisplay(message.bet);
        console.log('[Main Page] Transformed bet:', transformed);
        setRecentBets(prev => {
          // Check if bet already exists (avoid duplicates)
          const exists = prev.some(bet => bet.bet === transformed.bet);
          if (exists) {
            console.log('[Main Page] Bet already exists, skipping:', transformed.bet);
            return prev;
          }
          // Add new bet at the beginning and keep only last 3
          return [transformed, ...prev].slice(0, 3);
        });
      } catch (error) {
        console.error('[Main Page] Error transforming bet:', error, message.bet);
      }
    }
  }, []);

  // WebSocket error handler
  const handleWebSocketError = useCallback((error) => {
    console.error('[WebSocket] Error:', error);
  }, []);

  // WebSocket connect handler
  const handleWebSocketConnect = useCallback(() => {
    console.log('[WebSocket] Connected to bet updates');
    setWsConnected(true);
  }, []);

  // Get WebSocket URL from API URL
  const getWebSocketUrl = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    // Handle both http:// and https://, and also handle URLs without protocol
    let wsUrl;
    if (apiUrl.startsWith('http://')) {
      wsUrl = apiUrl.replace('http://', 'ws://');
    } else if (apiUrl.startsWith('https://')) {
      wsUrl = apiUrl.replace('https://', 'wss://');
    } else if (apiUrl.startsWith('ws://') || apiUrl.startsWith('wss://')) {
      wsUrl = apiUrl;
    } else {
      // Assume http if no protocol
      wsUrl = `ws://${apiUrl.replace(/^https?:\/\//, '')}`;
    }
    const fullUrl = `${wsUrl}/ws/bets`;
    console.log('[Main Page] WebSocket URL:', fullUrl);
    return fullUrl;
  };

  // Connect to WebSocket for real-time bet updates
  const { isConnected } = useWebSocket(
    getWebSocketUrl(),
    handleBetMessage,
    handleWebSocketError,
    handleWebSocketConnect
  );

  // Update connection status
  useEffect(() => {
    setWsConnected(isConnected);
  }, [isConnected]);

  // Prevent hydration mismatch by showing loading state until mounted
  if (!mounted || loading) {
    return (
      <div className="min-h-screen bg-[url('/bg.png')] bg-cover bg-center bg-no-repeat flex items-center justify-center" suppressHydrationWarning>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white mb-4" suppressHydrationWarning></div>
          <p className="text-white text-lg" suppressHydrationWarning>Loading game data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[url('/bg.png')] bg-cover bg-center bg-no-repeat flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-400 text-xl mb-4">⚠️ Error Loading Data</div>
          <p className="text-white mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-[#222] text-white rounded-lg hover:bg-[#333] transition"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (wallets.length === 0) {
    return (
      <div className="min-h-screen bg-[url('/bg.png')] bg-cover bg-center bg-no-repeat flex items-center justify-center">
        <div className="text-center">
          <p className="text-white text-lg">No wallets available</p>
          <p className="text-white text-sm mt-2">Please configure wallets in admin panel</p>
        </div>
      </div>
    );
  }

  return (
    <div className="" suppressHydrationWarning>
      <Navbar />

      <div className="bg-[url('/bg.png')] bg-cover bg-center bg-no-repeat">
        <div className="pt-4 pb-20 max-w-[1250px] mx-auto w-full z-20 px-4">
          <div className='rounded-[5px] bg-[rgba(0,0,0,0.80)] p-3 mb-5'>
            <div className="text-center mb-4">
              <p className="text-[#FFF] font-inter md:text-[23px] tracking-[0.0444em]">
                Select Your Odds &amp; Win Multiplier
              </p>
            </div>
            <div className='hidden md:block'>


              <div className="flex justify-between items-center bg-black/50 backdrop-blur-sm rounded-lg p-3 mb-4 gap-2 flex-wrap border border-[#FF8C00]/20">
                {multipliers.map((mult, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedIndex(i)}
                    className={`flex flex-col items-center justify-center px-3 py-2 rounded min-w-[80px] transition-all ${selectedIndex === i ? 'bg-[#FF8C00] shadow-md scale-105 text-white' : 'hover:bg-[#FF8C00]/30 text-white'}`}
                  >
                    <p className="text-xs font-medium mb-1">Multiplier</p>
                    <p className="text-xl font-bold">{mult.label}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="relative mb-4 hidden md:block">
              <div
                ref={multiplierProgressBarRef}
                onMouseDown={handleMultiplierMouseDown}
                className="relative rounded border border-[#FF8C00]/30 bg-black/50 shadow-inner w-full h-5 overflow-hidden cursor-pointer"
              >
                <div
                  className="absolute top-0 left-0 h-full rounded-l transition-all duration-150"
                  style={{
                    width: `${getMultiplierProgressPosition()}%`,
                    background: 'linear-gradient(90deg, #FF8C00 0%, #FFA500 100%)'
                  }}
                />
                <div
                  className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 transition-all duration-150"
                  style={{ left: `${getMultiplierProgressPosition()}%` }}
                >
                  <div className="w-9 h-7 bg-[#FF8C00] rounded shadow-lg border border-[#FFA500] flex items-center justify-center gap-0.5 cursor-grab active:cursor-grabbing">
                    <div className="w-px h-4 bg-white/50"></div>
                    <div className="w-px h-4 bg-white/50"></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex md:justify-between justify-center md:items-center gap-4 md:gap-1 flex-wrap">
              {multipliers.map((mult, i) => (
                <button
                  key={i}
                  onClick={() => setSelectedIndex(i)}
                  className="flex flex-col items-center justify-center w-20 px-1 py-1 rounded-full text-white font-medium text-sm  transition-all hover:scale-105"
                  style={{
                    background: 'linear-gradient(135deg, #FF8C00 0%, #FFA500 100%)',
                    boxShadow: '0 2px 8px rgba(255, 140, 0, 0.3)'
                  }}
                >
                  <div className="text-xs opacity-90">Chance</div>
                  <span className="text-xs font-medium">{mult.chance}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_320px] gap-4">
            {/* Left Panel — Bet Amount */}
            <div className="rounded-[5px] bg-[rgba(0,0,0,0.20)] p-3">
              <div className="pb-3 text-center">
                <p className="text-[#FFF] font-inter text-[23px] tracking-[0.0444em]">Select Bet Amount</p>
              </div>

              <div className="pb-3">
                <div className="flex py-2 px-2 justify-between items-center rounded-[5px] bg-black/50 w-full border border-[#FF8C00]/20">
                  <input
                    type="text"
                    value={betAmountInput}
                    onChange={handleBetAmountInputChange}
                    onBlur={() => {
                      // Ensure input is formatted correctly on blur
                      if (currency === 'USD') {
                        setBetAmountInput((betAmount * usdRate).toFixed(2));
                      } else {
                        setBetAmountInput(formatBTC(betAmount));
                      }
                    }}
                    className="bg-transparent border-none outline-none text-[#FFF] font-arial text-lg flex-1 text-left"
                    style={{ width: 'auto', minWidth: '60px' }}
                    placeholder="0.00"
                  />
                  <div className="relative">
                    <div className="flex rounded-md overflow-hidden" style={{ background: '#333' }}>
                      <button
                        onClick={() => setCurrency('BTC')}
                        className="px-3 py-2 text-xs font-medium text-white transition-all"
                        style={{
                          background: currency === 'BTC' ? '#FF8C00' : 'transparent'
                        }}
                      >
                        BTC
                      </button>
                      <button
                        onClick={() => setCurrency('USD')}
                        className="px-3 py-2 text-xs font-medium text-white transition-all"
                        style={{
                          background: currency === 'USD' ? '#FF8C00' : 'transparent'
                        }}
                      >
                        USD
                      </button>
                    </div>
                  </div>
                </div>
                <div className="text-center pt-1.5">
                  <p className="text-[#FFF] font-inter text-[15px] leading-6">
                    {currency === 'BTC' ? `$${(betAmount * usdRate).toFixed(2)} USD` : `${formatBTC(betAmount)} BTC`}
                  </p>
                </div>
              </div>

              {/* Profit Calculator */}
              {selectedWallet && (
                <div className="pb-3">
                  <div className="rounded-[5px] bg-black/50 border border-[#FF8C00]/20 p-3">
                    <p className="text-[#FFF] font-inter text-xs mb-2 text-center opacity-75">Potential Profit (if you win)</p>
                    <div className="text-center">
                      <p className="text-[#FF8C00] font-inter text-lg font-semibold mb-1">
                        {((betAmount * (selectedWallet.multiplier - 1)).toFixed(6))} BTC
                      </p>
                      <p className="text-[#FFF] font-inter text-sm opacity-75">
                        ${((betAmount * (selectedWallet.multiplier - 1)) * usdRate).toFixed(2)} USD
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Bet slider */}
              <div className="pb-2 relative">
                <div
                  ref={betProgressBarRef}
                  onMouseDown={handleBetMouseDown}
                  className="relative flex flex-col justify-center items-start rounded border border-[#FF8C00]/30 bg-black/50 shadow-inner w-full h-[18px] cursor-pointer overflow-hidden"
                >
                  <div
                    className="absolute top-0 left-0 h-full bg-[#FF8C00] transition-all duration-150"
                    style={{ width: `${getBetProgressPosition()}%` }}
                  />
                  <div
                    className="absolute top-0 transition-all duration-150"
                    style={{ left: `${getBetProgressPosition()}%`, transform: 'translateX(-50%)' }}
                  >
                    <div className="shrink-0 shadow-[0_0_1px_1px_#FF8C00_inset] w-[34px] h-7 relative cursor-grab active:cursor-grabbing bg-[#FF8C00] border border-[#FFA500]">
                      <div className="bg-white/50 w-px h-3.5 absolute left-[15px] top-[7px]"></div>
                      <div className="bg-white/50 w-px h-3.5 absolute left-[18px] top-[7px]"></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Min / 1/2 / x2 / Max buttons */}
              <div className="pt-4">
                <div className="flex justify-between items-center rounded-[5px] bg-black/50 w-full text-white font-inter text-[15px] border border-[#FF8C00]/20">
                  <button
                    onClick={() => handleBetChange(minBet)}
                    className="p-2 rounded-[5px] w-[25%] text-center hover:bg-[#FF8C00]/30 transition"
                  >
                    Min
                  </button>
                  <button
                    onClick={() => handleBetChange(betAmount / 2)}
                    className="py-2 px-2 border-x border-[#FF8C00]/30 w-[25%] text-center text-sm hover:bg-[#FF8C00]/30 transition"
                  >
                    1/2
                  </button>
                  <button
                    onClick={() => handleBetChange(betAmount * 2)}
                    className="py-2 px-2 border-r border-[#FF8C00]/30 w-[25%] text-center hover:bg-[#FF8C00]/30 transition"
                  >
                    x2
                  </button>
                  <button
                    onClick={() => handleBetChange(maxBet)}
                    className="p-2 rounded-[5px] w-[25%] text-center hover:bg-[#FF8C00]/30 transition"
                  >
                    Max
                  </button>
                </div>
              </div>

              {/* Game Info */}
              <div className="mt-4">
                <p className="text-[#FFF] font-inter text-[23px] tracking-[0.0437em] text-center mb-2">Game Info</p>
                <div className="grid grid-cols-2 gap-1.5 mb-1.5">
                  <div className="py-1.5 px-2 bg-black/50 rounded-[5px] text-center border border-[#FF8C00]/20">
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">Roll Lower than:</p>
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">{calculateRollLowerThan()}</p>
                  </div>
                  <div className="py-1.5 px-2 bg-black/50 rounded-[5px] text-center border border-[#FF8C00]/20">
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">Maximum Roll</p>
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">65535</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-1.5">
                  <div className="py-1.5 px-2 bg-black/50 rounded-[5px] text-center border border-[#FF8C00]/20">
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">Min Bet</p>
                    <p className="text-[#FF8C00] font-inter text-[11px] leading-3">{minBet.toFixed(6)} BTC</p>
                  </div>
                  <div className="py-1.5 px-2 bg-black/50 rounded-[5px] text-center border border-[#FF8C00]/20">
                    <p className="text-[#FFF] font-inter text-[11px] leading-3">Max Bet</p>
                    <p className="text-[#FF8C00] font-inter text-[11px] leading-3">{maxBet.toFixed(6)} BTC</p>
                  </div>
                </div>
              </div>
            </div>
            <div className='hidden md:block'>
              <div className="flex flex-col gap-4">

                <div className=" p-3">
                  <p className="text-[#FFF] font-inter text-[23px] tracking-[0.0444em] text-center mb-3">Total Bets</p>
                  <div className="flex justify-center items-start min-h-[56px]">
                    {totalBets !== null ? (
                      totalBets.toLocaleString().split('').map((char, i) => (
                        <React.Fragment key={i}>
                          {char === "," ? (
                            <div className="flex items-end px-0.5">
                              <p className="text-[#222] font-inter text-[40px] leading-8">,</p>
                            </div>
                          ) : (
                            <div className="p-0.5">
                              <div className="p-2 bg-black/50 rounded-[5px] shadow-[0_1px_3px_0_rgba(255,140,0,0.30)] w-10 flex justify-center border border-[#FF8C00]/20">
                                <p className="text-[#FFF] font-inter text-[40px] leading-8">{char}</p>
                              </div>
                            </div>
                          )}
                        </React.Fragment>
                      ))
                    ) : (
                      <div className="p-2 bg-black/50 rounded-[5px] shadow-[0_1px_3px_0_rgba(255,140,0,0.30)] border border-[#FF8C00]/20">
                        <p className="text-[#FFF] font-inter text-[20px]">Loading...</p>
                      </div>
                    )}
                  </div>
                </div>


                <div className=" p-3">
                  <div className="flex justify-between items-center mb-3">
                    <p className="text-[#FFF] font-inter text-[23px] tracking-[0.0444em]">Recent Games</p>
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                      <p className="text-[#FFF] font-inter text-xs">
                        {wsConnected ? 'Live' : 'Reconnecting...'}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                    {recentBets.length > 0 ? (
                      recentBets.map((bet, idx) => (
                        <div key={idx} className="flex justify-between items-center rounded-[5px] bg-black/50 p-2 h-[68px] border border-[#FF8C00]/20">
                          <div className="flex flex-col items-center w-[70px]">
                            <div className="w-5 h-5 relative mb-0.5 flex items-center justify-center">
                              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                {bet.result === 'win' ? (
                                  <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#FF8C00" />
                                ) : (
                                  <path d="M10 0C4.47 0 0 4.47 0 10C0 15.53 4.47 20 10 20C15.53 20 20 15.53 20 10C20 4.47 15.53 0 10 0ZM15 13.59L13.59 15L10 11.41L6.41 15L5 13.59L8.59 10L5 6.41L6.41 5L10 8.59L13.59 5L15 6.41L11.41 10L15 13.59Z" fill="#FF4444" stroke="#FF6666" strokeWidth="0.5" />
                                )}
                              </svg>
                            </div>
                            <p className="text-white font-inter text-[13px]">{bet.result === 'win' ? "Win" : "Lose"}</p>
                          </div>

                          <div className="text-center flex-1 px-2">
                            <p className="text-white font-inter text-[15px]">Bet Amount</p>
                            <p className="text-[#FF8C00] font-inter text-sm mt-0.5">
                              {bet.betAmount} BTC
                            </p>
                            <p className="text-white/70 font-inter text-xs">
                              (${(bet.betAmountSat / SATOSHIS_PER_BTC * usdRate).toFixed(2)} USD)
                            </p>
                          </div>

                          <div className="text-center flex-1 px-2">
                            <p className="text-white font-inter text-[15px]">Payout</p>
                            <p className={`${bet.result === 'win' ? "text-[#FF8C00]" : "text-white/50"} font-inter text-sm mt-0.5`}>
                              {bet.payoutAmount} BTC
                            </p>
                            <p className="text-white/70 font-inter text-xs">
                              (${(bet.payoutAmountSat / SATOSHIS_PER_BTC * usdRate).toFixed(2)} USD)
                            </p>
                          </div>

                          <div className="text-center w-[70px]">
                            <p className="text-white font-inter text-[15px]">Bet</p>
                            <p className="text-white font-inter text-xs mt-0.5">{bet.bet}</p>
                          </div>
                          <div className="text-center w-[70px]">
                            <p className="text-white font-inter text-base">Roll</p>
                            <p className="text-white font-inter text-xs mt-0.5">{bet.roll}</p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-4">
                        <p className="text-gray-500 text-sm">
                          {wsConnected ? 'Waiting for bets...' : 'Connecting...'}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Right Panel — Deposit Address */}
            <div className="rounded-[5px] bg-[rgba(0,0,0,0.80)] p-3 border border-[#FF8C00]/20">
              <div className="text-center mb-3">
                <p className="text-[#FFF] font-inter text-[23px] tracking-[0.0437em]">Send <span className="text-[#FF8C00]">BTC</span> to Play</p>
              </div>
              <div className="flex justify-center mb-3">
                {walletAddress ? (
                  logoDataUrl ? (
                    <QRCode 
                      size={250} 
                      logoImage={logoDataUrl}
                      logoWidth={120}
                      logoHeight={120}
                      logoOpacity={0.8}
                      removeQrCodeBehindLogo={true}
                      value={`bitcoin:${walletAddress}?amount=${betAmount.toFixed(8)}`} 
                    />
                  ) : (
                    <QRCode 
                      size={250} 
                      logoImage='/assets/dice-bitcoin.svg'
                      logoWidth={120}
                      logoHeight={120}
                      logoOpacity={0.8}
                      removeQrCodeBehindLogo={true}
                      value={`bitcoin:${walletAddress}?amount=${betAmount.toFixed(8)}`} 
                    />
                  )
                ) : (
                  <div className="w-[250px] h-[250px] bg-gray-200 flex items-center justify-center rounded">
                    <p className="text-gray-500">Loading...</p>
                  </div>
                )}
              </div>
              <div className="text-center px-2 mb-3 break-all">
                <p className="text-[#FFF] font-inter text-[13px]">
                  {walletAddress || 'Loading address...'}
                </p>
              </div>
              <div className="flex justify-center mb-2 px-2">
                <button
                  onClick={() => walletAddress && navigator.clipboard.writeText(walletAddress)}
                  disabled={!walletAddress}
                  className="cursor-pointer w-full text-nowrap py-2 px-8 rounded-[5px] bg-[#222] shadow-[0_1px_3px_0_rgba(34,34,34,0.30)] text-[#FFF] font-arial text-xs hover:bg-[#333] transition disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Copy Address
                </button>
              </div>
              <div className="px-2">
                <div className="p-2 text-center rounded-[5px] bg-black/50 shadow-[0_1px_3px_0_rgba(255,140,0,0.30)] border border-[#FF8C00]/20">
                  <p className="text-[#FFF] font-inter text-[11px]">Open in your wallet</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <BettingHistory />
      </div>
      <Footer />





    </div>
  );
}