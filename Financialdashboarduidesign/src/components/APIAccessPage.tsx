import { useState } from "react";
import { Code, Key, Copy, Check, ExternalLink, Activity, Newspaper, TrendingUp } from "lucide-react";

export function APIAccessPage() {
  const [apiKey, setApiKey] = useState("sk_live_************************");
  const [copied, setCopied] = useState(false);
  const [selectedEndpoint, setSelectedEndpoint] = useState("sentiment");

  const handleCopyKey = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const endpoints = [
    {
      id: "sentiment",
      name: "Sentiment Analysis",
      icon: Activity,
      method: "GET",
      path: "/api/v1/sentiment/{ticker}",
      description: "Get AI-powered sentiment analysis for a specific stock",
      params: [
        { name: "ticker", type: "string", required: true, description: "Stock ticker symbol (e.g., INFY, TCS)" },
        { name: "timeframe", type: "string", required: false, description: "Time period: 1d, 1w, 1m, 3m, 1y" },
      ],
      response: `{
  "ticker": "INFY",
  "sentiment_score": 78,
  "sentiment_label": "Positive",
  "confidence": 0.92,
  "analyzed_articles": 45,
  "timeframe": "1d",
  "breakdown": {
    "positive": 65,
    "neutral": 25,
    "negative": 10
  },
  "timestamp": "2024-11-01T10:30:00Z"
}`,
    },
    {
      id: "news",
      name: "News Feed",
      icon: Newspaper,
      method: "GET",
      path: "/api/v1/news",
      description: "Retrieve latest news articles with sentiment scores",
      params: [
        { name: "ticker", type: "string", required: false, description: "Filter by stock ticker" },
        { name: "limit", type: "integer", required: false, description: "Number of articles (max 100)" },
        { name: "category", type: "string", required: false, description: "Filter by category" },
        { name: "sentiment", type: "string", required: false, description: "Filter by sentiment: positive, neutral, negative" },
      ],
      response: `{
  "articles": [
    {
      "id": "news_123",
      "title": "Infosys Announces Major AI Partnership",
      "summary": "Strategic partnership to develop next-gen AI solutions...",
      "source": "Economic Times",
      "published_at": "2024-11-01T08:00:00Z",
      "ticker": "INFY",
      "stock_name": "Infosys Limited",
      "sentiment_score": 85,
      "sentiment_label": "Positive",
      "category": "Partnership",
      "url": "https://example.com/article"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 20
}`,
    },
    {
      id: "batch-sentiment",
      name: "Batch Sentiment",
      icon: TrendingUp,
      method: "POST",
      path: "/api/v1/sentiment/batch",
      description: "Get sentiment analysis for multiple stocks in one request",
      params: [
        { name: "tickers", type: "array", required: true, description: "Array of ticker symbols (max 50)" },
        { name: "timeframe", type: "string", required: false, description: "Time period for analysis" },
      ],
      response: `{
  "results": [
    {
      "ticker": "INFY",
      "sentiment_score": 78,
      "sentiment_label": "Positive"
    },
    {
      "ticker": "TCS",
      "sentiment_score": 82,
      "sentiment_label": "Positive"
    }
  ],
  "count": 2,
  "timestamp": "2024-11-01T10:30:00Z"
}`,
    },
  ];

  const selectedEndpointData = endpoints.find((e) => e.id === selectedEndpoint) || endpoints[0];
  const Icon = selectedEndpointData.icon;

  const codeExamples = {
    javascript: `// Using Fetch API
fetch('https://api.stockify.com${selectedEndpointData.path}', {
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));`,
    python: `# Using requests library
import requests

headers = {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.get(
    'https://api.stockify.com${selectedEndpointData.path}',
    headers=headers
)

data = response.json()
print(data)`,
    curl: `curl -X ${selectedEndpointData.method} \\
  'https://api.stockify.com${selectedEndpointData.path}' \\
  -H 'Authorization: Bearer YOUR_API_KEY' \\
  -H 'Content-Type: application/json'`,
  };

  const [selectedLanguage, setSelectedLanguage] = useState<keyof typeof codeExamples>("javascript");
  const [codeCopied, setCodeCopied] = useState(false);

  const handleCopyCode = () => {
    navigator.clipboard.writeText(codeExamples[selectedLanguage]);
    setCodeCopied(true);
    setTimeout(() => setCodeCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-[#E5E7EB] text-2xl mb-1">API Access</h2>
        <p className="text-[#9CA3AF] text-sm">
          Integrate Stockify's sentiment analysis and news data into your applications
        </p>
      </div>

      {/* API Key Section */}
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <div className="flex items-center gap-2 mb-4">
          <Key className="w-5 h-5 text-[#3B82F6]" />
          <h3 className="text-[#E5E7EB]">Your API Key</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-[#0B1120] border border-gray-800 rounded-lg px-4 py-3 font-mono text-sm text-[#E5E7EB] overflow-x-auto">
            {apiKey}
          </div>
          <button
            onClick={handleCopyKey}
            className="px-4 py-3 bg-[#3B82F6] hover:bg-[#3B82F6]/90 rounded-lg transition-colors flex items-center gap-2 text-white"
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <p className="text-[#9CA3AF] text-xs mt-3">
          Keep your API key secure. Do not share it publicly or commit it to version control.
        </p>
      </div>

      {/* Usage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
          <p className="text-[#9CA3AF] text-xs mb-1">Requests Today</p>
          <p className="text-[#E5E7EB] text-2xl">1,247</p>
          <p className="text-[#10B981] text-xs mt-1">+12% from yesterday</p>
        </div>
        <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
          <p className="text-[#9CA3AF] text-xs mb-1">Monthly Quota</p>
          <p className="text-[#E5E7EB] text-2xl">10,000</p>
          <p className="text-[#9CA3AF] text-xs mt-1">87.5% remaining</p>
        </div>
        <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
          <p className="text-[#9CA3AF] text-xs mb-1">Success Rate</p>
          <p className="text-[#E5E7EB] text-2xl">99.8%</p>
          <p className="text-[#10B981] text-xs mt-1">Excellent</p>
        </div>
        <div className="bg-[#111827] rounded-xl p-5 border border-gray-800">
          <p className="text-[#9CA3AF] text-xs mb-1">Avg Response</p>
          <p className="text-[#E5E7EB] text-2xl">124ms</p>
          <p className="text-[#10B981] text-xs mt-1">Fast</p>
        </div>
      </div>

      {/* API Endpoints */}
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800">
        <h3 className="text-[#E5E7EB] mb-4">Available Endpoints</h3>
        <div className="flex flex-wrap gap-2 mb-6">
          {endpoints.map((endpoint) => {
            const EndpointIcon = endpoint.icon;
            return (
              <button
                key={endpoint.id}
                onClick={() => setSelectedEndpoint(endpoint.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                  selectedEndpoint === endpoint.id
                    ? "bg-[#3B82F6] text-white"
                    : "bg-[#0B1120] text-[#9CA3AF] hover:text-[#E5E7EB] border border-gray-800"
                }`}
              >
                <EndpointIcon className="w-4 h-4" />
                {endpoint.name}
              </button>
            );
          })}
        </div>

        {/* Endpoint Details */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Icon className="w-6 h-6 text-[#3B82F6]" />
            <div className="flex-1">
              <h4 className="text-[#E5E7EB] text-lg">{selectedEndpointData.name}</h4>
              <p className="text-[#9CA3AF] text-sm">{selectedEndpointData.description}</p>
            </div>
            <span className="px-3 py-1 bg-[#10B981]/10 text-[#10B981] rounded text-sm border border-[#10B981]/20">
              {selectedEndpointData.method}
            </span>
          </div>

          <div className="bg-[#0B1120] border border-gray-800 rounded-lg p-4">
            <code className="text-[#3B82F6] text-sm">
              https://api.stockify.com{selectedEndpointData.path}
            </code>
          </div>

          {/* Parameters */}
          <div>
            <h5 className="text-[#E5E7EB] text-sm mb-2">Parameters</h5>
            <div className="bg-[#0B1120] border border-gray-800 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-800">
                    <th className="text-left p-3 text-[#9CA3AF] text-xs">Name</th>
                    <th className="text-left p-3 text-[#9CA3AF] text-xs">Type</th>
                    <th className="text-left p-3 text-[#9CA3AF] text-xs">Required</th>
                    <th className="text-left p-3 text-[#9CA3AF] text-xs">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedEndpointData.params.map((param, index) => (
                    <tr key={index} className="border-b border-gray-800 last:border-0">
                      <td className="p-3 text-[#E5E7EB] text-sm font-mono">{param.name}</td>
                      <td className="p-3 text-[#9CA3AF] text-sm">{param.type}</td>
                      <td className="p-3">
                        {param.required ? (
                          <span className="text-red-500 text-xs">Required</span>
                        ) : (
                          <span className="text-[#9CA3AF] text-xs">Optional</span>
                        )}
                      </td>
                      <td className="p-3 text-[#9CA3AF] text-sm">{param.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Code Examples */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-[#E5E7EB] text-sm">Code Example</h5>
              <div className="flex gap-2">
                {(["javascript", "python", "curl"] as const).map((lang) => (
                  <button
                    key={lang}
                    onClick={() => setSelectedLanguage(lang)}
                    className={`px-3 py-1 rounded text-xs transition-all ${
                      selectedLanguage === lang
                        ? "bg-[#3B82F6] text-white"
                        : "bg-[#0B1120] text-[#9CA3AF] hover:text-[#E5E7EB]"
                    }`}
                  >
                    {lang.charAt(0).toUpperCase() + lang.slice(1)}
                  </button>
                ))}
              </div>
            </div>
            <div className="relative">
              <pre className="bg-[#0B1120] border border-gray-800 rounded-lg p-4 overflow-x-auto">
                <code className="text-[#E5E7EB] text-sm">{codeExamples[selectedLanguage]}</code>
              </pre>
              <button
                onClick={handleCopyCode}
                className="absolute top-3 right-3 px-3 py-1.5 bg-[#111827] hover:bg-[#1F2937] border border-gray-800 rounded text-xs text-[#9CA3AF] hover:text-[#E5E7EB] transition-colors flex items-center gap-1"
              >
                {codeCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {codeCopied ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          {/* Response Example */}
          <div>
            <h5 className="text-[#E5E7EB] text-sm mb-2">Response Example</h5>
            <pre className="bg-[#0B1120] border border-gray-800 rounded-lg p-4 overflow-x-auto">
              <code className="text-[#10B981] text-sm">{selectedEndpointData.response}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* Documentation Link */}
      <div className="bg-[#111827] rounded-xl p-6 border border-gray-800 flex items-center justify-between">
        <div>
          <h3 className="text-[#E5E7EB] mb-1">Need More Help?</h3>
          <p className="text-[#9CA3AF] text-sm">
            Check out our comprehensive API documentation for detailed guides and examples
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white rounded-lg transition-colors">
          View Docs
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
