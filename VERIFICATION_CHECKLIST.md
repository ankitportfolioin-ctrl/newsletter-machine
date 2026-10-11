# Runtime Verification Checklist

Use this checklist to verify the Newsletter Machine is working correctly after setup.

## Prerequisites Check

- [ ] Docker Desktop is installed and running
- [ ] Node.js 18+ is installed (`node --version`)
- [ ] npm is installed (`npm --version`)
- [ ] Git is installed (`git --version`)

## Setup Verification

### 1. Database Setup
```bash
./setup-database.sh
```

**Verify:**
- [ ] Script completes without errors
- [ ] PostgreSQL container is running: `docker-compose ps`
- [ ] Database is accessible: `docker exec newsletter_db pg_isready -U newsletter_user`

### 2. Backend Startup
```bash
npx tsx server/src/index.ts
```

**Verify:**
- [ ] Server starts without errors
- [ ] Logs show: "Database initialized successfully"
- [ ] Logs show: "Server running on port 3001"
- [ ] Health check works: `curl http://localhost:3001/health`
- [ ] Response: `{"status":"ok","timestamp":"..."}`

### 3. Frontend Startup
```bash
npm run dev
```

**Verify:**
- [ ] Vite dev server starts
- [ ] Frontend accessible at http://localhost:5173
- [ ] No console errors in browser
- [ ] Network tab shows successful API calls

## API Testing

### Automated Tests
```bash
chmod +x test-api.sh
./test-api.sh
```

**Expected Results:**
- [ ] All 13 tests pass
- [ ] No failures or errors
- [ ] Summary shows all checks ✓

### Manual API Tests

#### Authentication
```bash
# Register
curl -X POST http://localhost:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test"}'

# Login
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

**Verify:**
- [ ] Registration returns token
- [ ] Login returns token
- [ ] Token is valid JWT format

#### Niches
```bash
# Create niche (replace TOKEN with actual token)
curl -X POST http://localhost:3001/api/niches \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"AI News","keywords":["ai","ml"],"blogFeeds":["https://openai.com/blog/feed"]}'

# Get niches
curl -X GET http://localhost:3001/api/niches \
  -H "Authorization: Bearer TOKEN"
```

**Verify:**
- [ ] Niche created successfully
- [ ] Niche appears in list
- [ ] Niche has correct fields

#### Sources
```bash
curl -X GET http://localhost:3001/api/sources \
  -H "Authorization: Bearer TOKEN"
```

**Verify:**
- [ ] Returns array of sources
- [ ] Each source has platform, label, status
- [ ] Status reflects actual configuration (not mock data)

## UI Workflow Test

### 1. User Registration
- [ ] Navigate to http://localhost:5173
- [ ] See login page
- [ ] Click "Create new account"
- [ ] Fill in name, email, password
- [ ] Click "Create Account"
- [ ] Successfully redirected to dashboard

### 2. Create Niche
- [ ] Click "Niches" in sidebar
- [ ] Click "New Niche"
- [ ] Enter name: "Test Niche"
- [ ] Enter keywords: "test, ai, machine learning"
- [ ] Enter blog feeds: "https://openai.com/blog/feed"
- [ ] Click "Create Niche"
- [ ] Niche appears in list

### 3. Trigger Collection
- [ ] Click "Run History" in sidebar
- [ ] Select "Test Niche" from dropdown
- [ ] Click "Trigger Run"
- [ ] Run status shows "running"
- [ ] Wait 10-30 seconds
- [ ] Status changes to "completed"
- [ ] Stats show items collected

### 4. Verify Data in Database
```bash
docker exec -it newsletter_db psql -U newsletter_user -d newsletter_machine

# Check collected items
SELECT COUNT(*) FROM collected_items;
SELECT platform, title, url FROM collected_items LIMIT 5;

# Check runs
SELECT * FROM runs ORDER BY started_at DESC LIMIT 1;
```

**Verify:**
- [ ] collected_items table has records
- [ ] Items have real URLs and titles
- [ ] runs table shows completed run
- [ ] Stats JSON shows collection data

### 5. Test Deduplication
- [ ] Trigger another run for same niche
- [ ] Check database:
```sql
SELECT stats FROM runs ORDER BY started_at DESC LIMIT 1;
```
- [ ] Second run shows `deduplication.skipped > 0`

### 6. Test Persistence
- [ ] Refresh browser (F5)
- [ ] Navigate to all pages
- [ ] Verify all data is still present
- [ ] Niches still listed
- [ ] Runs still visible
- [ ] No data loss

### 7. Test Newsletter (Optional - Requires OpenAI Key)
If OpenAI API key is configured:
- [ ] Check "Newsletter Archive" page
- [ ] Newsletter should be generated
- [ ] Click on newsletter
- [ ] Verify content is based on collected items
- [ ] Verify source URLs are present

Without OpenAI key:
- [ ] Newsletter Archive shows empty state
- [ ] No errors or crashes
- [ ] Collection still works

## Database Verification

### Schema Check
```bash
docker exec -it newsletter_db psql -U newsletter_user -d newsletter_machine

