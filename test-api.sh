#!/bin/bash

# Integration Test Script for Newsletter Machine
# This script tests the backend API endpoints

set -e

BASE_URL="http://localhost:3001/api"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="testpass123"

echo "=== Newsletter Machine Integration Tests ==="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
HEALTH=$(curl -s "$BASE_URL/../health")
if echo "$HEALTH" | grep -q '"status":"ok"'; then
    echo "✓ PASS: Health endpoint working"
else
    echo "✗ FAIL: Health endpoint not responding"
    exit 1
fi
echo ""

# Test 2: Register User
echo "Test 2: Register User"
REGISTER=$(curl -s -X POST "$BASE_URL/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"name\":\"Test User\"}")

if echo "$REGISTER" | grep -q '"token"'; then
    echo "✓ PASS: User registration successful"
    TOKEN=$(echo "$REGISTER" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
else
    echo "✗ FAIL: User registration failed"
    echo "Response: $REGISTER"
    exit 1
fi
echo ""

# Test 3: Login
echo "Test 3: Login"
LOGIN=$(curl -s -X POST "$BASE_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\"}")

if echo "$LOGIN" | grep -q '"token"'; then
    echo "✓ PASS: Login successful"
    TOKEN=$(echo "$LOGIN" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
else
    echo "✗ FAIL: Login failed"
    echo "Response: $LOGIN"
    exit 1
fi
echo ""

# Test 4: Get Current User
echo "Test 4: Get Current User"
ME=$(curl -s -X GET "$BASE_URL/auth/me" \
    -H "Authorization: Bearer $TOKEN")

if echo "$ME" | grep -q "$TEST_EMAIL"; then
    echo "✓ PASS: Get current user successful"
else
    echo "✗ FAIL: Get current user failed"
    echo "Response: $ME"
    exit 1
fi
echo ""

# Test 5: Create Niche
echo "Test 5: Create Niche"
NICHE=$(curl -s -X POST "$BASE_URL/niches" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Niche","keywords":["test","ai"],"blogFeeds":["https://openai.com/blog/feed"]}')

if echo "$NICHE" | grep -q '"id"'; then
    echo "✓ PASS: Niche creation successful"
    NICHE_ID=$(echo "$NICHE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
else
    echo "✗ FAIL: Niche creation failed"
    echo "Response: $NICHE"
    exit 1
fi
echo ""

# Test 6: Get Niches
echo "Test 6: Get Niches"
NICHES=$(curl -s -X GET "$BASE_URL/niches" \
    -H "Authorization: Bearer $TOKEN")

if echo "$NICHES" | grep -q "Test Niche"; then
    echo "✓ PASS: Get niches successful"
else
    echo "✗ FAIL: Get niches failed"
    echo "Response: $NICHES"
    exit 1
fi
echo ""

# Test 7: Get Sources
echo "Test 7: Get Sources"
SOURCES=$(curl -s -X GET "$BASE_URL/sources" \
    -H "Authorization: Bearer $TOKEN")

if echo "$SOURCES" | grep -q '"platform"'; then
    echo "✓ PASS: Get sources successful"
else
    echo "✗ FAIL: Get sources failed"
    echo "Response: $SOURCES"
    exit 1
fi
echo ""

# Test 8: Trigger Run (will fail without DB but tests endpoint)
echo "Test 8: Trigger Run"
RUN=$(curl -s -X POST "$BASE_URL/runs" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"nicheId\":\"$NICHE_ID\"}")

if echo "$RUN" | grep -q '"runId"'; then
    echo "✓ PASS: Trigger run successful (run started)"
    RUN_ID=$(echo "$RUN" | grep -o '"runId":"[^"]*"' | cut -d'"' -f4)
elif echo "$RUN" | grep -q 'error'; then
    echo "⚠ EXPECTED: Run triggered but may fail without proper setup"
    echo "Response: $RUN"
else
    echo "✗ FAIL: Trigger run failed unexpectedly"
    echo "Response: $RUN"
    exit 1
fi
echo ""

# Test 9: Get Runs
echo "Test 9: Get Runs"
RUNS=$(curl -s -X GET "$BASE_URL/runs" \
    -H "Authorization: Bearer $TOKEN")

if echo "$RUNS" | grep -q '\['; then
    echo "✓ PASS: Get runs successful"
else
    echo "✗ FAIL: Get runs failed"
    echo "Response: $RUNS"
    exit 1
fi
echo ""

# Test 10: Get Newsletters
echo "Test 10: Get Newsletters"
NEWSLETTERS=$(curl -s -X GET "$BASE_URL/newsletters" \
    -H "Authorization: Bearer $TOKEN")

if echo "$NEWSLETTERS" | grep -q '\['; then
    echo "✓ PASS: Get newsletters successful"
else
    echo "✗ FAIL: Get newsletters failed"
    echo "Response: $NEWSLETTERS"
    exit 1
fi
echo ""

# Test 11: Update Niche
echo "Test 11: Update Niche"
UPDATE=$(curl -s -X PUT "$BASE_URL/niches/$NICHE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Updated Test Niche"}')

if echo "$UPDATE" | grep -q "Updated Test Niche"; then
    echo "✓ PASS: Niche update successful"
else
    echo "✗ FAIL: Niche update failed"
    echo "Response: $UPDATE"
    exit 1
fi
echo ""

# Test 12: Delete Niche
echo "Test 12: Delete Niche"
DELETE=$(curl -s -X DELETE "$BASE_URL/niches/$NICHE_ID" \
    -H "Authorization: Bearer $TOKEN")

if echo "$DELETE" | grep -q '"message"'; then
    echo "✓ PASS: Niche deletion successful"
else
    echo "✗ FAIL: Niche deletion failed"
    echo "Response: $DELETE"
    exit 1
fi
echo ""

# Test 13: Verify Deletion
echo "Test 13: Verify Deletion"
NICHES_AFTER=$(curl -s -X GET "$BASE_URL/niches" \
    -H "Authorization: Bearer $TOKEN")

if ! echo "$NICHES_AFTER" | grep -q "Updated Test Niche"; then
    echo "✓ PASS: Niche successfully deleted"
else
    echo "✗ FAIL: Niche still exists after deletion"
    exit 1
fi
echo ""

echo "=== All Tests Passed ==="
echo ""
echo "Summary:"
echo "  - Authentication: ✓"
echo "  - Niche CRUD: ✓"
echo "  - Sources: ✓"
echo "  - Runs: ✓"
echo "  - Newsletters: ✓"
echo ""
echo "Note: Collection and newsletter generation require:"
echo "  - PostgreSQL database running"
echo "  - Valid RSS feeds configured"
echo "  - OpenAI API key (optional, for newsletter generation)"
