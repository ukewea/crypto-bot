// Binance API service for fetching current market prices
export interface BinancePrice {
  symbol: string;
  price: string;
}

export interface PriceData {
  symbol: string;
  currentPrice: number;
  lastUpdated: Date;
}

// Binance public API endpoint (no auth required)
const BINANCE_API_URL = 'https://api.binance.com/api/v3';

// Cache to avoid excessive API calls
const priceCache = new Map<string, { price: number; timestamp: number }>();
const CACHE_DURATION = 30000; // 30 seconds

export const getCurrentPrice = async (symbol: string): Promise<number | null> => {
  try {
    const tradingPair = `${symbol.toUpperCase()}USDT`;
    
    // Check cache first
    const cached = priceCache.get(tradingPair);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      return cached.price;
    }

    const response = await fetch(`${BINANCE_API_URL}/ticker/price?symbol=${tradingPair}`);
    
    if (!response.ok) {
      console.warn(`Failed to fetch price for ${tradingPair}:`, response.status);
      return null;
    }

    const data: BinancePrice = await response.json();
    const price = parseFloat(data.price);
    
    // Update cache
    priceCache.set(tradingPair, { price, timestamp: Date.now() });
    
    return price;
  } catch (error) {
    console.error(`Error fetching price for ${symbol}:`, error);
    return null;
  }
};

export const getCurrentPrices = async (symbols: string[]): Promise<Map<string, number>> => {
  try {
    // Create trading pairs for batch request
    const tradingPairs = symbols.map(s => `${s.toUpperCase()}USDT`);
    
    // Check cache for all symbols first
    const prices = new Map<string, number>();
    const uncachedPairs: string[] = [];
    
    tradingPairs.forEach((pair, index) => {
      const cached = priceCache.get(pair);
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        prices.set(symbols[index], cached.price);
      } else {
        uncachedPairs.push(pair);
      }
    });

    // Fetch uncached prices
    if (uncachedPairs.length > 0) {
      const symbolsParam = uncachedPairs.map(pair => `"${pair}"`).join(',');
      const response = await fetch(`${BINANCE_API_URL}/ticker/price?symbols=[${symbolsParam}]`);
      
      if (response.ok) {
        const data: BinancePrice[] = await response.json();
        
        data.forEach(item => {
          const price = parseFloat(item.price);
          const symbol = item.symbol.replace('USDT', '');
          
          prices.set(symbol, price);
          
          // Update cache
          priceCache.set(item.symbol, { price, timestamp: Date.now() });
        });
      } else {
        console.warn('Failed to fetch batch prices from Binance API:', response.status);
        
        // Fallback: fetch individually for uncached symbols
        const fallbackPromises = uncachedPairs.map(async (pair) => {
          const symbol = pair.replace('USDT', '');
          const price = await getCurrentPrice(symbol);
          if (price !== null) {
            prices.set(symbol, price);
          }
        });
        
        await Promise.all(fallbackPromises);
      }
    }

    return prices;
  } catch (error) {
    console.error('Error fetching batch prices:', error);
    return new Map();
  }
};

export const calculateUnrealizedPnL = (
  _symbol: string, 
  holdings: number, 
  avgCost: number, 
  currentPrice: number
): { unrealizedPnL: number; unrealizedPnLPercent: number; currentValue: number } => {
  const currentValue = holdings * currentPrice;
  const totalCost = holdings * avgCost;
  const unrealizedPnL = currentValue - totalCost;
  const unrealizedPnLPercent = totalCost > 0 ? (unrealizedPnL / totalCost) * 100 : 0;

  return {
    unrealizedPnL,
    unrealizedPnLPercent,
    currentValue
  };
};

export const formatPrice = (price: number): string => {
  if (price >= 1) {
    return `$${price.toFixed(2)}`;
  } else if (price >= 0.01) {
    return `$${price.toFixed(4)}`;
  } else {
    return `$${price.toFixed(8)}`;
  }
};

export const clearPriceCache = () => {
  priceCache.clear();
};