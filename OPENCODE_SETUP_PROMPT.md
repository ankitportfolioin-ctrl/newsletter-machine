# OpenCode Setup Prompt for Newsletter Machine

## Context
You are setting up a full-stack Newsletter Machine application with:
- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Backend:** Node.js + Express + TypeScript
- **Database:** Supabase (PostgreSQL with built-in auth)
- **Authentication:** Google OAuth + Email/Password via Supabase

The project structure is already created. Your job is to configure, install dependencies, and verify everything works.

---

## Phase 1: Prerequisites Check

### Step 1.1: Verify Node.js Installation
```bash
node --version
```
**Expected:** v18.0.0 or higher

If not installed:
- Download from: https://nodejs.org/
- Or use: `nvm install 18` (if nvm is available)

### Step 1.2: Verify npm Installation
```bash
npm --version
```
**Expected:** 8.0.0 or higher

### Step 1.3: Check if PostgreSQL is Needed
**Note:** We're using Supabase (cloud PostgreSQL), so local PostgreSQL is NOT required.

---

## Phase 2: Supabase Setup

### Step 2.1: Create Supabase Account
1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub (recommended) or email
4. Verify your email

### Step 2.2: Create New Project
1. Click "New Project"
2. Fill in:
   - **Organization:** Select your organization
   - **Project name:** `newsletter-machine`
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your location
   - **Pricing Plan:** Free (to start)
3. Click "Create new project"
4. Wait ~2 minutes for project initialization

### Step 2.3: Get Supabase Credentials
1. In Supabase dashboard, go to **Project Settings** (gear icon) → **API**
2. Copy these values:
   - **Project URL:** `https://xxxxx.supabase.co`
   - **service_role key:** (secret - keep private!)
   - **anon public key:** (safe for frontend)

### Step 2.4: Configure Supabase Environment Variables

**Backend (.env file in server/ directory):**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key-here
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Server Configuration
PORT=3001
NODE_ENV=development
FRONTEND_URL=http://localhost:5173

# JWT Secret (generate with: openssl rand -base64 32)
JWT_SECRET=generate-a-secure-random-string-here

# Optional: API Keys (leave empty for now)
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
YOUTUBE_API_KEY=
OPENAI_API_KEY=
```

**Frontend (.env file in root directory):**
```bash
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-public-key-here
```

### Step 2.5: Enable Email Authentication
1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Make sure **Email** is enabled
3. Optional: Configure email templates

---

## Phase 3: Google OAuth Setup

### Step 3.1: Create Google Cloud Project
1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. **Project name:** `Newsletter Machine`
4. **Organization:** Select your organization
5. Click "Create"
6. Wait for project creation

### Step 3.2: Configure OAuth Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Click "Create"
4. Fill in:
   - **App name:** Newsletter Machine
   - **User support email:** your-email@example.com
   - **Developer contact information:** your-email@example.com
5. Click "Save and Continue"
6. On **Scopes** page:
   - Click "Add or Remove Scopes"
   - Search and select:
     - `.../auth/userinfo.email`
     - `.../auth/userinfo.profile`
   - Click "Update"
7. Click "Save and Continue"
8. On **Test users** page:
   - Click "Add users"
   - Add email addresses of people who will test the app
   - Click "Add"
9. Click "Save and Continue"
10. Review and click "Back to Dashboard"

### Step 3.3: Create OAuth 2.0 Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. **Application type:** Web application
4. **Name:** Newsletter Machine Web Client
5. Under **Authorized redirect URIs**, click "+ ADD URI"
6. Add: `https://your-project-id.supabase.co/auth/v1/callback`
   (Replace `your-project-id` with your actual Supabase project ID)
7. Click "Create"
8. **IMPORTANT:** Copy and save these credentials:
   - **Client ID:** `xxxxx.apps.googleusercontent.com`
   - **Client Secret:** `xxxxx`

### Step 3.4: Configure Google Auth in Supabase
1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Click on **Google**
3. Toggle "Enable Provider" to ON
4. Paste your credentials:
   - **Client ID:** (from Google Cloud Console)
   - **Client Secret:** (from Google Cloud Console)
5. Click "Save"

