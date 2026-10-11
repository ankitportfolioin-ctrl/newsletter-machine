import { Router, Response } from 'express';
import { supabaseAdmin } from '../config/supabase';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = Router();

// Get all newsletters for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { data, error } = await supabaseAdmin
      .from('newsletters')
      .select(`
        *,
        niches (
          name
        )
      `)
      .eq('user_id', req.userId)
      .order('date', { ascending: false })
      .order('created_at', { ascending: false });

    if (error) throw error;

    // Transform data to match expected format
    const newsletters = (data || []).map(nl => ({
      ...nl,
      niche_name: nl.niches?.name
    }));

    res.json(newsletters);
  } catch (error: any) {
    console.error('Get newsletters error:', error);
    res.status(500).json({ error: 'Failed to get newsletters' });
  }
});

// Get single newsletter
router.get('/:id', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { data, error } = await supabaseAdmin
      .from('newsletters')
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
        return res.status(404).json({ error: 'Newsletter not found' });
      }
      throw error;
    }

    const newsletter = {
      ...data,
      niche_name: data.niches?.name
    };

    res.json(newsletter);
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
    const { data: newsletter } = await supabaseAdmin
      .from('newsletters')
      .select('id')
      .eq('id', req.params.id)
      .eq('user_id', req.userId)
      .single();

    if (!newsletter) {
      return res.status(404).json({ error: 'Newsletter not found' });
    }

    // Upsert feedback
    const { error } = await supabaseAdmin
      .from('feedback')
      .upsert({
        user_id: req.userId,
        newsletter_id: req.params.id,
        story_id: storyId,
        vote
      }, {
        onConflict: 'user_id,newsletter_id,story_id'
      });

    if (error) throw error;

    res.json({ message: 'Feedback submitted' });
  } catch (error: any) {
    console.error('Feedback error:', error);
    res.status(500).json({ error: 'Failed to submit feedback' });
  }
});

// Get feedback stats
router.get('/feedback/stats', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    // Get total counts
    const { data: feedbackData, error } = await supabaseAdmin
      .from('feedback')
      .select('vote')
      .eq('user_id', req.userId);

    if (error) throw error;

    const totalUp = (feedbackData || []).filter(f => f.vote === 'up').length;
    const totalDown = (feedbackData || []).filter(f => f.vote === 'down').length;

    // Get by platform (simplified - would need joins for full implementation)
    const byPlatform: Record<string, { up: number; down: number }> = {};

    res.json({
      totalUp,
      totalDown,
      byPlatform,
      topRated: []
    });
  } catch (error: any) {
    console.error('Get feedback stats error:', error);
    res.status(500).json({ error: 'Failed to get feedback stats' });
  }
});

export default router;
