// Debug sentiment data from API vs Frontend
const API_BASE_URL = 'http://localhost:8000';

async function debugSentimentData() {
  console.log('🔍 Debugging Sentiment Data: API vs Frontend\n');
  
  try {
    // Fetch first page of news
    const response = await fetch(`${API_BASE_URL}/api/news?page=1&limit=5`);
    
    if (response.ok) {
      const data = await response.json();
      const newsItems = data.data;
      
      console.log('📊 Raw API Response Sample:');
      console.log('Meta:', JSON.stringify(data.meta, null, 2));
      console.log('\n📰 News Items Analysis:');
      
      newsItems.forEach((item, index) => {
        console.log(`\n--- News Item ${index + 1} ---`);
        console.log('Title:', item.title.substring(0, 50) + '...');
        console.log('Stock Symbol:', item.stock_symbol);
        console.log('Source:', item.source);
        console.log('Published:', item.published_at);
        
        // Focus on sentiment data
        console.log('\n🎯 SENTIMENT DATA:');
        console.log('  sentiment (string):', `"${item.sentiment}"`);
        console.log('  impact_score (number):', item.impact_score);
        console.log('  Data types:');
        console.log('    - sentiment type:', typeof item.sentiment);
        console.log('    - impact_score type:', typeof item.impact_score);
        
        // Check for other sentiment-related fields
        const otherFields = Object.keys(item).filter(key => 
          key.toLowerCase().includes('sentiment') || 
          key.toLowerCase().includes('score')
        );
        
        if (otherFields.length > 0) {
          console.log('  Other sentiment fields found:');
          otherFields.forEach(field => {
            console.log(`    - ${field}:`, item[field]);
          });
        }
        
        // Simulate frontend transformation
        console.log('\n🔄 Frontend Transformation:');
        
        let finalSentiment;
        if (typeof item.impact_score === 'number') {
          finalSentiment = item.impact_score;
          console.log(`  ✅ Using impact_score: ${finalSentiment}`);
        } else if (item.sentiment) {
          // Map sentiment string to number (current frontend logic)
          const mapSentimentToNumber = (sentiment) => {
            switch (sentiment.toLowerCase()) {
              case 'positive': return 80;
              case 'negative': return 30;
              case 'neutral': 
              default: return 60;
            }
          };
          finalSentiment = mapSentimentToNumber(item.sentiment);
          console.log(`  📝 Mapped '${item.sentiment}' to: ${finalSentiment}`);
        } else {
          finalSentiment = 60;
          console.log(`  ⚠️ Using default: ${finalSentiment}`);
        }
        
        // Determine label based on -1 to 1 scale logic
        let sentimentLabel;
        if (finalSentiment > 0) {
          sentimentLabel = "Positive";
        } else if (finalSentiment === 0) {
          sentimentLabel = "Neutral";
        } else {
          sentimentLabel = "Negative";
        }
        
        console.log(`  🏷️  Final Label: ${sentimentLabel}`);
        console.log(`  📊 Final Score: ${finalSentiment}`);
        
        // Check if this matches expected behavior
        const isExpected = (item.impact_score === 0 && sentimentLabel === "Neutral");
        console.log(`  ${isExpected ? '✅' : '❌'} Expected behavior: ${isExpected ? 'YES' : 'NO'}`);
      });
      
      // Summary analysis
      console.log('\n' + '='.repeat(60));
      console.log('📋 SUMMARY ANALYSIS:');
      
      const allNeutral = newsItems.every(item => item.sentiment.toLowerCase() === 'neutral');
      const allZeroScore = newsItems.every(item => item.impact_score === 0);
      
      console.log(`📊 All items have sentiment="neutral": ${allNeutral ? 'YES ⚠️' : 'NO ✅'}`);
      console.log(`📊 All items have impact_score=0: ${allZeroScore ? 'YES ⚠️' : 'NO ✅'}`);
      
      if (allNeutral && allZeroScore) {
        console.log('\n🚨 ISSUE IDENTIFIED:');
        console.log('  - API is returning all items with sentiment="neutral" and impact_score=0');
        console.log('  - This suggests the backend sentiment analysis is not working');
        console.log('  - Or the database contains only neutral sentiment data');
        console.log('\n🔧 RECOMMENDED CHECKS:');
        console.log('  1. Check backend sentiment analysis pipeline');
        console.log('  2. Verify database has diverse sentiment scores');
        console.log('  3. Check if sentiment calculation is running correctly');
        console.log('  4. Verify data ingestion process includes sentiment analysis');
      } else {
        console.log('\n✅ SENTIMENT DATA LOOKS GOOD');
      }
      
    } else {
      console.log(`❌ API request failed: ${response.status} ${response.statusText}`);
    }
    
  } catch (error) {
    console.log(`❌ Error: ${error.message}`);
  }
}

debugSentimentData();