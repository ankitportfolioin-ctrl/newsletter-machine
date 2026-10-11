import { useState } from 'react';
import { Play, Loader2, CheckCircle2, XCircle, Rss, Clock, ExternalLink, Zap } from 'lucide-react';

interface ScrapedItem {
  source: string;
  title: string;
  link: string;
  author: string;
  pubDate: string;
  description: string;
  keywords: string[];
}

interface ScrapeResult {
  source: string;
  url: string;
  status: 'success' | 'error';
  items: ScrapedItem[];
  error?: string;
  fetchTime: number;
}

// Public RSS-to-JSON API (free, no CORS issues, no API key needed)
const RSS2JSON_BASE = 'https://api.rss2json.com/v1/api.json?rss_url=';

// Real live RSS feeds to scrape
const LIVE_FEEDS = [
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/' },
  { name: 'Hacker News', url: 'https://hnrss.org/frontpage' },
  { name: 'The Verge', url: 'https://www.theverge.com/rss/index.xml' },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index' },
  { name: 'Reddit r/technology', url: 'https://www.reddit.com/r/technology/.rss' },
  { name: 'Wired', url: 'https://www.wired.com/feed/rss' },
];

// Keywords to filter (simulating an "AI & Tech" niche)
const KEYWORDS = ['AI', 'artificial intelligence', 'machine learning', 'GPT', 'LLM', 'tech', 'technology', 'startup', 'software'];

