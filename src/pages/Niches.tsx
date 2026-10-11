import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, ToggleLeft, ToggleRight, X, AlertCircle } from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { Niche } from '../types';

export default function Niches() {
  const [niches, setNiches] = useState<Niche[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    name: '',
    keywords: '',
    subreddits: '',
    blogFeeds: '',
    includeTerms: '',
    excludeTerms: '',
    enabled: true,
  });

  const loadNiches = async () => {
    try {
      const data = await apiClient.getNiches();
      setNiches(data);
    } catch (err) {
      console.error('Failed to load niches:', err);
    }
  };

  useEffect(() => { loadNiches(); }, []);

  const resetForm = () => {
    setForm({ name: '', keywords: '', subreddits: '', blogFeeds: '', includeTerms: '', excludeTerms: '', enabled: true });
    setEditingId(null);
    setShowForm(false);
    setError('');
  };

  const handleEdit = (niche: Niche) => {
    setForm({
      name: niche.name,
      keywords: niche.keywords.join(', '),
      subreddits: niche.subreddits.join(', '),
      blogFeeds: niche.blogFeeds.join(', '),
      includeTerms: niche.includeTerms.join(', '),
      excludeTerms: niche.excludeTerms.join(', '),
      enabled: niche.enabled,
    });
    setEditingId(niche.id);
    setShowForm(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const parseList = (s: string) => s.split(',').map(x => x.trim()).filter(Boolean);

    try {
      if (editingId) {
        await apiClient.updateNiche(editingId, {
          name: form.name,
          keywords: parseList(form.keywords),
          subreddits: parseList(form.subreddits),
          blogFeeds: parseList(form.blogFeeds),
          includeTerms: parseList(form.includeTerms),
          excludeTerms: parseList(form.excludeTerms),
          enabled: form.enabled,
        });
      } else {
        await apiClient.createNiche({
          name: form.name,
          keywords: parseList(form.keywords),
          subreddits: parseList(form.subreddits),
          blogFeeds: parseList(form.blogFeeds),
          includeTerms: parseList(form.includeTerms),
          excludeTerms: parseList(form.excludeTerms),
          enabled: form.enabled,
        });
      }
      resetForm();
      loadNiches();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleToggle = async (niche: Niche) => {
    try {
      await apiClient.updateNiche(niche.id, { enabled: !niche.enabled });
      loadNiches();
    } catch (err) {
      console.error('Failed to toggle niche:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Delete this niche? This cannot be undone.')) {
      try {
        await apiClient.deleteNiche(id);
        loadNiches();
      } catch (err) {
        console.error('Failed to delete niche:', err);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Niches</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">Manage content topics and sources</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Niche
        </button>
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl w-full max-w-lg max-h-[90vh] overflow-auto border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-lg">{editingId ? 'Edit Niche' : 'Create Niche'}</h3>
              <button onClick={resetForm} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              {error && (
                <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
                  <span className="text-sm text-red-700 dark:text-red-400">{error}</span>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium mb-1">Name *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="e.g., AI Tools for Marketers"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Keywords (comma-separated)</label>
                <input
                  type="text"
                  value={form.keywords}
                  onChange={(e) => setForm({ ...form, keywords: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="AI marketing, generative AI, content automation"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Subreddits (comma-separated)</label>
                <input
                  type="text"
                  value={form.subreddits}
                  onChange={(e) => setForm({ ...form, subreddits: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="r/artificial, r/marketing, r/ChatGPT"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Blog/RSS Feeds (comma-separated URLs)</label>
                <input
                  type="text"
                  value={form.blogFeeds}
                  onChange={(e) => setForm({ ...form, blogFeeds: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="https://blog.hubspot.com/marketing"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Include Terms</label>
                  <input
                    type="text"
                    value={form.includeTerms}
                    onChange={(e) => setForm({ ...form, includeTerms: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="AI, automation, LLM"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Exclude Terms</label>
                  <input
                    type="text"
                    value={form.excludeTerms}
                    onChange={(e) => setForm({ ...form, excludeTerms: e.target.value })}
                    className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="crypto, NFT"
                  />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setForm({ ...form, enabled: !form.enabled })}
                  className="flex items-center gap-2"
                >
                  {form.enabled ? (
                    <ToggleRight className="w-8 h-8 text-green-500" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-400" />
                  )}
                  <span className="text-sm font-medium">{form.enabled ? 'Enabled' : 'Disabled'}</span>
                </button>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  type="submit"
                  className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors"
                >
                  {editingId ? 'Save Changes' : 'Create Niche'}
                </button>
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg font-medium transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Niche list */}
      {niches.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <p className="text-gray-500 dark:text-gray-400">No niches yet. Create your first niche to get started.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {niches.map((niche) => (
            <div
              key={niche.id}
              className={`bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 ${
                !niche.enabled ? 'opacity-60' : ''
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{niche.name}</h3>
                    {!niche.enabled && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-500">
                        Disabled
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {niche.keywords.slice(0, 5).map((kw) => (
                      <span key={kw} className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                        {kw}
                      </span>
                    ))}
                    {niche.keywords.length > 5 && (
                      <span className="text-xs text-gray-400">+{niche.keywords.length - 5} more</span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-3 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    {niche.subreddits.length > 0 && <span>{niche.subreddits.length} subreddits</span>}
                    {niche.blogFeeds.length > 0 && <span>{niche.blogFeeds.length} feeds</span>}
                    <span>Updated {new Date(niche.updatedAt).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleToggle(niche)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                    title={niche.enabled ? 'Disable' : 'Enable'}
                  >
                    {niche.enabled ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5" />}
                  </button>
                  <button
                    onClick={() => handleEdit(niche)}
                    className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                    title="Edit"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(niche.id)}
                    className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-500 hover:text-red-500"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
