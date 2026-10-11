#!/usr/bin/env node

/**
 * Create Test Account Script
 * Creates a test user with specific credentials
 * 
 * Usage: node create-test-account.js
 */

import bcrypt from 'bcryptjs';
import pool from './src/config/database.js';

const TEST_USER = {
  email: 'test@gmail.com',
  password: 'test@123',
  name: 'Test User'
};

async function createTestAccount() {
  console.log('🔧 Creating test account...\n');

  try {
    // Check if user already exists
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE email = $1',
      [TEST_USER.email]
    );

    if (existingUser.rows.length > 0) {
      console.log('⚠️  Test account already exists');
      console.log(`   Email: ${TEST_USER.email}`);
      console.log('   Updating password...\n');
      
      // Update password
      const passwordHash = await bcrypt.hash(TEST_USER.password, 10);
      await pool.query(
        'UPDATE users SET password_hash = $1 WHERE email = $2',
        [passwordHash, TEST_USER.email]
      );
      
      console.log('✅ Password updated successfully!\n');
    } else {
      // Hash password
      const passwordHash = await bcrypt.hash(TEST_USER.password, 10);

      // Create user
      const result = await pool.query(
        'INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id, email, name',
        [TEST_USER.email, passwordHash, TEST_USER.name]
      );

      const user = result.rows[0];
      console.log('✅ Test account created successfully!\n');
    }

    console.log('📧 Test Account Credentials:');
    console.log('   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`   Email:    ${TEST_USER.email}`);
    console.log(`   Password: ${TEST_USER.password}`);
    console.log(`   Name:     ${TEST_USER.name}`);
    console.log('   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

    console.log('🚀 Next Steps:');
    console.log('   1. Start the backend: cd server && npm run dev');
    console.log('   2. Start the frontend: npm run dev');
    console.log('   3. Open http://localhost:5173');
    console.log(`   4. Login with: ${TEST_USER.email} / ${TEST_USER.password}\n`);

  } catch (error) {
    console.error('❌ Failed to create test account:', error.message);
    if (error.code === 'ECONNREFUSED') {
      console.error('\n💡 Database connection failed. Make sure PostgreSQL is running.');
      console.error('   Run: docker-compose up -d postgres');
    }
    process.exit(1);
  } finally {
    await pool.end();
  }
}

createTestAccount();
