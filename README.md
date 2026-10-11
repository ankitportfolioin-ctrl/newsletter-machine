# Newsletter Machine

An intelligent newsletter generation platform that collects content from multiple sources and creates personalized, AI-powered newsletters.

## 🎯 What This Does

Newsletter Machine helps you stay informed by:
- Collecting content from your favorite blogs, Reddit, and YouTube
- Filtering content based on topics you care about
- Generating beautiful, AI-powered newsletters
- Delivering them to your inbox on your schedule

## ✅ What Actually Works

### Fully Supported (Free & Easy Setup)

| Platform | Status | Setup Time | Requirements |
|----------|--------|------------|--------------|
| **Blogs & RSS** | ✅ Works | 0 minutes | Just a URL with an RSS feed |
| **Reddit** | ✅ Works | 5 minutes | Free Reddit API credentials |
| **YouTube** | ✅ Works | 5 minutes | Free Google API key |

These three platforms provide excellent coverage for most use cases and are completely free to use.

### Not Currently Supported

We believe in transparency. Here's why some platforms aren't available:

| Platform | Status | Why |
|----------|--------|-----|
| **X (Twitter)** | ❌ Paid Only | API costs $100-$5,000/month |
| **LinkedIn** | ❌ Restricted | Requires partnership approval |
| **Instagram** | ❌ Restricted | Only works for your own business accounts |
| **Facebook** | ❌ Restricted | Public content access blocked since 2018 |
| **Quora** | ❌ No API | No official API exists |

**Workaround:** Use RSS feeds from blogs and news sites that cover these platforms.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- PostgreSQL 14+ (or use Docker)
- (Optional) Reddit API credentials
- (Optional) YouTube API key

### Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd newsletter-machine

# 2. Install dependencies
npm install

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# 4. Set up the database
npm run db:setup

# 5. Start the development server
npm run dev
```

The app will be available at `http://localhost:3000`

## 📖 First-Time Setup

When you first log in, you'll see an onboarding wizard that guides you through:

1. **Creating your first niche** - A topic you want to follow (e.g., "AI News", "Startup Funding")
2. **Adding content sources** - RSS feeds, Reddit subreddits, or YouTube channels
3. **Generating your first newsletter** - We'll collect content and create a beautiful newsletter for you

### Step 1: Create a Niche

A niche is a topic you want to track. Examples:
- "AI and Machine Learning"
- "Startup Funding News"
- "Web Development Trends"
- "Cryptocurrency Updates"

For each niche, you can specify:
- **Keywords** - Terms to search for
- **RSS Feeds** - Blogs and news sites to monitor
- **Subreddits** - Reddit communities to track
- **YouTube Channels** - Video content sources

### Step 2: Add Sources

#### RSS Feeds (Easiest)
Just paste the URL of any blog or news site with an RSS feed:
- `https://techcrunch.com/feed/`
- `https://www.wired.com/feed/rss`
- `https://openai.com/blog/rss.xml`

