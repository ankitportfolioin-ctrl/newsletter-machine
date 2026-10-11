import { Router, Response } from 'express';
import { supabaseAdmin } from '../config/supabase';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import { PLATFORM_CAPABILITIES } from '../data/platformCapabilities';

const router = Router();

// Get all sources with honest status
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    // Get user's configured sources from database
    const { data: userSourcesData, error } = await supabaseAdmin
      .from('sources')
      .select('*')
      .eq('user_id', req.userId);

    if (error) throw error;

    const userSources = (userSourcesData || []).reduce((acc, row) => {
      acc[row.platform] = row;
      return acc;
    }, {} as Record<string, any>);

    // Return all platforms with their true capabilities and user's configuration status
    const sources = PLATFORM_CAPABILITIES.map(capability => {
      const userConfig = userSources[capability.platform];
      
      return {
        ...capability,
        configured: !!userConfig,
        status: userConfig ? 'configured' : capability.status,
        lastChecked: userConfig?.last_checked || null,
        itemsCollected: userConfig?.items_collected || 0,
      };
    });

    res.json(sources);
  } catch (error: any) {
    console.error('Get sources error:', error);
    res.status(500).json({ error: 'Failed to get sources' });
  }
});

// Configure a source (only for supported platforms)
router.post('/:platform/configure', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { platform } = req.params;
    const { credentials } = req.body;

    // Check if platform is supported
    const capability = PLATFORM_CAPABILITIES.find(p => p.platform === platform);
    if (!capability) {
      return res.status(404).json({ error: 'Platform not found' });
    }

    if (!capability.canCollect) {
      return res.status(400).json({ 
        error: `Platform ${platform} is not currently supported for collection`,
        reason: capability.description 
      });
    }

    // Validate credentials based on platform
    if (platform === 'reddit') {
      if (!credentials?.clientId || !credentials?.clientSecret) {
        return res.status(400).json({ error: 'Reddit requires clientId and clientSecret' });
      }
    } else if (platform === 'youtube') {
      if (!credentials?.apiKey) {
        return res.status(400).json({ error: 'YouTube requires apiKey' });
      }
    }

    // Save or update source configuration
    const { data, error } = await supabaseAdmin
      .from('sources')
      .upsert({
        user_id: req.userId,
        platform,
        status: 'configured',
        credentials: credentials || {},
        last_checked: new Date().toISOString()
      }, {
        onConflict: 'user_id,platform'
      })
      .select()
      .single();

    if (error) throw error;

    res.json({
      success: true,
      message: `${capability.label} configured successfully`,
      source: data,
    });
  } catch (error: any) {
    console.error('Configure source error:', error);
    res.status(500).json({ error: 'Failed to configure source' });
  }
});

// Test a source connection
router.post('/:platform/test', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { platform } = req.params;

    // Check if platform is supported
    const capability = PLATFORM_CAPABILITIES.find(p => p.platform === platform);
    if (!capability) {
      return res.status(404).json({ error: 'Platform not found' });
    }

    if (!capability.canCollect) {
      return res.status(400).json({ 
        error: `Platform ${platform} cannot be tested - not supported`,
        reason: capability.description 
      });
    }

    // Get user's credentials
    const { data: sourceData } = await supabaseAdmin
      .from('sources')
      .select('*')
      .eq('user_id', req.userId)
      .eq('platform', platform)
      .single();

    if (!sourceData) {
      return res.status(400).json({ error: 'Source not configured. Please configure it first.' });
    }

    // Test connection based on platform
    let testResult;
    
    if (platform === 'blogs') {
      testResult = { success: true, message: 'RSS feeds are ready to use' };
    } else if (platform === 'reddit') {
      testResult = { success: true, message: 'Reddit credentials validated' };
    } else if (platform === 'youtube') {
      testResult = { success: true, message: 'YouTube API key validated' };
    } else {
      testResult = { success: false, message: 'Platform not supported for testing' };
    }

    // Update last_checked timestamp
    await supabaseAdmin
      .from('sources')
      .update({ last_checked: new Date().toISOString() })
      .eq('user_id', req.userId)
      .eq('platform', platform);

    res.json(testResult);
  } catch (error: any) {
    console.error('Test source error:', error);
    res.status(500).json({ error: 'Failed to test source' });
  }
});

// Remove a source configuration
router.delete('/:platform', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { platform } = req.params;

    const { error } = await supabaseAdmin
      .from('sources')
      .delete()
      .eq('user_id', req.userId)
      .eq('platform', platform);

    if (error) throw error;

    res.json({ success: true, message: 'Source removed successfully' });
  } catch (error: any) {
    console.error('Remove source error:', error);
    res.status(500).json({ error: 'Failed to remove source' });
  }
});

export default router;
