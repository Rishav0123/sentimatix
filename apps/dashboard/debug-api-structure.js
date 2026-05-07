// Debug API response structure vs frontend expectations
const API_BASE_URL = 'http://localhost:8000';

async function debugApiStructure() {
  console.log('🔍 Debugging API Response Structure vs Frontend Mapping\n');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/news?page=1&limit=1`);
    
    if (response.ok) {
      const data = await response.json();
      const newsItem = data.data[0];
      
      console.log('📊 RAW API RESPONSE:');
      console.log(JSON.stringify(newsItem, null, 2));
      
      console.log('\n🎯 FIELD MAPPING ANALYSIS:');
      
      // Check each field mapping
      const mappings = [
        { frontend: 'id', api: 'id', value: newsItem.id },
        { frontend: 'title', api: 'title', value: newsItem.title },
        { frontend: 'summary', api: 'content', value: newsItem.content },
        { frontend: 'source', api: 'source', value: newsItem.source },
        { frontend: 'time', api: 'published_at', value: newsItem.published_at },
        { frontend: 'ticker', api: 'stock_symbol/yfin_symbol', value: newsItem.stock_symbol || newsItem.yfin_symbol },
        { frontend: 'stockName', api: 'stock_name', value: newsItem.stock_name },
        { frontend: 'sentiment', api: 'impact_score/sentiment_score', value: newsItem.impact_score || newsItem.sentiment_score },
        { frontend: 'category', api: 'tags', value: newsItem.tags }
      ];
      
      mappings.forEach(mapping => {
        console.log(`\n${mapping.frontend}:`);
        console.log(`  🎯 Frontend expects: ${mapping.frontend}`);
        console.log(`  📡 API provides: ${mapping.api}`);
        console.log(`  💾 Actual value: ${JSON.stringify(mapping.value)}`);
        console.log(`  ✅ Status: ${mapping.value !== undefined && mapping.value !== null ? 'FOUND' : '❌ MISSING'}`);
      });
      
      console.log('\n🚨 ISSUES DETECTED:');
      
      // Check for common issues
      if (!newsItem.stock_symbol && !newsItem.yfin_symbol) {
        console.log('❌ Missing stock symbol field (stock_symbol OR yfin_symbol)');
      }
      
      if (!newsItem.impact_score && !newsItem.sentiment_score) {
        console.log('❌ Missing sentiment score field (impact_score OR sentiment_score)');
      }
      
      if (!newsItem.content) {
        console.log('❌ Missing content/summary field');
      }
      
      if (!newsItem.stock_name) {
        console.log('❌ Missing stock_name field');
      }
      
      console.log('\n🔧 REQUIRED FRONTEND FIXES:');
      console.log('1. Update field mappings in NewsFeedPage.tsx');
      console.log('2. Handle missing fields gracefully');
      console.log('3. Fix sentiment score mapping');
      
    } else {
      console.log(`❌ API Error: ${response.status}`);
    }
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

debugApiStructure();