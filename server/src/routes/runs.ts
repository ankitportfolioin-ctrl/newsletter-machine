import { Router, Response } from 'express';
import { supabaseAdmin } from '../config/supabase';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import { collectionService } from '../services/collectionService';

const router = Router();

// Get all runs for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { data, error } = await supabaseAdmin
      .from('runs')
      .select(`
        *,
        niches (
          name
        )
      `)
      .eq('user_id', req.userId)
      .order('started_at', { ascending: false })
      .limit(50);

    if (error) throw error;

    // Transform data to match expected format
    const runs = (data || []).map(run => ({
      ...run,
      niche_name: run.niches?.name
    }));

    res.json(runs);
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
    const { data: niche, error: nicheError } = await supabaseAdmin
      .from('niches')
      .select('id, name')
      .eq('id', nicheId)
      .eq('user_id', req.userId)
      .single();

    if (nicheError || !niche) {
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
    const { data, error } = await supabaseAdmin
      .from('runs')
      .select(`
        *,
        niches (
          name
        )
      `)
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .single();

    if (error) {
      if (error.code === 'PGRST116') {
        return res.status(404).json({ error: 'Run not found' });
      }
      throw error;
    }

    const run = {
      ...data,
      niche_name: data.niches?.name
    };

    res.json(run);
  } catch (error: any) {
    console.error('Get run error:', error);
    res.status(500).json({ error: 'Failed to get run' });
  }
});

export default router;
