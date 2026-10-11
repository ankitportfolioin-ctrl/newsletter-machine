import { useState } from 'react';
import { Save, RefreshCw, Trash2, Key, Info } from 'lucide-react';
import { clearAllData, seedDemoData } from '../services/api';

export default function Settings() {
  const [saved, setSaved] = useState(false);

  const handleReseed = () => {
    if (confirm('Reset all data to demo defaults? This will clear your niches, runs, and newsletters.')) {
      seedDemoData();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  const handleClear = () => {
    if (confirm('Clear ALL data? This cannot be undone.')) {
      clearAllData();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Settings</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Configure your newsletter machine</p>
      </div>

      {saved && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl p-4 text-sm text-green-700 dark:text-green-400">
          ✓ Changes saved successfully
        </div>
      )}

      {/* API Configuration */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Key className="w-5 h-5 text-indigo-500" /> API Configuration
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          In production, these would be stored in your .env file. This demo uses simulated data.
        </p>
        <div className="space-y-3">
          {[
            { label: 'Reddit API Client ID', env: 'REDDIT_CLIENT_ID', status: 'configured' },
            { label: 'YouTube Data API Key', env: 'YOUTUBE_API_KEY', status: 'configured' },
            { label: 'X (Twitter) Bearer Token', env: 'TWITTER_BEARER_TOKEN', status: 'missing' },
            { label: 'LinkedIn Client ID', env: 'LINKEDIN_CLIENT_ID', status: 'missing' },
            { label: 'Instagram Access Token', env: 'INSTAGRAM_ACCESS_TOKEN', status: 'missing' },
            { label: 'Facebook App Token', env: 'FACEBOOK_APP_TOKEN', status: 'missing' },
            { label: 'OpenAI API Key', env: 'OPENAI_API_KEY', status: 'configured' },
            { label: 'Dashboard Auth Token', env: 'DASHBOARD_TOKEN', status: 'configured' },
          ].map((item) => (
            <div key={item.env} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{item.label}</p>
                <code className="text-xs text-gray-400">{item.env}</code>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                item.status === 'configured'
                  ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                  : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
              }`}>
                {item.status === 'configured' ? '✓ Set' : '✗ Missing'}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Collection settings */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Save className="w-5 h-5 text-indigo-500" /> Collection Settings
        </h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Schedule</label>
            <select className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500">
              <option>Daily at 2:00 PM UTC</option>
              <option>Every 12 hours</option>
              <option>Weekly on Mondays</option>
              <option>Manual only</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Max items per source</label>
            <input
              type="number"
              defaultValue={25}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Content freshness (hours)</label>
            <input
              type="number"
              defaultValue={24}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" id="dedup" defaultChecked className="rounded border-gray-300" />
            <label htmlFor="dedup" className="text-sm text-gray-700 dark:text-gray-300">Deduplicate across sources</label>
          </div>
          <div className="flex items-center gap-3">
            <input type="checkbox" id="ai-summary" defaultChecked className="rounded border-gray-300" />
            <label htmlFor="ai-summary" className="text-sm text-gray-700 dark:text-gray-300">Use AI for summarization</label>
          </div>
        </div>
      </div>

      {/* Data management */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <RefreshCw className="w-5 h-5 text-indigo-500" /> Data Management
        </h3>
        <div className="space-y-3">
          <button
            onClick={handleReseed}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 rounded-lg text-sm font-medium transition-colors w-full justify-center"
          >
            <RefreshCw className="w-4 h-4" />
            Reset to Demo Data
          </button>
          <button
            onClick={handleClear}
            className="flex items-center gap-2 px-4 py-2 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-700 dark:text-red-300 rounded-lg text-sm font-medium transition-colors w-full justify-center"
          >
            <Trash2 className="w-4 h-4" />
            Clear All Data
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">About This Demo</p>
            <p className="text-blue-600 dark:text-blue-400">
              This is a fully functional demo of the Newsletter Machine. All data is stored locally in your browser.
              In production, this would connect to real APIs for Reddit, YouTube, X, LinkedIn, Instagram, Quora, Facebook,
              and RSS feeds. Newsletter content would be generated using AI (OpenAI/Anthropic) based on collected items.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
