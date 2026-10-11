import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Clock, ExternalLink } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { SourceStatus } from '../types';

const statusConfig = {
  connected: { icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50 dark:bg-green-900/20', border: 'border-green-200 dark:border-green-800', label: 'Connected' },
  missing_credentials: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800', label: 'Missing Credentials' },
  rate_limited: { icon: AlertTriangle, color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-200 dark:border-yellow-800', label: 'Rate Limited' },
  error: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-200 dark:border-red-800', label: 'Error' },
  unavailable: { icon: XCircle, color: 'text-gray-500', bg: 'bg-gray-50 dark:bg-gray-800', border: 'border-gray-200 dark:border-gray-700', label: 'Unavailable' },
};

export default function Sources() {
  const [sources, setSources] = useState<SourceStatus[]>([]);

  useEffect(() => {
    apiClient.getSources().then(setSources).catch(err => {
      console.error('Failed to load sources:', err);
    });
  }, []);

  const connected = sources.filter(s => s.status === 'connected').length;
  const total = sources.length;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Sources & Tier Status</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Platform connection status · {connected}/{total} connected
        </p>
      </div>

      {/* Summary bar */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="text-sm">Connected: {sources.filter(s => s.status === 'connected').length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <span className="text-sm">Rate Limited: {sources.filter(s => s.status === 'rate_limited').length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span className="text-sm">Missing Creds: {sources.filter(s => s.status === 'missing_credentials').length}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-400" />
            <span className="text-sm">Unavailable: {sources.filter(s => s.status === 'unavailable').length}</span>
          </div>
        </div>
      </div>

      {/* Source cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sources.map((source) => {
          const config = statusConfig[source.status];
          const StatusIcon = config.icon;

          return (
            <div
              key={source.platform}
              className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 ${config.border}`}
            >
              <div className="flex items-start gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shrink-0"
                  style={{ backgroundColor: source.color }}
                >
                  {source.label.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{source.label}</h3>
                    <StatusIcon className={`w-4 h-4 ${config.color}`} />
                  </div>
                  <span className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full font-medium ${config.bg} ${config.color}`}>
                    {config.label}
                  </span>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">{source.message}</p>
                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(source.lastChecked).toLocaleString()}
                    </span>
                    {source.itemsCollected > 0 && (
                      <span>{source.itemsCollected} items collected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Info box */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4">
        <div className="flex items-start gap-2">
          <ExternalLink className="w-4 h-4 text-blue-500 mt-0.5 shrink-0" />
          <div className="text-sm text-blue-800 dark:text-blue-300">
            <p className="font-medium mb-1">About Source Tiers</p>
            <p className="text-blue-600 dark:text-blue-400">
              <strong>Connected:</strong> API credentials configured and working. Full collection available.<br />
              <strong>Rate Limited:</strong> No official API; using web scraping with rate limits.<br />
              <strong>Missing Credentials:</strong> API keys not configured. Add to .env file.<br />
              <strong>Unavailable:</strong> Platform doesn't allow public content access via API.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
