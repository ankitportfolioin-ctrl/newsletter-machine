import { Router, Response } from 'express';
import pool from '../config/database';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import { collectionService } from '../services/collectionService';

const router = Router();

// Get all runs for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT r.*, n.name as niche_name
       FROM runs r
       JOIN niches n ON r.niche_id = n.id
       WHERE r.user_id = $1
       ORDER BY r.started_at DESC
       LIMIT 50`,
      [req.userId]
    );
    res.json(result.rows);
  } catch (error: any) {
    console.error('Get runs error:', error);
    res.status(500).json({ error: 'Failed to get runs' });
  }
});

// Trigger new run
router.post('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { nicheId } = req.body;

    if (!nicheId) {
      return res.status(400).json({ error: 'nicheId is required' });
    }

    // Verify niche exists and belongs to user
    const niche = await pool.query(
      'SELECT id, name FROM niches WHERE id = $1 AND user_id = $2',
      [nicheId, req.userId]
    );

    if (niche.rows.length === 0) {
      return res.status(404).json({ error: 'Niche not found' });
    }

    // Run collection in background
    const runId = await collectionService.runCollection(req.userId!, nicheId);

    res.status(202).json({ runId, message: 'Collection started' });
  } catch (error: any) {
    console.error('Trigger run error:', error);
    res.status(500).json({ error: 'Failed to trigger run' });
  }
});

// Get single run
router.get('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT r.*, n.name as niche_name
       FROM runs r
       JOIN niches n ON r.niche_id = n.id
       WHERE r.id = $1 AND r.user_id = $2`,
      [req.params.id, req.userId]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Run not found' });
    }

    res.json(result.rows[0]);
  } catch (error: any) {
    console.error('Get run error:', error);
    res.status(500).json({ error: 'Failed to get run' });
  }
});

export default router;
