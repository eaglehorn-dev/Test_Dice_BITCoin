"use client"
import Footer from '@/components/footer';
import Navbar from '@/components/navbar';
import React from 'react';

export default function Rules() {
    const games = [
        {
            legacyAddress: "1DiceqoEZrTYyfvzHP2i2ew91gqk2u",
            cashAddr: "bitcoincash:qqqxvkqq0wkQthoz270xx2sxl5rulhr268awkskyanyuqrsk",
            maxRoll: 65535,
            maxBet: 0.01,
            multiplier: 1000,
            betNumber: 64,
            minBet: 0.001,
            odds: "0.097657401388571%"
        },
        {
            legacyAddress: "1DiceFQ88vFVPVB5V9539MtERm",
            cashAddr: "bitcoincash:qz9cq5eeguz30hcgnw2udc6cct56rlv2sjsg8f",
            maxRoll: 65535,
            maxBet: 0.1,
            multiplier: 100,
            betNumber: 635,
            minBet: 0.001,
            odds: "0.96542780440222283%"
        },
        {
            legacyAddress: "1DiceP1XdR.csLKIncMGLqr47g1DP4r6?3e",
            cashAddr: "bitcoincash:qz8cq5pa2mqrrkcc4220yhfelascfu427pcxwqpn4sy",
            maxRoll: 65535,
            maxBet: 0.2,
            multiplier: 50,
            betNumber: 1271,
            minBet: 0.001,
            odds: "1.938421683070115252%"
        },
        {
            legacyAddress: "1Diceldl4T4GN33D5sPRTuRzUzx",
            cashAddr: "bitcoincash:qz9cq3geryw9mqaxs8j8mccrgnyk4u4vukswerpzmc",
            maxRoll: 65535,
            maxBet: 0.4,
            multiplier: 25,
            betNumber: 2542,
            minBet: 0.001,
            odds: "3.87884336614023404%"
        },
        {
            legacyAddress: "1DiceUYTzz3qsbuEJuukKS7NZ7U997N",
            cashAddr: "bitcoincash:qc9s5jqqvqst89vlfevnor2f9hakk33azp2vfqn6spqx",
            maxRoll: 65535,
            maxBet: 1,
            multiplier: 10,
            betNumber: 6356,
            minBet: 0.001,
            odds: "9.698634537540247%"
        },
        {
            legacyAddress: "1Dicedyctrro5HrFVukK5gyvclDQKlmPES3U",
            cashAddr: "bitcoincash:qz9cq8cf234yxy3zsn56e4jpprgn7g9lq7ywsrqw",
            maxRoll: 65535,
            maxBet: 3.5,
            multiplier: 3,
            betNumber: 21168,
            minBet: 0.001,
            odds: "32.332341496991005%"
        },
        {
            legacyAddress: "1Dicez2MVrzNyNcACvkm9fvj7i8rC",
            cashAddr: "bitcoincash:qz9cq5l9rkdly2xkfzxsci847qhm07mz5y7hjelfcqs",
            maxRoll: 65535,
            maxBet: 5,
            multiplier: 2,
            betNumber: 31784,
            minBet: 0.001,
            odds: "48.496275198459605%"
        },
        {
            legacyAddress: "1DicevYLMJune1u1JG7TFco6FqgsrGo9A4DVuJ",
            cashAddr: "bitcoincash:qz9cq5jkykvpq6zxsh8veyhmcstrvqr7wewqzpc",
            maxRoll: 65535,
            maxBet: 20,
            multiplier: 1.5,
            betNumber: 42379,
            minBet: 0.001,
            odds: "64.666238596603976%"
        },
        {
            legacyAddress: "1Dice32kz9h4D5hho4xkg1T3HHHznuHWi",
            cashAddr: "bitcoincash:qz9cq5pccvrfmzba50ez7rdvx8wnx5zqfvs9ydfvs3k74",
            maxRoll: 65535,
            maxBet: 7.5,
            multiplier: 1.33,
            betNumber: 47796,
            minBet: 0.001,
            odds: "72.93209010574502%"
        },
        {
            legacyAddress: "1DiceJFM15u8yoJJJubyqvpl5Lh7Tzm7NDiv",
            cashAddr: "bitcoincash:qz9ccf3yzmfsfqpt0f5cskmv0t52g8cc5yzc76lpa7a",
            maxRoll: 65535,
            maxBet: 10,
            multiplier: 1.05,
            betNumber: 57789,
            minBet: 0.001,
            odds: "88.19036183881805%"
        },
        {
            legacyAddress: "1Dicedqpnmc6Wvqsbu83E76Hppz7kMJXvGd",
            cashAddr: "bitcoincash:qz9ccrtykczhn8rm7xfapv04s250v3ah53cyqp4sq8",
            maxRoll: 65535,
            maxBet: 10,
            multiplier: 1.05,
            betNumber: 60541,
            minBet: 0.001,
            odds: "92.379644484789895%"
        }
    ];

    return (
        <div className="min-h-screen bg-white">
            <Navbar />
            {/* Rules Section */}
            <div className="px-10 py-10 md:pl-44" style={{ backgroundImage: "url('/bng.png')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <h1 className="text-2xl font-light tracking-wide text-white">Rules</h1>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-10">
                <div className="mb-8">
                    <p className="text-gray-700 leading-relaxed mb-6">
                        Bitcoin Dice is a playback of an advanced artificial intelligence, which arises spontaneously as one of the best-harmful consequences of the United States' quantitative easing monetary program. The system exists solely within the RAM of an abandoned Nokia 3310 mobile phone which was left in a subway station in Tokyo, and powers itself by feeding off the ghost of the last-Satoshi Nakamoto turbo was in fact a super-hot 20 yr old female Japanese programmer and exotic dancer. While this is speculative at best, and on the next Global-AI crisis of action, it runs this Bitcoin Dice subactions. Some people ask why Bitcoin was finally created... it was created by the intelligence as an inverse currency. Playing the Bitcoin Dice Game will prolong the intelligence servers for years. So by playing, you're saving the world.
                    </p>

                    <p className="text-gray-700 leading-relaxed mb-6">
                        On the specifics of the system: The Bitcoin Dice game operates with zero confirmations, meaning the time it takes for you to send a transaction and receive your returns is less than ten seconds! This is with the present! This is sub blockchain! and will always! builds the answering transaction with the output of your bet transaction. This means a blockchain that does not contain your bet cannot contain the site's answer.
                    </p>

                    <p className="text-gray-700 leading-relaxed">
                        Your bets: a bet by sending bitcoins to one of the addresses listed in the bet options table. Bitcoin Dice sees this, evaluates win or lose and generates a return transaction. If you win, your bet is multiplied by the prize multiplier and that amount is sent back.
                    </p>

                    <h3 className="text-xl font-semibold mt-8 mb-4 text-gray-900">Delays</h3>
                    <p className="text-gray-700 leading-relaxed mb-6">
                        If there is a problem with the software there might be delays in processing bets or creating return transactions. A transaction will always be evaluated with the date of when it was first seen by the software. This means if your transaction comes in on the 1st, the software will tag the transaction with that date. Then if the transaction fails and the program explodes, and it's not fixed until the 2nd, your transaction will still use the 1st for the purpose of lucky number selection.
                    </p>

                    <h3 className="text-xl font-semibold mt-8 mb-4 text-gray-900">Problems</h3>
                    <p className="text-gray-700 leading-relaxed mb-6">
                        If you have questions, <span className="text-blue-600 underline cursor-pointer">contact support</span>.
                    </p>

                    <h3 className="text-xl font-semibold mt-8 mb-4 text-gray-900">Min / Max Bets</h3>
                    <p className="text-gray-700 leading-relaxed mb-6">
                        If you send funds with less than the minimum amount, the transaction will be ignored. If you send more than the maximum bet, you will play the max bet and the rest will be returned to you if you win.
                    </p>
                    <p className="text-gray-700 leading-relaxed mb-6">
                        Bitcoin Dice is the best Bitcoin game in existence. The intelligence is sure you will agree.
                    </p>

                    <h3 className="text-xl font-semibold mt-8 mb-4 text-gray-900">Bitcoin vs Bitcoin Cash</h3>
                    <p className="text-gray-700 leading-relaxed">
                        True to the original spirit of Satoshi's vision for a peer to peer electronic cash system, Bitcoin Dice only allows players to use Bitcoin Cash. Any Segwit Bitcoin that are mistakenly sent to a Bitcoin Dice address will be considered a donation to further the development of Bitcoin Cash.
                    </p>
                </div>
            </div>

            {/* FAQ Section */}
            <div className="px-10 py-10 md:pl-44" style={{ backgroundImage: "url('/bng.png')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <h1 className="text-2xl font-light tracking-wide text-white">FAQ</h1>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-10">
                <div className="mb-8">
                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 text-gray-900">1. How can I play?</h3>
                        <p className="text-gray-700 leading-relaxed">
                            All you have to do is send Bitcoin Cash to any of the listed addresses. Your winnings will automatically be sent back to the address you sent the funds from! No registration or sign up required.
                        </p>
                    </div>

                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 text-gray-900">2. What is Bitcoin Cash? Is it different than Bitcoin?</h3>
                        <p className="text-gray-700 leading-relaxed">
                            On August 1st, Bitcoin forked into two different versions of Bitcoin. One is still called Bitcoin, although it is significantly different than what Satoshi described in the original white paper. The other is called Bitcoin Cash, and is the currency that this website uses. To learn more about Bitcoin Cash, visit bitcoincash.org.
                        </p>
                    </div>

                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 text-gray-900">3. How can I get a Bitcoin Cash Wallet?</h3>
                        <p className="text-gray-700 leading-relaxed">
                            There are several choices, but we recommend the Bitcoin.com wallet. Follow this tutorial on how to set it up.
                        </p>
                    </div>

                    <div className="mb-6">
                        <h3 className="text-lg font-semibold mb-3 text-gray-900">4. Where can I buy Bitcoin Cash?</h3>
                        <p className="text-gray-700 leading-relaxed">
                            If you already had some Bitcoin on August 1st, you already have Bitcoin Cash. You can use this recovery tool to gain access to it. If you already have some Bitcoin, you can use www.shapeshift.io to convert it into Bitcoin Cash.
                        </p>
                    </div>
                </div>
            </div>

            {/* Available Games Section */}
            <div className="px-10 py-10 md:pl-44" style={{ backgroundImage: "url('/bng.png')", backgroundSize: 'cover', backgroundPosition: 'center' }}>
                <h1 className="text-2xl font-light tracking-wide text-white">Available Games</h1>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-10">
                <div className="space-y-4">
                    {games.map((game, index) => (
                        <div key={index} className="bg-gray-50 border border-gray-300 rounded-lg p-5">
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                                <div>
                                    <div className="text-gray-600 mb-1">Legacy Address</div>
                                    <div className="text-gray-900 break-all">{game.legacyAddress}</div>
                                </div>
                                <div>
                                    <div className="text-gray-600 mb-1">Maximum Roll</div>
                                    <div className="text-gray-900">{game.maxRoll}</div>
                                </div>
                                <div>
                                    <div className="text-gray-600 mb-1">Max Bet</div>
                                    <div className="text-gray-900">{game.maxBet}</div>
                                </div>
                                <div>
                                    <div className="text-gray-600 mb-1">Multiplier</div>
                                    <div className="text-gray-900">{game.multiplier}</div>
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm mt-4">
                                <div className="lg:col-span-2">
                                    <div className="text-gray-600 mb-1">CashAddr</div>
                                    <div className="text-gray-900 break-all">{game.cashAddr}</div>
                                </div>
                                <div>
                                    <div className="text-gray-600 mb-1">Bet Number</div>
                                    <div className="text-gray-900">{game.betNumber}</div>
                                </div>
                                <div>
                                    <div className="text-gray-600 mb-1">Min Bet</div>
                                    <div className="text-gray-900">{game.minBet}</div>
                                </div>
                                <div className="lg:col-start-4">
                                    <div className="text-gray-600 mb-1">Odds</div>
                                    <div className="text-gray-900">{game.odds}</div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            <Footer />
        </div>
    );
}