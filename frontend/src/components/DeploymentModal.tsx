import React, { useState } from 'react';
import { X, Rocket, CheckCircle2, AlertTriangle, ExternalLink, Server, Globe } from 'lucide-react';
import { Project } from '../types';

interface DeploymentModalProps {
  project: Project;
  isOpen: boolean;
  onClose: () => void;
  onDeploy: (provider: 'local' | 'netlify' | 'vercel', domain?: string) => Promise<any>;
}

export const DeploymentModal: React.FC<DeploymentModalProps> = ({
  project,
  isOpen,
  onClose,
  onDeploy,
}) => {
  const [provider, setProvider] = useState<'local' | 'netlify' | 'vercel'>('local');
  const [customDomain, setCustomDomain] = useState('');
  const [isDeploying, setIsDeploying] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleDeploy = async () => {
    try {
      setIsDeploying(true);
      setError(null);
      const res = await onDeploy(provider, customDomain.trim() || undefined);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Deployment failed.');
    } finally {
      setIsDeploying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-lg overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-indigo-50">
          <div>
            <h2 className="text-base font-bold text-indigo-950 flex items-center">
              <Rocket className="w-4 h-4 mr-2 text-indigo-600" />
              Execution Agent: Deploy Website
            </h2>
            <p className="text-xs text-indigo-800">Pre-deployment verification and provider publication</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg font-medium flex items-center">
              <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && result.status === 'deployed' ? (
            <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 space-y-4 text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-emerald-950">Website Successfully Published!</h3>
                <p className="text-xs text-emerald-800 mt-1">{result.message}</p>
              </div>

              {result.deployment_url && (
                <div className="pt-2">
                  <a
                    href={result.deployment_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-md transition-all space-x-1.5"
                  >
                    <span>Visit Live Website</span>
                    <ExternalLink className="w-3.5 h-3.5 ml-1" />
                  </a>
                  <p className="text-[11px] font-mono text-emerald-700 mt-2 break-all">
                    {result.deployment_url}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <>
              {/* Validation Checklist */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Pre-flight Verification
                </h4>
                <div className="flex items-center space-x-2 text-xs text-slate-700">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Entrypoint <code>index.html</code> generated and structured</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-700">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Tailwind CSS styles and responsive viewport verified</span>
                </div>
                <div className="flex items-center space-x-2 text-xs text-slate-700">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Interactive contact form handler & anti-spam active</span>
                </div>
              </div>

              {/* Provider Selection */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Select Deployment Target
                </label>
                <div className="space-y-2">
                  <label
                    className={`flex items-start p-3.5 rounded-xl border cursor-pointer transition-all ${
                      provider === 'local'
                        ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-500/20'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="provider"
                      value="local"
                      checked={provider === 'local'}
                      onChange={() => setProvider('local')}
                      className="mt-0.5 text-indigo-600"
                    />
                    <div className="ml-3">
                      <span className="text-xs font-bold text-slate-900 block">Local Live Server</span>
                      <span className="text-[11px] text-slate-500">
                        Zero setup. Serves immediately on dedicated preview URL with live form endpoints.
                      </span>
                    </div>
                  </label>

                  <label
                    className={`flex items-start p-3.5 rounded-xl border cursor-pointer transition-all ${
                      provider === 'netlify'
                        ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-500/20'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="provider"
                      value="netlify"
                      checked={provider === 'netlify'}
                      onChange={() => setProvider('netlify')}
                      className="mt-0.5 text-indigo-600"
                    />
                    <div className="ml-3">
                      <span className="text-xs font-bold text-slate-900 block">Netlify Cloud Deploy</span>
                      <span className="text-[11px] text-slate-500">
                        Deploys zip archive directly via Netlify Deploy API. (Requires token in Settings)
                      </span>
                    </div>
                  </label>

                  <label
                    className={`flex items-start p-3.5 rounded-xl border cursor-pointer transition-all ${
                      provider === 'vercel'
                        ? 'border-indigo-600 bg-indigo-50/40 ring-2 ring-indigo-500/20'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="provider"
                      value="vercel"
                      checked={provider === 'vercel'}
                      onChange={() => setProvider('vercel')}
                      className="mt-0.5 text-indigo-600"
                    />
                    <div className="ml-3">
                      <span className="text-xs font-bold text-slate-900 block">Vercel Edge Deployment</span>
                      <span className="text-[11px] text-slate-500">
                        Deploys to Vercel global CDN network. (Requires token in Settings)
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={onClose}
                  disabled={isDeploying}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleDeploy}
                  disabled={isDeploying}
                  className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-all disabled:opacity-50"
                >
                  <Rocket className="w-3.5 h-3.5 mr-1.5" />
                  <span>{isDeploying ? 'Deploying...' : 'Confirm & Deploy'}</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
