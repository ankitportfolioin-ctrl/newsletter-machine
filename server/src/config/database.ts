import { Pool } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
});

export default pool;

export const initializeDatabase = async () => {
  const client = await pool.connect();
  try {
    // Users table
    await client.query(`
      CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        name VARCHAR(255),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Niches table
    await client.query(`
      CREATE TABLE IF NOT EXISTS niches (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        name VARCHAR(500) NOT NULL,
        keywords TEXT[] DEFAULT '{}',
        subreddits TEXT[] DEFAULT '{}',
        blog_feeds TEXT[] DEFAULT '{}',
        include_terms TEXT[] DEFAULT '{}',
        exclude_terms TEXT[] DEFAULT '{}',
        enabled BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Sources configuration table
    await client.query(`
      CREATE TABLE IF NOT EXISTS sources (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        platform VARCHAR(50) NOT NULL,
        status VARCHAR(50) DEFAULT 'not_configured',
        credentials JSONB DEFAULT '{}',
        last_checked TIMESTAMP,
        items_collected INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_id, platform)
      )
    `);

    // Collected items table
    await client.query(`
      CREATE TABLE IF NOT EXISTS collected_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
        platform VARCHAR(50) NOT NULL,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        author VARCHAR(255),
        score INTEGER DEFAULT 0,
        excerpt TEXT,
        metadata JSONB DEFAULT '{}',
        collected_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Runs table
    await client.query(`
      CREATE TABLE IF NOT EXISTS runs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
        status VARCHAR(50) DEFAULT 'pending',
        started_at TIMESTAMP DEFAULT NOW(),
        completed_at TIMESTAMP,
        stats JSONB DEFAULT '{}',
        errors TEXT[] DEFAULT '{}',
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Newsletters table
    await client.query(`
      CREATE TABLE IF NOT EXISTS newsletters (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
        run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
        date DATE NOT NULL,
        subject TEXT NOT NULL,
        preheader TEXT,
        content JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT NOW()
      )
    `);

    // Feedback table
    await client.query(`
      CREATE TABLE IF NOT EXISTS feedback (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        newsletter_id UUID REFERENCES newsletters(id) ON DELETE CASCADE,
        story_id VARCHAR(255) NOT NULL,
        vote VARCHAR(10) NOT NULL CHECK (vote IN ('up', 'down')),
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(user_id, newsletter_id, story_id)
      )
    `);

    // Create indexes
    await client.query(`CREATE INDEX IF NOT EXISTS idx_niches_user_id ON niches(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_collected_items_niche_id ON collected_items(niche_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_newsletters_user_id ON newsletters(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id)`);

    console.log('Database initialized successfully');
  } catch (error) {
    console.error('Error initializing database:', error);
    throw error;
  } finally {
    client.release();
  }
};