### Step 3.5: Update Backend Environment Variables
Add to `server/.env`:
```bash
# Google OAuth (optional - configured in Supabase, but good to have)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## Phase 4: Install Dependencies

### Step 4.1: Install Frontend Dependencies
```bash
# From project root
npm install
```

**Expected output:**
```
added XXX packages in Xs
```

### Step 4.2: Install Backend Dependencies
```bash
# From server directory
cd server
npm install
```

**Expected output:**
```
added XXX packages in Xs
```

### Step 4.3: Verify Installation
```bash
# Check if node_modules exists
ls -la node_modules | head -5
ls -la server/node_modules | head -5
```

**Expected:** Both should show directory contents

---

## Phase 5: Start Backend Server

### Step 5.1: Start Backend in Development Mode
```bash
# From server directory
cd server
npm run dev
```

**Expected output:**
```
✅ Supabase database initialized
🚀 Server running on port 3001
🌍 Environment: development
💚 Health check: http://localhost:3001/health
```

**If you see errors:**
- Check `server/.env` has correct Supabase credentials
- Verify Supabase project is active
- Check internet connection

### Step 5.2: Test Backend Health Check
Open browser or use curl:
```bash
curl http://localhost:3001/health
```

**Expected response:**
```json
{
  "status": "ok",
  "timestamp": "2026-01-20T...",
  "environment": "development",
  "database": {
    "status": "healthy",
    "provider": "supabase"
  },
  "uptime": X.XX,
  "memory": {...}
}
```

### Step 5.3: Verify Database Tables
1. Go to Supabase dashboard
2. Click **Table Editor** in left sidebar
3. You should see these tables:
   - `niches`
   - `sources`
   - `collected_items`
   - `runs`
   - `newsletters`
   - `feedback`

**If tables don't exist:**
- Check backend logs for errors
- Verify `SUPABASE_SERVICE_KEY` is correct
- Restart backend server

---

## Phase 6: Start Frontend

### Step 6.1: Start Frontend in Development Mode
Open a **new terminal** and run:
```bash
# From project root
npm run dev
```

**Expected output:**
```
VITE v6.x.x  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
➜  press h + enter to show help
```

### Step 6.2: Open Application
1. Open browser
2. Go to: http://localhost:5173
3. You should see the **Login page**

---

## Phase 7: Test Authentication

### Step 7.1: Test Email/Password Sign Up
1. On login page, click **"Sign up"**
2. Fill in:
   - **Name:** Test User
   - **Email:** test@example.com
   - **Password:** test123456
3. Click **"Create Account"**

**Expected:**
- Success message: "Account created! Please check your email to verify."
- Check your email for verification link (if email confirmation enabled)
- After verification, you can log in

### Step 7.2: Test Email/Password Login
1. On login page, enter:
   - **Email:** test@example.com
   - **Password:** test123456
2. Click **"Sign In"**

**Expected:**
- Redirected to Dashboard
- See welcome message and navigation

### Step 7.3: Test Google Sign In
1. On login page, click **"Continue with Google"**
2. Select your Google account (must be in test users list)
3. Grant permissions

**Expected:**
- Redirected to Google login
- After approval, redirected back to app
- Logged in and on Dashboard

### Step 7.4: Test Forgot Password
1. Log out (click user icon → Logout)
2. On login page, click **"Forgot password?"**
3. Enter your email: test@example.com
4. Click **"Send Reset Email"**

**Expected:**
- Success message: "Password reset email sent! Check your inbox."
- Check email for reset link
- Click link and set new password
- Log in with new password

### Step 7.5: Test Protected Routes
1. Log out
2. Try to access: http://localhost:5173/#/niches

**Expected:**
- Redirected to login page
- After login, redirected back to niches page

---

## Phase 8: Test Core Features

### Step 8.1: Create a Niche
1. Click **"Niches"** in sidebar
2. Click **"New Niche"**
3. Fill in:
   - **Name:** AI News
   - **Keywords:** AI, machine learning, GPT
   - **Blog Feeds:** https://techcrunch.com/feed/
4. Click **"Create Niche"**

**Expected:**
- Niche appears in list
- Check Supabase Table Editor → niches table has new row

### Step 8.2: View Sources
1. Click **"Sources"** in sidebar

**Expected:**
- See list of platforms (Blogs, Reddit, YouTube, etc.)
- Status indicators show what's available

### Step 8.3: Trigger Collection (Optional - Requires API Keys)
**Note:** This requires Reddit/YouTube API keys. Skip if not configured.

1. Click **"Run History"**
2. Select your niche
3. Click **"Trigger Run"**

**Expected:**
- Run starts
- Status changes to "completed" after 10-30 seconds
- Check Supabase → collected_items table

---

## Phase 9: Verify Data Persistence

### Step 9.1: Test Data Persistence
1. Create a niche
2. Refresh the browser (F5)
3. Check if niche still exists

**Expected:**
- Niche persists after refresh
- Data is stored in Supabase

### Step 9.2: Test Multi-User Isolation
1. Log out
2. Create another account: test2@example.com
3. Log in with new account
4. Check niches

**Expected:**
- New user sees empty niches list
- Data is isolated per user

---

## Phase 10: Troubleshooting

### Issue: "Cannot connect to Supabase"
**Solution:**
1. Check `server/.env` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
2. Verify Supabase project is active
3. Check internet connection
4. Restart backend server

### Issue: "Invalid redirect_uri" (Google OAuth)
**Solution:**
1. Go to Google Cloud Console → Credentials
2. Edit OAuth client
3. Add exact redirect URI: `https://your-project-id.supabase.co/auth/v1/callback`
4. Save and wait 5 minutes for changes to propagate

