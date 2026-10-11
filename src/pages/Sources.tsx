import { useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, ExternalLink, Settings, HelpCircle } from 'lucide-react';
import { PLATFORM_CAPABILITIES, getWorkingPlatforms, getLimitedPlatforms } from '../data/platformCapabilities';
import { PlatformCapability } from '../types';

export default function Sources() {
  const [selectedPlatform, setSelectedPlatform] = useState<PlatformCapability | null>(null);
  const [showSetupGuide, setShowSetupGuide] = useState(false);

  const workingPlatforms = getWorkingPlatforms();
  const limitedPlatforms = getLimitedPlatforms();

  const getStatusBadge = (status: PlatformCapability['status']) => {
    switch (status) {
      case 'fully_supported':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle className="w-3 h-3" />
            Works Now
          </span>
        );
      case 'paid_only':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
            <AlertCircle className="w-3 h-3" />
            Paid Required
          </span>
        );
      case 'restricted':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
            <XCircle className="w-3 h-3" />
            Restricted
          </span>
        );
      case 'no_api':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
            <XCircle className="w-3 h-3" />
            No API
          </span>
        );
      default:
        return null;
    }
  };

  const getDifficultyBadge = (difficulty: PlatformCapability['setupDifficulty']) => {
    const colors = {
      easy: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      medium: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
      hard: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
      expert: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Data Sources</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Connect your content sources. We're transparent about what works and what doesn't.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ready to Use</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{workingPlatforms.length}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border-l-4 border-yellow-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Paid/Limited</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {PLATFORM_CAPABILITIES.filter(p => p.status === 'paid_only').length}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Not Available</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {PLATFORM_CAPABILITIES.filter(p => !p.canCollect).length}
              </p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Working Platforms */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Ready to Connect
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            These sources work out of the box with free API access
          </p>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {workingPlatforms.map((platform) => (
            <div
              key={platform.platform}
              className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
              onClick={() => {
                setSelectedPlatform(platform);
                setShowSetupGuide(true);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0"
                    style={{ backgroundColor: platform.color }}
                  >
                    {platform.label.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {platform.label}
                      </h3>
                      {getStatusBadge(platform.status)}
                      {getDifficultyBadge(platform.setupDifficulty)}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {platform.description}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        💰 {platform.cost}
                      </span>
                      <span className="flex items-center gap-1">
                        ⚡ {platform.setupDifficulty} setup
                      </span>
                    </div>
                  </div>
                </div>
                <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium text-sm flex items-center gap-1">
                  Setup Guide
                  <ExternalLink className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Limited/Restricted Platforms */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-500" />
            Limited or Restricted Access
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            These platforms have significant limitations or require paid plans
          </p>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {limitedPlatforms.map((platform) => (
            <div
              key={platform.platform}
              className="p-6 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer opacity-75"
              onClick={() => {
                setSelectedPlatform(platform);
                setShowSetupGuide(true);
              }}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4 flex-1">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0 grayscale"
                    style={{ backgroundColor: platform.color }}
                  >
                    {platform.label.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {platform.label}
                      </h3>
                      {getStatusBadge(platform.status)}
                      {getDifficultyBadge(platform.setupDifficulty)}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {platform.description}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        💰 {platform.cost}
                      </span>
                      <span className="flex items-center gap-1">
                        ⚠️ {platform.setupDifficulty} setup
                      </span>
                    </div>
                  </div>
                </div>
                <button className="text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium text-sm flex items-center gap-1">
                  Details
                  <HelpCircle className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Setup Guide Modal */}
      {showSetupGuide && selectedPlatform && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold text-lg"
                    style={{ backgroundColor: selectedPlatform.color }}
                  >
                    {selectedPlatform.label.charAt(0)}
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                      {selectedPlatform.label} Setup Guide
                    </h2>
                    {getStatusBadge(selectedPlatform.status)}
                  </div>
                </div>
                <button
                  onClick={() => setShowSetupGuide(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Description */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Overview</h3>
                <p className="text-gray-600 dark:text-gray-400">{selectedPlatform.description}</p>
              </div>

              {/* Requirements */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">What You Need</h3>
                <ul className="space-y-2">
                  {selectedPlatform.requirements.map((req, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="text-blue-500 mt-0.5">•</span>
                      {req}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Cost */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Cost</h3>
                <p className="text-gray-600 dark:text-gray-400">{selectedPlatform.cost}</p>
              </div>

              {/* Setup Difficulty */}
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Setup Difficulty</h3>
                <div className="flex items-center gap-2">
                  {getDifficultyBadge(selectedPlatform.setupDifficulty)}
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedPlatform.setupDifficulty === 'easy' && 'Takes 5-10 minutes'}
                    {selectedPlatform.setupDifficulty === 'medium' && 'Takes 15-30 minutes'}
                    {selectedPlatform.setupDifficulty === 'hard' && 'Takes 1-2 hours, requires approval'}
                    {selectedPlatform.setupDifficulty === 'expert' && 'Requires technical expertise'}
                  </span>
                </div>
              </div>

              {/* Status-specific guidance */}
              {selectedPlatform.status === 'fully_supported' && (
                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                  <h3 className="font-semibold text-green-900 dark:text-green-300 mb-2 flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    Ready to Set Up
                  </h3>
                  <p className="text-sm text-green-700 dark:text-green-400">
                    This source is fully supported and ready to connect. Click "Configure" to add your API credentials.
                  </p>
                  <button className="mt-3 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium text-sm transition-colors">
                    Configure Now
                  </button>
                </div>
              )}

              {selectedPlatform.status === 'paid_only' && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                  <h3 className="font-semibold text-yellow-900 dark:text-yellow-300 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    Paid Plan Required
                  </h3>
                  <p className="text-sm text-yellow-700 dark:text-yellow-400">
                    This platform requires a paid subscription. Consider using RSS feeds as a free alternative to collect similar content.
                  </p>
                </div>
              )}

              {(selectedPlatform.status === 'restricted' || selectedPlatform.status === 'no_api') && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                  <h3 className="font-semibold text-red-900 dark:text-red-300 mb-2 flex items-center gap-2">
                    <XCircle className="w-5 h-5" />
                    Not Currently Available
                  </h3>
                  <p className="text-sm text-red-700 dark:text-red-400 mb-3">
                    {selectedPlatform.status === 'no_api'
                      ? 'This platform does not provide an official API. Web scraping violates their Terms of Service.'
                      : 'This platform has restricted API access and requires special approval or partnership.'}
                  </p>
                  <p className="text-sm text-red-700 dark:text-red-400">
                    <strong>Alternative:</strong> Use RSS feeds to collect content from blogs and news sites covering this platform.
                  </p>
                </div>
              )}

              {/* Recommendations */}
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">💡 Recommendation</h3>
                <p className="text-sm text-blue-700 dark:text-blue-400">
                  For the best experience, start with <strong>Blogs & RSS Feeds</strong> (no setup required), 
                  then add <strong>Reddit</strong> and <strong>YouTube</strong> for comprehensive coverage.
                </p>
              </div>
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

      {/* Help Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2 flex items-center gap-2">
          <HelpCircle className="w-5 h-5" />
          Need Help Choosing Sources?
        </h3>
        <p className="text-sm text-blue-700 dark:text-blue-400 mb-3">
          Not sure which sources to connect? Here's what we recommend:
        </p>
        <ul className="space-y-2 text-sm text-blue-700 dark:text-blue-400">
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">✓</span>
            <span><strong>Start with RSS feeds</strong> — Add your favorite blogs and news sites. No API keys needed.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">✓</span>
            <span><strong>Add Reddit</strong> — Great for community discussions and trending topics. Free and easy to set up.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">✓</span>
            <span><strong>Add YouTube</strong> — Perfect for video content and tutorials. Free with generous limits.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-blue-500 mt-0.5">⚠</span>
            <span><strong>Skip restricted platforms</strong> — LinkedIn, Instagram, Facebook, and X have limited or paid API access.</span>
          </li>
        </ul>
        <div className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-400 mb-2">
            <strong>Want trending content from restricted platforms?</strong> We've compiled legitimate alternatives!
          </p>
          <a
            href="/alternative-sources"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
          >
            View Alternative Sources
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </div>
    </div>
  );
}
