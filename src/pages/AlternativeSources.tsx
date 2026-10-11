import { useState } from 'react';
import { ExternalLink, CheckCircle, AlertCircle, Zap, BookOpen, TrendingUp, Rss, MessageCircle } from 'lucide-react';
import { ALTERNATIVE_SOURCES, RECOMMENDED_RSS_FEEDS, AlternativeSource } from '../data/alternativeSources';

export default function AlternativeSources() {
  const [selectedSource, setSelectedSource] = useState<AlternativeSource | null>(null);
  const [showSetupGuide, setShowSetupGuide] = useState(false);

  const getLegalBadge = (status: AlternativeSource['legalStatus']) => {
    switch (status) {
      case 'fully_legal':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle className="w-3 h-3" />
            Fully Legal
          </span>
        );
      case 'gray_area':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
            <AlertCircle className="w-3 h-3" />
            Gray Area
          </span>
        );
      case 'tos_violation':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
            <AlertCircle className="w-3 h-3" />
            ToS Violation
          </span>
        );
    }
  };

  const getCostBadge = (cost: AlternativeSource['cost']) => {
    return cost === 'free' ? (
      <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
        Free
      </span>
    ) : (
      <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
        Paid
      </span>
    );
  };

  const getDifficultyBadge = (difficulty: AlternativeSource['setupDifficulty']) => {
    const colors = {
      easy: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    };
    return (
      <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[difficulty]}`}>
        {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Alternative Ways to Get Trending Content
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Can't access Twitter, LinkedIn, Instagram, or Facebook directly? Here are legitimate alternatives.
        </p>
      </div>

      {/* Quick Summary */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-blue-900 dark:text-blue-300 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5" />
          The Short Answer
        </h2>
        <div className="space-y-2 text-sm text-blue-800 dark:text-blue-300">
          <p>
            <strong>Yes, there are alternatives!</strong> While you can't directly access restricted platforms' APIs, 
            you can use these legitimate methods:
          </p>
          <ul className="space-y-1 ml-4">
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">✓</span>
              <span><strong>RSSHub</strong> - Converts social media to RSS feeds (self-hosted, free)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">✓</span>
              <span><strong>Google Trends</strong> - Track trending topics globally (free API)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">✓</span>
              <span><strong>Google Alerts</strong> - Monitor keywords across the web (free, RSS output)</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">✓</span>
              <span><strong>Reddit Discussions</strong> - Monitor subreddits that discuss these platforms</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-500 mt-0.5">✓</span>
              <span><strong>Tech News RSS</strong> - Read coverage from major publications</span>
            </li>
          </ul>
        </div>
      </div>

      {/* Alternative Sources Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ALTERNATIVE_SOURCES.map((source) => (
          <div
            key={source.id}
            className={`bg-white dark:bg-gray-800 rounded-lg shadow border-2 transition-all cursor-pointer hover:shadow-lg ${
              source.recommended ? 'border-green-300 dark:border-green-700' : 'border-gray-200 dark:border-gray-700'
            }`}
            onClick={() => {
              setSelectedSource(source);
              setShowSetupGuide(true);
            }}
          >
            <div className="p-5">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {source.name}
                </h3>
                {source.recommended && (
                  <span className="px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    Recommended
                  </span>
                )}
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {source.description}
              </p>

              <div className="flex items-center gap-2 flex-wrap mb-3">
                {getCostBadge(source.cost)}
                {getDifficultyBadge(source.setupDifficulty)}
                {getLegalBadge(source.legalStatus)}
              </div>

              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Works with:</span>
                <div className="flex gap-1 flex-wrap">
                  {source.platforms.slice(0, 4).map((platform) => (
                    <span
                      key={platform}
                      className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 capitalize"
                    >
                      {platform}
                    </span>
                  ))}
                  {source.platforms.length > 4 && (
                    <span className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                      +{source.platforms.length - 4}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Start Recommendations */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-6 h-6 text-blue-500" />
          Quick Start: Get Trending Content Now
        </h2>
        
        <div className="space-y-4">
          {/* Option 1: Google Trends */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Option 1: Google Trends (Easiest)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  See what's trending globally right now. No setup required.
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Free</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">2 minutes</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Fully Legal</span>
                </div>
                <a
                  href="https://trends.google.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                >
                  Open Google Trends <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>

          {/* Option 2: Google Alerts */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                <Rss className="w-5 h-5 text-green-600 dark:text-green-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Option 2: Google Alerts (Keyword Monitoring)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Get RSS feeds when new content matches your keywords.
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Free</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">5 minutes</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Fully Legal</span>
                </div>
                <a
                  href="https://www.google.com/alerts"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 mt-2 text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                >
                  Set up Google Alerts <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>

          {/* Option 3: Reddit Discussions */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                <MessageCircle className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Option 3: Reddit Discussions (Community Insights)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Monitor subreddits that discuss Twitter, LinkedIn, Instagram trends.
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Free</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Already set up!</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Fully Legal</span>
                </div>
                <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                  <strong>Recommended subreddits:</strong> r/twitter, r/linkedin, r/instagram, r/socialmedia
                </div>
              </div>
            </div>
          </div>

          {/* Option 4: Tech News RSS */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                <BookOpen className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Option 4: Tech News RSS (Editorial Coverage)
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Read coverage from major tech publications.
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Free</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Already set up!</span>
                  <span className="px-2 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">Fully Legal</span>
                </div>
                <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                  <strong>Recommended feeds:</strong> TechCrunch, The Verge, Wired, Social Media Today
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommended RSS Feeds */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Rss className="w-6 h-6 text-orange-500" />
          Ready-to-Use RSS Feeds
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Copy these URLs and add them to your niches. No setup required!
        </p>

        <div className="space-y-4">
          {/* Tech News */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Tech News (Covers All Platforms)</h3>
            <div className="space-y-1">
              {RECOMMENDED_RSS_FEEDS.techNews.map((feed) => (
                <div key={feed.url} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-sm">
                  <span className="text-gray-900 dark:text-white">{feed.name}</span>
                  <code className="text-xs text-gray-600 dark:text-gray-400 font-mono">{feed.url}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Social Media News */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Social Media News</h3>
            <div className="space-y-1">
              {RECOMMENDED_RSS_FEEDS.socialMediaNews.map((feed) => (
                <div key={feed.url} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-sm">
                  <span className="text-gray-900 dark:text-white">{feed.name}</span>
                  <code className="text-xs text-gray-600 dark:text-gray-400 font-mono">{feed.url}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Reddit Discussions */}
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Reddit Discussions (Platform-Specific)</h3>
            <div className="space-y-1">
              {RECOMMENDED_RSS_FEEDS.redditDiscussions.map((feed) => (
                <div key={feed.url} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded text-sm">
                  <span className="text-gray-900 dark:text-white">{feed.name}</span>
                  <code className="text-xs text-gray-600 dark:text-gray-400 font-mono">{feed.url}</code>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Setup Guide Modal */}
      {showSetupGuide && selectedSource && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                    {selectedSource.name}
                  </h2>
                  <div className="flex items-center gap-2 mt-2">
                    {getCostBadge(selectedSource.cost)}
                    {getDifficultyBadge(selectedSource.setupDifficulty)}
                    {getLegalBadge(selectedSource.legalStatus)}
                  </div>
                </div>
                <button
                  onClick={() => setShowSetupGuide(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <AlertCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Description</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">{selectedSource.description}</p>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Requirements</h3>
                <ul className="space-y-1">
                  {selectedSource.requirements.map((req, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="text-blue-500 mt-0.5">•</span>
                      {req}
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Limitations</h3>
                <ul className="space-y-1">
                  {selectedSource.limitations.map((limitation, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="text-yellow-500 mt-0.5">⚠</span>
                      {limitation}
                    </li>
                  ))}
                </ul>
              </div>

              {selectedSource.url && (
                <div>
                  <a
                    href={selectedSource.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
                  >
                    Visit Website <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setShowSetupGuide(false)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
