import React, { useState, useEffect } from 'react';
import {
  Globe, CheckCircle2, XCircle, RefreshCw, X, ExternalLink, Copy, Check
} from 'lucide-react';
import { api } from '../services/api';
import { Project, SubdomainCheckResponse } from '../types';

interface SubdomainDeployModalProps {
  project: Project;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (updatedSubdomain: string) => void;
}

export const SubdomainDeployModal: React.FC<SubdomainDeployModalProps> = ({
  project,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [subdomainInput, setSubdomainInput] = useState(
    project.subdomain || project.name.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/^-+|-+$/g, '') || 'my-site'
  );
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [checkResult, setCheckResult] = useState<SubdomainCheckResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deployedUrl, setDeployedUrl] = useState<string | null>(
    project.subdomain ? `http://127.0.0.1:8008/site/${project.subdomain}/index.html` : null
  );
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isOpen && subdomainInput.trim()) {
      handleCheckAvailability(subdomainInput.trim());
    }
  }, [isOpen]);

  const handleCheckAvailability = async (slugToCheck: string) => {
    const clean = slugToCheck.toLowerCase().replace(/[^a-z0-9-]/g, '');
    if (clean.length < 3) {
      setCheckResult(null);
      return;
    }

    setChecking(true);
    setError(null);
    try {
      const res = await api.checkSubdomain(clean, project.id);
      setCheckResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to check subdomain availability.');
    } finally {
      setChecking(false);
    }
  };

  const handleAssignSubdomain = async () => {
    if (!checkResult?.slug || !checkResult.available) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await api.assignSubdomain(project.id, checkResult.slug);
      setDeployedUrl(res.full_url);
      onSuccess(res.subdomain);
    } catch (err: any) {
      setError(err.message || 'Failed to reserve subdomain.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyUrl = () => {
    if (deployedUrl) {
      navigator.clipboard.writeText(deployedUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <Globe className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Subdomain Routing & Deployment</h2>
              <p className="text-xs text-slate-400">Deploy '{project.name}' on an isolated customer subdomain</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {deployedUrl && (
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Live Subdomain Active
                </span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300">
                  Online
                </span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={deployedUrl}
                  className="flex-1 bg-slate-900/80 border border-emerald-500/30 rounded-lg px-3 py-1.5 text-xs font-mono text-emerald-200 select-all focus:outline-none"
                />
                <button
                  onClick={handleCopyUrl}
                  className="p-2 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg transition"
                  title="Copy URL"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
                <a
                  href={deployedUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 text-white bg-emerald-600 hover:bg-emerald-500 rounded-lg transition flex items-center justify-center shadow-sm"
                  title="Visit Website"
                >
                  <ExternalLink className="w-4 h-4" />
                </a>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-400">
              Desired Subdomain Slug
            </label>
            <div className="flex items-center gap-2">
              <div className="flex-1 flex items-center bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-500">
                <input
                  type="text"
                  value={subdomainInput}
                  onChange={(e) => {
                    const val = e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '');
                    setSubdomainInput(val);
                    handleCheckAvailability(val);
                  }}
                  placeholder="pepsi"
                  className="bg-transparent text-sm text-white focus:outline-none w-full font-mono"
                />
                <span className="text-xs text-slate-500 font-mono select-none">.local</span>
              </div>

              <button
                type="button"
                onClick={() => handleCheckAvailability(subdomainInput)}
                disabled={checking}
                className="p-3 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition"
                title="Verify Availability"
              >
                <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Availability Status */}
          {checkResult && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs">
                {checkResult.available ? (
                  <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    '{checkResult.slug}' is available to reserve!
                  </span>
                ) : (
                  <span className="text-rose-400 flex items-center gap-1.5 font-medium">
                    <XCircle className="w-4 h-4" />
                    '{checkResult.slug}' is unavailable or reserved.
                  </span>
                )}
              </div>

              {/* Suggestions */}
              {checkResult.suggested_alternatives && checkResult.suggested_alternatives.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[11px] text-slate-400">Available suggestions:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {checkResult.suggested_alternatives.map((sug, i) => (
                      <button
                        key={i}
                        onClick={() => {
                          setSubdomainInput(sug);
                          handleCheckAvailability(sug);
                        }}
                        className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-blue-400 hover:bg-blue-950/60 hover:text-blue-300 border border-slate-700 transition font-mono"
                      >
                        {sug}.local
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-950/50 border border-rose-500/30 text-rose-300 text-xs">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/40 flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-400 hover:text-white rounded-xl transition"
          >
            Close
          </button>
          <button
            onClick={handleAssignSubdomain}
            disabled={!checkResult?.available || submitting}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-blue-600/20 flex items-center gap-2"
          >
            {submitting ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Reserving Subdomain...
              </>
            ) : (
              <>
                <Globe className="w-3.5 h-3.5" />
                Confirm & Route Subdomain
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
