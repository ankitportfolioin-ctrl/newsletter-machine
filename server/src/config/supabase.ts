import { createClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL!;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_KEY!;

// Admin client for server-side operations
export const supabaseAdmin = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

// Initialize database schema
export const initializeDatabase = async () => {
  try {
    // Create niches table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS niches (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
      `
    });

    // Create sources table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS sources (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
          platform VARCHAR(50) NOT NULL,
          status VARCHAR(50) DEFAULT 'not_configured',
          credentials JSONB DEFAULT '{}',
          last_checked TIMESTAMP,
          items_collected INTEGER DEFAULT 0,
          created_at TIMESTAMP DEFAULT NOW(),
          updated_at TIMESTAMP DEFAULT NOW(),
          UNIQUE(user_id, platform)
        )
      `
    });

    // Create collected_items table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
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
      `
    });

    // Create runs table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS runs (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
          niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
          status VARCHAR(50) DEFAULT 'pending',
          started_at TIMESTAMP DEFAULT NOW(),
          completed_at TIMESTAMP,
          stats JSONB DEFAULT '{}',
          errors TEXT[] DEFAULT '{}',
          created_at TIMESTAMP DEFAULT NOW()
        )
      `
    });

    // Create newsletters table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS newsletters (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
          niche_id UUID REFERENCES niches(id) ON DELETE CASCADE,
          run_id UUID REFERENCES runs(id) ON DELETE CASCADE,
          date DATE NOT NULL,
          subject TEXT NOT NULL,
          preheader TEXT,
          content JSONB NOT NULL,
          created_at TIMESTAMP DEFAULT NOW()
        )
      `
    });

    // Create feedback table
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE TABLE IF NOT EXISTS feedback (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
          newsletter_id UUID REFERENCES newsletters(id) ON DELETE CASCADE,
          story_id VARCHAR(255) NOT NULL,
          vote VARCHAR(10) NOT NULL CHECK (vote IN ('up', 'down')),
          created_at TIMESTAMP DEFAULT NOW(),
          UNIQUE(user_id, newsletter_id, story_id)
        )
      `
    });

    // Create indexes
    await supabaseAdmin.rpc('exec_sql', {
      sql: `
        CREATE INDEX IF NOT EXISTS idx_niches_user_id ON niches(user_id);
        CREATE INDEX IF NOT EXISTS idx_collected_items_niche_id ON collected_items(niche_id);
        CREATE INDEX IF NOT EXISTS idx_collected_items_url ON collected_items(url);
        CREATE INDEX IF NOT EXISTS idx_runs_user_id ON runs(user_id);
        CREATE INDEX IF NOT EXISTS idx_newsletters_user_id ON newsletters(user_id);
        CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON feedback(user_id);
      `
    });

    console.log('✅ Supabase database initialized successfully');
  } catch (error) {
    console.error('❌ Error initializing Supabase database:', error);
    throw error;
  }
};

// Health check
export const checkDatabaseHealth = async () => {
  try {
    const { data, error } = await supabaseAdmin.from('niches').select('count', { count: 'exact', head: true });
    
    if (error) throw error;

    return {
      status: 'healthy',
      provider: 'supabase',
      timestamp: new Date().toISOString()
    };
  } catch (error) {
    return {
      status: 'unhealthy',
      provider: 'supabase',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    };
  }
};
