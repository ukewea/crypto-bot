const express = require('express');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');
const cors = require('cors');

const app = express();
const PORT = process.env.PORT || 39583;

// Enable CORS for the React app (support both common Vite ports)
app.use(cors({
  origin: ['http://localhost:5173', 'http://localhost:5174']
}));

// Path to the asset-positions folder (relative to the crypto-bot root)
const ASSET_POSITIONS_PATH = path.join(__dirname, '../../../asset-positions');


// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'ok', 
    timestamp: new Date().toISOString(),
    assetPositionsPath: ASSET_POSITIONS_PATH
  });
});

// File watching functionality
let assetCache = {};
let lastModified = {};

const loadAssetCache = async () => {
  try {
    const files = await fs.readdir(ASSET_POSITIONS_PATH);
    const newCache = {};
    const newModified = {};

    for (const file of files) {
      if (file.endsWith('.json')) {
        const symbol = path.basename(file, '.json');
        const filePath = path.join(ASSET_POSITIONS_PATH, file);
        
        try {
          const stats = await fs.stat(filePath);
          const fileContent = await fs.readFile(filePath, 'utf8');
          const assetData = JSON.parse(fileContent);
          
          if (assetData.transactions && assetData.transactions.length > 0) {
            newCache[symbol] = assetData;
            newModified[symbol] = stats.mtime.getTime();
          }
        } catch (fileError) {
          console.error(`Error loading ${file} into cache:`, fileError.message);
        }
      }
    }

    assetCache = newCache;
    lastModified = newModified;
    console.log(`Asset cache updated with ${Object.keys(assetCache).length} assets`);
    
  } catch (error) {
    console.error('Error loading asset cache:', error);
  }
};

// Watch for file changes
const setupFileWatcher = () => {
  if (fsSync.existsSync(ASSET_POSITIONS_PATH)) {
    fsSync.watch(ASSET_POSITIONS_PATH, { persistent: true }, async (eventType, filename) => {
      if (filename && filename.endsWith('.json')) {
        console.log(`File change detected: ${filename} (${eventType})`);
        
        // Debounce file changes (wait 1 second before reloading)
        setTimeout(async () => {
          await loadAssetCache();
        }, 1000);
      }
    });
    console.log('File watcher setup for asset-positions folder');
  } else {
    console.warn('Asset positions folder does not exist:', ASSET_POSITIONS_PATH);
  }
};

// Update API endpoints to use cache
app.get('/api/assets', async (req, res) => {
  try {
    // Use cached data if available, otherwise load fresh
    if (Object.keys(assetCache).length === 0) {
      await loadAssetCache();
    }
    
    console.log(`Serving ${Object.keys(assetCache).length} assets from cache`);
    res.json(assetCache);

  } catch (error) {
    console.error('Error serving assets:', error);
    res.status(500).json({ 
      error: 'Failed to load asset positions',
      message: error.message 
    });
  }
});

// Update specific asset endpoint
app.get('/api/assets/:symbol', async (req, res) => {
  try {
    const symbol = req.params.symbol.toUpperCase();
    
    // Check cache first
    if (assetCache[symbol]) {
      res.json({ [symbol]: assetCache[symbol] });
      return;
    }

    // If not in cache, try loading directly
    const filePath = path.join(ASSET_POSITIONS_PATH, `${symbol}.json`);
    const fileContent = await fs.readFile(filePath, 'utf8');
    const assetData = JSON.parse(fileContent);
    
    res.json({ [symbol]: assetData });
    
  } catch (error) {
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: `Asset ${req.params.symbol} not found` });
    } else {
      console.error(`Error loading asset ${req.params.symbol}:`, error);
      res.status(500).json({ 
        error: 'Failed to load asset position',
        message: error.message 
      });
    }
  }
});

// Add cache status endpoint
app.get('/api/cache-status', (req, res) => {
  res.json({
    cachedAssets: Object.keys(assetCache),
    lastModified: lastModified,
    cacheSize: Object.keys(assetCache).length,
    timestamp: new Date().toISOString()
  });
});

// Start the server
app.listen(PORT, async () => {
  console.log(`Asset positions API server running on http://localhost:${PORT}`);
  console.log(`Reading asset positions from: ${ASSET_POSITIONS_PATH}`);
  console.log(`CORS enabled for: http://localhost:5173, http://localhost:5174`);
  
  // Initialize cache and file watcher
  await loadAssetCache();
  setupFileWatcher();
});