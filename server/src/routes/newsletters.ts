import { Router, Response } from 'express';
import pool from '../config/database';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = Router();

// Get all newsletters for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT n.*, ni.name as niche_name
       FROM newsletters n
       JOIN niches ni ON n.niche_id = ni.id
       WHERE n.user_id = $1
       ORDER BY n.date DESC, n.created_at DESC`,
      [req.userId]
    );
    res.json(result.rows);
  } catch (error: any) {
    console.error('Get newsletters error:', error);
    res.status(500).json({ error: 'Failed to get newsletters' });
  }
});

// Get single newsletter
router.get('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT n.*, ni.name as niche_name
       FROM newsletters n
       JOIN niches ni ON n.niche_id = ni.id
       WHERE n.id = $1 AND n.user_id = $2`,
      [req.params.id, req.userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Newsletter not found' });
    }

    res.json(result.rows[0]);
  } catch (error: any) {
    console.error('Get newsletter error:', error);
    res.status(500).json({ error: 'Failed to get newsletter' });
  }
});

// Submit feedback
router.post('/:id/feedback', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { storyId, vote } = req.body;

    if (!storyId || !vote) {
      return res.status(400).json({ error: 'storyId and vote are required' });
    }

    if (!['up', 'down'].includes(vote)) {
      return res.status(400).json({ error: 'vote must be "up" or "down"' });
    }

    // Check if newsletter exists
    const newsletter = await pool.query(
      'SELECT id FROM newsletters WHERE id = $1 AND user_id = $2',
      [req.params.id, req.userId]
    );

    if (newsletter.rows.length === 0) {
      return res.status(404).json({ error: 'Newsletter not found' });
    }

    // Upsert feedback
    await pool.query(
      `INSERT INTO feedback (user_id, newsletter_id, story_id, vote)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (user_id, newsletter_id, story_id)
       DO UPDATE SET vote = $4, created_at = NOW()`,
      [req.userId, req.params.id, storyId, vote]
    );

    res.json({ message: 'Feedback submitted' });
  } catch (error: any) {
    console.error('Feedback error:', error);
    res.status(500).json({ error: 'Failed to submit feedback' });
  }
});

// Get feedback stats
router.get('/feedback/stats', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT
        COUNT(*) FILTER (WHERE vote = 'up') as total_up,
        COUNT(*) FILTER (WHERE vote = 'down') as total_down
       FROM feedback
       WHERE user_id = $1`,
      [req.userId]
    );

    const byPlatform = await pool.query(
      `SELECT
        ci.platform,
        COUNT(*) FILTER (WHERE f.vote = 'up') as up,
        COUNT(*) FILTER (WHERE f.vote = 'down') as down
       FROM feedback f
       JOIN newsletters n ON f.newsletter_id = n.id
       JOIN collected_items ci ON n.niche_id = ci.niche_id
       WHERE f.user_id = $1
       GROUP BY ci.platform`,
      [req.userId]
    );

    res.json({
      totalUp: parseInt(result.rows[0].total_up) || 0,
      totalDown: parseInt(result.rows[0].total_down) || 0,
      byPlatform: byPlatform.rows.reduce((acc, row) => {
        acc[row.platform] = { up: parseInt(row.up), down: parseInt(row.down) };
        return acc;
      }, {}),
    });
  } catch (error: any) {
    console.error('Get feedback stats error:', error);
    res.status(500).json({ error: 'Failed to get feedback stats' });
  }
});

export default router;
