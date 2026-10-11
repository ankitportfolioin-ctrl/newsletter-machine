import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { Loader2 } from 'lucide-react';

export default function AuthCallback() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    // Merge params from URL query, hash-router query, and raw fragments.
    // Supabase may deliver tokens as ?token_hash= (PKCE), ?code= (OAuth),
    // or #access_token= (implicit) — at URL level or inside the hash.
    const collectParams = (): URLSearchParams => {
      const merged = new URLSearchParams(window.location.search);
      const hash = window.location.hash;
      const qIndex = hash.indexOf('?');
      if (qIndex !== -1) {
        new URLSearchParams(hash.substring(qIndex + 1)).forEach((v, k) => {
          if (!merged.has(k)) merged.set(k, v);
        });
      }
      hash.split('#').slice(1).forEach((part) => {
        if (part.includes('=')) {
          new URLSearchParams(part).forEach((v, k) => {
            if (!merged.has(k)) merged.set(k, v);
          });
        }
      });
      searchParams.forEach((v, k) => {
        if (!merged.has(k)) merged.set(k, v);
      });
      return merged;
    };

    const handleCallback = async () => {
      try {
        const params = collectParams();

        // 0. Supabase error redirect (expired/invalid link, denied access)
        const urlError = params.get('error_description') || params.get('error');
        if (urlError) {
          throw new Error(
            urlError === 'access_denied'
              ? 'Access denied. The link may have expired — please request a new one.'
              : urlError
          );
        }

        // 1. Check for token in URL (from our backend callback)
        const token = params.get('token');

        if (token) {
          // Set the session with the token
          const { error } = await supabase.auth.setSession({
            access_token: token,
            refresh_token: '' // Will be handled by Supabase
          });

          if (error) throw error;
          navigate('/');
          return;
        }

        // 2. PKCE-style email confirmation / OAuth (?token_hash=&type= or ?code=)
        const tokenHash = params.get('token_hash');
        const type = params.get('type');
        if (tokenHash && type) {
          const { error } = await supabase.auth.verifyOtp({
            token_hash: tokenHash,
            type: type as any,
          });
          if (error) throw error;
          navigate('/');
          return;
        }

        const code = params.get('code');
        if (code) {
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) throw error;
          navigate('/');
          return;
        }

        // 3. Handle Supabase's built-in OAuth/implicit callback
        // (supabase-js auto-detects #access_token= sessions on load)
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) throw sessionError;

        if (session) {
          navigate('/');
        } else {
          setError('Authentication failed. Please try again.');
          setTimeout(() => navigate('/login'), 3000);
        }
      } catch (err: any) {
        setError(err.message || 'Authentication failed');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    handleCallback();
  }, [navigate, searchParams]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-indigo-950">
      <div className="text-center">
        {error ? (
          <>
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Authentication Failed</h2>
            <p className="text-gray-600 dark:text-gray-400">{error}</p>
            <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">Redirecting to login...</p>
          </>
        ) : (
          <>
            <Loader2 className="w-12 h-12 text-indigo-600 dark:text-indigo-400 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Completing sign in...</h2>
            <p className="text-gray-600 dark:text-gray-400">Please wait while we verify your account.</p>
          </>
        )}
      </div>
    </div>
  );
}
