import { useEffect, useState } from 'react';
import { ThumbsUp, ThumbsDown, TrendingUp } from 'lucide-react';
import { getFeedbackStats } from '../services/api';
import { FeedbackStats, Platform } from '../types';

const platformLabels: Record<Platform, string> = {
  reddit: 'Reddit',
  quora: 'Quora',
  linkedin: 'LinkedIn',
  instagram: 'Instagram',
  x: 'X (Twitter)',
  facebook: 'Facebook',
  blogs: 'Blogs/RSS',
  youtube: 'YouTube',
};

const platformColors: Record<string, string> = {
  reddit: '#ff4500',
  blogs: '#f97316',
  youtube: '#ff0000',
  quora: '#b92b27',
  linkedin: '#0077b5',
  x: '#1da1f2',
  instagram: '#e4405f',
  facebook: '#1877f2',
};

export default function Feedback() {
  const [stats, setStats] = useState<FeedbackStats | null>(null);

  useEffect(() => {
    getFeedbackStats().then(setStats);
  }, []);

  if (!stats) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full" />
      </div>
    );
  }

  const total = stats.totalUp + stats.totalDown;
  const upPercent = total > 0 ? Math.round((stats.totalUp / total) * 100) : 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Feedback Stats</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Community feedback on newsletter stories</p>
      </div>

      {/* Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{total}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Total Votes</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
          <div className="flex items-center justify-center gap-2">
            <ThumbsUp className="w-5 h-5 text-green-500" />
            <p className="text-3xl font-bold text-green-600 dark:text-green-400">{stats.totalUp}</p>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Thumbs Up ({upPercent}%)</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 text-center">
          <div className="flex items-center justify-center gap-2">
            <ThumbsDown className="w-5 h-5 text-red-500" />
            <p className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.totalDown}</p>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Thumbs Down ({100 - upPercent}%)</p>
        </div>
      </div>

      {/* By platform */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Feedback by Platform</h3>
        {Object.keys(stats.byPlatform).length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            No feedback yet. Vote on stories in the newsletter preview to see stats here.
          </p>
        ) : (
          <div className="space-y-3">
            {Object.entries(stats.byPlatform).map(([platform, data]) => (
              <div key={platform} className="flex items-center gap-3">
                <div className="w-20 text-sm font-medium capitalize" style={{ color: platformColors[platform] }}>
                  {platformLabels[platform as Platform] || platform}
                </div>
                <div className="flex-1 flex items-center gap-2">
                  <div className="flex-1 h-6 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden flex">
                    <div
                      className="h-full bg-green-400 transition-all"
                      style={{ width: `${data.up + data.down > 0 ? (data.up / (data.up + data.down)) * 100 : 0}%` }}
                    />
                    <div
                      className="h-full bg-red-400 transition-all"
                      style={{ width: `${data.up + data.down > 0 ? (data.down / (data.up + data.down)) * 100 : 0}%` }}
                    />
                  </div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 w-20 text-right">
                  <span className="text-green-600">↑{data.up}</span> / <span className="text-red-600">↓{data.down}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Top rated */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
        <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-500" /> Top Rated Stories
        </h3>
        {stats.topRated.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            No upvoted stories yet.
          </p>
        ) : (
          <div className="space-y-2">
            {stats.topRated.map((story, i) => (
              <div key={story.id} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <span className="text-sm font-bold text-gray-400 w-6">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{story.title}</p>
                  <p className="text-xs text-gray-400">{story.author} · {story.source}</p>
                </div>
                <div className="flex items-center gap-1 text-green-600 dark:text-green-400">
                  <ThumbsUp className="w-3 h-3" />
                  <span className="text-xs font-medium">liked</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
