import React, { useState, useEffect, useRef } from 'react';
import {
  Monitor, Tablet, Smartphone, RefreshCw, Send, ArrowLeft, Download,
  ExternalLink, Sparkles, Code2, Globe, Bot, User, CheckCircle2,
  FileCode, Database, GitCommit, Copy, Check, ChevronDown,
  Layers, ChevronRight, Eye, ShieldAlert, Cpu
} from 'lucide-react';
import { api } from '../services/api';
import { Project, AgentLog, WebsitePage, Checkpoint } from '../types';
import { SubdomainDeployModal } from './SubdomainDeployModal';

interface LovableWorkspaceProps {
  project: Project;
  onBackToDashboard: () => void;
  onProjectUpdated: (project: Project) => void;
}

type ViewportMode = 'desktop' | 'tablet' | 'mobile';
type LeftTab = 'chat' | 'agents' | 'code';

export const LovableWorkspace: React.FC<LovableWorkspaceProps> = ({
  project: initialProject,
  onBackToDashboard,
  onProjectUpdated,
}) => {
  const [project, setProject] = useState<Project>(initialProject);
  const [viewport, setViewport] = useState<ViewportMode>('desktop');
  const [activeTab, setActiveTab] = useState<LeftTab>('chat');

  // Multi-page navigation
  const [pages, setPages] = useState<WebsitePage[]>([]);
  const [activePageFile, setActivePageFile] = useState<string>('index.html');

  // Preview iframe control
  const [previewKey, setPreviewKey] = useState<number>(Date.now());
  const [isIframeLoading, setIsIframeLoading] = useState<boolean>(true);

  // NLP Chat & Iterations
  const [editPrompt, setEditPrompt] = useState('');
  const [isApplyingEdit, setIsApplyingEdit] = useState(false);
  const [chatMessages, setChatMessages] = useState<Array<{ sender: 'user' | 'assistant'; text: string; hash?: string }>>([
    {
      sender: 'assistant',
      text: `Hello! Your ${project.website_type || 'single-page'} website for ${project.name} is ready. Ask me any changes (colors, headlines, sections) and I will update your source code surgically.`,
    },
  ]);

  // Agent logs & checkpoints
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Code inspection
  const [filesList, setFilesList] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('index.html');
  const [fileContent, setFileContent] = useState<string>('');
  const [isLoadingFile, setIsLoadingFile] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);

  // Subdomain modal
  const [isSubdomainModalOpen, setIsSubdomainModalOpen] = useState(false);

  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Load project pages and files on mount
  useEffect(() => {
    loadProjectDetails();
    loadPages();
    loadFiles();
    loadLogs();
  }, [project.id]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages, isApplyingEdit]);

  const loadProjectDetails = async () => {
    try {
      const p = await api.getProject(project.id);
      setProject(p);
      onProjectUpdated(p);
    } catch (e) {
      console.error('Error fetching project:', e);
    }
  };

  const loadPages = async () => {
    try {
      const pgs = await api.getProjectPages(project.id);
      setPages(pgs);
      if (pgs.length > 0 && !pgs.some((p) => p.file_path === activePageFile)) {
        setActivePageFile(pgs[0].file_path);
      }
    } catch (e) {
      console.error('Error fetching pages:', e);
    }
  };

  const loadFiles = async () => {
    try {
      const res = await api.getProjectFiles(project.id);
      setFilesList(res.files || []);
      loadFileContent(selectedFile);
    } catch (e) {
      console.error('Error fetching files:', e);
    }
  };

  const loadFileContent = async (path: string) => {
    setIsLoadingFile(true);
    setSelectedFile(path);
    try {
      const res = await api.getFileContent(project.id, path);
      setFileContent(res.content);
    } catch (e) {
      setFileContent('// File not found or empty');
    } finally {
      setIsLoadingFile(false);
    }
  };

  const loadLogs = async () => {
    try {
      const logs = await api.getAgentLogs(project.id);
      setAgentLogs(logs);
      const chks = await api.getCheckpoints(project.id);
      setCheckpoints(chks);
    } catch (e) {
      console.error('Error fetching logs:', e);
    }
  };

  const handleApplyEdit = async (promptToApply?: string) => {
    const instruction = (promptToApply || editPrompt).trim();
    if (!instruction || isApplyingEdit) return;

    setEditPrompt('');
    setChatMessages((prev) => [...prev, { sender: 'user', text: instruction }]);
    setIsApplyingEdit(true);

    // Extract exact asset URL from user input if present
    const urlMatch = instruction.match(/https?:\/\/[^\s<>"')\]}]+/);
    const extractedUrl = urlMatch ? urlMatch[0].replace(/[,.'")\]}]+$/, '') : undefined;

    try {
      const res = await api.editWebsite(project.id, instruction, undefined, extractedUrl);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: res.message || `Applied change: "${instruction}".`,
          hash: res.commit_hash,
        },
      ]);
      // Reload preview iframe and files
      setPreviewKey(Date.now());
      loadFiles();
      loadLogs();
      loadProjectDetails();
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: `Could not apply modification: ${err.message || 'Unknown error'}`,
        },
      ]);
    } finally {
      setIsApplyingEdit(false);
    }
  };

  const handleRegenerate = async () => {
    setIsGenerating(true);
    try {
      await api.generateWebsite(project.id);
      setPreviewKey(Date.now());
      loadPages();
      loadFiles();
      loadLogs();
      loadProjectDetails();
    } catch (e) {
      console.error('Regeneration error:', e);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(fileContent);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const previewUrl = `/api/v1/preview/${project.id}/${activePageFile}`;
  const fullLiveUrl = `http://127.0.0.1:8008${previewUrl}`;
  const subdomainUrl = project.subdomain
    ? `http://127.0.0.1:8008/site/${project.subdomain}/${activePageFile}`
    : fullLiveUrl;

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Workspace Top Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-4 flex items-center justify-between shrink-0 z-30">
        {/* Left: Project title & Back */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onBackToDashboard}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-sm text-white tracking-tight">{project.name}</span>
            <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium">
              {project.website_type === 'multi-page' ? 'Multi-Page' : 'Single-Page'}
            </span>
            <span className="hidden sm:inline-block text-[10px] bg-slate-800 text-slate-400 border border-slate-700 px-2 py-0.5 rounded-full font-mono">
              React SPA
            </span>
          </div>
        </div>

        {/* Center: Viewport Switcher & Multi-page selector */}
        <div className="flex items-center space-x-3">
          {/* Page dropdown (if multi-page) */}
          {pages.length > 1 && (
            <div className="relative flex items-center bg-slate-800/80 border border-slate-700 rounded-xl px-2.5 py-1 text-xs">
              <span className="text-slate-400 mr-1.5 text-[10px] uppercase font-bold">Page:</span>
              <select
                value={activePageFile}
                onChange={(e) => {
                  setActivePageFile(e.target.value);
                  setIsIframeLoading(true);
                }}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer pr-4"
              >
                {pages.map((p) => (
                  <option key={p.id} value={p.file_path} className="bg-slate-900 text-white">
                    {p.title} ({p.file_path})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Device Viewports */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5 shadow-inner">
            <button
              onClick={() => setViewport('desktop')}
              className={`p-1.5 rounded-lg text-xs flex items-center gap-1 transition ${
                viewport === 'desktop' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Desktop (Full)"
            >
              <Monitor className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewport('tablet')}
              className={`p-1.5 rounded-lg text-xs flex items-center gap-1 transition ${
                viewport === 'tablet' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Tablet (768px)"
            >
              <Tablet className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewport('mobile')}
              className={`p-1.5 rounded-lg text-xs flex items-center gap-1 transition ${
                viewport === 'mobile' ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Mobile (375px)"
            >
              <Smartphone className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2">
          {/* Subdomain pill button */}
          <button
            onClick={() => setIsSubdomainModalOpen(true)}
            className="hidden md:flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{project.subdomain ? `${project.subdomain}.local` : 'Set Subdomain'}</span>
          </button>

          {/* Export ZIP */}
          <a
            href={`/api/v1/projects/${project.id}/export`}
            download
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Download ZIP"
          >
            <Download className="w-4 h-4" />
          </a>

          {/* Open live preview in new window */}
          <a
            href={subdomainUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Open in New Tab"
          >
            <ExternalLink className="w-4 h-4" />
          </a>
        </div>
      </header>

      {/* Main Workspace Workspace (Left sidebar + Center preview) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Lovable AI Sidebar (Chat, Agents, Code) */}
        <div className="w-96 flex flex-col bg-slate-900 border-r border-slate-800 shrink-0">
          {/* Tabs Header */}
          <div className="h-11 border-b border-slate-800 flex items-center px-3 bg-slate-950/50">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'chat'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              AI Assistant
            </button>
            <button
              onClick={() => setActiveTab('agents')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'agents'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              Agent Team
            </button>
            <button
              onClick={() => setActiveTab('code')}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition ${
                activeTab === 'code'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              Code & PHP
            </button>
          </div>

          {/* TAB 1: AI Chat (Natural Language Iterations) */}
          {activeTab === 'chat' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatMessages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-2.5 max-w-[90%] ${
                      msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                    }`}
                  >
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                        msg.sender === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-800 border border-slate-700 text-indigo-400'
                      }`}
                    >
                      {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                    </div>

                    <div className="space-y-1">
                      <div
                        className={`p-3 rounded-xl text-xs leading-relaxed ${
                          msg.sender === 'user'
                            ? 'bg-blue-600 text-white rounded-tr-none'
                            : 'bg-slate-800 border border-slate-700/80 text-slate-200 rounded-tl-none whitespace-pre-line'
                        }`}
                      >
                        {msg.text}
                      </div>
                    </div>
                  </div>
                ))}

                {isApplyingEdit && (
                  <div className="flex items-center gap-2 text-xs text-slate-400 pl-2">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-500" />
                    <span>Orchestrating surgical code update...</span>
                  </div>
                )}

                <div ref={chatBottomRef} />
              </div>

              {/* Quick suggestions */}
              <div className="px-3 py-2 bg-slate-950/60 border-t border-slate-800/80 flex flex-wrap gap-1.5">
                {[
                  'Change theme to emerald green',
                  'Change theme to purple',
                  'Make headline more punchy',
                  'Update contact section style',
                ].map((sug, i) => (
                  <button
                    key={i}
                    onClick={() => handleApplyEdit(sug)}
                    disabled={isApplyingEdit}
                    className="text-[11px] px-2 py-1 rounded bg-slate-800/90 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700/80 transition"
                  >
                    + {sug}
                  </button>
                ))}
              </div>

              {/* Chat Input */}
              <div className="p-3 bg-slate-950 border-t border-slate-800">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleApplyEdit();
                  }}
                  className="flex items-center gap-1.5"
                >
                  <input
                    type="text"
                    value={editPrompt}
                    onChange={(e) => setEditPrompt(e.target.value)}
                    placeholder="Ask AI to modify design or text..."
                    disabled={isApplyingEdit}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  />
                  <button
                    type="submit"
                    disabled={!editPrompt.trim() || isApplyingEdit}
                    className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white rounded-xl text-xs font-bold transition flex items-center justify-center"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 2: Agent Timeline */}
          {activeTab === 'agents' && (
            <div className="flex-1 flex flex-col overflow-hidden p-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Pipeline Timeline</span>
                <button
                  onClick={handleRegenerate}
                  disabled={isGenerating}
                  className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                >
                  <RefreshCw className={`w-3 h-3 ${isGenerating ? 'animate-spin' : ''}`} />
                  Rerun Pipeline
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3">
                {agentLogs.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No agent logs recorded yet.</p>
                ) : (
                  agentLogs.map((log) => (
                    <div
                      key={log.id}
                      className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-200">{log.agent_name}</span>
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded font-mono uppercase ${
                            log.status === 'success'
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : log.status === 'failed'
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : 'bg-blue-500/20 text-blue-400'
                          }`}
                        >
                          {log.status}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">{log.message}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 3: Code & PHP Viewer */}
          {activeTab === 'code' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* File list pills */}
              <div className="p-2 border-b border-slate-800 bg-slate-950 flex flex-wrap gap-1 max-h-28 overflow-y-auto">
                {filesList.map((f, i) => {
                  const fpath = typeof f === 'string' ? f : f.path;
                  const isPHP = fpath.includes('.php') || fpath.includes('.sql');
                  return (
                    <button
                      key={i}
                      onClick={() => loadFileContent(fpath)}
                      className={`text-[11px] px-2 py-1 rounded font-mono transition flex items-center gap-1 ${
                        selectedFile === fpath
                          ? 'bg-blue-600 text-white font-bold'
                          : isPHP
                          ? 'bg-indigo-950/60 text-indigo-300 hover:bg-indigo-900 border border-indigo-800/40'
                          : 'bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700'
                      }`}
                    >
                      {isPHP ? <Database className="w-3 h-3 text-indigo-400" /> : <FileCode className="w-3 h-3 text-blue-400" />}
                      {fpath}
                    </button>
                  );
                })}
              </div>

              {/* Code viewer box */}
              <div className="flex-1 flex flex-col overflow-hidden bg-slate-950">
                <div className="px-3 py-1.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs">
                  <span className="font-mono text-slate-400 text-[11px]">{selectedFile}</span>
                  <button
                    onClick={handleCopyCode}
                    className="p-1 text-slate-400 hover:text-white rounded transition flex items-center gap-1 text-[11px]"
                  >
                    {copiedCode ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    {copiedCode ? 'Copied' : 'Copy'}
                  </button>
                </div>

                <pre className="flex-1 overflow-auto p-3 text-[11px] font-mono text-slate-300 leading-relaxed select-all">
                  {isLoadingFile ? 'Loading file...' : fileContent}
                </pre>
              </div>
            </div>
          )}
        </div>

        {/* Center Panel: Live Responsive Preview (with simulated device frame) */}
        <div className="flex-1 flex flex-col bg-slate-900 overflow-hidden">
          {/* Preview Navigation & URL Bar */}
          <div className="h-10 bg-slate-950 border-b border-slate-800 px-4 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 flex-1 max-w-xl">
              <button
                onClick={() => {
                  setIsIframeLoading(true);
                  setPreviewKey(Date.now());
                }}
                className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition"
                title="Reload Preview"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>

              <div className="flex-1 flex items-center bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1 text-slate-400 font-mono text-[11px]">
                <Globe className="w-3 h-3 text-emerald-400 mr-2 shrink-0" />
                <span className="truncate">{subdomainUrl}</span>
              </div>
            </div>

            <div className="flex items-center gap-2 text-slate-500 font-mono text-[10px]">
              <span>
                {viewport === 'desktop' ? '100% (Desktop)' : viewport === 'tablet' ? '768px (Tablet)' : '375px (Mobile)'}
              </span>
            </div>
          </div>

          {/* Iframe Viewport Frame */}
          <div className="flex-1 flex items-center justify-center p-2 sm:p-4 bg-slate-950/80 overflow-auto">
            <div
              className={`h-full transition-all duration-300 rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-white flex flex-col ${
                viewport === 'desktop'
                  ? 'w-full'
                  : viewport === 'tablet'
                  ? 'w-[768px] max-w-full'
                  : 'w-[375px] max-w-full'
              }`}
            >
              <iframe
                key={previewKey}
                src={previewUrl}
                title="Website Live Preview"
                onLoad={() => setIsIframeLoading(false)}
                className="w-full h-full border-0 bg-white"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Subdomain Deployment Modal */}
      <SubdomainDeployModal
        project={project}
        isOpen={isSubdomainModalOpen}
        onClose={() => setIsSubdomainModalOpen(false)}
        onSuccess={(assignedSlug) => {
          setProject((prev) => ({ ...prev, subdomain: assignedSlug }));
          loadProjectDetails();
        }}
      />
    </div>
  );
};
