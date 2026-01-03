import { useState } from "react";

export default function App() {
  const [count, setCount] = useState(0);

  return (
    <div style={{ 
      padding: '20px', 
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#0B1120',
      color: '#E5E7EB',
      minHeight: '100vh'
    }}>
      <h1>🚀 Financial Dashboard Test</h1>
      <p>If you can see this, React is working!</p>
      <button 
        onClick={() => setCount(count + 1)}
        style={{
          padding: '10px 20px',
          backgroundColor: '#3B82F6',
          color: 'white',
          border: 'none',
          borderRadius: '6px',
          cursor: 'pointer'
        }}
      >
        Count: {count}
      </button>
      
      <div style={{ marginTop: '20px' }}>
        <h2>API Test</h2>
        <button 
          onClick={async () => {
            try {
              const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '').replace(/\/api$/, '');
              const response = await fetch(`${API_BASE_URL}/api/standouts?limit=2`);
              const data = await response.json();
              console.log('API Response:', data);
              alert('API working! Check console for data.');
            } catch (error) {
              console.error('API Error:', error);
              alert('API Error: ' + error.message);
            }
          }}
          style={{
            padding: '10px 20px',
            backgroundColor: '#10B981',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          Test API Connection
        </button>
      </div>
    </div>
  );
}