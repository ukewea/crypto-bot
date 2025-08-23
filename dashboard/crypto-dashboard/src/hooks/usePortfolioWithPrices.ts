import { useState, useEffect } from 'react';
import type { AssetData } from '../types/trading';
import { getCurrentPrices, calculateUnrealizedPnL } from '../services/priceService';
import { calculateAssetMetrics } from '../utils/dataParser';

export interface EnhancedAssetData extends AssetData {
  currentPrice?: number;
  currentValue?: number;
  unrealizedPnL?: number;
  unrealizedPnLPercent?: number;
  totalPnL?: number; // realized + unrealized
  totalPnLPercent?: number;
  priceChangePercent?: number;
}

export interface EnhancedPortfolioSummary {
  totalCurrentValue: number;
  totalCost: number;
  totalRealizedPnL: number;
  totalUnrealizedPnL: number;
  totalPnL: number;
  totalPnLPercent: number;
  assets: EnhancedAssetData[];
  lastPriceUpdate?: Date;
}

export const usePortfolioWithPrices = (assets: AssetData[]) => {
  const [enhancedAssets, setEnhancedAssets] = useState<EnhancedAssetData[]>([]);
  const [portfolioSummary, setPortfolioSummary] = useState<EnhancedPortfolioSummary>({
    totalCurrentValue: 0,
    totalCost: 0,
    totalRealizedPnL: 0,
    totalUnrealizedPnL: 0,
    totalPnL: 0,
    totalPnLPercent: 0,
    assets: []
  });
  const [pricesLoading, setPricesLoading] = useState(false);
  const [pricesError, setPricesError] = useState<string | null>(null);

  const loadPricesAndCalculate = async () => {
    if (assets.length === 0) {
      setEnhancedAssets([]);
      setPortfolioSummary({
        totalCurrentValue: 0,
        totalCost: 0,
        totalRealizedPnL: 0,
        totalUnrealizedPnL: 0,
        totalPnL: 0,
        totalPnLPercent: 0,
        assets: []
      });
      return;
    }

    setPricesLoading(true);
    setPricesError(null);

    try {
      // Extract symbols from assets
      const symbols = assets.map(asset => asset.symbol);
      
      // Fetch current prices
      const currentPrices = await getCurrentPrices(symbols);
      
      // Calculate enhanced metrics for each asset
      const enhanced: EnhancedAssetData[] = assets.map(asset => {
        const metrics = calculateAssetMetrics(asset);
        const currentPrice = currentPrices.get(asset.symbol);
        
        if (currentPrice) {
          const unrealized = calculateUnrealizedPnL(
            asset.symbol,
            metrics.openQuantity,
            metrics.avgBuyPrice,
            currentPrice
          );
          
          const totalPnL = metrics.realizedGain + unrealized.unrealizedPnL;
          const totalPnLPercent = metrics.openCost > 0 ? (totalPnL / metrics.openCost) * 100 : 0;
          
          return {
            ...asset,
            currentPrice,
            currentValue: unrealized.currentValue,
            unrealizedPnL: unrealized.unrealizedPnL,
            unrealizedPnLPercent: unrealized.unrealizedPnLPercent,
            totalPnL,
            totalPnLPercent
          };
        }
        
        // Fallback if price fetch failed
        return {
          ...asset,
          currentPrice: undefined,
          currentValue: metrics.openCost, // Use cost as fallback value
          unrealizedPnL: 0,
          unrealizedPnLPercent: 0,
          totalPnL: metrics.realizedGain,
          totalPnLPercent: metrics.openCost > 0 ? (metrics.realizedGain / metrics.openCost) * 100 : 0
        };
      });

      // Calculate portfolio summary
      const summary: EnhancedPortfolioSummary = {
        totalCurrentValue: enhanced.reduce((sum, asset) => sum + (asset.currentValue || 0), 0),
        totalCost: enhanced.reduce((sum, asset) => {
          const metrics = calculateAssetMetrics(asset);
          return sum + metrics.openCost;
        }, 0),
        totalRealizedPnL: enhanced.reduce((sum, asset) => {
          const metrics = calculateAssetMetrics(asset);
          return sum + metrics.realizedGain;
        }, 0),
        totalUnrealizedPnL: enhanced.reduce((sum, asset) => sum + (asset.unrealizedPnL || 0), 0),
        totalPnL: enhanced.reduce((sum, asset) => sum + (asset.totalPnL || 0), 0),
        totalPnLPercent: 0, // Will calculate after
        assets: enhanced,
        lastPriceUpdate: new Date()
      };

      // Calculate total P&L percentage
      summary.totalPnLPercent = summary.totalCost > 0 ? (summary.totalPnL / summary.totalCost) * 100 : 0;

      setEnhancedAssets(enhanced);
      setPortfolioSummary(summary);

    } catch (error) {
      console.error('Error loading prices:', error);
      setPricesError(error instanceof Error ? error.message : 'Failed to load current prices');
      
      // Fallback to basic calculations without current prices
      const fallbackAssets: EnhancedAssetData[] = assets.map(asset => {
        const metrics = calculateAssetMetrics(asset);
        return {
          ...asset,
          currentValue: metrics.openCost,
          unrealizedPnL: 0,
          unrealizedPnLPercent: 0,
          totalPnL: metrics.realizedGain,
          totalPnLPercent: metrics.openCost > 0 ? (metrics.realizedGain / metrics.openCost) * 100 : 0
        };
      });
      
      setEnhancedAssets(fallbackAssets);
    } finally {
      setPricesLoading(false);
    }
  };

  useEffect(() => {
    loadPricesAndCalculate();
  }, [assets]);

  const refreshPrices = async () => {
    await loadPricesAndCalculate();
  };

  return {
    enhancedAssets,
    portfolioSummary,
    pricesLoading,
    pricesError,
    refreshPrices
  };
};