import React, { useState } from 'react';
import { X, Sparkles, Send, Lightbulb } from 'lucide-react';
import { Project } from '../types';

interface EditWebsiteModalProps {
  project: Project;
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (instruction: string) => Promise<void>;
}

const QUICK_PROMPTS = [
  "Change the theme color to emerald green (#059669)",
  "Change headline to 'Empowering Enterprise Intelligence at Global Scale'",
  "Change theme color to deep indigo (#4f46e5)",
  "Change headline to 'Next-Generation Autonomous Systems for Modern Business'"
];

export const EditWebsiteModal: React.FC<EditWebsiteModalProps> = ({
  project,
  isOpen,
  onClose,
  onSubmit,
}) => {
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!instruction.trim()) return;

    try {
      setIsSubmitting(true);
      setError(null);
      await onSubmit(instruction.trim());
      setInstruction('');
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to apply changes.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-lg overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center">
              <Sparkles className="w-4 h-4 mr-2 text-blue-600" />
              Ask for Changes (Natural Language)
            </h2>
            <p className="text-xs text-slate-500">The Orchestrator Agent will formulate and apply targeted fixes</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg font-medium">
              {error}
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              What would you like to update?
            </label>
            <textarea
              required
              rows={4}
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="e.g. Change the primary color to emerald green and update the hero headline to 'Next-Gen Cybersecurity Solutions'..."
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 leading-relaxed"
            />
          </div>

          <div>
            <div className="flex items-center space-x-1.5 text-xs text-slate-500 font-semibold mb-2">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
              <span>Quick Refinements:</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  type="button"
                  key={prompt}
                  onClick={() => setInstruction(prompt)}
                  className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 text-left transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>

          <div className="pt-4 border-t border-slate-200 flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !instruction.trim()}
              className="inline-flex items-center px-5 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <Send className="w-3.5 h-3.5 mr-1.5" />
              <span>{isSubmitting ? 'Applying Changes...' : 'Apply Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
