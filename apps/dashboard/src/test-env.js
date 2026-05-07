// Quick test to verify environment variables and API setup
console.log('🔧 Environment Test Script');
console.log('===========================');

// Test Vite environment variable access
try {
  console.log('✅ Vite environment variable access test:');
  console.log('VITE_API_URL:', import.meta.env.VITE_API_URL || 'undefined');
  console.log('Base URL will be:', import.meta.env.VITE_API_URL || 'http://localhost:8000');
  // Build trigger: minor log change to force rebuild in Render when pushed
  console.log('Build trigger - re-deploy check');
} catch (error) {
  console.error('❌ Environment variable access failed:', error.message);
}

// Test API endpoint construction
try {
  const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '').replace(/\/api$/, '');
  const stocksEndpoint = `${API_BASE_URL}/api/stocks`;
  const newsEndpoint = `${API_BASE_URL}/api/news`;
  
  console.log('\n📡 API Endpoints:');
  console.log('Stocks:', stocksEndpoint);
  console.log('News:', newsEndpoint);
} catch (error) {
  console.error('❌ API endpoint construction failed:', error.message);
}

console.log('\n🚀 Environment test complete!');