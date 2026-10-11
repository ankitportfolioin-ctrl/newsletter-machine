#!/usr/bin/env node

/**
 * Database Seed Script
 * Creates a default test user for development/testing
 * 
 * Usage: node seed.js
 */

import bcrypt from 'bcryptjs';
import pool from './src/config/database.js';

const DEFAULT_USER = {
  email: 'admin@newsmachine.local',
  password: 'Admin123!',
  name: 'Admin User'
};

async function seed() {
  console.log('🌱 Starting database seed...\n');

  try {
    // Check if user already exists
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE email = $1',
      [DEFAULT_USER.email]
    );

    if (existingUser.rows.length > 0) {
      console.log('⚠️  Default user already exists');
      console.log(`   Email: ${DEFAULT_USER.email}`);
      console.log('   Skipping creation.\n');
    } else {
      // Hash password
      const passwordHash = await bcrypt.hash(DEFAULT_USER.password, 10);

      // Create user
      const result = await pool.query(
        'INSERT INTO users (email, password_hash, name) VALUES ($1, $2, $3) RETURNING id, email, name',
        [DEFAULT_USER.email, passwordHash, DEFAULT_USER.name]
      );

      const user = result.rows[0];
      console.log('✅ Default user created successfully!\n');
      console.log('📧 Login Credentials:');
      console.log(`   Email:    ${DEFAULT_USER.email}`);
      console.log(`   Password: ${DEFAULT_USER.password}`);
      console.log(`   Name:     ${DEFAULT_USER.name}\n`);
      console.log('⚠️  IMPORTANT: Change this password after first login!\n');
    }

    // Create some sample niches for the user
    const userResult = await pool.query(
      'SELECT id FROM users WHERE email = $1',
      [DEFAULT_USER.email]
    );

    if (userResult.rows.length > 0) {
      const userId = userResult.rows[0].id;

      // Check if niches already exist
      const existingNiches = await pool.query(
        'SELECT COUNT(*) FROM niches WHERE user_id = $1',
        [userId]
      );

      if (parseInt(existingNiches.rows[0].count) === 0) {
        console.log('📝 Creating sample niches...\n');

        const sampleNiches = [
          {
            name: 'AI & Machine Learning',
            keywords: ['AI', 'artificial intelligence', 'machine learning', 'GPT', 'LLM'],
            blogFeeds: [
              'https://techcrunch.com/category/artificial-intelligence/feed/',
              'https://openai.com/blog/rss.xml'
            ],
            subreddits: ['artificial', 'MachineLearning'],
            enabled: true
          },
          {
            name: 'Tech News',
            keywords: ['technology', 'startup', 'software', 'programming'],
            blogFeeds: [
              'https://techcrunch.com/feed/',
              'https://www.theverge.com/rss/index.xml'
            ],
            subreddits: ['technology', 'programming'],
            enabled: true
          },
          {
            name: 'Web Development',
            keywords: ['React', 'JavaScript', 'TypeScript', 'Node.js', 'web development'],
            blogFeeds: [
              'https://dev.to/feed',
              'https://css-tricks.com/feed/'
            ],
            subreddits: ['webdev', 'javascript'],
            enabled: true
          }
        ];

        for (const niche of sampleNiches) {
          await pool.query(
            `INSERT INTO niches (user_id, name, keywords, blog_feeds, subreddits, enabled)
             VALUES ($1, $2, $3, $4, $5, $6)`,
            [
              userId,
              niche.name,
              niche.keywords,
              niche.blogFeeds,
              niche.subreddits,
              niche.enabled
            ]
          );
          console.log(`   ✅ Created niche: ${niche.name}`);
        }

        console.log('\n');
      } else {
        console.log('⚠️  Sample niches already exist, skipping.\n');
      }
    }

    console.log('🎉 Seed completed successfully!\n');
    console.log('📋 Next Steps:');
    console.log('   1. Start the backend: cd server && npm run dev');
    console.log('   2. Start the frontend: npm run dev');
    console.log('   3. Open http://localhost:5173');
    console.log(`   4. Login with: ${DEFAULT_USER.email} / ${DEFAULT_USER.password}`);
    console.log('   5. Change your password immediately!\n');

  } catch (error) {
    console.error('❌ Seed failed:', error);
    process.exit(1);
  } finally {
    await pool.end();
  }
}

seed();
