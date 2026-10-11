import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Niches from './pages/Niches';
import Sources from './pages/Sources';
import RunHistory from './pages/RunHistory';
import Archive from './pages/Archive';
import NewsletterPreview from './pages/NewsletterPreview';
import Feedback from './pages/Feedback';
import Settings from './pages/Settings';
import NotFound from './pages/NotFound';
import { apiClient } from './services/apiClient';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  if (!apiClient.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

export default function App() {
  useEffect(() => {
    // Initialize theme
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.className = savedTheme;
  }, []);

  return (
    <HashRouter>
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
        <Route path="*" element={<NotFound />} />
      </Routes>
    </HashRouter>
  );
}
