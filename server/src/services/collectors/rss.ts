import Parser from 'rss-parser';

const parser = new Parser({
  timeout: 10000,
  headers: {
    'User-Agent': 'NewsletterMachine/1.0',
  },
});

export class RSSCollector {
  async collectFromFeeds(
    feedUrls: string[],
    keywords: string[],
    maxItemsPerFeed: number = 10
  ): Promise<any[]> {
    const items: any[] = [];

    for (const feedUrl of feedUrls) {
      try {
        const feed = await parser.parseURL(feedUrl);
        
        const relevantItems = feed.items
          .filter(item => {
            const text = `${item.title || ''} ${item.contentSnippet || ''} ${item.content || ''}`.toLowerCase();
            return keywords.some(keyword => text.includes(keyword.toLowerCase()));
          })
          .slice(0, maxItemsPerFeed);

        items.push(
          ...relevantItems.map(item => ({
            platform: 'blogs',
            title: item.title || 'Untitled',
            url: item.link || feedUrl,
            author: item.creator || item.author || feed.title || 'Unknown',
            score: 0,
            excerpt: (item.contentSnippet || item.content || '').substring(0, 500),
            metadata: {
              feedUrl,
              feedTitle: feed.title,
              pubDate: item.pubDate || item.isoDate,
              categories: item.categories || [],
            },
          }))
        );
      } catch (error) {
        console.error(`Error parsing feed ${feedUrl}:`, error);
      }
    }

    return items;
  }
}

export const rssCollector = new RSSCollector();
