import { Niche, SourceStatus, Newsletter, RunRecord, Platform, FeedbackStats, Story } from '../types';
import { DEMO_NICHES, DEMO_SOURCES, DEMO_NEWSLETTERS, DEMO_RUNS, DEMO_AUTH_TOKEN } from '../data/demoData';

const STORAGE_KEYS = {
  niches: 'nm_niches',
  runs: 'nm_runs',
  newsletters: 'nm_newsletters',
  feedback: 'nm_feedback',
  auth: 'nm_auth_token',
  theme: 'nm_theme',
};

function getItem<T>(key: string, fallback: T): T {
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
}

function setItem<T>(key: string, value: T): void {
  localStorage.setItem(key, JSON.stringify(value));
}

// Simulate network delay
function delay(ms: number = 300): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============ AUTH ============
export async function authenticate(token: string): Promise<{ success: boolean; message: string }> {
  await delay(500);
  if (token === DEMO_AUTH_TOKEN || token === 'demo') {
    setItem(STORAGE_KEYS.auth, token);
    return { success: true, message: 'Authenticated successfully' };
  }
  return { success: false, message: 'Invalid token. Use "demo" for demo access.' };
}

export function isAuthenticated(): boolean {
  return !!localStorage.getItem(STORAGE_KEYS.auth);
}

export function logout(): void {
  localStorage.removeItem(STORAGE_KEYS.auth);
}

// ============ NICHES ============
export async function getNiches(): Promise<Niche[]> {
  await delay(200);
  const stored = getItem<Niche[] | null>(STORAGE_KEYS.niches, null);
  if (!stored) {
    setItem(STORAGE_KEYS.niches, DEMO_NICHES);
    return DEMO_NICHES;
  }
  return stored;
}

