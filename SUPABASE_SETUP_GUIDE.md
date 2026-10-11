# Supabase & Google Authentication Setup Guide

This guide will help you set up Supabase database and Google OAuth authentication for the Newsletter Machine.

## 📋 Prerequisites

- A Supabase account (free tier available)
- A Google Cloud account (free tier available)
- Node.js 18+ installed
- npm or yarn package manager

---

## 🗄️ Step 1: Set Up Supabase

### 1.1 Create a Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in the details:
   - **Name:** Newsletter Machine
   - **Database Password:** (save this somewhere secure)
   - **Region:** Choose closest to your users
   - **Pricing Plan:** Free (to start)
5. Click "Create new project"
6. Wait for the project to initialize (takes ~2 minutes)

### 1.2 Get Your Supabase Credentials

1. In your Supabase dashboard, go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **service_role key** (secret key - keep this private!)
   - **anon public key** (safe to expose in frontend)

### 1.3 Configure Environment Variables

Create a `.env` file in the `server/` directory:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_KEY=your-service-key-here

# Server
PORT=3001
NODE_ENV=development
FRONTEND_URL=http://localhost:5173

# JWT Secret (generate with: openssl rand -base64 32)
JWT_SECRET=your-jwt-secret-here
```

Create a `.env` file in the root directory for the frontend:

```bash
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here
```

### 1.4 Enable Email Auth (Optional)

1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Make sure **Email** is enabled
3. Configure email templates if needed

---

## 🔐 Step 2: Set Up Google OAuth

### 2.1 Create Google Cloud Project

1. Go to [https://console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project:
   - **Project name:** Newsletter Machine
   - **Organization:** Your organization
3. Wait for project creation

### 2.2 Configure OAuth Consent Screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill in the required fields:
   - **App name:** Newsletter Machine
   - **User support email:** your-email@example.com
   - **Developer contact information:** your-email@example.com
4. Click **Save and Continue**
5. On **Scopes** page, click **Add or Remove Scopes**
6. Search for and add:
   - `.../auth/userinfo.email`
   - `.../auth/userinfo.profile`
7. Click **Update**
8. Click **Save and Continue**
9. On **Test users** page, click **Add users**
10. Add the email addresses of users who will test the app
11. Click **Save and Continue**
12. Review and click **Back to Dashboard**

### 2.3 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. **Application type:** Web application
4. **Name:** Newsletter Machine Web Client
5. Under **Authorized redirect URIs**, add:
   ```
   https://your-project.supabase.co/auth/v1/callback
   ```
   (Replace `your-project` with your actual Supabase project ID)
6. Click **Create**
7. **Important:** Copy and save these credentials:
   - **Client ID**
   - **Client Secret**

### 2.4 Configure Google Auth in Supabase

1. In Supabase dashboard, go to **Authentication** → **Providers**
2. Click on **Google**
3. Enable the Google provider
4. Paste your credentials:
   - **Client ID:** (from Google Cloud Console)
   - **Client Secret:** (from Google Cloud Console)
5. Click **Save**

### 2.5 Update Environment Variables

Add to your `server/.env`:

```bash
# Google OAuth (optional - configured in Supabase)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

---

## 🗃️ Step 3: Initialize Database Schema

The database schema will be automatically created when you start the backend server for the first time. The following tables will be created:

- `niches` - User-configured content topics
- `sources` - Platform connection configurations
- `collected_items` - Scraped content items
- `runs` - Collection run history
- `newsletters` - Generated newsletters
- `feedback` - User feedback on stories

Supabase's built-in `auth.users` table will handle user authentication.

---

## 🚀 Step 4: Start the Application

### 4.1 Install Dependencies

```bash
# Install frontend dependencies
npm install

# Install backend dependencies
cd server
npm install
```

### 4.2 Start Backend Server

```bash
cd server
npm run dev
```

You should see:
```
✅ Supabase database initialized
🚀 Server running on port 3001
🌍 Environment: development
💚 Health check: http://localhost:3001/health
```

### 4.3 Start Frontend

In a new terminal:

```bash
npm run dev
```

You should see:
```
VITE v6.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

## ✅ Step 5: Test Authentication

### 5.1 Test Email/Password Sign Up

1. Open `http://localhost:5173`
2. Click "Sign up"
3. Enter:
   - Name: Test User
   - Email: test@example.com
   - Password: test123456
4. Click "Create Account"
5. Check your email for verification link (if email confirmation is enabled)

### 5.2 Test Google Sign In

1. On the login page, click "Continue with Google"
2. Select your Google account (must be in the test users list)
3. Grant permissions
4. You should be redirected back to the app and logged in

### 5.3 Test Forgot Password

1. Log out
2. Click "Forgot password?"
3. Enter your email
4. Check your email for reset link
5. Click the link and set a new password
6. Log in with the new password

---

## 🔧 Troubleshooting

### Issue: "Invalid redirect_uri"

**Solution:** Make sure the redirect URI in Google Cloud Console exactly matches:
```
https://your-project.supabase.co/auth/v1/callback
```

### Issue: "User not in test users list"

**Solution:** Add the user's email to the test users list in Google Cloud Console OAuth consent screen.

### Issue: "Database connection failed"

**Solution:** 
1. Check your `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` in `.env`
2. Make sure your Supabase project is active
3. Check the Supabase dashboard for any errors

### Issue: "CORS error"

**Solution:** 
1. In Supabase dashboard, go to **Authentication** → **URL Configuration**
2. Add `http://localhost:5173` to **Site URL**
3. Add `http://localhost:5173/**` to **Redirect URLs**

---

## 📊 Supabase Dashboard Features

Once set up, you can use the Supabase dashboard to:

- **View users:** Authentication → Users
- **Manage database:** Table Editor
- **View logs:** Logs → API
- **Monitor usage:** Project Settings → Billing
- **Configure auth:** Authentication → Providers
- **Manage storage:** Storage (for file uploads)

---

## 🔒 Security Best Practices

1. **Never commit `.env` files** - They contain sensitive keys
2. **Use environment variables** - Never hardcode secrets
3. **Enable Row Level Security (RLS)** - In Supabase Table Editor
4. **Use service_role key only on backend** - Never expose in frontend
5. **Rotate keys regularly** - Especially if compromised
6. **Enable 2FA** - On Supabase and Google accounts
7. **Monitor usage** - Check Supabase dashboard regularly

---

## 📚 Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Auth Guide](https://supabase.com/docs/guides/auth)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript/introduction)

---

## 🎯 Next Steps

After setting up authentication:

1. **Configure RLS policies** - Protect your data
2. **Set up email templates** - Customize auth emails
3. **Add more OAuth providers** - GitHub, Twitter, etc.
4. **Configure custom domains** - For production
5. **Set up monitoring** - Track usage and errors
6. **Deploy to production** - Follow deployment guide

---

## ✅ Checklist

- [ ] Created Supabase project
- [ ] Copied Supabase credentials to `.env`
- [ ] Created Google Cloud project
- [ ] Configured OAuth consent screen
- [ ] Created OAuth 2.0 credentials
- [ ] Added redirect URI to Google Cloud
- [ ] Enabled Google provider in Supabase
- [ ] Added test users to Google OAuth
- [ ] Started backend server
- [ ] Started frontend dev server
- [ ] Tested email/password sign up
- [ ] Tested Google sign in
- [ ] Tested forgot password flow
- [ ] Verified database tables created
- [ ] Checked authentication working

---

**Need help?** Check the troubleshooting section or visit the Supabase Discord community.
