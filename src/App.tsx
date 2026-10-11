import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, Suspense, lazy } from 'react';
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Login from './pages/Login';
import NotFound from './pages/NotFound';
import { apiClient } from './services/apiClient';

// Lazy load pages for better performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Niches = lazy(() => import('./pages/Niches'));
const Sources = lazy(() => import('./pages/Sources'));
const RunHistory = lazy(() => import('./pages/RunHistory'));
const Archive = lazy(() => import('./pages/Archive'));
const NewsletterPreview = lazy(() => import('./pages/NewsletterPreview'));
const Feedback = lazy(() => import('./pages/Feedback'));
const Settings = lazy(() => import('./pages/Settings'));
const AlternativeSources = lazy(() => import('./pages/AlternativeSources'));
const LiveScrapeDemo = lazy(() => import('./pages/LiveScrapeDemo'));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!apiClient.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Loading...</p>
      </div>
    </div>
  );
}

export default function App() {
  useEffect(() => {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.className = savedTheme;
  }, []);

  return (
    <ErrorBoundary>
      <HashRouter>
        <Suspense fallback={<LoadingFallback />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/niches" element={<ProtectedRoute><Niches /></ProtectedRoute>} />
            <Route path="/sources" element={<ProtectedRoute><Sources /></ProtectedRoute>} />
            <Route path="/runs" element={<ProtectedRoute><RunHistory /></ProtectedRoute>} />
            <Route path="/archive" element={<ProtectedRoute><Archive /></ProtectedRoute>} />
            <Route path="/newsletter/:id" element={<ProtectedRoute><NewsletterPreview /></ProtectedRoute>} />
            <Route path="/feedback" element={<ProtectedRoute><Feedback /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
            <Route path="/alternative-sources" element={<ProtectedRoute><AlternativeSources /></ProtectedRoute>} />
            <Route path="/live-scrape" element={<ProtectedRoute><LiveScrapeDemo /></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </HashRouter>
    </ErrorBoundary>
  );
}
