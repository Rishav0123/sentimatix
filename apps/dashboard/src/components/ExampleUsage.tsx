import { useState } from 'react';
import { Copy, Check, Terminal } from 'lucide-react';

export function ExampleUsage() {
  const [copiedCurl, setCopiedCurl] = useState(false);
  const [copiedPython, setCopiedPython] = useState(false);

  const curlCode = `curl -X GET "https://sentimatix-production.up.railway.app/api/v1/news?limit=5" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`;

  const pythonCode = `import requests

url = "https://sentimatix-production.up.railway.app/api/v1/news?limit=5"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.json())`;

  const copyToClipboard = (text: string, type: 'curl' | 'python') => {
    navigator.clipboard.writeText(text);
    if (type === 'curl') {
      setCopiedCurl(true);
      setTimeout(() => setCopiedCurl(false), 2000);
    } else {
      setCopiedPython(true);
      setTimeout(() => setCopiedPython(false), 2000);
    }
  };

  return (
    <div className="bg-[#111827] rounded-xl border border-gray-800 overflow-hidden mt-6">
      <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-[#1f2937]">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-blue-400" />
          <h3 className="text-[#E5E7EB] font-semibold">Example Usage: Get News Sentiment</h3>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-gray-800">
        {/* cURL Snippet */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-400">cURL</span>
            <button
              onClick={() => copyToClipboard(curlCode, 'curl')}
              className="text-gray-400 hover:text-white transition-colors p-1"
              title="Copy cURL"
            >
              {copiedCurl ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
          <pre className="bg-[#0B1120] p-4 rounded-lg overflow-x-auto border border-gray-800/50">
            <code className="text-sm text-green-400 font-mono whitespace-pre">{curlCode}</code>
          </pre>
        </div>

        {/* Python Snippet */}
        <div className="p-6">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-gray-400">Python</span>
            <button
              onClick={() => copyToClipboard(pythonCode, 'python')}
              className="text-gray-400 hover:text-white transition-colors p-1"
              title="Copy Python"
            >
              {copiedPython ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
          <pre className="bg-[#0B1120] p-4 rounded-lg overflow-x-auto border border-gray-800/50">
            <code className="text-sm text-blue-300 font-mono whitespace-pre">{pythonCode}</code>
          </pre>
        </div>
      </div>
    </div>
  );
}