#### Reddit (5-minute setup)
1. Go to [Reddit Apps](https://www.reddit.com/prefs/apps)
2. Click "create another app..."
3. Choose "script" type
4. Copy the Client ID and Client Secret
5. Paste them in the Sources page

#### YouTube (5-minute setup)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable "YouTube Data API v3"
4. Create an API key
5. Paste it in the Sources page

### Step 3: Generate Newsletters

Once your sources are configured:
1. Go to your niche
2. Click "Generate Newsletter"
3. Wait a few minutes while we collect and analyze content
4. Review your AI-generated newsletter
5. Schedule automatic generation (daily, weekly, etc.)

## 🎨 Features

### Content Collection
- **RSS Feed Parsing** - Collect from any blog or news site
- **Reddit Integration** - Track posts from specific subreddits
- **YouTube Integration** - Monitor channels and search for videos
- **Smart Filtering** - Only collect content matching your keywords
- **Deduplication** - Never see the same article twice

### AI-Powered Newsletters
- **Intelligent Summaries** - AI creates concise, readable summaries
- **Trend Detection** - Identifies emerging topics and patterns
- **Source Attribution** - Every claim links back to the original source
- **Customizable Format** - Choose your preferred newsletter style

### User Experience
- **Guided Onboarding** - Step-by-step setup wizard
- **Honest Status Indicators** - Clear information about what works
- **Visual Feedback** - See collection progress in real-time
- **Responsive Design** - Works on desktop, tablet, and mobile

## 🔧 Technical Details

### Architecture
- **Frontend**: React 18 + TypeScript + Tailwind CSS
- **Backend**: Node.js + Express + TypeScript
- **Database**: PostgreSQL
- **AI**: OpenAI GPT-4 (optional, for newsletter generation)

### API Endpoints

#### Authentication
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

#### Niches
- `GET /api/niches` - List all niches
- `POST /api/niches` - Create niche
- `PUT /api/niches/:id` - Update niche
- `DELETE /api/niches/:id` - Delete niche

#### Sources
- `GET /api/sources` - List all sources with status
- `POST /api/sources/:platform/configure` - Configure a source
- `POST /api/sources/:platform/test` - Test connection
- `DELETE /api/sources/:platform` - Remove source

#### Collection
- `POST /api/collect/:nicheId` - Trigger content collection
- `GET /api/collect/status/:jobId` - Check collection status

#### Newsletters
- `GET /api/newsletters` - List newsletters
- `GET /api/newsletters/:id` - Get newsletter
- `POST /api/newsletters/generate` - Generate newsletter
- `POST /api/newsletters/:id/feedback` - Submit feedback

## 🔒 Security & Privacy

- **No Data Sharing** - Your content and preferences stay private
- **Secure Authentication** - JWT tokens with bcrypt password hashing
- **Rate Limiting** - Protection against API abuse
- **Input Validation** - All user input is sanitized
- **HTTPS Ready** - Configure for production with SSL

## 📊 What's NOT Included (And Why)

### Social Media Platforms
We don't support LinkedIn, Instagram, Facebook, X (Twitter), or Quora because:
- They require expensive paid API access ($100-$5000/month)
- They heavily restrict public content access
- They require special partnership approvals
- Web scraping violates their Terms of Service

**Alternative:** Use RSS feeds from blogs and news sites that cover these platforms.

### Email Delivery
Email delivery is not built-in because:
- You can use services like Mailgun, SendGrid, or AWS SES
- It requires domain verification and DNS setup
- It's better handled by dedicated email services

**Alternative:** Export newsletters as HTML/PDF and send manually, or integrate with your preferred email service.

## 🛠 Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Database
npm run db:setup     # Set up database
npm run db:migrate   # Run migrations
npm run db:seed      # Seed sample data

# Testing
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
npm run test:coverage # Run tests with coverage

# Linting
npm run lint         # Run ESLint
npm run lint:fix     # Fix ESLint errors
```

### Project Structure

```
newsletter-machine/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page components
│   ├── services/      # API client and services
│   ├── types/         # TypeScript type definitions
│   └── data/          # Static data and configurations
├── server/
│   ├── src/
│   │   ├── routes/    # API route handlers
│   │   ├── services/  # Business logic
│   │   ├── collectors/ # Platform-specific collectors
│   │   └── data/      # Shared data structures
│   └── tests/         # Backend tests
└── public/            # Static assets
```

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## 📝 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: Check this README and the in-app help
- **Issues**: Report bugs on GitHub
- **Questions**: Open a discussion on GitHub

## 🎓 Learning Resources

### Setting Up Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Name your app (e.g., "Newsletter Machine")
4. Select "script" as the type
5. Set redirect URI to http://localhost:3000
6. Copy the Client ID (under the app name) and Client Secret

### Setting Up YouTube API
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Go to "APIs & Services" > "Library"
4. Search for "YouTube Data API v3" and enable it
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" > "API Key"
7. Copy the API key

### Finding RSS Feeds
Most blogs and news sites have RSS feeds. Look for:
- URL ending in `/feed`, `/rss`, or `.xml`
- RSS icon (orange square with white waves) in the browser
- "Subscribe" or "RSS" links in the footer

Popular RSS feeds:
- TechCrunch: https://techcrunch.com/feed/
- The Verge: https://www.theverge.com/rss/index.xml
- Wired: https://www.wired.com/feed/rss
- Hacker News: https://hnrss.org/frontpage

## 🚧 Roadmap

### Planned Features
- [ ] Scheduled newsletter generation
- [ ] Email delivery integration
- [ ] More content sources (with proper API access)
- [ ] Advanced filtering and ranking
- [ ] Newsletter templates
- [ ] Team collaboration
- [ ] Analytics dashboard

### Not Planned
- Paid social media API integrations (too expensive for most users)
- Web scraping (violates ToS)
- Real-time content streaming (not needed for newsletters)

---

**Built with honesty and transparency.** We tell you what works and what doesn't, so you can make informed decisions about your content strategy.
