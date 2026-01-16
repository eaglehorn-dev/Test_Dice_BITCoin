"use client"
import Footer from '@/components/footer';
import Navbar from '@/components/navbar';
import React, { useState, useEffect } from 'react';
import { getFairnessSeeds } from '@/utils/api';

export default function ProvablyFairPage() {
    const [fairGames, setFairGames] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        fetchSeeds();
    }, []);

    const formatDate = (isoDate) => {
        try {
            const date = new Date(isoDate);
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const month = months[date.getMonth()];
            const day = date.getDate();
            const year = date.getFullYear();
            return `${month} ${day}, ${year}`;
        } catch (err) {
            return isoDate; // Return original if parsing fails
        }
    };

    const fetchSeeds = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getFairnessSeeds();
            
            // Transform API response to match UI structure
            const transformedSeeds = data.seeds.map(seed => ({
                date: formatDate(seed.seed_date),
                serverSeed: seed.server_seed_hash,
                plaintext: seed.server_seed || "Not Published"
            }));
            
            setFairGames(transformedSeeds);
        } catch (err) {
            console.error('Error fetching fairness seeds:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to load fairness seeds');
        } finally {
            setLoading(false);
        }
    };


    return (
        <div className="min-h-screen bg-black">
            <Navbar />
            <div className="px-10 py-10 md:pl-28" style={{ backgroundImage: "url('/bng.png')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <h1 className="text-2xl font-light tracking-wide text-white">Provably Fair</h1>
                <div className="mb-10 text-white">
                    <p className=" leading-relaxed mb-6">
                        BitcoinOnly is a provably fair on-chain Bitcoin game.


                    </p>
                    <p className=" leading-relaxed mb-6">In order to ensure that there is no way for the system to change the outcome of a bet, the secret keys used are decided ahead of time. They are not released right away, since they could be used to submit selective transactions and win bets unfairly. However, the hash of the secrets is released and forever recorded in the blockchain. After the secrets are release users can verify that preceeding bets were provably fair.

                    </p>
                    <p className=" leading-relaxed mb-6">
                        Each bet transaction that comes in is assigned to the secret key of the current day when it is first processed. In most cases this will be as soon as the transaction is broadcast on the bitcoin network. However it could be later if the system has some problems processing or an outage. All times are in UTC (GMT).


                    </p>
                </div>
            </div>

            {/* Content Section */}
            <div className="max-w-7xl mx-auto px-6 py-10" suppressHydrationWarning>




                {!mounted || loading ? (
                    <div className="flex justify-center items-center min-h-[400px]">
                        <div className="text-center">
                            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-[#FF8C00] mb-4"></div>
                            <p className="text-white">Loading fairness data...</p>
                        </div>
                    </div>
                ) : error ? (
                    <div className="flex justify-center items-center min-h-[400px]">
                        <div className="text-center max-w-md">
                            <div className="text-red-400 text-xl mb-4">⚠️ Error Loading Data</div>
                            <p className="text-white mb-4">{error}</p>
                            <button
                                onClick={fetchSeeds}
                                className="px-6 py-2 bg-[#FF8C00] text-white rounded-lg hover:bg-[#FFA500] transition"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                ) : fairGames.length === 0 ? (
                    <div className="flex justify-center items-center min-h-[400px]">
                        <div className="text-center">
                            <p className="text-white text-lg">No fairness data available</p>
                            <p className="text-white/70 text-sm mt-2">Please check back later</p>
                        </div>
                    </div>
                ) : (
                    <FairTable fairGames={fairGames} />
                )}

            </div>


            <Footer />
        </div>
    );
}

const FairTable = ({ fairGames }) => {
    return (
        <div className="w-full max-w-6xl mx-auto p-4 min-h-screen">

            <div className="grid grid-cols-3 md:gap-4 gap-1 mb-4 px-6 py-4 bg-black/50 border border-[#FF8C00]/20 rounded-xl shadow-sm">
                <div className="text-center font-medium text-white">Use Date</div>
                <div className="text-center font-medium text-white">Server Seed Hash</div>
                <div className="text-center font-medium text-white">Server Seed Plaintext</div>
            </div>

            <div className="space-y-4">
                {fairGames.map((game, index) => (
                    <div
                        key={index}
                        className="grid grid-cols-3 gap-4 items-center px-6 py-8 bg-black/50 border border-[#FF8C00]/20 rounded-xl shadow-sm  transition-colors"
                    >
                        {/* Date Column */}
                        <div className="text-center font-medium text-white">
                            {game.date}
                        </div>

                        {/* Hash Column (Orange Link Style) */}
                        <div className="text-center">
                            <span className="text-[#FF8C00] font-mono text-xs break-all cursor-pointer hover:text-[#FFA500] hover:underline transition-colors">
                                {game.serverSeed}
                            </span>
                        </div>

                        {/* Plaintext Column */}
                        <div className="text-center font-mono text-sm text-white break-all">
                            {game.plaintext === "Not Published" ? (
                                <span className="text-white/50 italic">Not Published</span>
                            ) : (
                                game.plaintext
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};