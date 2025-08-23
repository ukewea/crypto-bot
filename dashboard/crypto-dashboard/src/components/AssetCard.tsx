import React from 'react';
import { TrendingUp, TrendingDown, Activity, Calendar, DollarSign, Zap } from 'lucide-react';
import type { EnhancedAssetData } from '../hooks/usePortfolioWithPrices';
import { calculateAssetMetrics, formatCurrency, formatPercentage } from '../utils/dataParser';
import { formatPrice } from '../services/priceService';

interface AssetCardProps {
  asset: EnhancedAssetData;
  onClick: () => void;
}

const AssetCard: React.FC<AssetCardProps> = ({ asset, onClick }) => {
  const metrics = calculateAssetMetrics(asset);
  const isUnrealizedProfitable = (asset.unrealizedPnL || 0) >= 0;
  const isTotalProfitable = (asset.totalPnL || 0) >= 0;
  const hasCurrentPrice = asset.currentPrice !== undefined;

  return (
    <div 
      className="bg-white rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition-shadow duration-300 border border-gray-200 hover:border-blue-300"
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-xl font-bold text-gray-800">{asset.symbol}</h3>
          {hasCurrentPrice && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">LIVE</span>
          )}
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          isTotalProfitable ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {formatPercentage(asset.totalPnLPercent || 0)}
        </div>
      </div>

      <div className="space-y-3">
        {/* Holdings and Current Price */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600 text-sm">Holdings</span>
          <span className="font-semibold text-gray-800">
            {metrics.openQuantity.toFixed(8)} {asset.symbol}
          </span>
        </div>

        {hasCurrentPrice && (
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">Current Price</span>
            <span className="font-semibold text-blue-600 flex items-center">
              <DollarSign size={14} className="mr-1" />
              {formatPrice(asset.currentPrice!)}
            </span>
          </div>
        )}

        {/* Current Value vs Cost */}
        <div className="flex justify-between items-center">
          <span className="text-gray-600 text-sm">Current Value</span>
          <span className="font-semibold text-gray-800">
            {formatCurrency(asset.currentValue || metrics.openCost)}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-600 text-sm">Total Cost</span>
          <span className="font-semibold text-gray-600">
            {formatCurrency(metrics.openCost)}
          </span>
        </div>

        {/* Unrealized P&L */}
        {hasCurrentPrice && (
          <div className={`flex justify-between items-center p-3 rounded-lg ${
            isUnrealizedProfitable ? 'bg-blue-50' : 'bg-orange-50'
          }`}>
            <span className="text-gray-600 text-sm flex items-center">
              <Zap size={16} className={`mr-1 ${isUnrealizedProfitable ? 'text-blue-600' : 'text-orange-600'}`} />
              Unrealized P&L
            </span>
            <span className={`font-bold ${
              isUnrealizedProfitable ? 'text-blue-600' : 'text-orange-600'
            }`}>
              {formatCurrency(asset.unrealizedPnL || 0)}
            </span>
          </div>
        )}

        {/* Total P&L */}
        <div className={`flex justify-between items-center p-3 rounded-lg ${
          isTotalProfitable ? 'bg-green-50' : 'bg-red-50'
        }`}>
          <span className="text-gray-600 text-sm flex items-center">
            {isTotalProfitable ? (
              <TrendingUp size={16} className="mr-1 text-green-600" />
            ) : (
              <TrendingDown size={16} className="mr-1 text-red-600" />
            )}
            Total P&L
          </span>
          <span className={`font-bold ${
            isTotalProfitable ? 'text-green-600' : 'text-red-600'
          }`}>
            {formatCurrency(asset.totalPnL || metrics.realizedGain)}
          </span>
        </div>

        <div className="border-t pt-3 mt-4">
          <div className="flex justify-between items-center text-sm text-gray-500">
            <span className="flex items-center">
              <Activity size={14} className="mr-1" />
              {metrics.totalTransactions} transactions
            </span>
            <span className="flex items-center">
              <Calendar size={14} className="mr-1" />
              {metrics.lastTransactionDate}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AssetCard;