export async function createNiche(niche: Omit<Niche, 'id' | 'createdAt' | 'updatedAt'>): Promise<Niche> {
  await delay(400);
  const niches = await getNiches();
  
  // Validation
  if (!niche.name.trim()) throw new Error('Niche name is required');
  if (niche.name.length > 500) throw new Error('Name must be under 500 characters');
  if (niches.some(n => n.name.toLowerCase() === niche.name.toLowerCase())) {
    throw new Error('A niche with this name already exists');
  }

  const newNiche: Niche = {
    ...niche,
    id: `niche-${Date.now()}`,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
  niches.push(newNiche);
  setItem(STORAGE_KEYS.niches, niches);
  return newNiche;
}

export async function updateNiche(id: string, updates: Partial<Niche>): Promise<Niche> {
  await delay(300);
  const niches = await getNiches();
  const idx = niches.findIndex(n => n.id === id);
  if (idx === -1) throw new Error('Niche not found');
  niches[idx] = { ...niches[idx], ...updates, updatedAt: new Date().toISOString() };
  setItem(STORAGE_KEYS.niches, niches);
  return niches[idx];
}

export async function deleteNiche(id: string): Promise<void> {
  await delay(300);
  const niches = await getNiches();
  setItem(STORAGE_KEYS.niches, niches.filter(n => n.id !== id));
}

// ============ SOURCES ============
export async function getSources(): Promise<SourceStatus[]> {
  await delay(300);
  return DEMO_SOURCES;
}

// ============ RUNS ============
export async function getRuns(): Promise<RunRecord[]> {
  await delay(200);
  const stored = getItem<RunRecord[] | null>(STORAGE_KEYS.runs, null);
  if (!stored) {
    setItem(STORAGE_KEYS.runs, DEMO_RUNS);
    return DEMO_RUNS;
  }
  return stored;
}

export async function triggerRun(nicheId: string): Promise<RunRecord> {
  const niches = await getNiches();
  const niche = niches.find(n => n.id === nicheId);
  if (!niche) throw new Error('Niche not found');

  const run: RunRecord = {
    id: `run-${Date.now()}`,
    startedAt: new Date().toISOString(),
    status: 'running',
    nicheId,
    nicheName: niche.name,
    stats: {},
    totalItems: 0,
    errors: [],
  };

  const runs = await getRuns();
  runs.unshift(run);
  setItem(STORAGE_KEYS.runs, runs);

  // Simulate collection progress
  const platforms: Platform[] = ['blogs', 'reddit', 'youtube', 'quora'];
  for (const platform of platforms) {
    await delay(1500);
    const currentRuns = getItem<RunRecord[]>(STORAGE_KEYS.runs, []);
    const currentRun = currentRuns.find(r => r.id === run.id);
    if (currentRun) {
      const collected = Math.floor(Math.random() * 20) + 5;
      const errors = Math.random() > 0.7 ? Math.floor(Math.random() * 3) : 0;
      currentRun.stats[platform] = {
        collected,
        errors,
        duration: Math.random() * 5 + 2,
      };
      currentRun.totalItems += collected;
      if (errors > 0) {
        currentRun.errors.push(`${platform}: ${errors} items failed to collect`);
      }
      setItem(STORAGE_KEYS.runs, currentRuns);
    }
  }

  // Mark complete
  await delay(500);
  const finalRuns = getItem<RunRecord[]>(STORAGE_KEYS.runs, []);
  const finalRun = finalRuns.find(r => r.id === run.id);
  if (finalRun) {
    finalRun.status = 'completed';
    finalRun.completedAt = new Date().toISOString();
    setItem(STORAGE_KEYS.runs, finalRuns);
    return finalRun;
  }
  return run;
}

// ============ NEWSLETTERS ============
export async function getNewsletters(): Promise<Newsletter[]> {
  await delay(200);
  const stored = getItem<Newsletter[] | null>(STORAGE_KEYS.newsletters, null);
  if (!stored) {
    setItem(STORAGE_KEYS.newsletters, DEMO_NEWSLETTERS);
    return DEMO_NEWSLETTERS;
  }
  return stored;
}

export async function getNewsletter(id: string): Promise<Newsletter | null> {
  await delay(200);
  const newsletters = await getNewsletters();
  return newsletters.find(n => n.id === id) || null;
}

// ============ FEEDBACK ============
export async function submitFeedback(
  newsletterId: string,
  storyId: string,
  vote: 'up' | 'down'
): Promise<void> {
  await delay(200);
  const feedback = getItem<Record<string, 'up' | 'down'>>(STORAGE_KEYS.feedback, {});
  feedback[storyId] = vote;
  setItem(STORAGE_KEYS.feedback, feedback);

  // Update newsletter story
  const newsletters = await getNewsletters();
  const nl = newsletters.find(n => n.id === newsletterId);
  if (nl) {
    const story = nl.topStories.find(s => s.id === storyId);
    if (story) {
      story.feedback = vote;
      setItem(STORAGE_KEYS.newsletters, newsletters);
    }
  }
}

export async function getFeedbackStats(): Promise<FeedbackStats> {
  await delay(200);
  const feedback = getItem<Record<string, 'up' | 'down'>>(STORAGE_KEYS.feedback, {});
  const newsletters = await getNewsletters();

  let totalUp = 0;
  let totalDown = 0;
  const byPlatform: FeedbackStats['byPlatform'] = {};
  const storyMap: Record<string, Story> = {};

  for (const nl of newsletters) {
    for (const story of nl.topStories) {
      storyMap[story.id] = story;
    }
  }

  for (const [storyId, vote] of Object.entries(feedback)) {
    if (vote === 'up') totalUp++;
    else totalDown++;

    const story = storyMap[storyId];
    if (story) {
      if (!byPlatform[story.source]) byPlatform[story.source] = { up: 0, down: 0 };
      if (vote === 'up') byPlatform[story.source]!.up++;
      else byPlatform[story.source]!.down++;
    }
  }

  const topRated = Object.entries(feedback)
    .filter(([, v]) => v === 'up')
    .map(([id]) => storyMap[id])
    .filter(Boolean)
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);

  return { totalUp, totalDown, byPlatform, topRated };
}

// ============ THEME ============
export function getTheme(): 'light' | 'dark' {
  return getItem<'light' | 'dark'>(STORAGE_KEYS.theme, 'dark');
}

export function setTheme(theme: 'light' | 'dark'): void {
  setItem(STORAGE_KEYS.theme, theme);
  document.documentElement.className = theme;
}

// ============ SEED DATA ============
export function seedDemoData(): void {
  setItem(STORAGE_KEYS.niches, DEMO_NICHES);
  setItem(STORAGE_KEYS.runs, DEMO_RUNS);
  setItem(STORAGE_KEYS.newsletters, DEMO_NEWSLETTERS);
}

export function clearAllData(): void {
  Object.values(STORAGE_KEYS).forEach(key => {
    if (key !== STORAGE_KEYS.auth && key !== STORAGE_KEYS.theme) {
      localStorage.removeItem(key);
    }
  });
}
