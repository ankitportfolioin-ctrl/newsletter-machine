import { Router, Response } from 'express';
import pool from '../config/database';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = Router();

// Get all niches for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT * FROM niches WHERE user_id = $1 ORDER BY created_at DESC',
      [req.userId]
    );
    res.json(result.rows);
  } catch (error: any) {
    console.error('Get niches error:', error);
    res.status(500).json({ error: 'Failed to get niches' });
  }
});

// Get single niche
router.get('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT * FROM niches WHERE id = $1 AND user_id = $2',
      [req.params.id, req.userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Niche not found' });
    }

    res.json(result.rows[0]);
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
    const existing = await pool.query(
      'SELECT id FROM niches WHERE user_id = $1 AND LOWER(name) = LOWER($2)',
      [req.userId, name]
    );

    if (existing.rows.length > 0) {
      return res.status(400).json({ error: 'A niche with this name already exists' });
    }

    const result = await pool.query(
      `INSERT INTO niches (user_id, name, keywords, subreddits, blog_feeds, include_terms, exclude_terms, enabled)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING *`,
      [
        req.userId,
        name,
        keywords || [],
        subreddits || [],
        blogFeeds || [],
        includeTerms || [],
        excludeTerms || [],
        enabled !== undefined ? enabled : true,
      ]
    );

    res.status(201).json(result.rows[0]);
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
    const existing = await pool.query(
      'SELECT id FROM niches WHERE id = $1 AND user_id = $2',
      [req.params.id, req.userId]
    );

    if (existing.rows.length === 0) {
      return res.status(404).json({ error: 'Niche not found' });
    }

    const result = await pool.query(
      `UPDATE niches SET
        name = COALESCE($1, name),
        keywords = COALESCE($2, keywords),
        subreddits = COALESCE($3, subreddits),
        blog_feeds = COALESCE($4, blog_feeds),
        include_terms = COALESCE($5, include_terms),
        exclude_terms = COALESCE($6, exclude_terms),
        enabled = COALESCE($7, enabled),
        updated_at = NOW()
       WHERE id = $8
       RETURNING *`,
      [name, keywords, subreddits, blogFeeds, includeTerms, excludeTerms, enabled, req.params.id]
    );

    res.json(result.rows[0]);
  } catch (error: any) {
    console.error('Update niche error:', error);
    res.status(500).json({ error: 'Failed to update niche' });
  }
});

// Delete niche
router.delete('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      'DELETE FROM niches WHERE id = $1 AND user_id = $2 RETURNING id',
      [req.params.id, req.userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Niche not found' });
    }

    res.json({ message: 'Niche deleted successfully' });
  } catch (error: any) {
    console.error('Delete niche error:', error);
    res.status(500).json({ error: 'Failed to delete niche' });
  }
});

export default router;
