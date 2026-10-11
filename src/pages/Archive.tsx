import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Archive as ArchiveIcon, Search, Calendar, Filter } from 'lucide-react';
import { getNewsletters } from '../services/api';
import { Newsletter } from '../types';

export default function Archive() {
  const [newsletters, setNewsletters] = useState<Newsletter[]>([]);
  const [search, setSearch] = useState('');
  const [nicheFilter, setNicheFilter] = useState('');
  const [sortBy, setSortBy] = useState<'date-desc' | 'date-asc'>('date-desc');
  const navigate = useNavigate();

  useEffect(() => {
    getNewsletters().then(setNewsletters);
  }, []);

  const niches = [...new Set(newsletters.map(n => n.nicheName))];

  const filtered = newsletters
    .filter(n => {
      if (search && !n.subject.toLowerCase().includes(search.toLowerCase())) return false;
      if (nicheFilter && n.nicheName !== nicheFilter) return false;
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'date-desc') return new Date(b.date).getTime() - new Date(a.date).getTime();
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Newsletter Archive</h2>
        <p className="text-gray-500 dark:text-gray-400 mt-1">{newsletters.length} newsletters generated</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search newsletters..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={nicheFilter}
            onChange={(e) => setNicheFilter(e.target.value)}
            className="pl-9 pr-8 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
          >
            <option value="">All Niches</option>
            {niches.map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="pl-9 pr-8 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-sm outline-none focus:ring-2 focus:ring-indigo-500 appearance-none"
          >
            <option value="date-desc">Newest First</option>
            <option value="date-asc">Oldest First</option>
          </select>
        </div>
      </div>

      {/* Newsletter list */}
      {filtered.length === 0 ? (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
          <ArchiveIcon className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400">
            {newsletters.length === 0 ? 'No newsletters yet. Run a collection to generate your first newsletter.' : 'No newsletters match your filters.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((nl) => (
            <button
              key={nl.id}
              onClick={() => navigate(`/newsletter/${nl.id}`)}
              className="w-full text-left bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md hover:border-indigo-200 dark:hover:border-indigo-800 transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center shrink-0">
                  <ArchiveIcon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-white truncate">{nl.subject}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{nl.preheader}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span className="px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                      {nl.nicheName}
                    </span>
                    <span>{new Date(nl.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
                    <span>{nl.topStories.length} stories</span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
