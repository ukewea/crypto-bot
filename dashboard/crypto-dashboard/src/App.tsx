import { useState } from 'react';
import { RefreshCw, AlertCircle, Server, DollarSign } from 'lucide-react';
import { useAssetData } from './hooks/useAssetData';
import { usePortfolioWithPrices } from './hooks/usePortfolioWithPrices';
import PortfolioSummary from './components/PortfolioSummary';
import AssetCard from './components/AssetCard';
import AssetDetailModal from './components/AssetDetailModal';
import PortfolioChart from './components/PortfolioChart';
import type { AssetData } from './types/trading';

function App() {
  const { assets, loading, error, refresh } = useAssetData();
  const { enhancedAssets, portfolioSummary, pricesLoading, pricesError, refreshPrices } = usePortfolioWithPrices(assets);
  const [selectedAsset, setSelectedAsset] = useState<AssetData | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleAssetClick = (asset: AssetData) => {
    setSelectedAsset(asset);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setSelectedAsset(null);
    setIsModalOpen(false);
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refresh();
      await refreshPrices();
    } catch (err) {
      console.error('Error refreshing data:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="animate-spin mx-auto mb-4 text-blue-600" size={48} />
          <p className="text-gray-600 text-lg">Loading portfolio data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center bg-white rounded-lg shadow-lg p-8 max-w-md">
          <AlertCircle className="mx-auto mb-4 text-red-500" size={48} />
          <h2 className="text-xl font-bold text-gray-800 mb-2">Error Loading Data</h2>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <div className="flex items-center justify-center gap-4 mb-4">
            <h1 className="text-4xl font-bold text-gray-800">
              Crypto Trading Dashboard
            </h1>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing || loading || pricesLoading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw size={16} className={isRefreshing || pricesLoading ? 'animate-spin' : ''} />
              {pricesLoading ? 'Loading Prices...' : 'Refresh'}
            </button>
          </div>
          <p className="text-gray-600">
            Monitor your cryptocurrency positions and trading performance
          </p>
          <div className="flex items-center justify-center gap-4 mt-2 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <Server size={14} />
              <span>API: localhost:{import.meta.env.VITE_API_PORT || '39583'}</span>
            </div>
            <div className="flex items-center gap-2">
              <DollarSign size={14} />
              <span>Live prices from Binance API</span>
              {portfolioSummary.lastPriceUpdate && (
                <span className="text-xs text-gray-400">
                  (updated {portfolioSummary.lastPriceUpdate.toLocaleTimeString()})
                </span>
              )}
            </div>
          </div>
          {pricesError && (
            <div className="mt-2 text-xs text-orange-600">
              ⚠️ Price data unavailable: {pricesError}
            </div>
          )}
        </header>

        {/* Portfolio Summary */}
        <PortfolioSummary summary={portfolioSummary} />

        {/* Portfolio Charts */}
        {enhancedAssets.length > 0 && (
          <div className="mb-8">
            <PortfolioChart assets={enhancedAssets} />
          </div>
        )}

        {/* Asset Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Your Assets</h2>
          {enhancedAssets.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No assets found</p>
              <p className="text-gray-400 text-sm mt-2">
                Make sure you have position data in the asset-positions folder
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {enhancedAssets.map((asset) => (
                <AssetCard
                  key={asset.symbol}
                  asset={asset}
                  onClick={() => handleAssetClick(asset)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="text-center py-8 text-gray-500 text-sm">
          <p>Crypto Trading Bot Dashboard • Built with React & TypeScript</p>
          <p className="mt-1">
            Last updated: {new Date().toLocaleString()}
          </p>
        </footer>
      </div>

      {/* Asset Detail Modal */}
      <AssetDetailModal
        asset={selectedAsset}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  );
}

export default App;
