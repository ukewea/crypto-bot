import { useState, useEffect } from 'react';
import type { AssetData } from '../types/trading';
import { parseAssetData } from '../utils/dataParser';
import { loadAssetFiles } from '../services/fileService';

export const useAssetData = () => {
  const [assets, setAssets] = useState<AssetData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAssetData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const assetFiles = await loadAssetFiles();
      const assetData: AssetData[] = [];

      // Convert asset files to AssetData format
      Object.entries(assetFiles).forEach(([symbol, position]) => {
        if (position && position.transactions && position.transactions.length > 0) {
          assetData.push(parseAssetData(symbol, position));
        }
      });

      setAssets(assetData);
      console.log(`Loaded ${assetData.length} assets with positions`);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load asset data';
      console.error('Asset data loading error:', errorMessage);
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssetData();
  }, []);

  const refresh = async () => {
    console.log('Refreshing asset data...');
    await loadAssetData();
  };

  return { assets, loading, error, refresh };
};