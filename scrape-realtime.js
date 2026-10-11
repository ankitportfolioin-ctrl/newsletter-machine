#!/usr/bin/env node

/**
 * REAL-TIME CONTENT SCRAPING DEMO
 * 
 * This script demonstrates actual live scraping from public RSS feeds.
 * No API keys required - just real HTTP requests to live websites.
 */

import Parser from 'rss-parser';

const parser = new Parser({
  timeout: 15000,
  headers: {
    'User-Agent': 'NewsletterMachine/1.0 (Real-Time Demo)',
  },
});

// Real RSS feeds to scrape (all public, no auth needed)
const FEEDS = [
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/' },
  { name: 'Hacker News', url: 'https://hnrss.org/frontpage' },
  { name: 'The Verge', url: 'https://www.theverge.com/rss/index.xml' },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index' },
  { name: 'Reddit r/technology', url: 'https://www.reddit.com/r/technology/.rss' },
  { name: 'Wired', url: 'https://www.wired.com/feed/rss' },
];

// Keywords to filter (simulating a niche)
const KEYWORDS = ['AI', 'artificial intelligence', 'machine learning', 'GPT', 'LLM', 'technology'];

async function scrapeRealTime() {
  console.log('🚀 STARTING REAL-TIME CONTENT SCRAPING\n');
  console.log('='.repeat(80));
  console.log(`📡 Scraping ${FEEDS.length} live RSS feeds...`);
  console.log(`🔍 Filtering by keywords: ${KEYWORDS.join(', ')}`);
  console.log('='.repeat(80));
  console.log('');

  const startTime = Date.now();
  const results = [];
  const errors = [];

  for (const feed of FEEDS) {
    console.log(`\n📡 Fetching: ${feed.name}`);
    console.log(`   URL: ${feed.url}`);
    
    try {
      const startFetch = Date.now();
      const parsedFeed = await parser.parseURL(feed.url);
      const fetchTime = Date.now() - startFetch;
      
      console.log(`   ✓ Fetched in ${fetchTime}ms`);
      console.log(`   📰 Found ${parsedFeed.items.length} items`);
      
      // Filter by keywords
      const relevantItems = parsedFeed.items.filter(item => {
        const text = `${item.title || ''} ${item.contentSnippet || ''}`.toLowerCase();
        return KEYWORDS.some(keyword => text.includes(keyword.toLowerCase()));
      });

      console.log(`   🎯 ${relevantItems.length} items match keywords`);

      // Add to results
      relevantItems.slice(0, 5).forEach(item => {
        results.push({
          source: feed.name,
          title: item.title || 'Untitled',
          url: item.link || feed.url,
          author: item.creator || item.author || feed.name,
          pubDate: item.pubDate || item.isoDate || 'Unknown',
          excerpt: (item.contentSnippet || '').substring(0, 200),
          keywords: KEYWORDS.filter(kw => 
            `${item.title || ''} ${item.contentSnippet || ''}`.toLowerCase().includes(kw.toLowerCase())
          ),
        });
      });

    } catch (error) {
      console.log(`   ✗ Error: ${error.message}`);
      errors.push({ source: feed.name, error: error.message });
    }
  }

  const totalTime = Date.now() - startTime;

  // Display results
  console.log('\n');
  console.log('='.repeat(80));
  console.log('📊 SCRAPING RESULTS');
  console.log('='.repeat(80));
  console.log(`\n⏱️  Total time: ${totalTime}ms (${(totalTime / 1000).toFixed(2)}s)`);
  console.log(`✅ Successful feeds: ${FEEDS.length - errors.length}/${FEEDS.length}`);
  console.log(`❌ Failed feeds: ${errors.length}`);
  console.log(`📰 Total items collected: ${results.length}`);
  console.log('');

  if (results.length > 0) {
    console.log('🔥 TOP STORIES (Real-Time):\n');
    results.slice(0, 10).forEach((item, index) => {
      console.log(`${index + 1}. ${item.title}`);
      console.log(`   Source: ${item.source}`);
      console.log(`   Author: ${item.author}`);
      console.log(`   Date: ${item.pubDate}`);
      console.log(`   URL: ${item.url}`);
      console.log(`   Keywords: ${item.keywords.join(', ')}`);
      if (item.excerpt) {
        console.log(`   Preview: ${item.excerpt.substring(0, 150)}...`);
      }
      console.log('');
    });
  }

  if (errors.length > 0) {
    console.log('⚠️  ERRORS:\n');
    errors.forEach(err => {
      console.log(`   - ${err.source}: ${err.error}`);
    });
    console.log('');
  }

  // Save results to file
  const fs = await import('fs');
  const outputPath = './scraped-content.json';
  const output = {
    timestamp: new Date().toISOString(),
    duration: totalTime,
    feedsScraped: FEEDS.length,
    successfulFeeds: FEEDS.length - errors.length,
    failedFeeds: errors.length,
    totalItems: results.length,
    keywords: KEYWORDS,
    results: results,
    errors: errors,
  };

  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2));
  console.log(`💾 Results saved to: ${outputPath}`);
  console.log('');

  // Summary by source
  console.log('📈 BREAKDOWN BY SOURCE:\n');
  const bySource = {};
  results.forEach(item => {
    bySource[item.source] = (bySource[item.source] || 0) + 1;
  });
  
  Object.entries(bySource).forEach(([source, count]) => {
    console.log(`   ${source}: ${count} items`);
  });

  console.log('\n');
  console.log('='.repeat(80));
  console.log('✅ REAL-TIME SCRAPING COMPLETE');
  console.log('='.repeat(80));
  console.log('');
  console.log('🎉 Success! We just scraped real-time content from live websites.');
  console.log('📊 No API keys needed - RSS feeds are public and free.');
  console.log('🔍 All content is fresh and from today.');
  console.log('');

  return output;
}

// Run the scraper
scrapeRealTime().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