# List tables
\dt

# Check table structure
\d users
\d niches
\d collected_items
\d runs
\d newsletters
```

**Verify:**
- [ ] All 7 tables exist
- [ ] Tables have correct columns
- [ ] Foreign keys are present
- [ ] Indexes are created

### Data Integrity
```sql
-- Check for orphaned records
SELECT * FROM niches WHERE user_id NOT IN (SELECT id FROM users);
SELECT * FROM collected_items WHERE niche_id NOT IN (SELECT id FROM niches);
SELECT * FROM runs WHERE user_id NOT IN (SELECT id FROM users);

-- Check for duplicates
SELECT url, COUNT(*) FROM collected_items GROUP BY url HAVING COUNT(*) > 1;
```

**Verify:**
- [ ] No orphaned records
- [ ] No duplicate URLs in collected_items

## Security Verification

### Authentication
- [ ] Can't access /api/niches without token
- [ ] Invalid token returns 403
- [ ] Expired token returns 403
- [ ] Valid token works correctly

### Multi-tenancy
- [ ] Create second user
- [ ] User A can't see User B's niches
- [ ] User A can't see User B's runs
- [ ] User A can't see User B's newsletters

### Rate Limiting
- [ ] Make 100+ rapid requests
- [ ] Rate limit kicks in
- [ ] Returns 429 status
- [ ] Error message is clear

## Error Handling

### Invalid Inputs
- [ ] Register with invalid email → error message
- [ ] Create niche with empty name → error message
- [ ] Create niche with duplicate name → error message
- [ ] Login with wrong password → error message

### Missing Data
- [ ] Request non-existent niche → 404
- [ ] Request non-existent newsletter → 404
- [ ] Request non-existent run → 404

### Network Errors
- [ ] Stop backend while frontend is open
- [ ] Frontend shows error message
- [ ] No infinite loading spinners
- [ ] Can recover when backend restarts

## Performance Check

### Response Times
- [ ] Health check: < 100ms
- [ ] Get niches: < 500ms
- [ ] Create niche: < 500ms
- [ ] Trigger run: < 1000ms
- [ ] Get newsletters: < 500ms

### Database Queries
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM niches WHERE user_id = '...';
EXPLAIN ANALYZE SELECT * FROM collected_items WHERE niche_id = '...';
```

**Verify:**
- [ ] Queries use indexes
- [ ] No full table scans
- [ ] Response times acceptable

## Cleanup

After testing:
```bash
# Stop backend (Ctrl+C)

# Stop frontend (Ctrl+C)

# Stop database
docker-compose down

# Optional: Remove database volume
docker volume rm newsletter_machine_postgres_data
```

## Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `docker-compose ps`
- Check .env file exists: `ls server/.env`
- Check DATABASE_URL is correct
- Check port 3001 is not in use

### Frontend can't connect
- Check backend is running on port 3001
- Check VITE_API_URL in .env
- Check CORS settings in backend
- Check browser console for errors

### Collection returns 0 items
- Check niche has blog_feeds configured
- Check feeds are accessible: `curl <feed-url>`
- Check backend logs for RSS errors
- Check keywords match feed content

### Newsletter not generated
- Check OpenAI API key is configured
- Check backend logs for OpenAI errors
- Check collected items count (need 5+)
- Note: Newsletter generation is optional

## Success Criteria

The application is fully verified when:
- [x] All setup steps complete without errors
- [x] All automated tests pass
- [x] Complete UI workflow works end-to-end
- [x] Data persists in database
- [x] Deduplication works correctly
- [x] Multi-tenancy is enforced
- [x] Error handling is graceful
- [x] Performance is acceptable

## Final Sign-off

- **Tester Name:** _______________
- **Date:** _______________
- **Environment:** _______________
- **All Checks Passed:** ☐ Yes ☐ No
- **Notes:** _______________

---

**If all checks pass, the Newsletter Machine is ready for limited MVP deployment.**
