export interface PlatformCapability {
  platform: string;
  label: string;
  status: 'fully_supported' | 'paid_only' | 'restricted' | 'no_api' | 'coming_soon';
  description: string;
  requirements: string[];
  cost: string;
  setupDifficulty: 'easy' | 'medium' | 'hard' | 'expert';
  icon: string;
  color: string;
  canCollect: boolean;
}

export const PLATFORM_CAPABILITIES: PlatformCapability[] = [
  {
    platform: 'blogs',
    label: 'Blogs & RSS Feeds',
    status: 'fully_supported',
    description: 'Collect from any blog or website with an RSS feed. No API keys required.',
    requirements: ['A blog URL with RSS/Atom feed'],
    cost: 'Free',
    setupDifficulty: 'easy',
    icon: 'rss',
    color: '#f97316',
    canCollect: true,
  },
  {
    platform: 'reddit',
    label: 'Reddit',
    status: 'fully_supported',
    description: 'Collect posts from any subreddit. Requires a free Reddit API app.',
    requirements: [
      'Reddit account',
      'Create an app at reddit.com/prefs/apps',
      'Client ID and Client Secret',
    ],
    cost: 'Free',
    setupDifficulty: 'easy',
    icon: 'reddit',
    color: '#ff4500',
    canCollect: true,
  },
  {
    platform: 'youtube',
    label: 'YouTube',
    status: 'fully_supported',
    description: 'Search and collect video content. Requires a free Google API key.',
    requirements: [
      'Google account',
      'Enable YouTube Data API v3 in Google Cloud Console',
      'API Key',
    ],
    cost: 'Free (10,000 units/day)',
    setupDifficulty: 'easy',
    icon: 'youtube',
    color: '#ff0000',
    canCollect: true,
  },
  {
    platform: 'x',
    label: 'X (Twitter)',
    status: 'paid_only',
    description: 'Twitter API now requires a paid subscription for most features.',
    requirements: [
      'Twitter Developer account',
      'Basic plan ($100/month) or Pro plan ($5,000/month)',
      'API keys',
    ],
    cost: '$100 - $5,000/month',
    setupDifficulty: 'medium',
    icon: 'x-twitter',
    color: '#1da1f2',
    canCollect: false,
  },
  {
    platform: 'linkedin',
    label: 'LinkedIn',
    status: 'restricted',
    description: 'LinkedIn heavily restricts API access. Only available to approved partners.',
    requirements: [
      'LinkedIn Developer account',
      'Partnership approval required',
      'Marketing Developer Platform access',
    ],
    cost: 'Requires partnership',
    setupDifficulty: 'expert',
    icon: 'linkedin',
    color: '#0077b5',
    canCollect: false,
  },
  {
    platform: 'instagram',
    label: 'Instagram',
    status: 'restricted',
    description: 'Instagram API only works for business accounts you own. Cannot collect public content.',
    requirements: [
      'Facebook Developer account',
      'Instagram Business account',
      'Facebook app review and approval',
    ],
    cost: 'Free but requires approval',
    setupDifficulty: 'hard',
    icon: 'instagram',
    color: '#e4405f',
    canCollect: false,
  },
  {
    platform: 'facebook',
    label: 'Facebook',
    status: 'restricted',
    description: 'Facebook restricts public content access since 2018. Only works for pages you manage.',
    requirements: [
      'Facebook Developer account',
      'App review required',
      'Can only access pages you manage',
    ],
    cost: 'Free but restricted',
    setupDifficulty: 'hard',
    icon: 'facebook',
    color: '#1877f2',
    canCollect: false,
  },
  {
    platform: 'quora',
    label: 'Quora',
    status: 'no_api',
    description: 'Quora does not provide an official API. Web scraping violates their Terms of Service.',
    requirements: ['No official API available'],
    cost: 'N/A',
    setupDifficulty: 'expert',
    icon: 'quora',
    color: '#b92b27',
    canCollect: false,
  },
];

export const getPlatformCapability = (platform: string): PlatformCapability | undefined => {
  return PLATFORM_CAPABILITIES.find(p => p.platform === platform);
};

export const getWorkingPlatforms = (): PlatformCapability[] => {
  return PLATFORM_CAPABILITIES.filter(p => p.canCollect);
};

export const getLimitedPlatforms = (): PlatformCapability[] => {
  return PLATFORM_CAPABILITIES.filter(p => !p.canCollect);
};
