export interface AlternativeSource {
  id: string;
  name: string;
  description: string;
  platforms: string[];
  cost: 'free' | 'paid';
  setupDifficulty: 'easy' | 'medium' | 'hard';
  requirements: string[];
  limitations: string[];
  legalStatus: 'fully_legal' | 'gray_area' | 'tos_violation';
  recommended: boolean;
  url?: string;
}

export const ALTERNATIVE_SOURCES: AlternativeSource[] = [
  {
    id: 'rsshub',
    name: 'RSSHub (Self-Hosted)',
    description: 'Open-source tool that converts social media to RSS feeds. Supports Twitter, Instagram, LinkedIn, and more.',
    platforms: ['twitter', 'instagram', 'linkedin', 'facebook', 'quora', 'tiktok', 'reddit'],
    cost: 'free',
    setupDifficulty: 'medium',
    requirements: [
      'Docker or Node.js server',
      'Basic technical knowledge',
      '5-10 minutes to set up',
    ],
    limitations: [
      'Requires self-hosting',
      'Some routes may break when platforms change',
      'Rate limits apply',
    ],
    legalStatus: 'gray_area',
    recommended: true,
    url: 'https://github.com/DIYgod/RSSHub',
  },
  {
    id: 'google-trends',
    name: 'Google Trends',
    description: 'Free API to track trending topics globally. Shows what people are searching for right now.',
    platforms: ['trending-topics'],
    cost: 'free',
    setupDifficulty: 'easy',
    requirements: [
      'Google account',
      'API key (free tier available)',
    ],
    limitations: [
      'Shows search interest, not actual content',
      'No direct links to posts',
      'Data is aggregated, not specific posts',
    ],
    legalStatus: 'fully_legal',
    recommended: true,
    url: 'https://trends.google.com/',
  },
  {
    id: 'google-alerts',
    name: 'Google Alerts',
    description: 'Free keyword monitoring that sends RSS feeds when new content matches your keywords across the web.',
    platforms: ['web', 'news', 'blogs'],
    cost: 'free',
    setupDifficulty: 'easy',
    requirements: [
      'Google account',
      'Keywords to monitor',
    ],
    limitations: [
      'Only monitors indexed content',
      'May miss real-time social media posts',
      'Delayed by hours or days',
    ],
    legalStatus: 'fully_legal',
    recommended: true,
    url: 'https://www.google.com/alerts',
  },
  {
    id: 'reddit-proxy',
    name: 'Reddit as Discussion Proxy',
    description: 'Monitor subreddits that discuss Twitter, LinkedIn, Instagram content. Get insights without direct API access.',
    platforms: ['twitter', 'linkedin', 'instagram', 'facebook'],
    cost: 'free',
    setupDifficulty: 'easy',
    requirements: [
      'Reddit account',
      'API credentials (free)',
    ],
    limitations: [
      'Second-hand information',
      'May miss original posts',
      'Community bias',
    ],
    legalStatus: 'fully_legal',
    recommended: true,
  },
  {
    id: 'news-aggregators',
    name: 'Tech News RSS Feeds',
    description: 'RSS feeds from major tech publications that cover all social media platforms.',
    platforms: ['twitter', 'linkedin', 'instagram', 'facebook', 'quora'],
    cost: 'free',
    setupDifficulty: 'easy',
    requirements: [
      'Just paste RSS URLs',
    ],
    limitations: [
      'Editorial coverage, not raw posts',
      'Delayed reporting',
      'Limited to major platforms',
    ],
    legalStatus: 'fully_legal',
    recommended: true,
  },
  {
    id: 'rss-bridge',
    name: 'RSS-Bridge',
    description: 'Another open-source tool similar to RSSHub. Generates RSS feeds from websites and social media.',
    platforms: ['twitter', 'instagram', 'facebook', 'linkedin'],
    cost: 'free',
    setupDifficulty: 'medium',
    requirements: [
      'PHP server',
      'Basic technical knowledge',
    ],
    limitations: [
      'Requires self-hosting',
      'Some bridges may break',
      'Less actively maintained than RSSHub',
    ],
    legalStatus: 'gray_area',
    recommended: false,
    url: 'https://github.com/RSS-Bridge/rss-bridge',
  },
  {
    id: 'nitter',
    name: 'Nitter Instances (Twitter)',
    description: 'Alternative Twitter frontends that provide RSS feeds. Many instances have shut down, but some still work.',
    platforms: ['twitter'],
    cost: 'free',
    setupDifficulty: 'easy',
    requirements: [
      'Find working Nitter instance',
    ],
    limitations: [
      'Many instances shut down',
      'Unreliable',
      'May violate Twitter ToS',
    ],
    legalStatus: 'gray_area',
    recommended: false,
  },
  {
    id: 'paid-services',
    name: 'Paid RSS Services',
    description: 'Commercial services like RSS.app, Feedly that provide social media RSS feeds.',
    platforms: ['twitter', 'instagram', 'linkedin', 'facebook'],
    cost: 'paid',
    setupDifficulty: 'easy',
    requirements: [
      'Subscription ($10-50/month)',
      'Account setup',
    ],
    limitations: [
      'Monthly cost',
      'Depends on third-party service',
      'May still violate platform ToS',
    ],
    legalStatus: 'gray_area',
    recommended: false,
    url: 'https://rss.app/',
  },
];

export const RECOMMENDED_RSS_FEEDS = {
  techNews: [
    { name: 'TechCrunch', url: 'https://techcrunch.com/feed/' },
    { name: 'The Verge', url: 'https://www.theverge.com/rss/index.xml' },
    { name: 'Wired', url: 'https://www.wired.com/feed/rss' },
    { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index' },
    { name: 'VentureBeat', url: 'https://venturebeat.com/feed/' },
  ],
  socialMediaNews: [
    { name: 'Social Media Today', url: 'https://www.socialmediatoday.com/feeds/' },
    { name: 'Social Media Examiner', url: 'https://www.socialmediaexaminer.com/feed/' },
    { name: 'Marketing Land', url: 'https://marketingland.com/feed' },
  ],
  redditDiscussions: [
    { name: 'r/twitter', url: 'https://www.reddit.com/r/twitter/.rss' },
    { name: 'r/linkedin', url: 'https://www.reddit.com/r/linkedin/.rss' },
    { name: 'r/instagram', url: 'https://www.reddit.com/r/instagram/.rss' },
    { name: 'r/facebook', url: 'https://www.reddit.com/r/facebook/.rss' },
    { name: 'r/socialmedia', url: 'https://www.reddit.com/r/socialmedia/.rss' },
  ],
};

export const getAlternativeSources = (): AlternativeSource[] => {
  return ALTERNATIVE_SOURCES;
};

export const getRecommendedSources = (): AlternativeSource[] => {
  return ALTERNATIVE_SOURCES.filter(s => s.recommended);
};