export default function LiveScrapeDemo() {
  const [isScraping, setIsScraping] = useState(false);
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [allItems, setAllItems] = useState<ScrapedItem[]>([]);
  const [totalTime, setTotalTime] = useState<number | null>(null);
  const [hasRun, setHasRun] = useState(false);

  const startScraping = async () => {
    setIsScraping(true);
    setResults([]);
    setAllItems([]);
    setHasRun(true);
    const startTime = Date.now();
    const newResults: ScrapeResult[] = [];

    for (const feed of LIVE_FEEDS) {
      const fetchStart = Date.now();
      try {
        const response = await fetch(`${RSS2JSON_BASE}${encodeURIComponent(feed.url)}&count=20`);
        const data = await response.json();
        const fetchTime = Date.now() - fetchStart;

        if (data.status === 'ok' && data.items) {
          // Filter by keywords
          const relevantItems = data.items
            .filter((item: any) => {
              const text = `${item.title || ''} ${item.description || ''}`.toLowerCase();
              return KEYWORDS.some(kw => text.includes(kw.toLowerCase()));
            })
            .slice(0, 10)
            .map((item: any) => ({
              source: feed.name,
              title: item.title || 'Untitled',
              link: item.link || feed.url,
              author: item.author || feed.name,
              pubDate: item.pubDate || 'Unknown',
              description: (item.description || '').replace(/<[^>]*>/g, '').substring(0, 300),
              keywords: KEYWORDS.filter(kw =>
                `${item.title || ''} ${item.description || ''}`.toLowerCase().includes(kw.toLowerCase())
              ),
            }));

          const result: ScrapeResult = {
            source: feed.name,
            url: feed.url,
            status: 'success',
            items: relevantItems,
            fetchTime,
          };
          newResults.push(result);
          setResults([...newResults]);
        } else {
          newResults.push({
            source: feed.name,
            url: feed.url,
            status: 'error',
            items: [],
            error: data.message || 'Feed returned no items',
            fetchTime: Date.now() - fetchStart,
          });
          setResults([...newResults]);
        }
      } catch (error: any) {
        newResults.push({
          source: feed.name,
          url: feed.url,
          status: 'error',
          items: [],
          error: error.message,
          fetchTime: Date.now() - fetchStart,
        });
        setResults([...newResults]);
      }
    }

    const totalItems = newResults.flatMap(r => r.items);
    setAllItems(totalItems);
    setTotalTime(Date.now() - startTime);
    setIsScraping(false);
  };

  const successfulFeeds = results.filter(r => r.status === 'success').length;
  const failedFeeds = results.filter(r => r.status === 'error').length;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <Zap className="w-8 h-8 text-yellow-500" />
          Live Real-Time Scraping Demo
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Click the button below to scrape <strong>real content from live websites</strong> right now.
          No fake data. No pre-generated content. Just live HTTP requests.
        </p>
      </div>

      {/* Status Banner */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 mt-0.5" />
          <div className="text-sm text-green-800 dark:text-green-300">
            <p className="font-semibold mb-1">✅ Real-Time Scraping is ENABLED</p>
            <p className="text-green-700 dark:text-green-400">
              This demo makes <strong>actual HTTP requests</strong> to live RSS feeds. 
              Every result you see below is fetched in real-time from the internet.
            </p>
          </div>
        </div>
      </div>

      {/* Sources Being Scraped */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-5">
        <h2 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
          <Rss className="w-5 h-5 text-orange-500" />
          Live Sources ({LIVE_FEEDS.length} feeds)
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
          {LIVE_FEEDS.map((feed) => {
            const result = results.find(r => r.source === feed.name);
            return (
              <div
                key={feed.name}
                className={`flex items-center gap-2 p-2 rounded text-sm ${
                  !result
                    ? 'bg-gray-50 dark:bg-gray-700/50'
                    : result.status === 'success'
                    ? 'bg-green-50 dark:bg-green-900/20'
                    : 'bg-red-50 dark:bg-red-900/20'
                }`}
              >
                {isScraping && !result ? (
                  <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                ) : result?.status === 'success' ? (
                  <CheckCircle2 className="w-4 h-4 text-green-500" />
                ) : result?.status === 'error' ? (
                  <XCircle className="w-4 h-4 text-red-500" />
                ) : (
                  <div className="w-4 h-4 rounded-full bg-gray-300 dark:bg-gray-600" />
                )}
                <span className="font-medium text-gray-900 dark:text-white">{feed.name}</span>
                {result?.status === 'success' && (
                  <span className="ml-auto text-xs text-green-600 dark:text-green-400">
                    {result.items.length} items · {result.fetchTime}ms
                  </span>
                )}
                {result?.status === 'error' && (
                  <span className="ml-auto text-xs text-red-600 dark:text-red-400">Failed</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Scrape Button */}
      <div className="flex justify-center">
        <button
          onClick={startScraping}
          disabled={isScraping}
          className="flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-xl font-semibold text-lg shadow-lg transition-all disabled:cursor-not-allowed"
        >
          {isScraping ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Scraping Live Content...
            </>
          ) : (
            <>
              <Play className="w-6 h-6" />
              {hasRun ? 'Scrape Again (Fresh Data)' : 'Start Real-Time Scraping'}
            </>
          )}
        </button>
      </div>

      {/* Results */}
      {hasRun && (
        <>
          {/* Stats */}
          {totalTime !== null && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 text-center">
                <Clock className="w-6 h-6 text-blue-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{(totalTime! / 1000).toFixed(2)}s</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Total Time</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 text-center">
                <CheckCircle2 className="w-6 h-6 text-green-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{successfulFeeds}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Successful Feeds</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 text-center">
                <XCircle className="w-6 h-6 text-red-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{failedFeeds}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Failed Feeds</p>
              </div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 text-center">
                <Rss className="w-6 h-6 text-purple-500 mx-auto mb-1" />
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{allItems.length}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">Items Collected</p>
              </div>
            </div>
          )}

          {/* Live Items */}
          {allItems.length > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
              <div className="px-5 py-4 border-b border-gray-200 dark:border-gray-700">
                <h2 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-yellow-500" />
                  Live Scraped Content ({allItems.length} items)
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Filtered by keywords: {KEYWORDS.join(', ')}
                </p>
              </div>
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {allItems.map((item, idx) => (
                  <div key={idx} className="p-5 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-start gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium">
                            {item.source}
                          </span>
                          {item.keywords.slice(0, 3).map((kw, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400">
                              {kw}
                            </span>
                          ))}
                        </div>
                        <h3 className="font-semibold text-gray-900 dark:text-white text-base">
                          {item.title}
                        </h3>
                        {item.description && (
                          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                            {item.description}
                          </p>
                        )}
                        <div className="flex items-center gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
                          <span>by {item.author}</span>
                          <span>·</span>
                          <span>{new Date(item.pubDate).toLocaleString()}</span>
                          <a
                            href={item.link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-1 text-blue-600 dark:text-blue-400 hover:underline ml-auto"
                          >
                            View Source <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Errors */}
          {failedFeeds > 0 && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <h3 className="font-semibold text-red-900 dark:text-red-300 mb-2">Failed Feeds</h3>
              <ul className="space-y-1 text-sm text-red-700 dark:text-red-400">
                {results.filter(r => r.status === 'error').map((r, i) => (
                  <li key={i}>
                    <strong>{r.source}:</strong> {r.error}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {allItems.length === 0 && !isScraping && (
            <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 text-center">
              <p className="text-yellow-800 dark:text-yellow-300">
                Scraping completed but no items matched the keywords. Try different keywords or feeds.
              </p>
            </div>
          )}
        </>
      )}

      {/* Explanation */}
      <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-5">
        <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2 flex items-center gap-2">
          🔬 How This Works
        </h3>
        <ol className="space-y-2 text-sm text-blue-800 dark:text-blue-300 list-decimal list-inside">
          <li>When you click the button, the browser makes <strong>real HTTP GET requests</strong> to live RSS feeds</li>
          <li>Each feed is fetched from its actual URL (e.g., <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">techcrunch.com/feed/</code>)</li>
          <li>The RSS XML is parsed into JSON using the rss2json.com API (free, no key needed)</li>
          <li>Items are filtered by keywords (AI, tech, startup, etc.)</li>
          <li>Results are displayed in real-time as each feed completes</li>
          <li>All data is <strong>100% live</strong> — refresh and scrape again to see new content</li>
        </ol>
        <p className="mt-3 text-sm text-blue-700 dark:text-blue-400">
          <strong>Note:</strong> In production, this same scraping logic runs on the backend server 
          using the <code className="bg-blue-100 dark:bg-blue-900/40 px-1 rounded">rss-parser</code> library, 
          with direct HTTP requests (no proxy needed).
        </p>
      </div>
    </div>
  );
}
