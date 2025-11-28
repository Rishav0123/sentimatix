// Quick API Test Script
// Open your browser's developer console and run this to test your API

const testStockAPI = async () => {
  console.log('🔍 Testing Stock API Connection...');
  
  const API_URL = 'http://localhost:8000/api/stocks';
  
  try {
    console.log(`📡 Fetching from: ${API_URL}`);
    
    const response = await fetch(API_URL, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    console.log(`📊 Response Status: ${response.status}`);
    console.log(`📊 Response OK: ${response.ok}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    console.log('✅ API Response received!');
    console.log('📈 Data:', data);
    console.log(`📊 Number of stocks: ${data.length}`);
    
    if (data.length > 0) {
      console.log('🎯 First stock sample:', data[0]);
    }
    
    return data;
    
  } catch (error) {
    console.error('❌ API Test Failed:', error);
    console.log('🔧 Common Issues:');
    console.log('1. FastAPI server not running on localhost:8000');
    console.log('2. CORS policy blocking the request');
    console.log('3. /api/stocks endpoint returns empty array');
    console.log('4. Network connectivity issues');
    
    // Test if server is reachable at all
    try {
      const healthCheck = await fetch('http://localhost:8000/');
      console.log('✅ Server is reachable at root endpoint');
    } catch (healthError) {
      console.log('❌ Server not reachable at localhost:8000');
    }
    
    return null;
  }
};

// Run the test
testStockAPI();