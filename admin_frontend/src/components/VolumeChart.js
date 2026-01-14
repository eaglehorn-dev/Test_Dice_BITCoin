import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { formatSats } from '../utils/format';

function VolumeChart({ data }) {
  const chartData = data.map(item => ({
    name: `${item.multiplier}x`,
    bets: item.bet_count,
    wagered: item.total_wagered,
    paidOut: item.total_paid_out,
    profit: item.profit
  }));

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">📊 Volume by Multiplier</h2>
      
      {/* Summary Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {data.map((item) => (
          <div key={item.multiplier} className="border-2 border-gray-200 rounded-lg p-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{item.multiplier}x</p>
              <p className="text-sm text-gray-600 mt-1">{item.bet_count} bets</p>
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="text-xs text-gray-600">Wagered</div>
                <div className="font-semibold">{formatSats(item.total_wagered)} sats</div>
              </div>
              <div className="mt-2">
                <div className="text-xs text-gray-600">Profit</div>
                <div className={`font-bold ${item.profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {item.profit >= 0 ? '+' : ''}{formatSats(item.profit)} sats
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bar Chart */}
      <div className="mt-6">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip 
              formatter={(value) => formatSats(value) + ' sats'}
              labelStyle={{ color: '#000' }}
            />
            <Legend />
            <Bar dataKey="wagered" fill="#3b82f6" name="Wagered" />
            <Bar dataKey="paidOut" fill="#ef4444" name="Paid Out" />
            <Bar dataKey="profit" fill="#10b981" name="Profit" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default VolumeChart;
