import { supabaseAdmin } from '../config/supabase';
import { redditCollector } from './collectors/reddit';
import { youtubeCollector } from './collectors/youtube';
import { rssCollector } from './collectors/rss';
import { newsletterGenerator } from './newsletterGenerator';

export class CollectionService {
  async runCollection(userId: string, nicheId: string): Promise<string> {
    // Create run record
    const { data: runData, error: runError } = await supabaseAdmin
      .from('runs')
      .insert({
        user_id: userId,
        niche_id: nicheId,
        status: 'running',
        started_at: new Date().toISOString()
      })
      .select('id')
      .single();

    if (runError) throw runError;
    const runId = runData.id;

    try {
      // Get niche details
      const { data: nicheData, error: nicheError } = await supabaseAdmin
        .from('niches')
        .select('*')
        .eq('id', nicheId)
        .eq('user_id', userId)
        .single();

      if (nicheError || !nicheData) {
        throw new Error('Niche not found');
      }

      const niche = nicheData;
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

      // Save collected items with deduplication
      let duplicatesSkipped = 0;
      for (const item of allItems) {
        // Check if item already exists (by URL and niche)
        const { data: existing } = await supabaseAdmin
          .from('collected_items')
          .select('id')
          .eq('url', item.url)
          .eq('niche_id', nicheId);

        if (existing && existing.length > 0) {
          duplicatesSkipped++;
          continue; // Skip duplicate
        }

        await supabaseAdmin
          .from('collected_items')
          .insert({
            niche_id: nicheId,
            platform: item.platform,
            title: item.title,
            url: item.url,
            author: item.author,
            score: item.score,
            excerpt: item.excerpt,
            metadata: item.metadata
          });
      }

      // Add deduplication stats
      stats.deduplication = { skipped: duplicatesSkipped };

      // Generate newsletter if we have enough items
      let newsletterId = null;
      if (allItems.length >= 5) {
        try {
          const newsletter = await newsletterGenerator.generateNewsletter(
            niche.name,
            allItems,
            new Date().toISOString().split('T')[0]
          );

          const { data: nlData, error: nlError } = await supabaseAdmin
            .from('newsletters')
            .insert({
              user_id: userId,
              niche_id: nicheId,
              run_id: runId,
              date: newsletter.date,
              subject: newsletter.subject,
              preheader: newsletter.preheader,
              content: newsletter
            })
            .select('id')
            .single();

          if (!nlError && nlData) {
            newsletterId = nlData.id;
          }
        } catch (error: any) {
          errors.push(`Newsletter generation: ${error.message}`);
        }
      }

      // Update run record
      await supabaseAdmin
        .from('runs')
        .update({
          status: 'completed',
          completed_at: new Date().toISOString(),
          stats,
          errors
        })
        .eq('id', runId);

      return runId;
    } catch (error: any) {
      await supabaseAdmin
        .from('runs')
        .update({
          status: 'failed',
          completed_at: new Date().toISOString(),
          errors: [error.message]
        })
        .eq('id', runId);
      throw error;
    }
  }
}

export const collectionService = new CollectionService();
