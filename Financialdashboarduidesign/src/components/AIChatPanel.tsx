import { X, Send, Sparkles, Loader2, AlertCircle } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { mcpAPI, MCPMessage } from "../services/mcpAPI";
import ReactMarkdown from 'react-markdown';

interface AIChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const exampleMessages: MCPMessage[] = [
  { 
    role: "assistant" as const, 
    content: "Hi! I'm Stockify AI powered by RAG (Retrieval-Augmented Generation). Ask me about any stock - just mention the stock name naturally!\n\n**Try asking:**\n- TCS news last month\n- Tell me about HDFC Bank\n- What's happening with Reliance?\n- Give me Infosys summary\n- Show ICICI updates this week",
    timestamp: new Date().toISOString()
  },
];

export function AIChatPanel({ isOpen, onClose }: AIChatPanelProps) {
  const [messages, setMessages] = useState<MCPMessage[]>(exampleMessages);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [mcpStatus, setMcpStatus] = useState<'online' | 'offline' | 'checking'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check MCP server health on mount
  useEffect(() => {
    const checkHealth = async () => {
      const isHealthy = await mcpAPI.healthCheck();
      setMcpStatus(isHealthy ? 'online' : 'offline');
    };
    checkHealth();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: MCPMessage = { 
      role: "user", 
      content: input,
      timestamp: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Call MCP API to process the query
      const aiResponse = await mcpAPI.processQuery(input);
      setMessages((prev) => [...prev, aiResponse]);
    } catch (error) {
      const errorMessage: MCPMessage = {
        role: "assistant",
        content: `❌ I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}.\n\nPlease ensure the MCP server is running on http://localhost:8002`,
        timestamp: new Date().toISOString()
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed top-0 right-0 w-96 h-full bg-[#111827] border-l border-gray-800 shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[#3B82F6]" />
          <h2 className="text-[#E5E7EB]">Stockify AI + RAG</h2>
          <div className={`w-2 h-2 rounded-full ${
            mcpStatus === 'online' ? 'bg-green-500' : 
            mcpStatus === 'offline' ? 'bg-red-500' : 
            'bg-yellow-500'
          }`} title={`MCP Server: ${mcpStatus}`} />
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-lg hover:bg-[#0B1120] flex items-center justify-center transition-colors"
        >
          <X className="w-5 h-5 text-[#9CA3AF]" />
        </button>
      </div>

      {/* MCP Status Warning */}
      {mcpStatus === 'offline' && (
        <div className="bg-red-950/30 border-l-4 border-red-500 p-3 mx-4 mt-4 rounded">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <p className="text-xs text-red-300">
              MCP Server offline. Start it with: <code className="bg-black/30 px-1 rounded">python mcp/run_server.py</code>
            </p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 ${
                message.role === "user"
                  ? "bg-[#3B82F6] text-white"
                  : "bg-[#0B1120] text-[#E5E7EB] border border-gray-800"
              }`}
            >
              <div className="text-sm prose prose-invert prose-sm max-w-none">
                {message.content.split('\n').map((line, i) => {
                  // Basic markdown-like rendering
                  if (line.startsWith('**') && line.endsWith('**')) {
                    return <p key={i} className="font-bold text-[#3B82F6] mb-1">{line.replace(/\*\*/g, '')}</p>;
                  } else if (line.startsWith('# ')) {
                    return <h3 key={i} className="font-bold text-lg mb-2">{line.substring(2)}</h3>;
                  } else if (line.startsWith('- ')) {
                    return <li key={i} className="ml-4 mb-1">{line.substring(2)}</li>;
                  } else if (line.match(/^\d+\./)) {
                    return <li key={i} className="ml-4 mb-2">{line}</li>;
                  } else if (line.startsWith('_') && line.endsWith('_')) {
                    return <p key={i} className="text-xs text-gray-400 mb-1">{line.replace(/_/g, '')}</p>;
                  } else if (line.trim()) {
                    return <p key={i} className="mb-2">{line}</p>;
                  }
                  return <br key={i} />;
                })}
              </div>
              {message.metadata && (
                <div className="mt-2 pt-2 border-t border-gray-700/50 flex items-center gap-3 text-xs">
                  {message.metadata.price_change !== undefined && (
                    <span className={message.metadata.price_change >= 0 ? "text-green-400" : "text-red-400"}>
                      {message.metadata.price_change >= 0 ? '↗' : '↘'} {Math.abs(message.metadata.price_change).toFixed(2)}%
                    </span>
                  )}
                  {message.metadata.sentiment_score !== undefined && (
                    <span className="text-blue-400">
                      💭 {(message.metadata.sentiment_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-[#0B1120] border border-gray-800 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-[#3B82F6] animate-spin" />
                <p className="text-sm text-[#9CA3AF]">Analyzing with RAG...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Example Prompts */}
      <div className="px-4 pb-2">
        <p className="text-[#9CA3AF] text-xs mb-2">Quick prompts:</p>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setInput("TCS news last month")}
            className="px-2 py-1 text-xs bg-[#0B1120] text-[#9CA3AF] rounded border border-gray-800 hover:border-gray-700 transition-colors"
            disabled={isLoading}
          >
            � TCS news
          </button>
          <button
            onClick={() => setInput("Tell me about HDFC Bank")}
            className="px-2 py-1 text-xs bg-[#0B1120] text-[#9CA3AF] rounded border border-gray-800 hover:border-gray-700 transition-colors"
            disabled={isLoading}
          >
            🏦 HDFC summary
          </button>
          <button
            onClick={() => setInput("What's happening with Infosys?")}
            className="px-2 py-1 text-xs bg-[#0B1120] text-[#9CA3AF] rounded border border-gray-800 hover:border-gray-700 transition-colors"
            disabled={isLoading}
          >
            💼 Infosys updates
          </button>
          <button
            onClick={() => setInput("Reliance performance this quarter")}
            className="px-2 py-1 text-xs bg-[#0B1120] text-[#9CA3AF] rounded border border-gray-800 hover:border-gray-700 transition-colors"
            disabled={isLoading}
          >
            � Reliance Q3
          </button>
        </div>
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && !isLoading && handleSend()}
            placeholder="Ask naturally: 'TCS news last month' or 'Tell me about HDFC'"
            disabled={isLoading}
            className="flex-1 bg-[#0B1120] border border-gray-800 rounded-lg px-3 py-2 text-[#E5E7EB] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#3B82F6] transition-colors text-sm disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="w-10 h-10 bg-[#3B82F6] hover:bg-[#3B82F6]/90 rounded-lg flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <Send className="w-4 h-4 text-white" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
