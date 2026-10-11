import { Router, Response } from 'express';
import pool from '../config/database';
import { authenticateToken, AuthRequest } from '../middleware/auth';

const router = Router();

// Get all sources for user
router.get('/', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      'SELECT * FROM sources WHERE user_id = $1 ORDER BY platform',
      [req.userId]
    );

    // Map database records to frontend format
    const sources = result.rows.map(row => ({
      platform: row.platform,
      label: getPlatformLabel(row.platform),
      status: row.status,
      lastChecked: row.last_checked || new Date().toISOString(),
      itemsCollected: row.items_collected || 0,
      message: getStatusMessage(row.platform, row.status),
      icon: row.platform,
      color: getPlatformColor(row.platform),
    }));

    res.json(sources);
  } catch (error: any) {
    console.error('Get sources error:', error);
    res.status(500).json({ error: 'Failed to get sources' });
  }
});

// Update source status
router.put('/:platform', authenticateToken, async (req: AuthRequest, res: Response) => {
  try {
    const { platform } = req.params;
    const { status, credentials } = req.body;

    const result = await pool.query(
      `INSERT INTO sources (user_id, platform, status, credentials, last_checked)
       VALUES ($1, $2, $3, $4, NOW())
       ON CONFLICT (user_id, platform)
       DO UPDATE SET status = $3, credentials = $4, last_checked = NOW(), updated_at = NOW()
       RETURNING *`,
      [req.userId, platform, status, JSON.stringify(credentials || {})]
    );

    res.json(result.rows[0]);
  } catch (error: any) {
    console.error('Update source error:', error);
    res.status(500).json({ error: 'Failed to update source' });
  }
});

// Helper functions
function getPlatformLabel(platform: string): string {
  const labels: Record<string, string> = {
    reddit: 'Reddit',
    youtube: 'YouTube',
    blogs: 'Blogs & RSS',
    x: 'X (Twitter)',
    linkedin: 'LinkedIn',
    instagram: 'Instagram',
    facebook: 'Facebook',
    quora: 'Quora',
  };
  return labels[platform] || platform;
}

function getPlatformColor(platform: string): string {
  const colors: Record<string, string> = {
    reddit: '#ff4500',
    youtube: '#ff0000',
    blogs: '#f97316',
    x: '#1da1f2',
    linkedin: '#0077b5',
    instagram: '#e4405f',
    facebook: '#1877f2',
    quora: '#b92b27',
  };
  return colors[platform] || '#6b7280';
}

function getStatusMessage(platform: string, status: string): string {
  const messages: Record<string, string> = {
    connected: `Connected via ${platform} API`,
    not_configured: `${platform} API credentials not configured`,
    error: `Error connecting to ${platform}`,
    rate_limited: `${platform} rate limit reached`,
  };
  return messages[status] || status;
}

export default router;
