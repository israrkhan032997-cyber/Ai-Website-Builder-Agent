import React from 'react';
import { Globe, Plus, Settings, Layers, Code, ShieldCheck, Sparkles } from 'lucide-react';

interface NavbarProps {
  activeTab: 'dashboard' | 'projects' | 'workflow' | 'preview' | 'leads';
  setActiveTab: (tab: 'dashboard' | 'projects' | 'workflow' | 'preview' | 'leads') => void;
  onOpenCreate: () => void;
  onOpenConversationalWizard?: () => void;
  onOpenSettings: () => void;
  selectedProjectName?: string;
  hasPendingApprovals?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  onOpenCreate,
  onOpenConversationalWizard,
  onOpenSettings,
  selectedProjectName,
  hasPendingApprovals,
}) => {
  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand identity */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Globe className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-slate-900 tracking-tight text-base">AI Website Builder</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 border border-blue-200">
                Multi-Agent
              </span>
            </div>
            <p className="text-xs text-slate-500">Autonomous Business Website Engineering</p>
          </div>
        </div>

        {/* Center navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors ${
              activeTab === 'dashboard'
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            Dashboard
          </button>

          {selectedProjectName && (
            <>
              <button
                onClick={() => setActiveTab('workflow')}
                className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center space-x-1.5 ${
                  activeTab === 'workflow'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>Agent Workflow</span>
                {hasPendingApprovals && (
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                )}
              </button>

              <button
                onClick={() => setActiveTab('preview')}
                className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center space-x-1.5 ${
                  activeTab === 'preview'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <Code className="w-4 h-4" />
                <span>Live Preview</span>
              </button>

              <button
                onClick={() => setActiveTab('leads')}
                className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center space-x-1.5 ${
                  activeTab === 'leads'
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Contact Inquiries</span>
              </button>
            </>
          )}
        </nav>

        {/* Right actions */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Configure AI & Deployment Providers"
          >
            <Settings className="w-5 h-5" />
          </button>

          <button
            onClick={onOpenConversationalWizard || onOpenCreate}
            className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-md shadow-blue-500/20 transition-all active:scale-95"
          >
            <Sparkles className="w-4 h-4 mr-1.5" />
            <span>AI Chat Builder</span>
          </button>
        </div>
      </div>
    </header>
  );
};
