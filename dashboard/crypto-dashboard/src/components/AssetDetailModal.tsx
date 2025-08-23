import React from 'react';
import { X, BarChart3, TrendingUp } from 'lucide-react';
import type { AssetData } from '../types/trading';
import { calculateAssetMetrics, formatCurrency, formatPercentage } from '../utils/dataParser';
import TransactionHistory from './TransactionHistory';

interface AssetDetailModalProps {
  asset: AssetData | null;
  isOpen: boolean;
  onClose: () => void;
}

const AssetDetailModal: React.FC<AssetDetailModalProps> = ({ asset, isOpen, onClose }) => {
  if (!isOpen || !asset) return null;

  const metrics = calculateAssetMetrics(asset);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <BarChart3 className="mr-3 text-blue-600" />
            {asset.symbol} - Detailed View
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        <div className="p-6">
          {/* Asset Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white p-6 rounded-lg">
              <h3 className="text-sm font-medium text-blue-100 mb-2">Current Holdings</h3>
              <p className="text-2xl font-bold">{metrics.openQuantity.toFixed(8)}</p>
              <p className="text-sm text-blue-100">{asset.symbol}</p>
            </div>

            <div className="bg-gradient-to-r from-green-500 to-green-600 text-white p-6 rounded-lg">
              <h3 className="text-sm font-medium text-green-100 mb-2">Total Investment</h3>
              <p className="text-2xl font-bold">{formatCurrency(metrics.openCost)}</p>
              <p className="text-sm text-green-100">Average: {formatCurrency(metrics.avgBuyPrice)}</p>
            </div>

            <div className={`bg-gradient-to-r ${metrics.realizedGain >= 0 
              ? 'from-emerald-500 to-emerald-600' 
              : 'from-red-500 to-red-600'} text-white p-6 rounded-lg`}>
              <h3 className={`text-sm font-medium mb-2 ${metrics.realizedGain >= 0 
                ? 'text-emerald-100' 
                : 'text-red-100'}`}>
                Realized P&L
              </h3>
              <p className="text-2xl font-bold">{formatCurrency(metrics.realizedGain)}</p>
              <p className={`text-sm ${metrics.realizedGain >= 0 
                ? 'text-emerald-100' 
                : 'text-red-100'}`}>
                {formatPercentage(metrics.realizedGain / metrics.openCost * 100)}
              </p>
            </div>
          </div>

          {/* Trading Activity Summary */}
          <div className="bg-gray-50 rounded-lg p-6 mb-8">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <TrendingUp className="mr-2 text-blue-600" />
              Trading Activity
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{metrics.totalTransactions}</p>
                <p className="text-sm text-gray-600">Total Trades</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{metrics.buyTransactions}</p>
                <p className="text-sm text-gray-600">Buy Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{metrics.sellTransactions}</p>
                <p className="text-sm text-gray-600">Sell Orders</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{formatCurrency(metrics.totalCommission)}</p>
                <p className="text-sm text-gray-600">Total Fees</p>
              </div>
            </div>
            
            <div className="mt-4 text-sm text-gray-600">
              <p><strong>First Trade:</strong> {metrics.firstTransactionDate}</p>
              <p><strong>Last Trade:</strong> {metrics.lastTransactionDate}</p>
            </div>
          </div>

          {/* Transaction History */}
          <TransactionHistory transactions={asset.position.transactions} symbol={asset.symbol} />
        </div>
      </div>
    </div>
  );
};

export default AssetDetailModal;