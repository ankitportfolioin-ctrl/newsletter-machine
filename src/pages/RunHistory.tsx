import { useEffect, useState } from 'react';
import { Play, CheckCircle, XCircle, Loader, ChevronDown, ChevronUp } from 'lucide-react';
import { getRuns, getNiches, triggerRun } from '../services/api';
import { RunRecord, Niche } from '../types';

export default function RunHistory() {
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [niches, setNiches] = useState<Niche[]>([]);
  const [expandedRun, setExpandedRun] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [selectedNiche, setSelectedNiche] = useState('');

  const loadData = async () => {
    const [r, n] = await Promise.all([getRuns(), getNiches()]);
    setRuns(r);
    setNiches(n);
    if (n.length > 0 && !selectedNiche) setSelectedNiche(n[0].id);
  };

  useEffect(() => { loadData(); }, []);

  const handleTrigger = async () => {
    if (!selectedNiche) return;
    setTriggering(true);
    try {
      await triggerRun(selectedNiche);
      await loadData();
    } catch (err) {
      console.error(err);
    }
    setTriggering(false);
  };

  const activeNiches = niches.filter(n => n.enabled);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Run History</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Collection runs and their results</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={selectedNiche}
            onChange={(e) => setSelectedNiche(e.target.value)}
            className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {activeNiches.map(n => (
              <option key={n.id} value={n.id}>{n.name}</option>
            ))}
          </select>
          <button
            onClick={handleTrigger}
            disabled={triggering || activeNiches.length === 0}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-lg text-sm font-medium transition-colors"
          >
            {triggering ? <Loader className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            {triggering ? 'Running...' : 'Trigger Run'}
          </button>
        </div>
      </div>

      {/* Running indicator */}
      {triggering && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-xl p-4 flex items-center gap-3">
          <Loader className="w-5 h-5 text-yellow-500 animate-spin" />
          <div>
            <p className="font-medium text-yellow-800 dark:text-yellow-300">Collection in progress...</p>
            <p className="text-sm text-yellow-600 dark:text-yellow-400">Scanning sources for relevant content. This typically takes 5-15 minutes.</p>
          </div>
        </div>
      )}

      {/* Runs list */}
      {runs.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400">No runs yet. Trigger your first collection run above.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <div
              key={run.id}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden"
            >
              <button
                onClick={() => setExpandedRun(expandedRun === run.id ? null : run.id)}
                className="w-full p-4 flex items-center gap-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  run.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30' :
                  run.status === 'running' ? 'bg-yellow-100 dark:bg-yellow-900/30' :
                  'bg-red-100 dark:bg-red-900/30'
                }`}>
                  {run.status === 'completed' ? <CheckCircle className="w-4 h-4 text-green-500" /> :
                   run.status === 'running' ? <Loader className="w-4 h-4 text-yellow-500 animate-spin" /> :
                   <XCircle className="w-4 h-4 text-red-500" />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white">{run.nicheName}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {new Date(run.startedAt).toLocaleString()} · {run.totalItems} items
                    {run.completedAt && ` · ${Math.round((new Date(run.completedAt).getTime() - new Date(run.startedAt).getTime()) / 1000)}s`}
                  </p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                  run.status === 'completed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                  run.status === 'running' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400' :
                  'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
                }`}>
                  {run.status}
                </span>
                {expandedRun === run.id ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
              </button>

              {expandedRun === run.id && (
                <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700 pt-4 space-y-4">
                  {/* Platform stats */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {Object.entries(run.stats).map(([platform, stats]) => (
                      <div key={platform} className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                        <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{platform}</p>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.collected}</p>
                        <p className="text-xs text-gray-400">
                          {stats.errors > 0 ? `${stats.errors} errors · ` : ''}{stats.duration.toFixed(1)}s
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Errors */}
                  {run.errors.length > 0 && (
                    <div>
                      <p className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">Errors ({run.errors.length})</p>
                      <ul className="space-y-1">
                        {run.errors.map((err, i) => (
                          <li key={i} className="text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
                            <XCircle className="w-3 h-3 text-red-400 mt-1 shrink-0" />
                            {err}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