### Issue: "User not in test users list"
**Solution:**
1. Go to Google Cloud Console → OAuth consent screen
2. Add user's email to test users
3. Save changes

### Issue: "CORS error"
**Solution:**
1. In Supabase dashboard → Authentication → URL Configuration
2. Add `http://localhost:5173` to Site URL
3. Add `http://localhost:5173/**` to Redirect URLs

### Issue: "Database tables not created"
**Solution:**
1. Check backend logs for errors
2. Verify `SUPABASE_SERVICE_KEY` is correct (not anon key)
3. Restart backend server
4. Check Supabase dashboard for any error messages

### Issue: "Port 3001 already in use"
**Solution:**
```bash
# Find process using port 3001
lsof -i :3001

# Kill the process
kill -9 <PID>

# Or change port in server/.env
PORT=3002
```

### Issue: "Module not found" errors
**Solution:**
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install

cd server
rm -rf node_modules package-lock.json
npm install
```

---

## Phase 11: Production Deployment (Optional)

### Step 11.1: Build for Production
```bash
# Build frontend
npm run build

# Build backend
cd server
npm run build
```

### Step 11.2: Deploy Backend
Options:
- **Railway:** https://railway.app (easiest)
- **Render:** https://render.com
- **Fly.io:** https://fly.io
- **AWS/GCP/Azure:** Manual setup

### Step 11.3: Deploy Frontend
Options:
- **Vercel:** https://vercel.com (easiest)
- **Netlify:** https://netlify.com
- **Cloudflare Pages:** https://pages.cloudflare.com

### Step 11.4: Update Environment Variables
Update `FRONTEND_URL` and CORS settings for production domain.

---

## Phase 12: Final Checklist

### Authentication
- [ ] Email/password sign up works
- [ ] Email/password login works
- [ ] Google sign in works
- [ ] Forgot password sends email
- [ ] Reset password works
- [ ] Logout works
- [ ] Protected routes redirect to login

### Database
- [ ] Supabase connection works
- [ ] Tables created automatically
- [ ] CRUD operations work
- [ ] User data is isolated
- [ ] Data persists after refresh

### Frontend
- [ ] Builds without errors
- [ ] All pages load
- [ ] Navigation works
- [ ] Responsive design works
- [ ] Dark mode works

### Backend
- [ ] Starts without errors
- [ ] Health check returns 200
- [ ] API endpoints respond
- [ ] Error handling works
- [ ] Logs are informative

### Security
- [ ] No secrets in frontend code
- [ ] CORS configured correctly
- [ ] Rate limiting works
- [ ] Input validation works
- [ ] Authentication required for protected routes

---

## Phase 13: Next Steps

After successful setup:

1. **Configure Row Level Security (RLS)** in Supabase
   - Go to Supabase → Authentication → Policies
   - Enable RLS on all tables
   - Add policies to restrict access to user's own data

2. **Add More OAuth Providers** (optional)
   - GitHub, Twitter, etc.
   - Follow same pattern as Google

3. **Configure Email Templates**
   - Customize welcome emails
   - Customize password reset emails

4. **Set Up Monitoring**
   - Supabase dashboard → Logs
   - Set up error tracking (Sentry, etc.)

5. **Deploy to Production**
   - Follow deployment guide
   - Update environment variables
   - Test thoroughly

---

## Success Criteria

You've successfully set up the project when:

✅ Backend starts without errors  
✅ Frontend starts without errors  
✅ You can sign up with email/password  
✅ You can sign in with Google  
✅ You can reset your password  
✅ Database tables are created  
✅ You can create niches  
✅ Data persists after refresh  
✅ Protected routes work  
✅ No console errors in browser  

---

## Need Help?

- **Supabase Docs:** https://supabase.com/docs
- **Google OAuth Docs:** https://developers.google.com/identity/protocols/oauth2
- **Project Documentation:** Check README.md, SUPABASE_SETUP_GUIDE.md

---

## Summary

**What you've accomplished:**
1. ✅ Created Supabase project
2. ✅ Configured Google OAuth
3. ✅ Installed all dependencies
4. ✅ Started backend server
5. ✅ Started frontend dev server
6. ✅ Tested authentication flows
7. ✅ Verified database operations
8. ✅ Confirmed data persistence

**Your Newsletter Machine is now ready to use!** 🎉
