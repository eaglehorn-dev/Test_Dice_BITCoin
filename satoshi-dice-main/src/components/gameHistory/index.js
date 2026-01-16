"use client"
import { useState, useEffect, useCallback, useRef } from 'react';
import { getBetHistory } from '@/utils/api';
import { useWebSocket } from '@/utils/websocket';

export default function BettingHistory() {
    const SATOSHIS_PER_BTC = 100000000;
    const USD_RATE = 586.1; // TODO: Fetch from API if needed

    // State management
    const [bets, setBets] = useState([]);
    const [loading, setLoading] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [page, setPage] = useState(1);
    const [activeTab, setActiveTab] = useState('all');
    const [search] = useState('');
    const [sort] = useState('newest');
    const [error, setError] = useState(null);

    // Refs for scroll detection
    const observerTarget = useRef(null);
    const loadingRef = useRef(false);
    
    // WebSocket connection status
    const [wsConnected, setWsConnected] = useState(false);

    // Format bet amount from satoshis to BTC (shorter format, max 6 chars)
    const formatBetAmount = (satoshis) => {
        const btc = satoshis / SATOSHIS_PER_BTC;
        if (btc >= 1) return btc.toFixed(2);
        if (btc >= 0.01) return btc.toFixed(4);
        return btc.toFixed(6);
    };
    
    // Format BTC amount with max 6 character limit (excluding " BTC")
    const formatBTCShort = (btcString) => {
        if (!btcString || btcString === 'N/A' || btcString === '0.00') return '0.00';
        const num = parseFloat(btcString);
        if (isNaN(num)) return '0.00';
        // Format to max 6 characters
        if (num >= 1000) return num.toFixed(0);
        if (num >= 100) return num.toFixed(1);
        if (num >= 10) return num.toFixed(2);
        if (num >= 1) return num.toFixed(2);
        if (num >= 0.1) return num.toFixed(3);
        if (num >= 0.01) return num.toFixed(4);
        return num.toFixed(5);
    };

    // Format time ago
    const formatTimeAgo = (dateString) => {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        return date.toLocaleDateString();
    };

    // Transform bet data for display
    const transformBetForDisplay = (bet) => {
        try {
            const isWin = bet.is_win === true; // Explicitly check for true
            const payoutAmount = bet.payout_amount || 0;
            
            return {
                id: bet.bet_id || bet.bet_id || 'unknown',
                result: isWin ? 'win' : 'lose',
                betAmount: formatBetAmount(bet.bet_amount || 0),
                betAmountSat: bet.bet_amount || 0,
                betUsd: `$${((bet.bet_amount || 0) / SATOSHIS_PER_BTC * USD_RATE).toFixed(2)}`,
                payout: isWin ? formatBetAmount(payoutAmount) : '0.00',
                payoutAmountSat: isWin ? payoutAmount : 0,
                payoutUsd: isWin ? `$${(payoutAmount / SATOSHIS_PER_BTC * USD_RATE).toFixed(2)}` : '$0.00',
                time: formatTimeAgo(bet.created_at),
                gameId: bet.bet_number || (bet.bet_id ? bet.bet_id.slice(-8) : 'N/A'),
                depositTx: bet.deposit_txid ? `${bet.deposit_txid.slice(0, 10)}...` : 'N/A',
                depositTxFull: bet.deposit_txid || null,
                payoutTx: bet.payout_txid ? `${bet.payout_txid.slice(0, 10)}...` : 'N/A',
                payoutTxFull: bet.payout_txid || null,
                bet: bet.bet_number || (bet.bet_id ? bet.bet_id.slice(-8) : 'N/A'),
                roll: bet.roll_result !== undefined && bet.roll_result !== null ? bet.roll_result : 'N/A'
            };
        } catch (error) {
            console.error('Error transforming bet:', error, bet);
            return null; // Return null to filter out invalid bets
        }
    };

    // Fetch bets function
    const fetchBets = useCallback(async (pageNum = 1, reset = false) => {
        if (loadingRef.current) return; // Prevent concurrent requests
        loadingRef.current = true;

        try {
            setLoading(true);
            setError(null);

            console.log('Fetching all bets');
            console.log('Query params:', { page: pageNum, page_size: 50, filter: activeTab, sort, search });

            const response = await getBetHistory('all', {
                page: pageNum,
                page_size: 50,
                filter: activeTab,
                sort: sort,
                search: search || null
            });

            console.log('Bet history response:', response);
            console.log('Response structure:', {
                hasBets: !!response.bets,
                betsLength: response.bets?.length || 0,
                hasPagination: !!response.pagination,
                hasStats: !!response.stats,
                fullResponse: response
            });

            if (!response) {
                console.error('No response received');
                setError('No response from server');
                if (reset) {
                    setBets([]);
                }
                return;
            }

            if (!response.bets) {
                console.error('Response missing bets array:', response);
                setError('Invalid response structure: missing bets array');
                if (reset) {
                    setBets([]);
                }
                return;
            }

            console.log('Number of bets received:', response.bets.length);
            console.log('Sample bet data:', response.bets[0]);

            const transformedBets = response.bets.map(transformBetForDisplay).filter(bet => bet !== null);
            console.log('Transformed bets count:', transformedBets.length);
            console.log('Sample transformed bet:', transformedBets[0]);

            if (reset) {
                setBets(transformedBets);
            } else {
                setBets(prev => [...prev, ...transformedBets]);
            }

            // Handle pagination - check if it exists
            if (response.pagination) {
                setHasMore(response.pagination.has_next || false);
            } else {
                // If no pagination, assume no more if we got fewer bets than page size
                setHasMore(transformedBets.length >= 50);
                console.warn('Response missing pagination object');
            }


            if (transformedBets.length === 0 && pageNum === 1) {
                setError('No bets found for this address');
            }

        } catch (err) {
            console.error('Error fetching bets:', err);
            console.error('Error details:', err.response?.data);
            setError(err.response?.data?.detail || err.response?.data?.message || err.message || 'Failed to load bet history');
            if (reset) {
                setBets([]);
            }
        } finally {
            setLoading(false);
            loadingRef.current = false;
        }
    }, [activeTab, sort, search]);

    // Effect for initial load and filter/search changes
    useEffect(() => {
        setPage(1);
        setBets([]);
        setHasMore(true);
        // Reset loading ref when filter/search changes
        loadingRef.current = false;
        fetchBets(1, true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [activeTab, sort, search]);

    // Effect for pagination
    useEffect(() => {
        if (page > 1 && !loading) {
            fetchBets(page, false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page]);

    // Infinite scroll observer
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && hasMore && !loading) {
                    setPage(prev => prev + 1);
                }
            },
            { threshold: 0.1 }
        );

        if (observerTarget.current) {
            observer.observe(observerTarget.current);
        }

        return () => {
            if (observerTarget.current) {
                observer.unobserve(observerTarget.current);
            }
        };
    }, [hasMore, loading]);

    // WebSocket message handler for new bets
    const handleBetMessage = useCallback((message) => {
        if (message.type === 'new_bet' && message.bet) {
            console.log('[Bet History] Received new bet via WebSocket:', message.bet);
            
            // Transform the bet data to match our display format
            const transformedBet = transformBetForDisplay(message.bet);
            
            if (transformedBet) {
                // Add new bet to the beginning of the list
                setBets(prev => {
                    // Check if bet already exists (avoid duplicates)
                    const exists = prev.some(bet => bet.id === transformedBet.id);
                    if (exists) {
                        console.log('[Bet History] Bet already exists, skipping:', transformedBet.id);
                        return prev;
                    }
                    
                    // Add new bet at the beginning
                    return [transformedBet, ...prev];
                });
                
                // If we're on the first page and showing "all" bets, we might want to refresh
                // But for now, just add the new bet to the list
            }
        }
    }, []);

    // WebSocket error handler
    const handleWebSocketError = useCallback((error) => {
        console.error('[Bet History WebSocket] Error:', error);
    }, []);

    // WebSocket connect handler
    const handleWebSocketConnect = useCallback(() => {
        console.log('[Bet History WebSocket] Connected to bet updates');
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
        console.log('[Bet History] WebSocket URL:', fullUrl);
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

    // Handle transaction link click
    const handleTxClick = (txid, isPayout = false) => {
        if (!txid || txid === 'N/A') return;
        const network = process.env.NEXT_PUBLIC_NETWORK || 'testnet';
        const baseUrl = network === 'testnet' 
            ? 'https://mempool.space/testnet/tx' 
            : 'https://mempool.space/tx';
        window.open(`${baseUrl}/${isPayout ? txid : txid}`, '_blank');
    };

    return (
        <div className="min-h-screen bg-black p-4">
            <div className="max-w-7xl mx-auto">
                <h1 className="text-3xl font-bold text-white mb-6 text-center">All Bets History</h1>
                
                {error && (
                    <div className="mb-6 bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                        <div className="text-red-400 text-sm">{error}</div>
                    </div>
                )}

                {/* Filter Tabs */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-0 mb-6 border-2 border-[#FF8C00]/30 rounded-lg overflow-hidden bg-black/50">
                    <button
                        onClick={() => setActiveTab('all')}
                        className={`py-3 md:py-4 text-sm md:text-base font-semibold transition-colors relative
                        ${activeTab === 'all'
                                ? 'bg-[#FF8C00] text-white'
                                : 'bg-black/50 text-white/70 hover:bg-[#FF8C00]/30'
                            }`}
                    >
                        All
                        {activeTab === 'all' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#FFA500]"></div>}
                    </button>
                    <button
                        onClick={() => setActiveTab('wins')}
                        className={`py-3 md:py-4 text-sm md:text-base font-semibold transition-colors relative border-l-2 border-[#FF8C00]/30
                        ${activeTab === 'wins'
                                ? 'bg-[#FF8C00] text-white'
                                : 'bg-black/50 text-white/70 hover:bg-[#FF8C00]/30'
                            }`}
                    >
                        Wins
                        {activeTab === 'wins' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#FFA500]"></div>}
                    </button>
                    <button
                        onClick={() => setActiveTab('big_wins')}
                        className={`py-3 md:py-4 text-sm md:text-base font-semibold transition-colors relative border-l-2 border-[#FF8C00]/30
                        ${activeTab === 'big_wins'
                                ? 'bg-[#FF8C00] text-white'
                                : 'bg-black/50 text-white/70 hover:bg-[#FF8C00]/30'
                            }`}
                    >
                        Big Wins
                        {activeTab === 'big_wins' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#FFA500]"></div>}
                    </button>
                    <button
                        onClick={() => setActiveTab('rare_wins')}
                        className={`py-3 md:py-4 text-sm md:text-base font-semibold transition-colors relative border-l-2 border-[#FF8C00]/30
                        ${activeTab === 'rare_wins'
                                ? 'bg-[#FF8C00] text-white'
                                : 'bg-black/50 text-white/70 hover:bg-[#FF8C00]/30'
                            }`}
                    >
                        Rare Wins
                        {activeTab === 'rare_wins' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#FFA500]"></div>}
                    </button>
                </div>

                {/* Bet List */}
                <div className="space-y-4">
                    {bets.length > 0 ? (
                        <>
                            {bets.map((item) => (
                                <div key={item.id} className="bg-black/50 border border-[#FF8C00]/20 rounded-lg p-2 md:p-3 max-w-full">
                                    <div className="flex flex-col lg:grid lg:grid-cols-12 gap-2 lg:gap-2 lg:items-center">
                                        {/* Result Section */}
                                        <div className="lg:col-span-2 flex items-center justify-between lg:block border-b lg:border-b-0 pb-2 lg:pb-0 lg:pr-0">
                                            <div className="text-xs font-semibold text-white lg:text-center lg:mb-1">Result</div>
                                            <div className="flex items-center gap-2 lg:flex-col lg:gap-1">
                                                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0`}>
                                                    {item.result === 'win' ? (
                                                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                            <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="#FF8C00" />
                                                        </svg>
                                                    ) : (
                                                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                            <path d="M10 0C4.47 0 0 4.47 0 10C0 15.53 4.47 20 10 20C15.53 20 20 15.53 20 10C20 4.47 15.53 0 10 0ZM15 13.59L13.59 15L10 11.41L6.41 15L5 13.59L8.59 10L5 6.41L6.41 5L10 8.59L13.59 5L15 6.41L11.41 10L15 13.59Z" fill="#3C3C3C" />
                                                        </svg>
                                                    )}
                                                </div>
                                                <span className={`text-sm font-semibold capitalize ${item.result === 'win' ? 'text-[#FF8C00]' : 'text-white/50'}`}>
                                                    {item.result}
                                                </span>
                                            </div>
                                        </div>

                                        {/* Bet Amount & Payout */}
                                        <div className="lg:col-span-3 grid grid-cols-2 gap-2">
                                            <div className="border border-[#FF8C00]/30 bg-black/50 rounded-md p-1.5 text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Bet Amount</div>
                                                <div className="font-semibold text-[11px] leading-tight truncate text-[#FF8C00]">
                                                    {formatBTCShort(item.betAmount)} BTC
                                                </div>
                                                <div className="text-[9px] text-white/70 mt-0.5">{item.betUsd}</div>
                                            </div>
                                            <div className="border border-[#FF8C00]/30 bg-black/50 rounded-md p-1.5 text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Payout</div>
                                                <div className={`font-semibold text-[11px] leading-tight truncate ${item.result === 'win' ? 'text-[#FF8C00]' : 'text-white/50'}`}>
                                                    {formatBTCShort(item.payout)} BTC
                                                </div>
                                                <div className="text-[9px] text-white/70 mt-0.5">{item.payoutUsd}</div>
                                            </div>
                                        </div>

                                        {/* Details Grid - All in one row */}
                                        <div className="lg:col-span-7 grid grid-cols-6 gap-1.5 pt-2 lg:pt-0 border-t lg:border-t-0 border-[#FF8C00]/20">
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Time</div>
                                                <div className="text-[11px] text-white">{item.time}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Game ID</div>
                                                <div className="text-[11px] text-[#FF8C00] hover:text-[#FFA500] hover:underline cursor-pointer truncate">{item.gameId}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Bet ID</div>
                                                <div className="text-[11px] text-white truncate">{item.bet}</div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Deposit TX</div>
                                                <div 
                                                    className="text-[11px] text-[#FF8C00] hover:text-[#FFA500] hover:underline cursor-pointer truncate"
                                                    onClick={() => handleTxClick(item.depositTxFull)}
                                                    title={item.depositTxFull}
                                                >
                                                    {item.depositTx}
                                                </div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Payout TX</div>
                                                <div 
                                                    className={`text-[11px] truncate ${item.payoutTx === 'N/A' ? 'text-white/50' : 'text-[#FF8C00] hover:text-[#FFA500] hover:underline cursor-pointer'}`}
                                                    onClick={() => item.payoutTxFull && handleTxClick(item.payoutTxFull, true)}
                                                    title={item.payoutTxFull}
                                                >
                                                    {item.payoutTx === 'N/A' ? <span className="text-white/50">N/A</span> : item.payoutTx}
                                                </div>
                                            </div>
                                            <div className="text-center">
                                                <div className="text-[10px] font-semibold text-white mb-0.5">Roll</div>
                                                <div className="text-[11px] text-white">{item.roll}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Infinite Scroll Trigger */}
                            <div ref={observerTarget} className="h-10 flex items-center justify-center">
                                {loading && (
                                    <div className="text-white/70">Loading more bets...</div>
                                )}
                                {!hasMore && bets.length > 0 && (
                                    <div className="text-white/70">No more bets to load</div>
                                )}
                            </div>
                        </>
                    ) : loading ? (
                        <div className="text-center py-8">
                            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-[#FF8C00]"></div>
                            <p className="mt-2 text-white">Loading bet history...</p>
                        </div>
                    ) : !loading ? (
                        <div className="text-center py-8">
                            <p className="text-white">No bets found</p>
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}
