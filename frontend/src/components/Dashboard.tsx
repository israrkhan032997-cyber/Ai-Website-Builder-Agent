import React from 'react';
import { Project } from '../types';
import {
  Globe, ArrowRight, Eye, Download, Trash2, Edit3, Rocket, MessageSquare,
  Plus, CheckCircle2, Clock, AlertTriangle, Sparkles, Layers, Code2
} from 'lucide-react';

interface DashboardProps {
  projects: Project[];
  onSelectProject: (project: Project, tab?: 'workflow' | 'preview' | 'leads') => void;
  onOpenCreate: () => void;
  onOpenConversationalWizard: () => void;
  onOpenWorkspace: (project: Project) => void;
  onOpenEdit: (project: Project) => void;
  onOpenDeploy: (project: Project) => void;
  onDeleteProject: (projectId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  projects,
  onSelectProject,
  onOpenCreate,
  onOpenConversationalWizard,
  onOpenWorkspace,
  onOpenEdit,
  onOpenDeploy,
  onDeleteProject,
}) => {
  const readyCount = projects.filter((p) => p.status === 'ready').length;
  const multipageCount = projects.filter((p) => p.website_type === 'multi-page').length;

  const getStatusBadge = (status: Project['status']) => {
    switch (status) {
      case 'ready':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Ready
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertTriangle className="w-3.5 h-3.5 mr-1" /> Error
          </span>
        );
      case 'draft':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <Clock className="w-3.5 h-3.5 mr-1" /> Draft
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 animate-pulse">
            <Clock className="w-3.5 h-3.5 mr-1" /> In Progress ({status.replace('_', ' ')})
          </span>
        );
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-violet-700 text-white p-8 sm:p-10 shadow-xl shadow-blue-500/15">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-white/20 text-white backdrop-blur-sm border border-white/20">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            Conversational AI & Lovable-Style Workspace
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight leading-tight">
            Turn Business Ideas into Production Multi-Page Websites
          </h1>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed">
            Chat with specialized AI agents to plan, design, code, and deploy responsive React frontends paired with genuine PHP backends on customer subdomains.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <button
              onClick={onOpenConversationalWizard}
              className="inline-flex items-center px-5 py-3 rounded-xl font-bold text-sm bg-white text-blue-700 hover:bg-blue-50 shadow-lg shadow-black/10 transition-all active:scale-95"
            >
              <Sparkles className="w-4 h-4 mr-2 text-indigo-600" />
              Build with Conversational AI
            </button>
            <button
              onClick={onOpenCreate}
              className="inline-flex items-center px-4 py-3 rounded-xl font-bold text-sm bg-white/10 hover:bg-white/20 text-white border border-white/25 backdrop-blur-sm transition-all"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Quick Form
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Projects</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Globe className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{projects.length}</p>
          <p className="text-xs text-slate-500 mt-1">Autonomous workspace environments</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Ready Websites</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{readyCount}</p>
          <p className="text-xs text-slate-500 mt-1">Verified with live preview active</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Multi-Page Sites</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Layers className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{multipageCount}</p>
          <p className="text-xs text-slate-500 mt-1">Dedicated multi-page architectures</p>
        </div>
      </div>

      {/* Projects List Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Website Projects</h2>
            <p className="text-xs text-slate-500">Manage, edit, preview, and deploy customer websites</p>
          </div>
          <button
            onClick={onOpenConversationalWizard}
            className="inline-flex items-center px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-sm transition"
          >
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            New Website
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="p-12 text-center space-y-4">
            <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">No websites generated yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Start by describing your business in natural language. Our conversational assistant and AI agent pipeline will do the rest.
            </p>
            <button
              onClick={onOpenConversationalWizard}
              className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold bg-blue-600 text-white hover:bg-blue-700 shadow-md transition"
            >
              Start Conversational Builder
            </button>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {projects.map((proj) => (
              <div
                key={proj.id}
                className="p-6 hover:bg-slate-50/60 transition-colors flex flex-col lg:flex-row lg:items-center justify-between gap-6"
              >
                <div className="space-y-2 flex-grow">
                  <div className="flex items-center space-x-3">
                    <h3
                      onClick={() => onOpenWorkspace(proj)}
                      className="text-base font-bold text-slate-900 hover:text-blue-600 cursor-pointer transition-colors flex items-center gap-2"
                    >
                      {proj.name}
                      <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                    </h3>
                    {getStatusBadge(proj.status)}
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">
                      {proj.website_type === 'multi-page' ? 'Multi-Page' : 'Single-Page'}
                    </span>
                    {proj.subdomain && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {proj.subdomain}.local
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-slate-500">
                    <span className="font-semibold text-slate-700">{proj.industry}</span>
                    <span>•</span>
                    <span>Style: {proj.style || 'Modern'}</span>
                    <span>•</span>
                    <span className="flex items-center space-x-1">
                      <span className="w-2.5 h-2.5 rounded-full inline-block" style={{ backgroundColor: proj.primary_color || '#2563eb' }}></span>
                      <span>Palette</span>
                    </span>
                    <span>•</span>
                    <span>Stack: React + PHP</span>
                    <span>•</span>
                    <span>Updated {new Date(proj.updated_at).toLocaleDateString()}</span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-1 max-w-3xl">
                    {proj.description}
                  </p>
                </div>

                {/* Quick actions */}
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    onClick={() => onOpenWorkspace(proj)}
                    className="px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-600/15 transition-all flex items-center space-x-1.5 active:scale-95"
                    title="Open interactive Lovable-style Workspace"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Workspace</span>
                  </button>

                  <button
                    onClick={() => onSelectProject(proj, 'preview')}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="View Live Preview"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Preview</span>
                  </button>

                  <button
                    onClick={() => onOpenEdit(proj)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="Request changes with natural language"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Edit</span>
                  </button>

                  <button
                    onClick={() => onSelectProject(proj, 'leads')}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="View Contact Submissions"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Leads</span>
                  </button>

                  <button
                    onClick={() => onOpenDeploy(proj)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors flex items-center space-x-1"
                    title="Deploy website"
                  >
                    <Rocket className="w-3.5 h-3.5" />
                    <span>Deploy</span>
                  </button>

                  <a
                    href={`/api/v1/projects/${proj.id}/export`}
                    className="p-2 rounded-xl text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                    title="Download ZIP"
                  >
                    <Download className="w-4 h-4" />
                  </a>

                  <button
                    onClick={() => {
                      if (confirm(`Are you sure you want to permanently delete "${proj.name}"?`)) {
                        onDeleteProject(proj.id);
                      }
                    }}
                    className="p-2 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
