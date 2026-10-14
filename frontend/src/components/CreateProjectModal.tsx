import React, { useState } from 'react';
import { X, Sparkles, Palette, Briefcase, Users, Layout } from 'lucide-react';
import { Project } from '../types';

interface CreateProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<Project>) => Promise<void>;
}

const COLOR_PRESETS = [
  { name: 'Royal Blue', primary: '#2563eb', secondary: '#0f172a', accent: '#38bdf8' },
  { name: 'Emerald Tech', primary: '#059669', secondary: '#064e3b', accent: '#34d399' },
  { name: 'Deep Indigo', primary: '#4f46e5', secondary: '#1e1b4b', accent: '#818cf8' },
  { name: 'Sunset Crimson', primary: '#e11d48', secondary: '#4c0519', accent: '#fb7185' },
  { name: 'Warm Amber', primary: '#d97706', secondary: '#451a03', accent: '#fbbf24' },
  { name: 'Modern Charcoal', primary: '#334155', secondary: '#020617', accent: '#94a3b8' },
];

const STYLES = [
  'Modern & Clean',
  'Minimalist & Bold',
  'Luxury & Premium',
  'Technical & Sleek',
  'Warm & Approachable',
];

export const CreateProjectModal: React.FC<CreateProjectModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [description, setDescription] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  const [style, setStyle] = useState('Modern & Clean');
  const [primaryColor, setPrimaryColor] = useState('#2563eb');
  const [secondaryColor, setSecondaryColor] = useState('#0f172a');
  const [accentColor, setAccentColor] = useState('#38bdf8');
  const [logoUrl, setLogoUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !industry.trim() || !description.trim()) {
      setError('Please provide business name, industry, and description.');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit({
        name: name.trim(),
        industry: industry.trim(),
        description: description.trim(),
        target_audience: targetAudience.trim() || undefined,
        style,
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        accent_color: accentColor,
        logo_url: logoUrl.trim() || undefined,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create project.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-2xl overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center">
              <Sparkles className="w-5 h-5 mr-2 text-blue-600" />
              Create Business Website
            </h2>
            <p className="text-xs text-slate-500">Provide business details for the AI agents to plan and code</p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg font-medium">
              {error}
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Business Name *
              </label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Lumina Health Solutions"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Industry Sector *
              </label>
              <input
                type="text"
                required
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                placeholder="e.g. Healthcare, SaaS, Real Estate"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Business Description & Value Proposition *
            </label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what your business offers, your primary strengths, target customer benefits, and key services..."
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Target Audience
              </label>
              <input
                type="text"
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                placeholder="e.g. Enterprise leaders, medical clinics"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Visual Style
              </label>
              <select
                value={style}
                onChange={(e) => setStyle(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {STYLES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Color Palette Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Brand Color Palette
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
              {COLOR_PRESETS.map((preset) => {
                const isSelected = primaryColor === preset.primary;
                return (
                  <button
                    type="button"
                    key={preset.name}
                    onClick={() => {
                      setPrimaryColor(preset.primary);
                      setSecondaryColor(preset.secondary);
                      setAccentColor(preset.accent);
                    }}
                    className={`p-2.5 rounded-xl border text-left flex items-center space-x-2.5 transition-all ${
                      isSelected
                        ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex -space-x-1">
                      <span className="w-5 h-5 rounded-full border border-white" style={{ backgroundColor: preset.primary }}></span>
                      <span className="w-5 h-5 rounded-full border border-white" style={{ backgroundColor: preset.secondary }}></span>
                      <span className="w-5 h-5 rounded-full border border-white" style={{ backgroundColor: preset.accent }}></span>
                    </div>
                    <span className="text-xs font-semibold text-slate-800">{preset.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Optional Logo URL */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Logo Image URL (Optional)
            </label>
            <input
              type="url"
              value={logoUrl}
              onChange={(e) => setLogoUrl(e.target.value)}
              placeholder="https://example.com/logo.png (If empty, an SVG brandmark is generated)"
              className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="pt-4 border-t border-slate-200 flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2.5 rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex items-center px-6 py-2.5 rounded-xl text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md transition-all disabled:opacity-50"
            >
              {isSubmitting ? 'Starting Agents...' : 'Generate Website'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
