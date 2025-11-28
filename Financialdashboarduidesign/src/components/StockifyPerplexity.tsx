import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, ArrowUpRight, Menu, Share2, ThumbsUp, ThumbsDown, Copy, 
  MoreVertical, Mic, Image as ImageIcon, Paperclip, ChevronDown
} from 'lucide-react';
import { mcpAPI } from '../services/mcpAPI';

// --- INTERFACES ---

interface ChatMsg {
  id: number;
  type: 'user' | 'bot';
  text: string;
  metadata?: {
    symbol?: string;
    price_change?: number;
    sentiment_score?: number;
    correlation?: number;
  };
  timestamp: string;
}

interface Suggestion {
  icon: React.ReactNode;
  text: string;
  query: string;
}

// --- CHAT MESSAGE COMPONENT ---

const ChatMessage = ({ msg }: { msg: ChatMsg }) => {
  const isUser = msg.type === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-8 animate-fade-in">
        <div className="max-w-[80%]">
          <div className="text-white rounded-3xl px-6 py-3 inline-block" style={{ backgroundColor: '#1f1f1f' }}>
            <p className="text-[15px] leading-relaxed">{msg.text}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-4 mb-10 animate-fade-in group">
      {/* Gemini Avatar */}
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
        <Sparkles size={20} className="text-white" />
      </div>

      {/* Message Content */}
      <div className="flex-1 max-w-[85%]">
        <div className="mb-4">
          <div className="prose prose-invert prose-lg max-w-none">
            {msg.text.split('\n\n').map((paragraph, i) => (
              <p key={i} className="text-[15px] leading-relaxed text-[#e3e3e3] mb-4">
                {paragraph.split('\n').map((line, j) => (
                  <React.Fragment key={j}>
                    {line.split('**').map((part, k) => 
                      k % 2 === 0 ? part : <strong key={k} className="font-semibold text-white">{part}</strong>
                    )}
                    {j < paragraph.split('\n').length - 1 && <br />}
                  </React.Fragment>
                ))}
              </p>
            ))}
          </div>
        </div>

        {/* Metadata Chips */}
        {msg.metadata && (
          <div className="flex gap-2 flex-wrap mb-4">
            {msg.metadata.symbol && (
              <span className="px-3 py-1 text-slate-300 rounded-full text-xs font-medium" style={{ backgroundColor: '#1f1f1f' }}>
                {msg.metadata.symbol}
              </span>
            )}
            {msg.metadata.price_change !== undefined && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                msg.metadata.price_change >= 0 
                  ? 'bg-emerald-500/10 text-emerald-400' 
                  : 'bg-rose-500/10 text-rose-400'
              }`}>
                {msg.metadata.price_change >= 0 ? '↗' : '↘'} {Math.abs(msg.metadata.price_change).toFixed(2)}%
              </span>
            )}
            {msg.metadata.sentiment_score !== undefined && (
              <span className="px-3 py-1 bg-indigo-500/10 text-indigo-400 rounded-full text-xs font-medium">
                💭 Sentiment {(msg.metadata.sentiment_score * 100).toFixed(0)}%
              </span>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <button 
            onClick={handleCopy}
            className="p-2 hover:bg-[#1f1f1f] rounded-full transition-colors"
            title={copied ? "Copied!" : "Copy"}
          >
            <Copy size={16} className={copied ? "text-green-400" : "text-slate-400"} />
          </button>
          <button className="p-2 hover:bg-[#1f1f1f] rounded-full transition-colors" title="Good response">
            <ThumbsUp size={16} className="text-slate-400" />
          </button>
          <button className="p-2 hover:bg-[#1f1f1f] rounded-full transition-colors" title="Bad response">
            <ThumbsDown size={16} className="text-slate-400" />
          </button>
          <button className="p-2 hover:bg-[#1f1f1f] rounded-full transition-colors" title="More options">
            <MoreVertical size={16} className="text-slate-400" />
          </button>
        </div>
      </div>
    </div>
  );
};

// --- MAIN GEMINI-STYLE APP ---

export default function StockifyPerplexity() {
  const [inputValue, setInputValue] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMsg[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Suggestions for empty state
  const suggestions: Suggestion[] = [
    { icon: <Sparkles size={16} />, text: "Explain TCS price movement", query: "Give me analysis of TCS last month" },
    { icon: <Sparkles size={16} />, text: "Market sentiment today", query: "What's the market sentiment today?" },
    { icon: <Sparkles size={16} />, text: "Compare IT stocks", query: "Compare TCS vs Infosys performance" },
    { icon: <Sparkles size={16} />, text: "HDFC Bank analysis", query: "Tell me about HDFC Bank this quarter" },
  ];

  // Auto-scroll chat
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isSearching]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  const handleSearch = async (queryText?: string) => {
    const query = queryText || inputValue;
    if (!query.trim()) return;

    setInputValue('');
    setShowSuggestions(false);
    
    const userMsg: ChatMsg = { 
      id: Date.now(), 
      type: 'user', 
      text: query,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, userMsg]);
    setIsSearching(true);

    try {
      const mcpResponse = await mcpAPI.processQuery(query);
      
      const botMsg: ChatMsg = {
        id: Date.now() + 1,
        type: 'bot',
        text: mcpResponse.content,
        metadata: mcpResponse.metadata,
        timestamp: new Date().toISOString()
      };

      setChatHistory(prev => [...prev, botMsg]);
    } catch (error) {
      console.error('Error processing query:', error);
      const errorMsg: ChatMsg = {
        id: Date.now() + 1,
        type: 'bot',
        text: `I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the MCP server is running on port 8001.`,
        timestamp: new Date().toISOString()
      };
      setChatHistory(prev => [...prev, errorMsg]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="h-screen w-full flex flex-col" style={{ backgroundColor: '#131314', color: 'white' }}>
      
      {/* Top Bar */}
      <header className="border-b px-4 py-3 flex items-center justify-between" style={{ borderColor: '#2d2d2d' }}>
        <div className="flex items-center gap-3">
          <button className="p-2 hover:bg-[#1f1f1f] rounded-lg transition-colors lg:hidden">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center">
              <Sparkles size={18} className="text-white" />
            </div>
            <span className="font-medium text-lg hidden sm:block">Stockify</span>
            <ChevronDown size={16} className="text-slate-400 hidden sm:block" />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="px-4 py-2 hover:bg-[#1f1f1f] rounded-full text-sm transition-colors hidden sm:flex items-center gap-2">
            <Share2 size={16} />
            Share
          </button>
          <button 
            onClick={() => window.location.href = '/'}
            className="px-4 py-2 bg-[#1f1f1f] hover:bg-[#2d2d2d] rounded-full text-sm transition-colors"
          >
            Dashboard
          </button>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-8">
          
          {/* Welcome / Empty State */}
          {chatHistory.length === 0 && !isSearching && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] animate-fade-in">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center mb-8 shadow-2xl shadow-purple-500/30">
                <Sparkles size={48} className="text-white" />
              </div>
              <h1 className="text-5xl font-light mb-4 tracking-tight">Hello, I'm Stockify AI</h1>
              <p className="text-slate-400 text-lg mb-16">How can I help you with the markets today?</p>

              {/* Suggestion Cards */}
              {showSuggestions && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
                  {suggestions.map((sug, i) => (
                    <button
                      key={i}
                      onClick={() => handleSearch(sug.query)}
                      className="p-5 rounded-xl text-left transition-all hover:scale-[1.02] group border border-gray-800"
                      style={{ backgroundColor: '#1a1a1a' }}
                    >
                      <div className="flex items-start gap-3">
                        <div className="text-blue-400 mt-0.5">
                          {sug.icon}
                        </div>
                        <p className="text-slate-300 text-[15px] group-hover:text-white transition-colors leading-relaxed">
                          {sug.text}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Chat Messages */}
          {chatHistory.map(msg => <ChatMessage key={msg.id} msg={msg} />)}
          
          {/* Loading State */}
          {isSearching && (
            <div className="flex gap-4 mb-10 animate-fade-in">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                <Sparkles size={20} className="text-white animate-pulse" />
              </div>
              <div className="flex-1">
                <div className="flex gap-2 mt-2">
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={chatBottomRef} />
        </div>
      </main>

      {/* Input Area - Fixed at Bottom */}
      <div className="border-t px-4 py-6" style={{ borderColor: '#2d2d2d', backgroundColor: '#131314' }}>
        <div className="max-w-3xl mx-auto">
          <div className="relative rounded-full border" style={{ backgroundColor: '#1f1f1f', borderColor: '#3f3f3f' }}>
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask Stockify AI about stocks, markets, or news..."
              rows={1}
              disabled={isSearching}
              className="w-full text-white placeholder-slate-500 px-6 py-4 pr-40 resize-none focus:outline-none text-[15px] leading-relaxed max-h-40 disabled:opacity-50 rounded-full"
              style={{ backgroundColor: 'transparent', minHeight: '60px' }}
            />
            
            {/* Bottom Actions */}
            <div className="absolute right-3 bottom-3 flex items-center gap-1">
              <button 
                disabled={isSearching}
                className="p-2.5 hover:bg-[#2d2d2d] rounded-full transition-colors text-slate-400 hover:text-white disabled:opacity-50"
                title="Attach file"
              >
                <Paperclip size={20} />
              </button>
              <button 
                disabled={isSearching}
                className="p-2.5 hover:bg-[#2d2d2d] rounded-full transition-colors text-slate-400 hover:text-white disabled:opacity-50"
                title="Add image"
              >
                <ImageIcon size={20} />
              </button>
              <button 
                disabled={isSearching}
                className="p-2.5 hover:bg-[#2d2d2d] rounded-full transition-colors text-slate-400 hover:text-white disabled:opacity-50"
                title="Voice input"
              >
                <Mic size={20} />
              </button>
              <button
                onClick={() => handleSearch()}
                disabled={!inputValue.trim() || isSearching}
                className="ml-1 p-3 bg-white hover:bg-slate-100 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-full transition-colors text-black disabled:text-slate-500"
                title="Send"
              >
                <ArrowUpRight size={20} />
              </button>
            </div>
          </div>

          {/* Footer Text */}
          <p className="text-center text-xs text-slate-600 mt-4">
            Stockify AI can make mistakes. Verify important financial information.
          </p>
        </div>
      </div>
    </div>
  );
}
