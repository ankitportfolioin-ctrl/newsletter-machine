import pool from '../config/database';
import { redditCollector } from './collectors/reddit';
import { youtubeCollector } from './collectors/youtube';
import { rssCollector } from './collectors/rss';
import { newsletterGenerator } from './newsletterGenerator';

export class CollectionService {
  async runCollection(userId: string, nicheId: string): Promise<string> {
    // Create run record
    const runResult = await pool.query(
      `INSERT INTO runs (user_id, niche_id, status, started_at)
       VALUES ($1, $2, 'running', NOW())
       RETURNING id`,
      [userId, nicheId]
    );
    const runId = runResult.rows[0].id;

    try {
      // Get niche details
      const nicheResult = await pool.query(
        'SELECT * FROM niches WHERE id = $1 AND user_id = $2',
        [nicheId, userId]
      );

      if (nicheResult.rows.length === 0) {
        throw new Error('Niche not found');
      }

      const niche = nicheResult.rows[0];
      const stats: any = {};
      const errors: string[] = [];
      const allItems: any[] = [];

      // Collect from Reddit
      if (niche.subreddits && niche.subreddits.length > 0) {
        try {
          const startTime = Date.now();
          const redditItems = await redditCollector.collectFromSubreddits(
            niche.subreddits,
            niche.keywords,
            25
          );
          stats.reddit = {
            collected: redditItems.length,
            errors: 0,
            duration: (Date.now() - startTime) / 1000,
          };
          allItems.push(...redditItems);
        } catch (error: any) {
          stats.reddit = { collected: 0, errors: 1, duration: 0 };
          errors.push(`Reddit: ${error.message}`);
        }
      }

      // Collect from YouTube
      if (niche.keywords && niche.keywords.length > 0) {
        try {
          const startTime = Date.now();
          const query = niche.keywords.slice(0, 3).join(' ');
          const youtubeItems = await youtubeCollector.searchVideos(query, 10);
          stats.youtube = {
            collected: youtubeItems.length,
            errors: 0,
            duration: (Date.now() - startTime) / 1000,
          };
          allItems.push(...youtubeItems);
        } catch (error: any) {
          stats.youtube = { collected: 0, errors: 1, duration: 0 };
          errors.push(`YouTube: ${error.message}`);
        }
      }

      // Collect from RSS feeds
      if (niche.blog_feeds && niche.blog_feeds.length > 0) {
        try {
          const startTime = Date.now();
          const rssItems = await rssCollector.collectFromFeeds(
            niche.blog_feeds,
            niche.keywords,
            10
          );
          stats.blogs = {
            collected: rssItems.length,
            errors: 0,
            duration: (Date.now() - startTime) / 1000,
          };
          allItems.push(...rssItems);
        } catch (error: any) {
          stats.blogs = { collected: 0, errors: 1, duration: 0 };
          errors.push(`RSS: ${error.message}`);
        }
      }

      // Save collected items
      for (const item of allItems) {
        await pool.query(
          `INSERT INTO collected_items (niche_id, platform, title, url, author, score, excerpt, metadata)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
          [
            nicheId,
            item.platform,
            item.title,
            item.url,
            item.author,
            item.score,
            item.excerpt,
            JSON.stringify(item.metadata),
          ]
        );
      }

      // Generate newsletter if we have enough items
      let newsletterId = null;
      if (allItems.length >= 5) {
        try {
          const newsletter = await newsletterGenerator.generateNewsletter(
            niche.name,
            allItems,
            new Date().toISOString().split('T')[0]
          );

          const nlResult = await pool.query(
            `INSERT INTO newsletters (user_id, niche_id, run_id, date, subject, preheader, content)
             VALUES ($1, $2, $3, $4, $5, $6, $7)
             RETURNING id`,
            [
              userId,
              nicheId,
              runId,
            newsletter.date,
              newsletter.subject,
              newsletter.preheader,
              JSON.stringify(newsletter),
            ]
          );
          newsletterId = nlResult.rows[0].id;
        } catch (error: any) {
          errors.push(`Newsletter generation: ${error.message}`);
        }
      }

      // Update run record
      await pool.query(
        `UPDATE runs SET status = 'completed', completed_at = NOW(), stats = $1, errors = $2
         WHERE id = $3`,
        [JSON.stringify(stats), errors, runId]
      );

      return runId;
    } catch (error: any) {
      await pool.query(
        `UPDATE runs SET status = 'failed', completed_at = NOW(), errors = $1
         WHERE id = $2`,
        [[error.message], runId]
      );
      throw error;
    }
  }
}

export const collectionService = new CollectionService();
