import type { AssetPosition } from '../types/trading';

// API configuration - support environment variable for port
const API_PORT = import.meta.env.VITE_API_PORT || '39583';
const API_BASE_URL = `http://localhost:${API_PORT}/api`;

// Service to dynamically load asset data from the backend API
export const loadAssetFiles = async (): Promise<Record<string, AssetPosition>> => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const assetFiles: Record<string, AssetPosition> = await response.json();
    console.log('Loaded assets from API:', Object.keys(assetFiles));
    
    return assetFiles;
    
  } catch (error) {
    console.error('Error loading asset files from API:', error);
    
    // Fallback to empty data if API is not available
    console.warn(`Falling back to empty asset data. Make sure the API server is running on port ${API_PORT}.`);
    return {};
  }
};

// Function to get available asset symbols dynamically from API
export const getAssetSymbols = async (): Promise<string[]> => {
  try {
    const assets = await loadAssetFiles();
    return Object.keys(assets);
  } catch (error) {
    console.error('Error getting asset symbols:', error);
    return [];
  }
};

// Function to read a specific asset file from API
export const readAssetFile = async (symbol: string): Promise<AssetPosition | null> => {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/${symbol.toUpperCase()}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        console.warn(`Asset ${symbol} not found`);
        return null;
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const assetData = await response.json();
    return assetData[symbol.toUpperCase()] || null;
    
  } catch (error) {
    console.error(`Error reading asset file for ${symbol}:`, error);
    return null;
  }
};

// Function to refresh asset data (useful for manual refresh)
export const refreshAssetData = async (): Promise<Record<string, AssetPosition>> => {
  console.log('Refreshing asset data from files...');
  return loadAssetFiles();
};