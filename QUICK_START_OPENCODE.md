# 🚀 Quick Start Guide for OpenCode

## Copy This Prompt to OpenCode

```
I need you to help me set up the Newsletter Machine project. The project is already created with all the code. I need you to:

1. VERIFY PREREQUISITES
   - Check Node.js version (need v18+)
   - Check npm version (need v8+)
   - Confirm no local PostgreSQL needed (we use Supabase)

2. SETUP SUPABASE
   - Guide me to create a Supabase project at https://supabase.com
   - Help me get the project URL, anon key, and service role key
   - Update server/.env with Supabase credentials
   - Update root .env with Supabase URL and anon key
   - Enable Email authentication in Supabase dashboard

3. SETUP GOOGLE OAUTH
   - Guide me to create a Google Cloud project
   - Configure OAuth consent screen (External, add test users)
   - Create OAuth 2.0 credentials (Web application)
   - Add redirect URI: https://[project-id].supabase.co/auth/v1/callback
   - Copy Client ID and Client Secret
   - Enable Google provider in Supabase Authentication → Providers
   - Update server/.env with Google credentials

4. INSTALL DEPENDENCIES
   - Run: npm install (frontend)
   - Run: cd server && npm install (backend)
   - Verify node_modules exist in both locations

5. START BACKEND
   - Run: cd server && npm run dev
   - Verify output shows: "✅ Supabase database initialized"
   - Verify output shows: "🚀 Server running on port 3001"
   - Test health check: curl http://localhost:3001/health
   - Verify database tables created in Supabase dashboard

6. START FRONTEND
   - Open new terminal
   - Run: npm run dev
   - Verify output shows: "Local: http://localhost:5173/"
   - Open browser to http://localhost:5173

7. TEST AUTHENTICATION
   - Test email/password sign up
   - Test email/password login
   - Test Google sign in
   - Test forgot password flow
   - Test logout
   - Test protected routes redirect to login

8. TEST CORE FEATURES
   - Create a niche
   - View sources page
   - Verify data persists after browser refresh
   - Verify data is isolated between users

9. VERIFY SUCCESS
   - Backend running on port 3001
   - Frontend running on port 5173
   - Can sign up/login with email
   - Can sign in with Google
   - Can reset password
   - Database tables exist in Supabase
   - Can create niches
   - Data persists after refresh

If any step fails, help me troubleshoot by:
- Checking error messages
- Verifying environment variables
- Checking Supabase dashboard for errors
- Checking Google Cloud Console configuration
- Reviewing browser console for errors

Please guide me through each step one at a time and wait for my confirmation before proceeding to the next step.
```

---

## 📋 What You'll Need

### Before Starting
- [ ] Node.js v18+ installed
- [ ] npm v8+ installed
- [ ] Supabase account (free)
- [ ] Google Cloud account (free)
- [ ] Text editor (VS Code recommended)
- [ ] Terminal/command prompt

### Credentials to Prepare
- [ ] Supabase project URL
- [ ] Supabase anon key
- [ ] Supabase service role key
- [ ] Google OAuth Client ID
- [ ] Google OAuth Client Secret

---

## 🎯 Expected Timeline

- **Supabase Setup:** 5 minutes
- **Google OAuth Setup:** 10 minutes
- **Install Dependencies:** 2 minutes
- **Start Servers:** 1 minute
- **Test Everything:** 10 minutes

**Total:** ~30 minutes

---

## ✅ Success Indicators

You know it's working when:

1. **Backend Terminal Shows:**
   ```
   ✅ Supabase database initialized
   🚀 Server running on port 3001
   💚 Health check: http://localhost:3001/health
   ```

2. **Frontend Terminal Shows:**
   ```
   VITE v6.x.x  ready in XXX ms
   ➜  Local:   http://localhost:5173/
   ```

3. **Browser Shows:**
   - Login page at http://localhost:5173
   - Can sign up with email
   - Can sign in with Google
   - Dashboard loads after login

4. **Supabase Dashboard Shows:**
   - Tables created (niches, sources, etc.)
   - Users in Authentication → Users
   - Data in tables after creating niches

---

## 🐛 Common Issues & Solutions

### "Module not found" errors
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
cd server && rm -rf node_modules package-lock.json && npm install
```

### "Port already in use"
```bash
# Kill process on port 3001
lsof -i :3001
kill -9 <PID>
```

### "Invalid redirect_uri" (Google)
- Wait 5 minutes after updating Google Cloud Console
- Verify exact match: `https://[project-id].supabase.co/auth/v1/callback`

### "User not in test users"
- Add email to Google Cloud Console → OAuth consent screen → Test users

### "CORS error"
- Add `http://localhost:5173` to Supabase → Authentication → URL Configuration

---

## 📚 Detailed Documentation

For complete details, see:
- **OPENCODE_SETUP_PROMPT.md** - Full step-by-step guide
- **SUPABASE_SETUP_GUIDE.md** - Supabase configuration details
- **GOOGLE_AUTH_IMPLEMENTATION.md** - Authentication implementation details

---

## 🎉 After Setup

Once everything is working:

1. **Explore the app:**
   - Create niches
   - Add RSS feeds
   - View sources
   - Check out the Live Scrape Demo

2. **Configure RLS (important for production):**
   - Supabase → Table Editor
   - Enable RLS on all tables
   - Add policies for user data isolation

3. **Deploy to production:**
   - Follow PRODUCTION_DEPLOYMENT_GUIDE.md
   - Update environment variables
   - Configure custom domain

---

## 💡 Tips for OpenCode

When working with OpenCode:

1. **Be specific** - Tell it exactly what you want
2. **One step at a time** - Don't rush through setup
3. **Share errors** - Copy/paste exact error messages
4. **Verify each step** - Don't proceed until current step works
5. **Ask questions** - If something is unclear, ask for clarification

---

## 🚀 Ready to Start?

1. Open this project in your code editor
2. Open a terminal
3. Copy the prompt above to OpenCode
4. Follow the instructions step by step
5. Enjoy your Newsletter Machine! 🎉

---

**Need help?** Check the troubleshooting section in OPENCODE_SETUP_PROMPT.md or refer to the detailed guides.
