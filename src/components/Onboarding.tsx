import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, ArrowRight, Rss, Youtube, MessageCircle, Sparkles } from 'lucide-react';

interface OnboardingProps {
  onComplete: () => void;
}

export default function Onboarding({ onComplete }: OnboardingProps) {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const totalSteps = 4;

  const handleComplete = () => {
    onComplete();
    navigate('/niches');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Step {step} of {totalSteps}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {Math.round((step / totalSteps) * 100)}% complete
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        {/* Step content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8">
          {step === 1 && (
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome to Newsletter Machine!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Let's get you set up in just a few minutes. We'll help you create your first newsletter niche and connect your content sources.
              </p>
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                <p className="text-sm text-blue-700 dark:text-blue-400">
                  <strong>What you'll need:</strong> Just a few minutes and your favorite blogs or topics you want to follow. 
                  No technical skills required!
                </p>
              </div>
              <button
                onClick={() => setStep(2)}
                className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
              >
                Let's Get Started
                <ArrowRight className="w-5 h-5" />
              </button>
            </div>
          )}

          {step === 2 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                Choose Your Content Sources
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Select the platforms you want to collect content from. Don't worry — you can always add more later!
              </p>

              <div className="space-y-3 mb-6">
                <div className="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <Rss className="w-6 h-6 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Blogs & RSS Feeds</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Add any blog or website with an RSS feed. <strong>No API keys needed!</strong>
                    </p>
                    <span className="inline-block mt-2 px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-xs font-medium rounded">
                      ✓ Recommended - Start here
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
                  <MessageCircle className="w-6 h-6 text-orange-600 dark:text-orange-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">Reddit</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Collect posts from subreddits. Free API access with a Reddit account.
                    </p>
                    <span className="inline-block mt-2 px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400 text-xs font-medium rounded">
                      ⚡ Easy setup - 5 minutes
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <Youtube className="w-6 h-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">YouTube</h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      Search and collect video content. Free Google API with generous limits.
                    </p>
                    <span className="inline-block mt-2 px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 text-xs font-medium rounded">
                      ⚡ Easy setup - 5 minutes
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
                <p className="text-sm text-yellow-700 dark:text-yellow-400">
                  <strong>Note:</strong> LinkedIn, Instagram, Facebook, X (Twitter), and Quora have limited or paid API access. 
                  We'll show you workarounds in the next step.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(1)}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(3)}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  Continue
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                About Restricted Platforms
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                We believe in transparency. Here's the truth about social media platforms:
              </p>

              <div className="space-y-3 mb-6">
                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    ❌ LinkedIn, Instagram, Facebook
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    These platforms heavily restrict API access. You need special partnership approval or can only access your own business accounts.
                  </p>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    💰 X (Twitter)
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Twitter API now requires a paid subscription ($100-$5,000/month) for most features.
                  </p>
                </div>

                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
                    ❌ Quora
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    No official API available. Web scraping violates their Terms of Service.
                  </p>
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">💡 The Workaround</h3>
                <p className="text-sm text-blue-700 dark:text-blue-400">
                  Use <strong>RSS feeds</strong> to collect content from blogs and news sites that cover these platforms. 
                  For example, add TechCrunch, The Verge, or platform-specific blogs to get coverage without API restrictions.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(2)}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep(4)}
                  className="flex-1 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  Continue
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                You're All Set!
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Ready to create your first newsletter? Let's start by setting up your first niche.
              </p>

              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-6 text-left">
                <h3 className="font-semibold text-green-900 dark:text-green-300 mb-2">What's Next?</h3>
                <ul className="space-y-2 text-sm text-green-700 dark:text-green-400">
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">1.</span>
                    <span>Create your first niche (topic you want to follow)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">2.</span>
                    <span>Add RSS feeds from your favorite blogs</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">3.</span>
                    <span>Optionally connect Reddit or YouTube</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">4.</span>
                    <span>Generate your first newsletter!</span>
                  </li>
                </ul>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setStep(3)}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-lg font-medium transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={handleComplete}
                  className="flex-1 px-6 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
                >
                  Create My First Niche
                  <ArrowRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Skip option */}
        {step < totalSteps && (
          <div className="text-center mt-4">
            <button
              onClick={handleComplete}
              className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            >
              Skip onboarding and go to dashboard
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
