import { Router, Response } from 'express';
import { supabaseAdmin } from '../config/supabase';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = Router();

// Get all niches for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { data, error } = await supabaseAdmin
      .from('niches')
      .select('*')
      .eq('user_id', req.userId)
      .order('created_at', { ascending: false });

    if (error) throw error;

    res.json(data || []);
  } catch (error: any) {
    console.error('Get niches error:', error);
    res.status(500).json({ error: 'Failed to get niches' });
  }
});

// Get single niche
router.get('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { data, error } = await supabaseAdmin
      .from('niches')
      .select('*')
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({ error: 'Niche not found' });
      }
      throw error;
    }

    res.json(data);
  } catch (error: any) {
    console.error('Get niche error:', error);
    res.status(500).json({ error: 'Failed to get niche' });
  }
});

// Create niche
router.post('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { name, keywords, subreddits, blogFeeds, includeTerms, excludeTerms, enabled } = req.body;

    if (!name || name.trim().length === 0) {
      return res.status(400).json({ error: 'Niche name is required' });
    }

    if (name.length > 500) {
      return res.status(400).json({ error: 'Name must be under 500 characters' });
    }

    // Check for duplicate name
    const { data: existing } = await supabaseAdmin
      .from('niches')
      .select('id')
      .eq('user_id', req.userId)
      .ilike('name', name);

    if (existing && existing.length > 0) {
      return res.status(400).json({ error: 'A niche with this name already exists' });
    }

    const { data, error } = await supabaseAdmin
      .from('niches')
      .insert({
        user_id: req.userId,
        name,
        keywords: keywords || [],
        subreddits: subreddits || [],
        blog_feeds: blogFeeds || [],
        include_terms: includeTerms || [],
        exclude_terms: excludeTerms || [],
        enabled: enabled !== undefined ? enabled : true
      })
      .select()
      .single();

    if (error) throw error;

    res.status(201).json(data);
  } catch (error: any) {
    console.error('Create niche error:', error);
    res.status(500).json({ error: 'Failed to create niche' });
  }
});

// Update niche
router.put('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { name, keywords, subreddits, blogFeeds, includeTerms, excludeTerms, enabled } = req.body;

    // Check if niche exists and belongs to user
    const { data: existing } = await supabaseAdmin
      .from('niches')
      .select('id')
      .eq('id', req.params.id)
      .eq('user_id', req.userId);

    if (!existing || existing.length === 0) {
      return res.status(404).json({ error: 'Niche not found' });
    }

    const updates: any = { updated_at: new Date().toISOString() };
    if (name !== undefined) updates.name = name;
    if (keywords !== undefined) updates.keywords = keywords;
    if (subreddits !== undefined) updates.subreddits = subreddits;
    if (blogFeeds !== undefined) updates.blog_feeds = blogFeeds;
    if (includeTerms !== undefined) updates.include_terms = includeTerms;
    if (excludeTerms !== undefined) updates.exclude_terms = excludeTerms;
    if (enabled !== undefined) updates.enabled = enabled;

    const { data, error } = await supabaseAdmin
      .from('niches')
      .update(updates)
      .eq('id', req.params.id)
      .select()
      .single();

    if (error) throw error;

    res.json(data);
  } catch (error: any) {
    console.error('Update niche error:', error);
    res.status(500).json({ error: 'Failed to update niche' });
  }
});

// Delete niche
router.delete('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { error } = await supabaseAdmin
      .from('niches')
      .delete()
      .eq('id', req.params.id)
      .eq('user_id', req.userId);

    if (error) throw error;

    res.json({ message: 'Niche deleted successfully' });
  } catch (error: any) {
    console.error('Delete niche error:', error);
    res.status(500).json({ error: 'Failed to delete niche' });
  }
});

export default router;
