import { useState } from "react";
import { Copy, Eye, EyeOff, Key, Code, Book, Zap } from "lucide-react";
import { trackEvent } from "../lib/mixpanel";

export function APIAccess() {
  const [showApiKey, setShowApiKey] = useState(false);
  const stripeKey = process.env.STRIPE_API_KEY;
  const [selectedEndpoint, setSelectedEndpoint] = useState("stocks");

  const endpoints = [
    {
      id: "stocks",
      name: "Stocks Data",
      method: "GET",
      url: "/api/stocks",
      description: "Get real-time stock prices and data"
    },
    {
      id: "news",
      name: "News Feed",
      method: "GET",
      url: "/api/news",
      description: "Access latest market news with sentiment analysis"
    },
    {
      id: "indices",
      name: "Market Indices",
      method: "GET",
      url: "/api/indices",
      description: "Get market index data and performance"
    },
    {
      id: "standouts",
      name: "Market Standouts",
      method: "GET",
      url: "/api/standouts",
      description: "Top performing and declining stocks"
    }
  ];

  const codeExamples = {
    stocks: `// Get stock data
fetch('https://api.stockify.com/api/stocks', {
  headers: {
    'Authorization': 'Bearer ${apiKey}',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));`,

    news: `// Get news with sentiment
fetch('https://api.stockify.com/api/news?limit=10', {
  headers: {
    'Authorization': 'Bearer ${apiKey}',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));`,

    indices: `// Get market indices
fetch('https://api.stockify.com/api/indices', {
  headers: {
    'Authorization': 'Bearer ${apiKey}',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));`,

    standouts: `// Get market standouts
fetch('https://api.stockify.com/api/standouts', {
  headers: {
    'Authorization': 'Bearer ${apiKey}',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));`
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  const copyApiKey = () => {
    copyToClipboard(apiKey);
    trackEvent('api_key_copied');
  };

  const copyCode = () => {
    copyToClipboard(codeExamples[selectedEndpoint as keyof typeof codeExamples]);
    trackEvent('code_snippet_copied', { endpoint: selectedEndpoint });
  };

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-white text-2xl font-bold mb-2">API Access</h1>
        <p className="text-gray-400">Integrate Stockify data into your applications</p>
      </div>

      {/* API Key Section */}
      <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Key className="w-5 h-5 text-blue-400" />
          <h3 className="text-white text-lg font-semibold">API Key</h3>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex-1 bg-[#0F172A] border border-gray-700 rounded-lg p-3">
            <code className="text-green-400 font-mono">
              {showApiKey ? apiKey : "sk_live_" + "•".repeat(32)}
            </code>
          </div>

          <button
            onClick={() => setShowApiKey(!showApiKey)}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            {showApiKey ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
          </button>

          <button
            onClick={copyApiKey}
            className="p-2 text-gray-400 hover:text-white transition-colors"
          >
            <Copy className="w-5 h-5" />
          </button>
        </div>

        <div className="text-sm text-gray-400">
          Keep your API key secure and never share it publicly. Include it in the Authorization header as a Bearer token.
        </div>
      </div>

      {/* Usage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-5 h-5 text-yellow-400" />
            <h4 className="text-white font-semibold">Requests Today</h4>
          </div>
          <div className="text-2xl font-bold text-white">1,247</div>
          <div className="text-sm text-gray-400">of 10,000 limit</div>
        </div>

        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Code className="w-5 h-5 text-green-400" />
            <h4 className="text-white font-semibold">Success Rate</h4>
          </div>
          <div className="text-2xl font-bold text-white">99.8%</div>
          <div className="text-sm text-gray-400">last 30 days</div>
        </div>

        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-2">
            <Book className="w-5 h-5 text-blue-400" />
            <h4 className="text-white font-semibold">Plan</h4>
          </div>
          <div className="text-2xl font-bold text-white">Pro</div>
          <div className="text-sm text-gray-400">10K requests/day</div>
        </div>
      </div>

      {/* API Documentation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Endpoints List */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <h3 className="text-white text-lg font-semibold mb-4">Available Endpoints</h3>

          <div className="space-y-3">
            {endpoints.map((endpoint) => (
              <button
                key={endpoint.id}
                onClick={() => setSelectedEndpoint(endpoint.id)}
                className={`w-full text-left p-4 rounded-lg border transition-all ${selectedEndpoint === endpoint.id
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-gray-700 hover:border-gray-600'
                  }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="bg-green-500/20 text-green-400 px-2 py-1 rounded text-xs font-mono">
                    {endpoint.method}
                  </span>
                  <code className="text-blue-400 font-mono">{endpoint.url}</code>
                </div>
                <div className="text-white font-medium">{endpoint.name}</div>
                <div className="text-gray-400 text-sm">{endpoint.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Code Example */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white text-lg font-semibold">Code Example</h3>
            <button
              onClick={copyCode}
              className="flex items-center gap-2 px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm transition-colors"
            >
              <Copy className="w-4 h-4" />
              Copy
            </button>
          </div>

          <div className="bg-[#0F172A] rounded-lg p-4 overflow-x-auto">
            <pre className="text-sm">
              <code className="text-white">
                {codeExamples[selectedEndpoint as keyof typeof codeExamples]}
              </code>
            </pre>
          </div>
        </div>
      </div>

      {/* Rate Limits */}
      <div className="mt-6 bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
        <h3 className="text-white text-lg font-semibold mb-4">Rate Limits & Guidelines</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-white font-medium mb-2">Rate Limits</h4>
            <ul className="space-y-2 text-white text-sm">
              <li>• Pro Plan: 10,000 requests per day</li>
              <li>• Maximum 100 requests per minute</li>
              <li>• Burst limit: 10 requests per second</li>
              <li>• Rate limit headers included in responses</li>
            </ul>
          </div>

          <div>
            <h4 className="text-white font-medium mb-2">Best Practices</h4>
            <ul className="space-y-2 text-white text-sm">
              <li>• Cache responses when possible</li>
              <li>• Use appropriate request intervals</li>
              <li>• Handle rate limit errors gracefully</li>
              <li>• Monitor your usage regularly</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}