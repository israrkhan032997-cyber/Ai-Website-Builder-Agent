import React from 'react';
import { Project, AgentLog, CommandApproval } from '../types';
import { Layers, Image, Code, Server, CheckCircle2, AlertCircle, Clock, Play, ArrowRight, ShieldAlert, History } from 'lucide-react';

interface AgentWorkflowViewProps {
  project: Project;
  logs: AgentLog[];
  approvals: CommandApproval[];
  isGenerating: boolean;
  onTriggerGenerate: () => void;
  onOpenPreview: () => void;
  onOpenApprovals: () => void;
  onOpenCheckpoints: () => void;
}

export const AgentWorkflowView: React.FC<AgentWorkflowViewProps> = ({
  project,
  logs,
  approvals,
  isGenerating,
  onTriggerGenerate,
  onOpenPreview,
  onOpenApprovals,
  onOpenCheckpoints,
}) => {
  const pendingApprovals = approvals.filter((a) => a.status === 'pending');

  const AGENTS = [
    {
      name: 'Orchestrator Agent',
      role: 'Architecture & Specifications',
      description: 'Analyzes business requirements, defines section hierarchy, colors, typography, and validation criteria.',
      icon: Layers,
      color: 'blue',
      isCurrent: project.current_agent?.includes('Orchestrator'),
      isCompleted: ['generating_assets', 'generating_design', 'generating_backend', 'validating', 'ready'].includes(project.status),
    },
    {
      name: 'Asset Agent',
      role: 'Imagery & Brandmarks',
      description: 'Sources verified high-res photography, generates vector brand logo mark, and curates icon sets.',
      icon: Image,
      color: 'purple',
      isCurrent: project.current_agent?.includes('Asset'),
      isCompleted: ['generating_design', 'generating_backend', 'validating', 'ready'].includes(project.status),
    },
    {
      name: 'Design Agent',
      role: 'Frontend Engineering',
      description: 'Generates responsive semantic HTML5, modern Tailwind CSS classes, and interactive scripts.',
      icon: Code,
      color: 'emerald',
      isCurrent: project.current_agent?.includes('Design'),
      isCompleted: ['generating_backend', 'validating', 'ready'].includes(project.status),
    },
    {
      name: 'Backend Agent',
      role: 'Server Submissions & API',
      description: 'Builds functional contact form handler, anti-spam honeypot validation, and serverless deployment route.',
      icon: Server,
      color: 'amber',
      isCurrent: project.current_agent?.includes('Backend'),
      isCompleted: ['validating', 'ready'].includes(project.status),
    },
    {
      name: 'Execution & Deployment Agent',
      role: 'Validation, Git & Security',
      description: 'Enforces security command approval policies, saves immutable Git checkpoints, and coordinates verified deployments.',
      icon: CheckCircle2,
      color: 'indigo',
      isCurrent: project.current_agent?.includes('Execution'),
      isCompleted: project.status === 'ready',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-extrabold text-slate-900">{project.name}</h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-700 border border-slate-200">
              {project.industry}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Status: <span className="font-semibold text-slate-700 capitalize">{project.status.replace('_', ' ')}</span> • Progress: {project.progress_percentage}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {pendingApprovals.length > 0 && (
            <button
              onClick={onOpenApprovals}
              className="px-3.5 py-2 rounded-xl text-xs font-bold text-amber-900 bg-amber-100 hover:bg-amber-200 border border-amber-300 flex items-center space-x-1.5 transition-colors animate-pulse"
            >
              <ShieldAlert className="w-4 h-4 text-amber-700" />
              <span>{pendingApprovals.length} Approval Pending</span>
            </button>
          )}

          <button
            onClick={onOpenCheckpoints}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors flex items-center space-x-1.5"
            title="Inspect Git version checkpoints"
          >
            <History className="w-4 h-4 text-slate-500" />
            <span>Git Checkpoints</span>
          </button>

          <button
            onClick={onTriggerGenerate}
            disabled={isGenerating}
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 mr-1.5 fill-current" />
            <span>{isGenerating ? 'Running Pipeline...' : 'Run Generation Pipeline'}</span>
          </button>

          {project.status === 'ready' && (
            <button
              onClick={onOpenPreview}
              className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors"
            >
              <span>View Live Website</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex justify-between items-center text-xs text-slate-600 font-semibold mb-2">
          <span>Multi-Agent Pipeline Execution</span>
          <span>{project.progress_percentage}</span>
        </div>
        <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-500 ease-out"
            style={{ width: project.progress_percentage }}
          ></div>
        </div>
        {project.current_step && (
          <p className="text-xs text-slate-500 mt-2 flex items-center">
            <Clock className="w-3.5 h-3.5 mr-1.5 text-blue-500 animate-spin" />
            {project.current_step}
          </p>
        )}
      </div>

      {/* 5 Agent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {AGENTS.map((agent, idx) => {
          const Icon = agent.icon;
          return (
            <div
              key={agent.name}
              className={`p-4 rounded-2xl border transition-all ${
                agent.isCurrent
                  ? 'border-blue-500 bg-blue-50/40 ring-2 ring-blue-500/20 shadow-sm'
                  : agent.isCompleted
                  ? 'border-emerald-200 bg-emerald-50/20'
                  : 'border-slate-200 bg-white opacity-85'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-[11px] font-bold text-slate-400">Step {idx + 1}</span>
                {agent.isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : agent.isCurrent ? (
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-600 animate-ping"></span>
                ) : (
                  <Clock className="w-4 h-4 text-slate-300" />
                )}
              </div>

              <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-700 flex items-center justify-center mb-3">
                <Icon className="w-4 h-4" />
              </div>

              <h3 className="text-xs font-bold text-slate-900 leading-snug">{agent.name}</h3>
              <p className="text-[11px] font-semibold text-slate-500 mb-2">{agent.role}</p>
              <p className="text-[11px] text-slate-600 leading-relaxed line-clamp-3">
                {agent.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Real Execution Logs Terminal */}
      <div className="bg-slate-900 rounded-2xl border border-slate-800 shadow-xl overflow-hidden">
        <div className="px-5 py-3.5 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
            </div>
            <span className="text-xs font-mono text-slate-400 ml-2">Live Agent Activity Log</span>
          </div>
          <span className="text-[11px] font-mono text-slate-500">{logs.length} entries recorded</span>
        </div>

        <div className="p-5 font-mono text-xs text-slate-300 max-h-80 overflow-y-auto space-y-2.5">
          {logs.length === 0 ? (
            <p className="text-slate-500 italic">No agent actions recorded yet. Click "Run Generation Pipeline" above to begin.</p>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="flex items-start space-x-2 leading-relaxed">
                <span className="text-slate-500 text-[10px] flex-shrink-0 mt-0.5">
                  [{new Date(log.created_at).toLocaleTimeString()}]
                </span>
                <span className="font-bold text-blue-400 flex-shrink-0">
                  {log.agent_name}:
                </span>
                <span className={log.status === 'failed' ? 'text-rose-400' : 'text-slate-200'}>
                  {log.message}
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
