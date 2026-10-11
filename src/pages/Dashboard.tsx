import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Target, Rss, History, Archive, TrendingUp, Zap } from 'lucide-react';
import { getNiches, getSources, getRuns, getNewsletters } from '../services/api';
import { Niche, SourceStatus, RunRecord, Newsletter } from '../types';

export default function Dashboard() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [sources, setSources] = useState<SourceStatus[]>([]);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [newsletters, setNewsletters] = useState<Newsletter[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([getNiches(), getSources(), getRuns(), getNewsletters()]).then(
      ([n, s, r, nl]) => {
        setNiches(n);
        setSources(s);
        setRuns(r);
        setNewsletters(nl);
      }
    );
  }, []);

  const connectedSources = sources.filter(s => s.status === 'connected').length;
  const activeNiches = niches.filter(n => n.enabled).length;
  const completedRuns = runs.filter(r => r.status === 'completed').length;

  const stats = [
    { label: 'Active Niches', value: activeNiches, icon: Target, iconBg: 'bg-indigo-100 dark:bg-indigo-900/30', iconColor: 'text-indigo-600 dark:text-indigo-400', link: '/niches' },
    { label: 'Connected Sources', value: `${connectedSources}/${sources.length}`, icon: Rss, iconBg: 'bg-green-100 dark:bg-green-900/30', iconColor: 'text-green-600 dark:text-green-400', link: '/sources' },
    { label: 'Total Runs', value: completedRuns, icon: History, iconBg: 'bg-blue-100 dark:bg-blue-900/30', iconColor: 'text-blue-600 dark:text-blue-400', link: '/runs' },
    { label: 'Newsletters', value: newsletters.length, icon: Archive, iconBg: 'bg-purple-100 dark:bg-purple-900/30', iconColor: 'text-purple-600 dark:text-purple-400', link: '/archive' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Overview of your newsletter machine</p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <button
            key={stat.label}
            onClick={() => navigate(stat.link)}
            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-left hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between">
              <div className={`p-2 rounded-lg ${stat.iconBg}`}>
                <stat.icon className={`w-5 h-5 ${stat.iconColor}`} />
              </div>
              <TrendingUp className="w-4 h-4 text-gray-300 dark:text-gray-600" />
            </div>
            <div className="mt-3">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent runs */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Runs</h3>
            <button
              onClick={() => navigate('/runs')}
              className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              View all
            </button>
          </div>
          <div className="space-y-3">
            {runs.slice(0, 4).map((run) => (
              <div key={run.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <div className={`w-2 h-2 rounded-full ${
                  run.status === 'completed' ? 'bg-green-500' :
                  run.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                  'bg-red-500'
                }`} />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{run.nicheName}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(run.startedAt).toLocaleDateString()} · {run.totalItems} items
                  </p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  run.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                  run.status === 'running' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                  'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                }`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Source status */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Source Status</h3>
            <button
              onClick={() => navigate('/sources')}
              className="text-sm text-indigo-600 dark:text-indigo-400 hover:underline"
            >
              Manage
            </button>
          </div>
          <div className="space-y-2">
            {sources.map((source) => (
              <div key={source.platform} className="flex items-center gap-3 p-2.5 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ backgroundColor: source.color }}>
                  {source.label.charAt(0)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{source.label}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  source.status === 'connected' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                  source.status === 'rate_limited' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                  'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                }`}>
                  {source.status === 'connected' ? '✓ Connected' :
                   source.status === 'rate_limited' ? '⚠ Limited' :
                   source.status === 'missing_credentials' ? '✗ No Creds' :
                   '✗ Unavailable'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
        <div className="flex items-center gap-3 mb-2">
          <Zap className="w-6 h-6" />
          <h3 className="text-lg font-bold">Quick Actions</h3>
        </div>
        <p className="text-indigo-100 mb-4 text-sm">Trigger a new collection run or view your latest newsletter</p>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => navigate('/runs')}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors backdrop-blur-sm"
          >
            Trigger New Run
          </button>
          <button
            onClick={() => navigate('/archive')}
            className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-sm font-medium transition-colors backdrop-blur-sm"
          >
            View Latest Newsletter
          </button>
        </div>
      </div>
    </div>
  );
}
