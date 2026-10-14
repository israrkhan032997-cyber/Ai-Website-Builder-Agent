import React, { useState, useEffect } from 'react';
import { X, Settings, Key, Cpu, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { SettingsData } from '../types';
import { api } from '../services/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onSaved,
}) => {
  const [data, setData] = useState<SettingsData | null>(null);
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash');
  const [netlifyToken, setNetlifyToken] = useState('');
  const [vercelToken, setVercelToken] = useState('');
  const [requireApproval, setRequireApproval] = useState(true);

  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ valid: boolean; message: string; model?: string } | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const res = await api.getSettings();
      setData(res);
      setGeminiModel(res.settings.gemini_model || 'gemini-2.5-flash');
      setRequireApproval(res.settings.require_command_approval ?? true);
    } catch (e: any) {
      setFeedback('Failed to load settings.');
    }
  };

  if (!isOpen) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setFeedback(null);
      await api.updateSettings({
        gemini_api_key: geminiKey.trim() || undefined,
        gemini_model: geminiModel,
        netlify_auth_token: netlifyToken.trim() || undefined,
        vercel_token: vercelToken.trim() || undefined,
        require_command_approval: requireApproval,
      });
      setFeedback('Settings successfully persisted!');
      onSaved();
      loadSettings();
    } catch (err: any) {
      setFeedback(`Error saving settings: ${err.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestGemini = async () => {
    try {
      setIsTesting(true);
      setTestResult(null);
      const res = await api.testGemini();
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ valid: false, message: err.message || 'Connection test failed.' });
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-xl overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center">
              <Settings className="w-4 h-4 mr-2 text-slate-700" />
              AI & Deployment Settings
            </h2>
            <p className="text-xs text-slate-500">Configure provider keys, default models, and execution security</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-6 space-y-6 max-h-[550px] overflow-y-auto">
          {feedback && (
            <div className={`p-3 text-xs rounded-xl font-medium ${feedback.includes('Error') ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-emerald-50 text-emerald-800 border border-emerald-200'}`}>
              {feedback}
            </div>
          )}

          {/* Provider Status Chips */}
          {data && (
            <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                Provider Connectivity Status
              </span>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {data.providers.map((p) => (
                  <div key={p.provider_name} className="p-2 bg-white rounded-lg border border-slate-200 flex items-center justify-between">
                    <span className="font-semibold text-slate-800">{p.provider_name}</span>
                    {p.configured ? (
                      <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                        Active
                      </span>
                    ) : (
                      <span className="text-[10px] font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded-full">
                        Fallback Mode
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Gemini API Key */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Google Gemini API Key
              </label>
              {data?.settings.gemini_api_key_masked && (
                <span className="text-[11px] font-mono text-slate-500">
                  Current: {data.settings.gemini_api_key_masked}
                </span>
              )}
            </div>

            <div className="flex space-x-2">
              <input
                type="password"
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                placeholder="Paste new Gemini API Key (e.g. AIzaSy...)"
                className="flex-grow px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono"
              />
              <button
                type="button"
                onClick={handleTestGemini}
                disabled={isTesting}
                className="px-3.5 py-2 rounded-xl text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-colors flex-shrink-0"
              >
                {isTesting ? 'Testing...' : 'Test Key'}
              </button>
            </div>

            {testResult && (
              <div className={`p-2.5 rounded-lg text-xs flex items-center space-x-2 ${testResult.valid ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}>
                {testResult.valid ? <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" /> : <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />}
                <span>{testResult.message}</span>
              </div>
            )}
            <p className="text-[11px] text-slate-500">
              Keys remain exclusively on the local server. When no key is set, the system seamlessly operates in deterministic offline-generation mode.
            </p>
          </div>

          {/* Model Selection */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Gemini Model
            </label>
            <select
              value={geminiModel}
              onChange={(e) => setGeminiModel(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="gemini-2.5-flash">Gemini 2.5 Flash (Recommended - Fastest & High Quality)</option>
              <option value="gemini-1.5-pro">Gemini 1.5 Pro (Deep Architecture Planning)</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash (Standard Lightweight)</option>
            </select>
          </div>

          {/* Security Gate */}
          <div className="pt-2 border-t border-slate-200">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded"
              />
              <div>
                <span className="text-xs font-bold text-slate-800 block">
                  Require Explicit Command Approval (Security Policy)
                </span>
                <span className="text-[11px] text-slate-500 block">
                  Prompts you before the Execution Agent runs any terminal commands.
                </span>
              </div>
            </label>
          </div>

          <div className="pt-4 border-t border-slate-200 flex justify-end space-x-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="px-5 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
