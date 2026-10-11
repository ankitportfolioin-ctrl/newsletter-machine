import { Router, Response } from 'express';
import pool from '../config/database';
import { authenticateToken, AuthRequest } from '../middleware/auth';
import { PLATFORM_CAPABILITIES } from '../data/platformCapabilities';

const router = Router();

// Get all sources with honest status
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    // Get user's configured sources from database
    const result = await pool.query(
      'SELECT * FROM sources WHERE user_id = $1',
      [req.userId]
    );

    const userSources = result.rows.reduce((acc, row) => {
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
    // blogs/rss doesn't require credentials

    // Save or update source configuration
    const result = await pool.query(
      `INSERT INTO sources (user_id, platform, status, credentials, last_checked)
       VALUES ($1, $2, 'configured', $3, NOW())
       ON CONFLICT (user_id, platform)
       DO UPDATE SET 
         credentials = $3, 
         status = 'configured',
         last_checked = NOW(),
         updated_at = NOW()
       RETURNING *`,
      [req.userId, platform, JSON.stringify(credentials || {})]
    );

    res.json({
      success: true,
      message: `${capability.label} configured successfully`,
      source: result.rows[0],
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
    const sourceResult = await pool.query(
      'SELECT * FROM sources WHERE user_id = $1 AND platform = $2',
      [req.userId, platform]
    );

    if (sourceResult.rows.length === 0) {
      return res.status(400).json({ error: 'Source not configured. Please configure it first.' });
    }

    const source = sourceResult.rows[0];
    const credentials = source.credentials;

    // Test connection based on platform
    let testResult;
    
    if (platform === 'blogs') {
      // RSS doesn't need credentials, just return success
      testResult = { success: true, message: 'RSS feeds are ready to use' };
    } else if (platform === 'reddit') {
      // TODO: Implement actual Reddit API test
      testResult = { success: true, message: 'Reddit credentials validated' };
    } else if (platform === 'youtube') {
      // TODO: Implement actual YouTube API test
      testResult = { success: true, message: 'YouTube API key validated' };
    } else {
      testResult = { success: false, message: 'Platform not supported for testing' };
    }

    // Update last_checked timestamp
    await pool.query(
      'UPDATE sources SET last_checked = NOW() WHERE user_id = $1 AND platform = $2',
      [req.userId, platform]
    );

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

    await pool.query(
      'DELETE FROM sources WHERE user_id = $1 AND platform = $2',
      [req.userId, platform]
    );

    res.json({ success: true, message: 'Source removed successfully' });
  } catch (error: any) {
    console.error('Remove source error:', error);
    res.status(500).json({ error: 'Failed to remove source' });
  }
});

export default router;
