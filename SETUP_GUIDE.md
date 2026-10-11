# Newsletter Machine - Setup and Runtime Verification Guide

## Prerequisites

1. **Node.js 18+** and npm
2. **Docker Desktop** or Docker Engine with docker-compose
3. **Git**

## Step 1: Start PostgreSQL Database

```bash
# Make the script executable
chmod +x setup-database.sh

# Run the setup script
./setup-database.sh
```

This will:
- Start a PostgreSQL container on port 5432
- Create the `newsletter_machine` database
- Create the `newsletter_user` user with password `newsletter_password`

**Verify PostgreSQL is running:**
```bash
docker-compose ps
# Should show newsletter_db as "Up"

docker exec newsletter_db pg_isready -U newsletter_user -d newsletter_machine
# Should return: "accepting connections"
```

## Step 2: Start Backend Server

The backend dependencies are already installed in the root `node_modules`. Start the server:

```bash
# From the project root
npx tsx server/src/index.ts
```

**Expected output:**
```
Database initialized successfully
Server running on port 3001
Environment: development
```

**Verify backend is running:**
```bash
curl http://localhost:3001/health
# Should return: {"status":"ok","timestamp":"..."}
```

## Step 3: Start Frontend

```bash
# From the project root (in a new terminal)
npm run dev
```

**Expected output:**
```
VITE v6.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

## Step 4: Verify Frontend-Backend Connection

Open http://localhost:5173 in your browser.

**Expected behavior:**
- You should see the login page
- The page should NOT show any console errors about API connection
- Network tab should show successful requests to `http://localhost:3001/api/*`

## Step 5: Test Complete Workflow

### 5.1 Register a Test User

1. Click "Create new account"
2. Enter:
   - Name: Test User
   - Email: test@example.com
   - Password: testpassword123
3. Click "Create Account"

**Expected:** Successfully logged in and redirected to dashboard

### 5.2 Create a Niche

1. Navigate to "Niches" in the sidebar
2. Click "New Niche"
3. Enter:
   - Name: AI News
   - Keywords: artificial intelligence, machine learning, AI
   - Blog Feeds: https://openai.com/blog/feed, https://blog.google/technology/ai/rss/
4. Click "Create Niche"

**Expected:** Niche appears in the list

### 5.3 Trigger Collection

1. Navigate to "Run History"
2. Select the "AI News" niche from dropdown
3. Click "Trigger Run"

**Expected:**
- Run status shows "running"
- After 10-30 seconds, status changes to "completed"
- Stats show items collected from RSS feeds

### 5.4 Verify Collected Items

Check the database directly:
```bash
docker exec -it newsletter_db psql -U newsletter_user -d newsletter_machine

# Count collected items
SELECT COUNT(*) FROM collected_items;

# View recent items
SELECT platform, title, url, collected_at 
FROM collected_items 
ORDER BY collected_at DESC 
LIMIT 10;
```

**Expected:** Multiple items collected from RSS feeds with real URLs and titles

### 5.5 Test Deduplication

Trigger another run for the same niche:
1. Go to "Run History"
2. Click "Trigger Run" again

Check database:
```sql
-- Should show duplicates were skipped
SELECT * FROM runs ORDER BY started_at DESC LIMIT 2;
```

The second run should show `deduplication.skipped > 0` in the stats JSON.

### 5.6 View Newsletter (if OpenAI key configured)

If you have an OpenAI API key:
1. Edit `server/.env` and add: `OPENAI_API_KEY=your-key-here`
2. Restart the backend
3. Trigger a collection run
4. Navigate to "Newsletter Archive"
5. Click on the generated newsletter

**Expected:** Full newsletter with AI-generated content based on collected items

**Without OpenAI key:** Newsletter generation will be skipped, but collection still works.

## Step 6: Verify Data Persistence

1. Refresh the browser (F5)
2. Navigate through all pages
3. Verify all data is still present

**Expected:** All niches, runs, and newsletters persist across refreshes

## Troubleshooting

### Backend won't start

**Error:** `Cannot find module 'express'`
**Solution:** Dependencies are in root node_modules. Run from project root: `npx tsx server/src/index.ts`

**Error:** `database "newsletter_machine" does not exist`
**Solution:** Run `./setup-database.sh` to create the database

**Error:** `connection refused` on port 5432
**Solution:** Check PostgreSQL is running: `docker-compose ps`

### Frontend can't connect to backend

**Error:** CORS errors in browser console
**Solution:** Verify `FRONTEND_URL` in `server/.env` matches your frontend URL (default: http://localhost:5173)

**Error:** Network requests fail
**Solution:** Verify backend is running on port 3001: `curl http://localhost:3001/health`

### Collection returns 0 items

**Issue:** RSS feeds not returning data
**Solution:** 
- Check niche has blog_feeds configured
- Verify feeds are accessible: `curl https://openai.com/blog/feed`
- Check backend logs for RSS parsing errors

### Newsletter not generated

**Issue:** OpenAI API key not configured
**Solution:** 
- Add `OPENAI_API_KEY` to `server/.env`
- Restart backend
- Note: Newsletter generation is optional; collection works without it

## API Endpoints Reference

All endpoints require authentication (JWT token in Authorization header).

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Niches
- `GET /api/niches` - List all niches
- `POST /api/niches` - Create niche
- `PUT /api/niches/:id` - Update niche
- `DELETE /api/niches/:id` - Delete niche

### Sources
- `GET /api/sources` - List all sources with status
- `PUT /api/sources/:platform` - Update source status

### Runs
- `GET /api/runs` - List collection runs
- `POST /api/runs` - Trigger new collection
- `GET /api/runs/:id` - Get run details

### Newsletters
- `GET /api/newsletters` - List newsletters
- `GET /api/newsletters/:id` - Get newsletter
- `POST /api/newsletters/:id/feedback` - Submit feedback
- `GET /api/newsletters/feedback/stats` - Get feedback stats

## Security Notes

- **Never commit `.env` files** - They contain secrets
- **Change JWT_SECRET** in production to a strong random string
- **Use strong passwords** for database and API keys
- **Enable HTTPS** in production
- **Rotate API keys** regularly

## Next Steps

After verifying the core workflow:
1. Configure Reddit API credentials for Reddit collection
2. Configure YouTube API key for YouTube collection
3. Set up OpenAI API for newsletter generation
4. Configure SMTP for email delivery (optional)
5. Deploy to production with proper security measures
