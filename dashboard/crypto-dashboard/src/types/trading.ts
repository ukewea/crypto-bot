export interface Transaction {
  time: string;
  activity: 'BUY' | 'SELL';
  symbol: string;
  trade_symbol: string;
  quantity: string;
  price: string;
  commission: string;
  commission_asset: string;
  commission_as_usdt: string;
  round_id: string;
  order_id: string;
  trade_id: string;
  closed_trade_ids: string[];
}

export interface AssetPosition {
  open_quantity: string;
  open_cost: string;
  realized_gain: string;
  total_commission_as_usdt: string;
  transactions: Transaction[];
}

export interface AssetData {
  symbol: string;
  position: AssetPosition;
}

export interface PortfolioSummary {
  totalValue: number;
  totalCost: number;
  totalPnL: number;
  totalPnLPercentage: number;
  assets: AssetData[];
}