import React from 'react';
import { Project } from '../types';
import { Globe, ArrowRight, Eye, Download, Trash2, Edit3, Rocket, MessageSquare, Plus, CheckCircle2, Clock, AlertTriangle } from 'lucide-react';

interface DashboardProps {
  projects: Project[];
  onSelectProject: (project: Project, tab?: 'workflow' | 'preview' | 'leads') => void;
  onOpenCreate: () => void;
  onOpenEdit: (project: Project) => void;
  onOpenDeploy: (project: Project) => void;
  onDeleteProject: (projectId: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  projects,
  onSelectProject,
  onOpenCreate,
  onOpenEdit,
  onOpenDeploy,
  onDeleteProject,
}) => {
  const readyCount = projects.filter((p) => p.status === 'ready').length;
  const deployedCount = projects.filter((p) => p.deployment_status === 'deployed').length;

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
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-700 text-white p-8 sm:p-10 shadow-lg shadow-blue-500/10">
        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-white/20 text-white backdrop-blur-sm">
            5 Specialized AI Agents Working in Harmony
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Turn Business Concepts into Production Websites
          </h1>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed">
            Our multi-agent pipeline coordinates Orchestrator, Asset, Design, Backend, and Execution agents to plan, design, code, and deploy real business websites.
          </p>
          <div className="pt-2">
            <button
              onClick={onOpenCreate}
              className="inline-flex items-center px-5 py-2.5 rounded-xl font-bold text-sm bg-white text-blue-700 hover:bg-blue-50 shadow-md transition-all"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Build a New Website
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Projects</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Globe className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{projects.length}</p>
          <p className="text-xs text-slate-500 mt-1">Autonomous workspace environments</p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Ready Websites</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{readyCount}</p>
          <p className="text-xs text-slate-500 mt-1">Fully coded & verified websites</p>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Deployments</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <Rocket className="w-4 h-4" />
            </div>
          </div>
          <p className="text-3xl font-extrabold text-slate-900">{deployedCount}</p>
          <p className="text-xs text-slate-500 mt-1">Live published websites</p>
        </div>
      </div>

      {/* Projects List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Your Website Projects</h2>
            <p className="text-xs text-slate-500">Manage, preview, iterate, and deploy your business websites</p>
          </div>
          <button
            onClick={onOpenCreate}
            className="inline-flex items-center px-4 py-2 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            Create Website
          </button>
        </div>

        {projects.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto mb-4">
              <Globe className="w-8 h-8" />
            </div>
            <h3 className="text-base font-bold text-slate-900 mb-1">No websites created yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mb-6">
              Describe your business once, and our 5-agent team will plan, design, code, and deploy your site.
            </p>
            <button
              onClick={onOpenCreate}
              className="inline-flex items-center px-5 py-2.5 rounded-xl font-bold text-sm bg-blue-600 text-white hover:bg-blue-700 shadow-sm transition-all"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Create First Website
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
                      onClick={() => onSelectProject(proj, 'preview')}
                      className="text-base font-bold text-slate-900 hover:text-blue-600 cursor-pointer transition-colors"
                    >
                      {proj.name}
                    </h3>
                    {getStatusBadge(proj.status)}
                    {proj.deployment_url && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        Live: {proj.deployment_provider || 'local'}
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
                    <span>Updated {new Date(proj.updated_at).toLocaleDateString()}</span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-1 max-w-3xl">
                    {proj.description}
                  </p>
                </div>

                {/* Quick actions */}
                <div className="flex items-center space-x-2 flex-shrink-0">
                  <button
                    onClick={() => onSelectProject(proj, 'workflow')}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="View Agent Workflow"
                  >
                    <span>Workflow</span>
                  </button>

                  <button
                    onClick={() => onSelectProject(proj, 'preview')}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors flex items-center space-x-1"
                    title="View Live Preview"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Preview</span>
                  </button>

                  <button
                    onClick={() => onOpenEdit(proj)}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="Request changes with natural language"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Edit</span>
                  </button>

                  <button
                    onClick={() => onSelectProject(proj, 'leads')}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    title="View Contact Submissions"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Leads</span>
                  </button>

                  <button
                    onClick={() => onOpenDeploy(proj)}
                    className="px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors flex items-center space-x-1"
                    title="Deploy website"
                  >
                    <Rocket className="w-3.5 h-3.5" />
                    <span>Deploy</span>
                  </button>

                  <a
                    href={`/api/v1/projects/${proj.id}/export`}
                    className="p-2 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
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
                    className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
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
