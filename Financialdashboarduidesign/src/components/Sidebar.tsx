import { Home, BarChart3, Newspaper, ArrowLeftRight, Code, Settings, ChevronLeft, Sparkles } from "lucide-react";
import { useState } from "react";

const navItems = [
  { icon: Home, label: "Dashboard", id: "dashboard" },
  { icon: Sparkles, label: "AI Search", id: "ai", highlighted: true },
  { icon: BarChart3, label: "Insights", id: "insights" },
  { icon: Newspaper, label: "News Feed", id: "news" },
  { icon: ArrowLeftRight, label: "Compare", id: "compare" },
  { icon: Code, label: "API Access", id: "api" },
  { icon: Settings, label: "Settings", id: "settings" },
];

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
}

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={`bg-[#111827] border-r border-gray-800 transition-all duration-300 flex flex-col ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      <div className="flex-1 py-6">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`w-full flex items-center gap-3 px-6 py-3 transition-all relative group ${
                isActive
                  ? "text-[#3B82F6] bg-[#3B82F6]/10"
                  : item.highlighted
                  ? "text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10"
                  : "text-[#9CA3AF] hover:text-[#E5E7EB] hover:bg-[#0B1120]/50"
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#3B82F6] rounded-r" />
              )}
              <Icon className={`w-5 h-5 flex-shrink-0 ${item.highlighted ? 'animate-pulse' : ''}`} />
              {!collapsed && (
                <span className="text-sm">
                  {item.label}
                  {item.highlighted && <span className="ml-2 text-[10px] bg-emerald-500/20 text-emerald-400 px-1.5 py-0.5 rounded">NEW</span>}
                </span>
              )}
              
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-[#111827] border border-gray-800 rounded text-xs whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity">
                  {item.label}
                </div>
              )}
            </button>
          );
        })}
      </div>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="p-4 border-t border-gray-800 hover:bg-[#0B1120]/50 transition-colors flex items-center justify-center"
      >
        <ChevronLeft
          className={`w-5 h-5 text-[#9CA3AF] transition-transform ${
            collapsed ? "rotate-180" : ""
          }`}
        />
      </button>
    </div>
  );
}
