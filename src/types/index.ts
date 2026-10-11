// Platforms that actually work with real API access
export type WorkingPlatform = 'reddit' | 'youtube' | 'blogs';

// Platforms with limited or no public API access
export type LimitedPlatform = 'x' | 'linkedin' | 'instagram' | 'facebook' | 'quora';

export type Platform = WorkingPlatform | LimitedPlatform;

export interface PlatformCapability {
  platform: Platform;
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

export interface Niche {
  id: string;
  name: string;
  keywords: string[];
  subreddits: string[];
  blogFeeds: string[];
  includeTerms: string[];
  excludeTerms: string[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface SourceStatus {
  platform: Platform;
  label: string;
  status: 'connected' | 'missing_credentials' | 'rate_limited' | 'error' | 'unavailable';
  lastChecked: string;
  itemsCollected: number;
  message?: string;
  icon: string;
  color: string;
}

export interface CollectedItem {
  id: string;
  platform: Platform;
  title: string;
  url: string;
  author: string;
  score: number;
  excerpt: string;
  collectedAt: string;
  nicheId: string;
}

export interface RunRecord {
  id: string;
  startedAt: string;
  completedAt?: string;
  status: 'running' | 'completed' | 'failed';
  nicheId: string;
  nicheName: string;
  stats: {
    [key in Platform]?: { collected: number; errors: number; duration: number };
  };
  totalItems: number;
  errors: string[];
}

export interface Newsletter {
  id: string;
  nicheId: string;
  nicheName: string;
  date: string;
  subject: string;
  preheader: string;
  tldr: string[];
  topStories: Story[];
  trendRadar: TrendItem[];
  platformHighlights: PlatformHighlight[];
  voicesAndHotTakes: Voice[];
  questionsOfTheDay: Question[];
  contentOpportunities: Opportunity[];
  actionOfTheDay: string;
  coverage: CoverageItem[];
  diagnostics: Diagnostic[];
}

export interface Story {
  id: string;
  title: string;
  summary: string;
  source: Platform;
  sourceUrl: string;
  author: string;
  score: number;
  feedback?: 'up' | 'down' | null;
}

export interface TrendItem {
  topic: string;
  momentum: 'rising' | 'stable' | 'falling';
  score: number;
  sources: Platform[];
}

export interface PlatformHighlight {
  platform: Platform;
  headline: string;
  summary: string;
  url: string;
  author: string;
}

export interface Voice {
  author: string;
  platform: Platform;
  quote: string;
  url: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

export interface Question {
  question: string;
  source: Platform;
  url: string;
  answers: number;
}

export interface Opportunity {
  title: string;
  angle: string;
  evidence: string;
  source: Platform;
  url: string;
}

export interface CoverageItem {
  platform: Platform;
  items: number;
  status: 'ok' | 'partial' | 'failed';
}

export interface Diagnostic {
  label: string;
  value: string;
  status: 'good' | 'warn' | 'bad';
}

export interface FeedbackStats {
  totalUp: number;
  totalDown: number;
  byPlatform: { [key in Platform]?: { up: number; down: number } };
  topRated: Story[];
}
