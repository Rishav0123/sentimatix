// Debug script to test your FastAPI news endpoint
// Run this with: node debug-news-api.js

const API_BASE_URL = 'http://localhost:8000';

async function testNewsAPI() {
  console.log('🚀 Testing FastAPI News API Integration...\n');
  
  try {
    console.log(`📡 Making request to: ${API_BASE_URL}/api/news`);
    
    const response = await fetch(`${API_BASE_URL}/api/news`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    console.log(`📊 Response Status: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('✅ API Response received!\n');
    
    // Check if it's an array or paginated response
    const newsArray = Array.isArray(data) ? data : data.data || [];
    
    console.log(`📰 Total news items: ${newsArray.length}`);
    
    if (newsArray.length > 0) {
      console.log('\n📋 Sample news item structure:');
      console.log(JSON.stringify(newsArray[0], null, 2));
      
      console.log('\n🔍 News item fields present:');
      console.log('- ID:', newsArray[0].id ? '✅' : '❌');
      console.log('- Title:', newsArray[0].title ? '✅' : '❌');
      console.log('- Content:', newsArray[0].content ? '✅' : '❌');
      console.log('- Source:', newsArray[0].source ? '✅' : '❌');
      console.log('- Stock Symbol:', newsArray[0].stock_symbol ? '✅' : '❌');
      console.log('- Published At:', newsArray[0].published_at ? '✅' : '❌');
      console.log('- Sentiment:', newsArray[0].sentiment ? '✅' : '❌');
      console.log('- Impact Score:', newsArray[0].impact_score !== undefined ? '✅' : '❌');
      
      console.log('\n📊 Transformed data preview:');
      const sampleNews = newsArray[0];
      
      // Test the new sentiment mapping logic
      const sentiment_score = sampleNews.sentiment_score;
      const sentiment_string = sampleNews.sentiment;
      const impact_score = sampleNews.impact_score;
      
      console.log('Original sentiment data:');
      console.log('- sentiment_score:', sentiment_score);
      console.log('- sentiment (string):', sentiment_string);
      console.log('- impact_score:', impact_score);
      
      // Apply the same logic as frontend
      let finalSentiment;
      if (sentiment_score !== undefined) {
        finalSentiment = sentiment_score;
      } else {
        // Map sentiment string to number
        const mappedSentiment = sentiment_string === 'positive' ? 80 : 
                               sentiment_string === 'negative' ? 30 : 60;
        finalSentiment = mappedSentiment || (impact_score ? impact_score * 100 : 60);
      }
      
      const transformed = {
        id: sampleNews.id || '1',
        title: sampleNews.title,
        summary: sampleNews.content || `News about ${sampleNews.stock_symbol}`,
        source: sampleNews.source,
        time: 'Just transformed',
        ticker: sampleNews.stock_symbol,
        sentiment: finalSentiment,
        category: sentiment_string === 'positive' ? 'Partnership' : 'General'
      };
      
      console.log('\nFinal transformed sentiment:', finalSentiment);
      console.log('Full transformed object:');
      console.log(JSON.stringify(transformed, null, 2));
    } else {
      console.log('⚠️ No news items found in API response');
    }
    
  } catch (error) {
    console.error('❌ Error testing news API:');
    console.error('Error message:', error.message);
    console.log('\n🔧 Troubleshooting steps:');
    console.log('1. Make sure your FastAPI server is running on http://localhost:8000');
    console.log('2. Check that the /api/news endpoint exists and returns data');
    console.log('3. Verify CORS is properly configured in your FastAPI server');
    console.log('4. Test the endpoint directly: curl http://localhost:8000/api/news');
  }
}

// Run the test
testNewsAPI();