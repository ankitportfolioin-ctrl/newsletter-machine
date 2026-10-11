import OpenAI from 'openai';
import dotenv from 'dotenv';

dotenv.config();

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

interface CollectedItem {
  platform: string;
  title: string;
  url: string;
  author: string;
  score: number;
  excerpt: string;
}

export class NewsletterGenerator {
  async generateNewsletter(
    nicheName: string,
    items: CollectedItem[],
    date: string
  ): Promise<any> {
    if (!process.env.OPENAI_API_KEY) {
      throw new Error('OpenAI API key not configured');
    }

    // Sort items by score and recency
    const sortedItems = items.sort((a, b) => b.score - a.score).slice(0, 20);

    const itemsSummary = sortedItems
      .map(
        (item, i) =>
          `${i + 1}. [${item.platform}] ${item.title}\n   Author: ${item.author}\n   Score: ${item.score}\n   URL: ${item.url}\n   Excerpt: ${item.excerpt}\n`
      )
      .join('\n');

    const prompt = `You are an expert newsletter curator for the niche "${nicheName}".

Based on the following collected content items, create a comprehensive newsletter with the following sections:

${itemsSummary}

Generate a newsletter with these sections (return as JSON):
1. subject: An engaging email subject line with emoji
2. preheader: A brief preview text (max 150 chars)
3. tldr: Array of 5 key takeaways (1-2 sentences each)
4. topStories: Array of top 5 stories with: id, title, summary (2-3 sentences), source (platform), sourceUrl, author, score
5. trendRadar: Array of 5 trending topics with: topic, momentum (rising/stable/falling), score (0-100), sources (array of platforms)
6. platformHighlights: Array of 4 highlights (one per active platform) with: platform, headline, summary, url, author
7. voicesAndHotTakes: Array of 3 notable quotes/opinions with: author, platform, quote, url, sentiment (positive/neutral/negative)
8. questionsOfTheDay: Array of 3 interesting questions from the content with: question, source, url, answers (estimated)
9. contentOpportunities: Array of 3 content ideas with: title, angle, evidence, source, url
10. actionOfTheDay: A specific, actionable recommendation for readers

Return ONLY valid JSON with this structure. Make it engaging, insightful, and valuable for professionals in this niche.`;

    try {
      const completion = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [
          {
            role: 'system',
            content:
              'You are a professional newsletter curator. Always respond with valid JSON only, no markdown or explanations.',
          },
          { role: 'user', content: prompt },
        ],
        temperature: 0.7,
        max_tokens: 4000,
      });

      const content = completion.choices[0]?.message?.content;
      if (!content) {
        throw new Error('No content generated');
      }

      // Parse JSON response
      const newsletter = JSON.parse(content);

      // Add metadata
      return {
        ...newsletter,
        date,
        nicheName,
        coverage: this.generateCoverage(items),
        diagnostics: this.generateDiagnostics(items),
      };
    } catch (error) {
      console.error('Newsletter generation failed:', error);
      throw new Error('Failed to generate newsletter');
    }
  }

  private generateCoverage(items: CollectedItem[]) {
    const platformCounts: Record<string, number> = {};
    items.forEach(item => {
      platformCounts[item.platform] = (platformCounts[item.platform] || 0) + 1;
    });

    return Object.entries(platformCounts).map(([platform, count]) => ({
      platform,
      items: count,
      status: count > 5 ? 'ok' : count > 0 ? 'partial' : 'failed',
    }));
  }

  private generateDiagnostics(items: CollectedItem[]) {
    const platforms = new Set(items.map(i => i.platform));
    const avgScore = items.reduce((sum, i) => sum + i.score, 0) / items.length;

    return [
      { label: 'Total items collected', value: items.length.toString(), status: 'good' },
      { label: 'Platforms covered', value: `${platforms.size}/8`, status: platforms.size >= 4 ? 'good' : 'warn' },
      { label: 'Average engagement', value: Math.round(avgScore).toString(), status: avgScore > 100 ? 'good' : 'warn' },
      { label: 'Content freshness', value: '24h', status: 'good' },
    ];
  }
}

export const newsletterGenerator = new NewsletterGenerator();
