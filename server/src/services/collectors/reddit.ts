import axios from 'axios';
import dotenv from 'dotenv';

dotenv.config();

interface RedditPost {
  id: string;
  title: string;
  url: string;
  author: string;
  score: number;
  selftext: string;
  subreddit: string;
  created_utc: number;
  permalink: string;
}

export class RedditCollector {
  private clientId: string;
  private clientSecret: string;
  private accessToken: string | null = null;

  constructor() {
    this.clientId = process.env.REDDIT_CLIENT_ID || '';
    this.clientSecret = process.env.REDDIT_CLIENT_SECRET || '';
  }

  async authenticate(): Promise<void> {
    if (!this.clientId || !this.clientSecret) {
      throw new Error('Reddit API credentials not configured');
    }

    try {
      const response = await axios.post(
        'https://www.reddit.com/api/v1/access_token',
        'grant_type=client_credentials',
        {
          auth: {
            username: this.clientId,
            password: this.clientSecret,
          },
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'NewsletterMachine/1.0',
          },
        }
      );

      this.accessToken = response.data.access_token;
    } catch (error) {
      console.error('Reddit authentication failed:', error);
      throw new Error('Failed to authenticate with Reddit API');
    }
  }

  async collectFromSubreddits(
    subreddits: string[],
    keywords: string[],
    limit: number = 25
  ): Promise<any[]> {
    if (!this.accessToken) {
      await this.authenticate();
    }

    const posts: any[] = [];

    for (const subreddit of subreddits) {
      try {
        const response = await axios.get(
          `https://oauth.reddit.com/r/${subreddit}/hot`,
          {
            headers: {
              Authorization: `Bearer ${this.accessToken}`,
              'User-Agent': 'NewsletterMachine/1.0',
            },
            params: { limit: limit * 2 }, // Get more to filter
          }
        );

        const relevantPosts = response.data.data.children
          .map((child: any) => child.data)
          .filter((post: RedditPost) => {
            // Filter by keywords
            const text = `${post.title} ${post.selftext}`.toLowerCase();
            return keywords.some(keyword => 
              text.includes(keyword.toLowerCase())
            );
          })
          .slice(0, limit);

        posts.push(
          ...relevantPosts.map((post: RedditPost) => ({
            platform: 'reddit',
            title: post.title,
            url: `https://reddit.com${post.permalink}`,
            author: post.author,
            score: post.score,
            excerpt: post.selftext.substring(0, 500),
            metadata: {
              subreddit: post.subreddit,
              postId: post.id,
              createdUtc: post.created_utc,
            },
          }))
        );

        // Rate limiting
        await new Promise(resolve => setTimeout(resolve, 1000));
      } catch (error) {
        console.error(`Error collecting from r/${subreddit}:`, error);
      }
    }

    return posts;
  }
}

export const redditCollector = new RedditCollector();
