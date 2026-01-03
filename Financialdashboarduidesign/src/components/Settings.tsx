import { useState } from "react";
import { Bell, Moon, Sun, Globe, Shield, User, Palette, Database } from "lucide-react";

export function Settings() {
  const [settings, setSettings] = useState({
    theme: 'dark',
    notifications: {
      priceAlerts: true,
      newsUpdates: true,
      earningsReminders: true,
      marketOpen: false
    },
    display: {
      currency: 'INR',
      language: 'en',
      timeFormat: '24h',
      compactMode: false
    },
    privacy: {
      dataSharing: false,
      analytics: true,
      marketingEmails: false
    }
  });

  const updateSetting = (category: keyof typeof settings, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...(prev[category] as any),
        [key]: value
      }
    }));
  };

  const updateDirectSetting = (key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="p-6 max-w-[1800px] mx-auto h-full overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-white text-2xl font-bold mb-2">Settings</h1>
        <p className="text-gray-400">Customize your Stockify experience</p>
      </div>

      <div className="space-y-6">
        {/* Profile Section */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <User className="w-5 h-5 text-blue-400" />
            <h3 className="text-white text-lg font-semibold">Profile</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Display Name</label>
              <input
                type="text"
                defaultValue="John Doe"
                className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Email</label>
              <input
                type="email"
                defaultValue="john.doe@example.com"
                className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Appearance */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Palette className="w-5 h-5 text-purple-400" />
            <h3 className="text-white text-lg font-semibold">Appearance</h3>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-400 mb-3">Theme</label>
              <div className="flex gap-3">
                {[
                  { id: 'light', label: 'Light', icon: Sun },
                  { id: 'dark', label: 'Dark', icon: Moon },
                  { id: 'auto', label: 'Auto', icon: Globe }
                ].map((theme) => {
                  const Icon = theme.icon;
                  return (
                    <button
                      key={theme.id}
                      onClick={() => updateDirectSetting('theme', theme.id)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg border transition-all ${
                        settings.theme === theme.id
                          ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                          : 'border-gray-700 text-gray-400 hover:border-gray-600'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {theme.label}
                    </button>
                  );
                })}
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Compact Mode</div>
                <div className="text-gray-400 text-sm">Reduce spacing and padding</div>
              </div>
              <button
                onClick={() => updateSetting('display', 'compactMode', !settings.display.compactMode)}
                className={`relative w-12 h-6 rounded-full transition-colors ${
                  settings.display.compactMode ? 'bg-blue-600' : 'bg-gray-600'
                }`}
              >
                <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                  settings.display.compactMode ? 'translate-x-7' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Bell className="w-5 h-5 text-yellow-400" />
            <h3 className="text-white text-lg font-semibold">Notifications</h3>
          </div>
          
          <div className="space-y-4">
            {[
              { key: 'priceAlerts', label: 'Price Alerts', desc: 'Get notified when stocks hit your target prices' },
              { key: 'newsUpdates', label: 'News Updates', desc: 'Breaking news and market updates' },
              { key: 'earningsReminders', label: 'Earnings Reminders', desc: 'Upcoming earnings announcements' },
              { key: 'marketOpen', label: 'Market Open/Close', desc: 'Daily market session notifications' }
            ].map((notification) => (
              <div key={notification.key} className="flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">{notification.label}</div>
                  <div className="text-gray-400 text-sm">{notification.desc}</div>
                </div>
                <button
                  onClick={() => updateSetting('notifications', notification.key, !settings.notifications[notification.key as keyof typeof settings.notifications])}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.notifications[notification.key as keyof typeof settings.notifications] ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    settings.notifications[notification.key as keyof typeof settings.notifications] ? 'translate-x-7' : 'translate-x-1'
                  }`} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Display Preferences */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Globe className="w-5 h-5 text-green-400" />
            <h3 className="text-white text-lg font-semibold">Display Preferences</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm text-gray-400 mb-2">Currency</label>
              <select
                value={settings.display.currency}
                onChange={(e) => updateSetting('display', 'currency', e.target.value)}
                className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="INR">Indian Rupee (₹)</option>
                <option value="USD">US Dollar ($)</option>
                <option value="EUR">Euro (€)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Language</label>
              <select
                value={settings.display.language}
                onChange={(e) => updateSetting('display', 'language', e.target.value)}
                className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="es">Spanish</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm text-gray-400 mb-2">Time Format</label>
              <select
                value={settings.display.timeFormat}
                onChange={(e) => updateSetting('display', 'timeFormat', e.target.value)}
                className="w-full px-3 py-2 bg-[#0F172A] border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
              >
                <option value="12h">12 Hour</option>
                <option value="24h">24 Hour</option>
              </select>
            </div>
          </div>
        </div>

        {/* Privacy & Security */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-red-400" />
            <h3 className="text-white text-lg font-semibold">Privacy & Security</h3>
          </div>
          
          <div className="space-y-4">
            {[
              { key: 'dataSharing', label: 'Data Sharing', desc: 'Share anonymized usage data to improve the platform' },
              { key: 'analytics', label: 'Analytics', desc: 'Allow collection of analytics data' },
              { key: 'marketingEmails', label: 'Marketing Emails', desc: 'Receive promotional emails and updates' }
            ].map((privacy) => (
              <div key={privacy.key} className="flex items-center justify-between">
                <div>
                  <div className="text-white font-medium">{privacy.label}</div>
                  <div className="text-gray-400 text-sm">{privacy.desc}</div>
                </div>
                <button
                  onClick={() => updateSetting('privacy', privacy.key, !settings.privacy[privacy.key as keyof typeof settings.privacy])}
                  className={`relative w-12 h-6 rounded-full transition-colors ${
                    settings.privacy[privacy.key as keyof typeof settings.privacy] ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                    settings.privacy[privacy.key as keyof typeof settings.privacy] ? 'translate-x-7' : 'translate-x-1'
                  }`} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Data Management */}
        <div className="bg-[#1E293B] rounded-lg p-6 border border-gray-700/50">
          <div className="flex items-center gap-2 mb-4">
            <Database className="w-5 h-5 text-cyan-400" />
            <h3 className="text-white text-lg font-semibold">Data Management</h3>
          </div>
          
          <div className="space-y-4">
            <button className="w-full md:w-auto px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
              Export My Data
            </button>
            
            <button className="w-full md:w-auto px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors">
              Clear Cache
            </button>
            
            <button className="w-full md:w-auto px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors">
              Delete Account
            </button>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end">
          <button className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
}