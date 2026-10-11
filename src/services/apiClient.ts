import { Niche, Newsletter, RunRecord, SourceStatus, FeedbackStats } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ user: any; token: string }> {
    const result = await this.request<{ user: any; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.token = result.token;
    localStorage.setItem('auth_token', result.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    return result;
  }

  async register(email: string, password: string, name?: string): Promise<{ user: any; token: string }> {
    const result = await this.request<{ user: any; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    this.token = result.token;
    localStorage.setItem('auth_token', result.token);
    localStorage.setItem('user', JSON.stringify(result.user));
    return result;
  }

  logout(): void {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getUser(): any {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  // Niches
  async getNiches(): Promise<Niche[]> {
    return this.request<Niche[]>('/niches');
  }

  async createNiche(niche: Partial<Niche>): Promise<Niche> {
    return this.request<Niche>('/niches', {
      method: 'POST',
      body: JSON.stringify(niche),
    });
  }

  async updateNiche(id: string, updates: Partial<Niche>): Promise<Niche> {
    return this.request<Niche>(`/niches/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async deleteNiche(id: string): Promise<void> {
    await this.request(`/niches/${id}`, { method: 'DELETE' });
  }

  // Runs
  async getRuns(): Promise<RunRecord[]> {
    return this.request<RunRecord[]>('/runs');
  }

  async triggerRun(nicheId: string): Promise<{ runId: string }> {
    return this.request<{ runId: string }>('/runs', {
      method: 'POST',
      body: JSON.stringify({ nicheId }),
    });
  }

  // Newsletters
  async getNewsletters(): Promise<Newsletter[]> {
    return this.request<Newsletter[]>('/newsletters');
  }

  async getNewsletter(id: string): Promise<Newsletter> {
    return this.request<Newsletter>(`/newsletters/${id}`);
  }

  async submitFeedback(newsletterId: string, storyId: string, vote: 'up' | 'down'): Promise<void> {
    await this.request(`/newsletters/${newsletterId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ storyId, vote }),
    });
  }

  async getFeedbackStats(): Promise<FeedbackStats> {
    return this.request<FeedbackStats>('/newsletters/feedback/stats');
  }

  // Sources
  async getSources(): Promise<SourceStatus[]> {
    return this.request<SourceStatus[]>('/sources');
  }
}

export const apiClient = new ApiClient();
