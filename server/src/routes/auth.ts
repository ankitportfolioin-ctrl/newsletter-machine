import { Router, Request, Response } from 'express';
import { supabaseAdmin } from '../config/supabase';

const router = Router();

// Sign up with email/password
router.post('/signup', async (req: Request, res: Response) => {
  try {
    const { email, password, name } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }

    const { data, error } = await supabaseAdmin.auth.admin.createUser({
      email,
      password,
      email_confirm: true,
      user_metadata: { name }
    });

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    res.status(201).json({
      user: {
        id: data.user.id,
        email: data.user.email,
        name: data.user.user_metadata?.name
      },
      message: 'User created successfully'
    });
  } catch (error: any) {
    console.error('Signup error:', error);
    res.status(500).json({ error: 'Signup failed' });
  }
});

// Login with email/password
router.post('/login', async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password required' });
    }

    const { data, error } = await supabaseAdmin.auth.signInWithPassword({
      email,
      password
    });

    if (error) {
      return res.status(401).json({ error: error.message });
    }

    res.json({
      user: {
        id: data.user.id,
        email: data.user.email,
        name: data.user.user_metadata?.name
      },
      token: data.session.access_token,
      refresh_token: data.session.refresh_token
    });
  } catch (error: any) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Login failed' });
  }
});

// Google OAuth - Generate auth URL
router.get('/google', (req: Request, res: Response) => {
  const redirectTo = process.env.FRONTEND_URL || 'http://localhost:5173';
  
  res.json({
    auth_url: `${process.env.SUPABASE_URL}/auth/v1/authorize?provider=google&redirect_to=${redirectTo}/auth/callback`
  });
});

// Google OAuth callback
router.get('/google/callback', async (req: Request, res: Response) => {
  try {
    const { code } = req.query;

    if (!code) {
      return res.status(400).json({ error: 'Authorization code required' });
    }

    const { data, error } = await supabaseAdmin.auth.exchangeCodeForSession(code as string);

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    // Redirect to frontend with token
    const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5173';
    res.redirect(`${frontendUrl}/auth/callback?token=${data.session.access_token}`);
  } catch (error: any) {
    console.error('Google callback error:', error);
    res.status(500).json({ error: 'Authentication failed' });
  }
});

// Forgot password - Send reset email
router.post('/forgot-password', async (req: Request, res: Response) => {
  try {
    const { email } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email required' });
    }

    const redirectTo = `${process.env.FRONTEND_URL || 'http://localhost:5173'}/auth/reset-password`;

    const { error } = await supabaseAdmin.auth.resetPasswordForEmail(email, {
      redirectTo
    });

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    res.json({ message: 'Password reset email sent' });
  } catch (error: any) {
    console.error('Forgot password error:', error);
    res.status(500).json({ error: 'Failed to send reset email' });
  }
});

// Reset password with token
router.post('/reset-password', async (req: Request, res: Response) => {
  try {
    const { token, new_password } = req.body;

    if (!token || !new_password) {
      return res.status(400).json({ error: 'Token and new password required' });
    }

    // Verify the token and update password
    const { data, error } = await supabaseAdmin.auth.verifyOtp({
      token_hash: token,
      type: 'recovery'
    });

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    if (!data.user) {
      return res.status(400).json({ error: 'Invalid or expired token' });
    }

    // Update password
    const { error: updateError } = await supabaseAdmin.auth.admin.updateUserById(
      data.user.id,
      { password: new_password }
    );

    if (updateError) {
      return res.status(400).json({ error: updateError.message });
    }

    res.json({ message: 'Password reset successfully' });
  } catch (error: any) {
    console.error('Reset password error:', error);
    res.status(500).json({ error: 'Failed to reset password' });
  }
});

// Get current user (requires auth header)
router.get('/me', async (req: Request, res: Response) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const token = authHeader.substring(7);
    
    const { data: { user }, error } = await supabaseAdmin.auth.getUser(token);

    if (error || !user) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    res.json({
      id: user.id,
      email: user.email,
      name: user.user_metadata?.name,
      created_at: user.created_at
    });
  } catch (error: any) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Failed to get user' });
  }
});

// Refresh token
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const { refresh_token } = req.body;

    if (!refresh_token) {
      return res.status(400).json({ error: 'Refresh token required' });
    }

    const { data, error } = await supabaseAdmin.auth.refreshSession({
      refresh_token
    });

    if (error) {
      return res.status(401).json({ error: error.message });
    }

    if (!data.session) {
      return res.status(401).json({ error: 'No session returned' });
    }

    res.json({
      token: data.session.access_token,
      refresh_token: data.session.refresh_token
    });
  } catch (error: any) {
    console.error('Refresh token error:', error);
    res.status(500).json({ error: 'Failed to refresh token' });
  }
});

// Logout
router.post('/logout', async (req: Request, res: Response) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const token = authHeader.substring(7);
    
    const { error } = await supabaseAdmin.auth.admin.signOut(token);

    if (error) {
      return res.status(400).json({ error: error.message });
    }

    res.json({ message: 'Logged out successfully' });
  } catch (error: any) {
    console.error('Logout error:', error);
    res.status(500).json({ error: 'Failed to logout' });
  }
});

export default router;
