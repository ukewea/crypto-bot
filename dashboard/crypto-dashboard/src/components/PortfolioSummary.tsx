import React from 'react';
import { TrendingUp, TrendingDown, DollarSign, PieChart, Target, Zap } from 'lucide-react';
import type { EnhancedPortfolioSummary } from '../hooks/usePortfolioWithPrices';
import { formatCurrency, formatPercentage } from '../utils/dataParser';

interface PortfolioSummaryProps {
  summary: EnhancedPortfolioSummary;
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({ summary }) => {
  const isProfitable = summary.totalPnL >= 0;
  const isUnrealizedProfitable = summary.totalUnrealizedPnL >= 0;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
        <PieChart className="mr-3 text-blue-600" />
        Portfolio Summary
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Current Portfolio Value */}
        <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm">Current Value</p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalCurrentValue)}</p>
            </div>
            <DollarSign size={24} className="text-blue-200" />
          </div>
        </div>

        {/* Total Cost Basis */}
        <div className="bg-gradient-to-r from-purple-500 to-purple-600 text-white p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm">Total Cost</p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalCost)}</p>
            </div>
            <Target size={24} className="text-purple-200" />
          </div>
        </div>

        {/* Realized P&L */}
        <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-4 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100 text-sm">Realized P&L</p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalRealizedPnL)}</p>
            </div>
            <Target size={24} className="text-green-200" />
          </div>
        </div>

        {/* Unrealized P&L */}
        <div className={`bg-gradient-to-r ${isUnrealizedProfitable 
          ? 'from-cyan-500 to-cyan-600' 
          : 'from-amber-500 to-amber-600'} text-white p-4 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${isUnrealizedProfitable ? 'text-cyan-100' : 'text-amber-100'} text-sm`}>
                Unrealized P&L
              </p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalUnrealizedPnL)}</p>
            </div>
            <Zap size={24} className={isUnrealizedProfitable ? 'text-cyan-200' : 'text-amber-200'} />
          </div>
        </div>

        {/* Total P&L */}
        <div className={`bg-gradient-to-r ${isProfitable 
          ? 'from-emerald-500 to-emerald-600' 
          : 'from-red-500 to-red-600'} text-white p-4 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${isProfitable ? 'text-emerald-100' : 'text-red-100'} text-sm`}>
                Total P&L
              </p>
              <p className="text-2xl font-bold">{formatCurrency(summary.totalPnL)}</p>
            </div>
            {isProfitable ? (
              <TrendingUp size={24} className="text-emerald-200" />
            ) : (
              <TrendingDown size={24} className="text-red-200" />
            )}
          </div>
        </div>

        {/* P&L Percentage */}
        <div className={`bg-gradient-to-r ${isProfitable 
          ? 'from-teal-500 to-teal-600' 
          : 'from-orange-500 to-orange-600'} text-white p-4 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${isProfitable ? 'text-teal-100' : 'text-orange-100'} text-sm`}>
                Total Return
              </p>
              <p className="text-2xl font-bold">{formatPercentage(summary.totalPnLPercent)}</p>
            </div>
            {isProfitable ? (
              <TrendingUp size={24} className="text-teal-200" />
            ) : (
              <TrendingDown size={24} className="text-orange-200" />
            )}
          </div>
        </div>
      </div>

      <div className="mt-6 text-center">
        <p className="text-gray-600 text-sm">
          Portfolio tracking {summary.assets.length} assets
        </p>
      </div>
    </div>
  );
};

export default PortfolioSummary;