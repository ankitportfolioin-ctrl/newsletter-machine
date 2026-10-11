import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, ThumbsUp, ThumbsDown, ExternalLink, TrendingUp, TrendingDown, Minus,
  MessageCircle, Lightbulb, Target, Zap, BarChart3, AlertCircle
} from 'lucide-react';
import { apiClient } from '../services/apiClient';
import { Newsletter, Story } from '../types';

const platformColors: Record<string, string> = {
  reddit: '#ff4500',
  blogs: '#f97316',
  youtube: '#ff0000',
  quora: '#b92b27',
  linkedin: '#0077b5',
  x: '#1da1f2',
  instagram: '#e4405f',
  facebook: '#1877f2',
};

export default function NewsletterPreview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [newsletter, setNewsletter] = useState<Newsletter | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      apiClient.getNewsletter(id).then((nl) => {
        setNewsletter(nl);
        setLoading(false);
      }).catch(err => {
        console.error('Failed to load newsletter:', err);
        setLoading(false);
      });
    }
  }, [id]);

  const handleFeedback = async (storyId: string, vote: 'up' | 'down') => {
    if (!newsletter) return;
    try {
      await apiClient.submitFeedback(newsletter.id, storyId, vote);
      // Refresh
      const updated = await apiClient.getNewsletter(newsletter.id);
      setNewsletter(updated);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full" />
      </div>
    );
  }

  if (!newsletter) {
    return (
      <div className="text-center py-20">
        <AlertCircle className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
        <p className="text-gray-500 dark:text-gray-400">Newsletter not found</p>
        <button onClick={() => navigate('/archive')} className="mt-4 text-indigo-600 hover:underline text-sm">
          ← Back to Archive
        </button>
      </div>
    );
  }

  const nl = newsletter;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <button onClick={() => navigate('/archive')} className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
        <ArrowLeft className="w-4 h-4" /> Back to Archive
      </button>

      {/* Subject & Preheader */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 md:p-8">
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 mb-3">
          <span className="px-2 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">{nl.nicheName}</span>
          <span>·</span>
          <span>{new Date(nl.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white leading-tight">{nl.subject}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-3 text-lg">{nl.preheader}</p>
      </div>

      {/* TL;DR */}
      <section className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-2xl border border-indigo-100 dark:border-indigo-800 p-6">
        <h2 className="text-lg font-bold text-indigo-900 dark:text-indigo-300 mb-3 flex items-center gap-2">
          <Zap className="w-5 h-5" /> TL;DR
        </h2>
        <ul className="space-y-2">
          {nl.tldr.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-indigo-800 dark:text-indigo-200">
              <span className="font-bold text-indigo-500 mt-0.5">{i + 1}.</span>
              {item}
            </li>
          ))}
        </ul>
      </section>

      {/* Top Stories */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-500" /> Top Stories
        </h2>
        <div className="space-y-4">
          {nl.topStories.map((story, i) => (
            <StoryCard key={story.id} story={story} rank={i + 1} onFeedback={handleFeedback} />
          ))}
        </div>
      </section>

      {/* Trend Radar */}
      <section className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-indigo-500" /> Trend Radar
        </h2>
        <div className="space-y-3">
          {nl.trendRadar.map((trend) => (
            <div key={trend.topic} className="flex items-center gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 dark:text-white text-sm">{trend.topic}</span>
                  {trend.momentum === 'rising' ? <TrendingUp className="w-3 h-3 text-green-500" /> :
                   trend.momentum === 'falling' ? <TrendingDown className="w-3 h-3 text-red-500" /> :
                   <Minus className="w-3 h-3 text-gray-400" />}
                </div>
                <div className="flex gap-1 mt-1">
                  {trend.sources.map(s => (
                    <span key={s} className="text-xs px-1.5 py-0.5 rounded capitalize" style={{ backgroundColor: platformColors[s] + '20', color: platformColors[s] }}>
                      {s}
                    </span>
                  ))}
                </div>
              </div>
              <div className="w-24">
                <div className="h-2 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                  <div className="h-full rounded-full bg-indigo-500" style={{ width: `${trend.score}%` }} />
                </div>
                <p className="text-xs text-gray-400 text-right mt-0.5">{trend.score}/100</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Platform Highlights */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-indigo-500" /> Platform Highlights
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {nl.platformHighlights.map((ph) => (
            <div key={ph.platform + ph.headline} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs px-2 py-0.5 rounded-full font-medium capitalize" style={{ backgroundColor: platformColors[ph.platform] + '20', color: platformColors[ph.platform] }}>
                  {ph.platform}
                </span>
              </div>
              <h3 className="font-semibold text-gray-900 dark:text-white text-sm">{ph.headline}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{ph.summary}</p>
              <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
                <span>by {ph.author}</span>
                <a href={ph.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-indigo-500">
                  Source <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Voices & Hot Takes */}
      <section className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          💬 Voices & Hot Takes
        </h2>
        <div className="space-y-4">
          {nl.voicesAndHotTakes.map((voice, i) => (
            <blockquote key={i} className="border-l-4 border-indigo-300 dark:border-indigo-600 pl-4">
              <p className="text-gray-700 dark:text-gray-300 italic">"{voice.quote}"</p>
              <footer className="mt-2 flex items-center gap-2 text-sm">
                <span className="font-medium text-gray-900 dark:text-white">— {voice.author}</span>
                <span className="text-xs px-1.5 py-0.5 rounded capitalize" style={{ backgroundColor: platformColors[voice.platform] + '20', color: platformColors[voice.platform] }}>
                  {voice.platform}
                </span>
                <a href={voice.url} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-400 hover:text-indigo-500 flex items-center gap-0.5">
                  source <ExternalLink className="w-3 h-3" />
                </a>
              </footer>
            </blockquote>
          ))}
        </div>
      </section>

      {/* Questions of the Day */}
      <section className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <MessageCircle className="w-5 h-5 text-indigo-500" /> Questions of the Day
        </h2>
        <div className="space-y-3">
          {nl.questionsOfTheDay.map((q, i) => (
            <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
              <span className="text-lg">❓</span>
              <div className="flex-1">
                <p className="font-medium text-gray-900 dark:text-white text-sm">{q.question}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                  <span className="px-1.5 py-0.5 rounded capitalize" style={{ backgroundColor: platformColors[q.source] + '20', color: platformColors[q.source] }}>
                    {q.source}
                  </span>
                  <span>{q.answers} answers</span>
                  <a href={q.url} target="_blank" rel="noopener noreferrer" className="hover:text-indigo-500 flex items-center gap-0.5">
                    view <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Content Opportunities */}
      <section>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Lightbulb className="w-5 h-5 text-yellow-500" /> Content Opportunities
        </h2>
        <div className="space-y-3">
          {nl.contentOpportunities.map((opp, i) => (
            <div key={i} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white">{opp.title}</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1"><strong>Angle:</strong> {opp.angle}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1"><strong>Evidence:</strong> {opp.evidence}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs px-1.5 py-0.5 rounded capitalize" style={{ backgroundColor: platformColors[opp.source] + '20', color: platformColors[opp.source] }}>
                  {opp.source}
                </span>
                <a href={opp.url} target="_blank" rel="noopener noreferrer" className="text-xs text-gray-400 hover:text-indigo-500 flex items-center gap-0.5">
                  source <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Action of the Day */}
      <section className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-2xl border border-green-200 dark:border-green-800 p-6">
        <h2 className="text-lg font-bold text-green-900 dark:text-green-300 mb-2 flex items-center gap-2">
          <Target className="w-5 h-5" /> Action of the Day
        </h2>
        <p className="text-green-800 dark:text-green-200">{nl.actionOfTheDay}</p>
      </section>

      {/* Coverage & Diagnostics */}
      <section className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Coverage & Diagnostics</h2>
        
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {nl.coverage.map((cov) => (
            <div key={cov.platform} className={`p-3 rounded-lg text-center ${
              cov.status === 'ok' ? 'bg-green-50 dark:bg-green-900/20' :
              cov.status === 'partial' ? 'bg-yellow-50 dark:bg-yellow-900/20' :
              'bg-red-50 dark:bg-red-900/20'
            }`}>
              <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{cov.platform}</p>
              <p className="text-lg font-bold text-gray-900 dark:text-white">{cov.items}</p>
              <p className={`text-xs ${
                cov.status === 'ok' ? 'text-green-600' :
                cov.status === 'partial' ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {cov.status === 'ok' ? '✓' : cov.status === 'partial' ? '⚠' : '✗'} {cov.status}
              </p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {nl.diagnostics.map((diag) => (
            <div key={diag.label} className="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
              <p className="text-xs text-gray-500 dark:text-gray-400">{diag.label}</p>
              <p className={`text-sm font-bold mt-0.5 ${
                diag.status === 'good' ? 'text-green-600 dark:text-green-400' :
                diag.status === 'warn' ? 'text-yellow-600 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400'
              }`}>{diag.value}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function StoryCard({ story, rank, onFeedback }: { story: Story; rank: number; onFeedback: (id: string, vote: 'up' | 'down') => void }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-5">
      <div className="flex items-start gap-4">
        <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900/30 flex items-center justify-center text-sm font-bold text-indigo-600 dark:text-indigo-400 shrink-0">
          {rank}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs px-2 py-0.5 rounded-full font-medium capitalize" style={{ backgroundColor: platformColors[story.source] + '20', color: platformColors[story.source] }}>
              {story.source}
            </span>
            <span className="text-xs text-gray-400">by {story.author}</span>
            <span className="text-xs text-gray-400">· score {story.score}</span>
          </div>
          <h3 className="font-semibold text-gray-900 dark:text-white">{story.title}</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{story.summary}</p>
          <div className="flex items-center justify-between mt-3">
            <a href={story.sourceUrl} target="_blank" rel="noopener noreferrer" className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1">
              View source <ExternalLink className="w-3 h-3" />
            </a>
            <div className="flex items-center gap-1">
              <button
                onClick={() => onFeedback(story.id, 'up')}
                className={`p-1.5 rounded-lg transition-colors ${
                  story.feedback === 'up' ? 'bg-green-100 dark:bg-green-900/30 text-green-600' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400'
                }`}
              >
                <ThumbsUp className="w-4 h-4" />
              </button>
              <button
                onClick={() => onFeedback(story.id, 'down')}
                className={`p-1.5 rounded-lg transition-colors ${
                  story.feedback === 'down' ? 'bg-red-100 dark:bg-red-900/30 text-red-600' : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400'
                }`}
              >
                <ThumbsDown className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
