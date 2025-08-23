import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import type { EnhancedAssetData } from '../hooks/usePortfolioWithPrices';
import { calculateAssetMetrics, formatCurrency } from '../utils/dataParser';

interface PortfolioChartProps {
  assets: EnhancedAssetData[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658'];

const PortfolioChart: React.FC<PortfolioChartProps> = ({ assets }) => {
  // Prepare data for pie chart (current value allocation)
  const pieData = assets.map((asset, index) => {
    return {
      name: asset.symbol,
      value: asset.currentValue || calculateAssetMetrics(asset).openCost,
      color: COLORS[index % COLORS.length]
    };
  });

  // Prepare data for bar chart (enhanced P&L by asset)
  const barData = assets.map((asset) => {
    const metrics = calculateAssetMetrics(asset);
    return {
      name: asset.symbol,
      cost: metrics.openCost,
      currentValue: asset.currentValue || metrics.openCost,
      realized: metrics.realizedGain,
      unrealized: asset.unrealizedPnL || 0,
      total: asset.totalPnL || metrics.realizedGain
    };
  });

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{`${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {`${entry.dataKey}: ${formatCurrency(entry.value)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const PieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold">{data.name}</p>
          <p style={{ color: data.payload.color }}>
            Value: {formatCurrency(data.value)}
          </p>
          <p className="text-sm text-gray-600">
            {((data.value / pieData.reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1)}%
          </p>
        </div>
      );
    }
    return null;
  };

  if (assets.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Portfolio Visualization</h3>
        <p className="text-gray-500 text-center py-8">No data available for charts</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Portfolio Allocation Pie Chart */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Portfolio Allocation (Current Value)</h3>
        <div style={{ width: '100%', height: 400 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(1)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<PieTooltip />} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Enhanced Asset Performance Bar Chart */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Asset Performance (Cost vs Current Value & P&L)</h3>
        <div style={{ width: '100%', height: 400 }}>
          <ResponsiveContainer>
            <BarChart data={barData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={(value) => formatCurrency(value)} />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="cost" fill="#8884d8" name="Total Cost" />
              <Bar dataKey="currentValue" fill="#0088fe" name="Current Value" />
              <Bar dataKey="realized" fill="#00c49f" name="Realized P&L" />
              <Bar dataKey="unrealized" fill="#ffbb28" name="Unrealized P&L" />
              <Bar dataKey="total" fill="#ff8042" name="Total P&L" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default PortfolioChart;