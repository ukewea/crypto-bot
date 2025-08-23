import type { AssetPosition, AssetData, PortfolioSummary } from '../types/trading';

export const parseAssetData = (symbol: string, data: AssetPosition): AssetData => {
  return {
    symbol,
    position: data
  };
};

export const calculateAssetMetrics = (asset: AssetData) => {
  const { position } = asset;
  const openQuantity = parseFloat(position.open_quantity);
  const openCost = parseFloat(position.open_cost);
  const realizedGain = parseFloat(position.realized_gain);
  const totalCommission = parseFloat(position.total_commission_as_usdt);
  
  // Calculate average buy price
  const avgBuyPrice = openQuantity > 0 ? openCost / openQuantity : 0;
  
  // Calculate total transactions
  const totalTransactions = position.transactions.length;
  const buyTransactions = position.transactions.filter(t => t.activity === 'BUY').length;
  const sellTransactions = position.transactions.filter(t => t.activity === 'SELL').length;
  
  // Get first and last transaction dates
  const sortedTransactions = position.transactions.sort((a, b) => 
    parseInt(a.time) - parseInt(b.time)
  );
  const firstTransactionDate = sortedTransactions.length > 0 
    ? new Date(parseInt(sortedTransactions[0].time)).toLocaleDateString()
    : null;
  const lastTransactionDate = sortedTransactions.length > 0 
    ? new Date(parseInt(sortedTransactions[sortedTransactions.length - 1].time)).toLocaleDateString()
    : null;

  return {
    openQuantity,
    openCost,
    realizedGain,
    totalCommission,
    avgBuyPrice,
    totalTransactions,
    buyTransactions,
    sellTransactions,
    firstTransactionDate,
    lastTransactionDate
  };
};

export const calculatePortfolioSummary = (assets: AssetData[]): PortfolioSummary => {
  const totalCost = assets.reduce((sum, asset) => 
    sum + parseFloat(asset.position.open_cost), 0);
  
  const totalRealizedGain = assets.reduce((sum, asset) => 
    sum + parseFloat(asset.position.realized_gain), 0);

  // Note: For unrealized P&L, we'd need current market prices
  // This would require an API call to get current prices
  const totalValue = totalCost; // Placeholder - would be current market value
  const totalPnL = totalRealizedGain; // Only realized P&L for now
  const totalPnLPercentage = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

  return {
    totalValue,
    totalCost,
    totalPnL,
    totalPnLPercentage,
    assets
  };
};

export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 6
  }).format(amount);
};

export const formatPercentage = (percentage: number): string => {
  return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
};

export const formatDate = (timestamp: string): string => {
  return new Date(parseInt(timestamp)).toLocaleString();
};