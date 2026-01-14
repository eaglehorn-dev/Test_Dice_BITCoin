import React from 'react';
import { formatSats, formatPercent } from '../utils/format';

function StatsCards({ dashboard }) {
  const periods = [
    { key: 'today_stats', title: 'Today', color: 'blue' },
    { key: 'week_stats', title: 'This Week', color: 'green' },
    { key: 'month_stats', title: 'This Month', color: 'purple' },
    { key: 'all_time_stats', title: 'All Time', color: 'gray' }
  ];

  const getColorClasses = (color, isProfit) => {
    const baseColors = {
      blue: 'bg-blue-50 border-blue-200',
      green: 'bg-green-50 border-green-200',
      purple: 'bg-purple-50 border-purple-200',
      gray: 'bg-gray-50 border-gray-200'
    };

    return baseColors[color];
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {periods.map(({ key, title, color }) => {
        const stats = dashboard[key];
        const isProfit = stats.net_profit >= 0;

        return (
          <div
            key={key}
            className={`${getColorClasses(color)} border-2 rounded-lg p-6 shadow`}
          >
            <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
            
            <div className="space-y-3">
              <div>
                <p className="text-xs text-gray-600">Total Bets</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_bets}</p>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <p className="text-xs text-gray-600">Wins</p>
                  <p className="text-lg font-semibold text-green-600">{stats.total_wins}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Losses</p>
                  <p className="text-lg font-semibold text-red-600">{stats.total_losses}</p>
                </div>
              </div>

              <div>
                <p className="text-xs text-gray-600">Income (Bets Received)</p>
                <p className="text-lg font-semibold text-gray-900">{formatSats(stats.total_income)} sats</p>
              </div>

              <div>
                <p className="text-xs text-gray-600">Outcome (Payouts Sent)</p>
                <p className="text-lg font-semibold text-gray-900">{formatSats(stats.total_payout)} sats</p>
              </div>

              <div className="pt-2 border-t-2 border-gray-200">
                <p className="text-xs text-gray-600">Net Profit</p>
                <p className={`text-2xl font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                  {isProfit ? '+' : ''}{formatSats(stats.net_profit)} sats
                </p>
              </div>

              <div>
                <p className="text-xs text-gray-600">Win Rate</p>
                <p className="text-sm font-semibold text-gray-700">{formatPercent(stats.win_rate)}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default StatsCards;
