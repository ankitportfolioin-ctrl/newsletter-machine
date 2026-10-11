# Newsletter Machine - Production Ready

> **Quick Start:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete setup instructions.

A full-stack AI-powered newsletter generation platform that aggregates content from multiple sources (Reddit, YouTube, RSS feeds) and generates curated newsletters using OpenAI.

## Features

- **Real User Authentication**: JWT-based auth with secure password hashing
- **Multi-Platform Content Collection**: 
  - Reddit API integration (OAuth2)
  - YouTube Data API v3
  - RSS/Atom feed parsing
- **AI-Powered Newsletter Generation**: OpenAI GPT-4 for content curation
- **PostgreSQL Database**: Persistent storage for all data
- **RESTful API**: Complete backend API with rate limiting
- **Modern Frontend**: React 18 + TypeScript + Tailwind CSS
- **Real-Time Updates**: Live collection status and progress tracking

## Architecture

```
┌─────────────────┐
│   React Frontend│
│   (Port 3000)   │
└────────┬────────┘
         │
         │ HTTP/REST
         │
┌────────▼────────┐
│  Express Backend│
│   (Port 3001)   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┐
    │         │          │          │
┌───▼──┐  ┌──▼───┐  ┌───▼───┐  ┌──▼────┐
│Reddit│  │YouTube│  │RSS/   │  │OpenAI │
│ API  │  │ API   │  │Blogs  │  │  API  │
└──────┘  └──────┘  └───────┘  └───────┘
         │
    ┌────▼────┐
    │PostgreSQL│
    │Database │
    └─────────┘
```

## Prerequisites

- Node.js 18+ and npm
- PostgreSQL 14+ (or Supabase)
- API Keys:
  - Reddit API (create app at https://www.reddit.com/prefs/apps)
  - YouTube Data API (https://console.cloud.google.com/)
  - OpenAI API (https://platform.openai.com/)

## Setup Instructions

### 1. Database Setup

**Option A: Local PostgreSQL**
```bash
# Create database
createdb newsletter_machine

# Or using psql
psql
CREATE DATABASE newsletter_machine;
```

**Option B: Supabase**
1. Create a new project at https://supabase.com
2. Get your connection string from Project Settings > Database

### 2. Backend Setup

```bash
# Navigate to server directory
cd server

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

**Required Environment Variables:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/newsletter_machine
JWT_SECRET=your-super-secret-jwt-key-change-this
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
FRONTEND_URL=http://localhost:3000
```

### 3. Frontend Setup

```bash
# From project root
npm install

# Create .env file (optional)
echo "VITE_API_URL=http://localhost:3001/api" > .env
```

### 4. Run the Application

**Development Mode (both frontend and backend):**
```bash
# Terminal 1 - Backend
cd server
npm run dev

# Terminal 2 - Frontend
npm run dev
```

**Production Build:**
```bash
# Build frontend
npm run build

# Build backend
cd server
npm run build
npm start
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Niches
- `GET /api/niches` - List all niches
- `POST /api/niches` - Create niche
- `PUT /api/niches/:id` - Update niche
- `DELETE /api/niches/:id` - Delete niche

### Runs
- `GET /api/runs` - List collection runs
- `POST /api/runs` - Trigger new collection run
- `GET /api/runs/:id` - Get run details

### Newsletters
- `GET /api/newsletters` - List newsletters
- `GET /api/newsletters/:id` - Get newsletter
- `POST /api/newsletters/:id/feedback` - Submit feedback
- `GET /api/newsletters/feedback/stats` - Get feedback stats

## Platform Integration Status

### Fully Implemented
- ✅ **Reddit**: Full OAuth2 authentication, subreddit collection, keyword filtering
- ✅ **YouTube**: Search API, video details, metadata extraction
- ✅ **RSS/Blogs**: Feed parsing, keyword filtering, metadata extraction
- ✅ **Newsletter Generation**: OpenAI GPT-4 integration with structured output

### Requires Additional Setup
- ⚠️ **X (Twitter)**: Requires API v2 access (apply at https://developer.twitter.com/)
- ⚠️ **LinkedIn**: Requires OAuth app approval
- ⚠️ **Instagram**: Requires Facebook app review
- ⚠️ **Facebook**: Requires app review for content access
- ⚠️ **Quora**: No official API (would need web scraping)

## Database Schema

The application automatically creates these tables on first run:

- `users` - User accounts with hashed passwords
- `niches` - Content topics and collection configuration
- `sources` - Platform connection status and credentials
- `collected_items` - Raw content collected from platforms
- `runs` - Collection run history and statistics
- `newsletters` - Generated newsletter content
- `feedback` - User feedback on newsletter stories

## Security Features

- JWT-based authentication with 7-day expiry
- Password hashing with bcrypt (10 rounds)
- CORS protection
- Helmet.js security headers
- Rate limiting (100 requests per 15 minutes)
- Input validation with Zod
- SQL injection protection (parameterized queries)

## Deployment

### Backend (Node.js)
```bash
cd server
npm run build
npm start
```

### Frontend (Static)
```bash
npm run build
# Serve dist/ folder with nginx, Vercel, Netlify, etc.
```

### Environment Variables for Production
```env
NODE_ENV=production
DATABASE_URL=your_production_database_url
JWT_SECRET=strong_random_secret
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
YOUTUBE_API_KEY=...
OPENAI_API_KEY=...
FRONTEND_URL=https://yourdomain.com
```

## Troubleshooting

**Database Connection Issues:**
- Verify DATABASE_URL is correct
- Check PostgreSQL is running: `pg_isready`
- Ensure database exists: `psql -l | grep newsletter_machine`

**API Authentication Errors:**
- Verify all API keys in .env
- Reddit: Ensure app type is "script" or "web app"
- YouTube: Enable YouTube Data API v3 in Google Cloud Console
- OpenAI: Check API key has sufficient credits

**CORS Errors:**
- Ensure FRONTEND_URL matches your frontend origin exactly
- Update backend CORS configuration if needed

## Development

```bash
# Run backend in watch mode
cd server
npm run dev

# Run frontend in dev mode
npm run dev

# Type checking
npm run typecheck

# Build
npm run build
```

## License

MIT

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation for your platforms
3. Check server logs for detailed error messages
