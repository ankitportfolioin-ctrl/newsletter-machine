# 🔐 Default Credentials & First User Setup

## Current Status: NO Default Credentials

**The application does NOT have any default email/password.**

This is intentional for security reasons. Production applications should never have hardcoded default credentials.

---

## ✅ How to Create Your First User

You have **3 options** to create your first user account:

---

### Option 1: Use the Seed Script (Recommended for Development)

I've created a seed script that will create a default admin user with sample data.

**Run the seed script:**
```bash
cd server
node seed.js
```

**This will create:**
- **Email:** `admin@newsmachine.local`
- **Password:** `Admin123!`
- **Name:** Admin User
- **3 sample niches** with pre-configured RSS feeds

**⚠️ IMPORTANT:** Change the password immediately after first login!

---

### Option 2: Register Through the UI (Recommended for Production)

1. Start the application:
   ```bash
   # Terminal 1 - Backend
   cd server
   npm run dev
   
   # Terminal 2 - Frontend
   npm run dev
   ```

2. Open your browser: `http://localhost:5173`

3. Click **"Create new account"** on the login page

4. Fill in the registration form:
   - **Name:** Your name
   - **Email:** your@email.com
   - **Password:** Choose a strong password (min 6 characters)

5. Click **"Create Account"**

6. You'll be automatically logged in and redirected to the dashboard

---

### Option 3: Use the API Directly (For Developers)

**Register a new user via API:**

```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourSecurePassword123!",
    "name": "Your Name"
  }'
```

**Response:**
```json
{
  "user": {
    "id": "uuid-here",
    "email": "your@email.com",
    "name": "Your Name"
  },
  "token": "jwt-token-here"
}
```

**Login with the created user:**

```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourSecurePassword123!"
  }'
```

---

## 🎯 Recommended Approach

### For Development/Testing:
```bash
# Use the seed script
cd server
node seed.js

# Login credentials:
# Email: admin@newsmachine.local
# Password: Admin123!
```

### For Production:
1. Deploy the application
2. Open the website
3. Click "Create new account"
4. Register with your real email and a strong password
5. Verify your email (if email verification is enabled)

---

## 🔒 Security Best Practices

### Password Requirements
- Minimum 6 characters (enforced by frontend)
- Recommended: 12+ characters
- Use a mix of: uppercase, lowercase, numbers, symbols
- Never use: "password", "123456", your name, etc.

### For Production Deployment
1. **Never use default credentials** - Always create your own account
2. **Use strong passwords** - 12+ characters with mixed case
3. **Enable 2FA** (if implemented in future)
4. **Regular password rotation** - Change passwords every 90 days
5. **Monitor login attempts** - Check for suspicious activity

---

## 📋 Quick Start Guide

### Step 1: Start the Application
```bash
# Terminal 1 - Backend
cd server
npm run dev

# Terminal 2 - Frontend (in a new terminal)
npm run dev
```

### Step 2: Create Your Account

**Option A: Use Seed Script**
```bash
cd server
node seed.js
# Then login with: admin@newsmachine.local / Admin123!
```

**Option B: Register via UI**
1. Open `http://localhost:5173`
2. Click "Create new account"
3. Fill in your details
4. Click "Create Account"

### Step 3: Start Using the App
1. Create your first niche
2. Add RSS feeds or connect Reddit/YouTube
3. Trigger a collection run
4. View your generated newsletter

---

## 🆘 Troubleshooting

### "User already exists" Error
If you get this error when running the seed script, it means the default user was already created. You can:
1. Login with the existing credentials
2. Delete the user from the database and re-run the seed
3. Register a new account through the UI

### "Invalid credentials" Error
- Double-check your email and password
- Make sure there are no extra spaces
- Try resetting your password (if password reset is implemented)
- Check the database to verify the user exists

### Database Connection Error
- Make sure PostgreSQL is running
- Verify your `DATABASE_URL` in `server/.env`
- Check that the database exists
- Run `npm run db:setup` to initialize the database

---

## 📊 What the Seed Script Creates

When you run `node seed.js`, it creates:

### 1. Default User
- **Email:** admin@newsmachine.local
- **Password:** Admin123!
- **Name:** Admin User

### 2. Sample Niches

**Niche 1: AI & Machine Learning**
- Keywords: AI, artificial intelligence, machine learning, GPT, LLM
- RSS Feeds: TechCrunch AI, OpenAI Blog
- Subreddits: r/artificial, r/MachineLearning

**Niche 2: Tech News**
- Keywords: technology, startup, software, programming
- RSS Feeds: TechCrunch, The Verge
- Subreddits: r/technology, r/programming

**Niche 3: Web Development**
- Keywords: React, JavaScript, TypeScript, Node.js, web development
- RSS Feeds: Dev.to, CSS-Tricks
- Subreddits: r/webdev, r/javascript

### 3. What You Can Do Next
- View the pre-configured niches
- Trigger a collection run for any niche
- View collected items
- Generate newsletters
- Add more niches or modify existing ones

---

## 🔐 After First Login

### Immediate Actions:
1. **Change your password** (if using seed script)
2. **Review your niches** - Customize or delete sample niches
3. **Add your own RSS feeds** - Follow your favorite blogs
4. **Configure sources** - Connect Reddit/YouTube if desired
5. **Trigger your first collection** - See the app in action

### Security Checklist:
- [ ] Changed default password (if used seed script)
- [ ] Using a strong, unique password
- [ ] Email is verified (if verification is enabled)
- [ ] Reviewed privacy policy
- [ ] Reviewed terms of service
- [ ] Configured notification preferences

---

## 📝 Summary

**Q: What is the current default email and password?**

**A: There are NO default credentials.** You must create an account.

**How to create your first account:**

1. **For Development:** Run `cd server && node seed.js`
   - Creates: `admin@newsmachine.local` / `Admin123!`
   - Includes 3 sample niches

2. **For Production:** Register through the UI
   - Open the app
   - Click "Create new account"
   - Fill in your details

3. **Via API:** Use the `/api/auth/register` endpoint
   - POST request with email, password, name
   - Returns JWT token for authentication

**Next Steps:**
1. Start the backend and frontend
2. Create your account using one of the methods above
3. Login and start using the Newsletter Machine!

---

## 🚀 Ready to Go!

Once you've created your account, you're ready to:
- ✅ Create niches
- ✅ Add RSS feeds
- ✅ Connect Reddit/YouTube
- ✅ Trigger collections
- ✅ Generate newsletters
- ✅ View analytics

**Happy newslettering!** 🎉
