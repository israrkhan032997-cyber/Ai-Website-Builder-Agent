import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, Send, Bot, User, ArrowRight, CheckCircle2,
  Layers, Code2, Palette, Globe, RefreshCw, X, ArrowLeft
} from 'lucide-react';
import { api } from '../services/api';
import { Project } from '../types';

interface ConversationalWizardProps {
  onProjectCreated: (project: Project) => void;
  onCancel: () => void;
}

interface ChatItem {
  id: string;
  sender: 'assistant' | 'user';
  text: string;
  options?: string[];
  isComplete?: boolean;
}

export const ConversationalWizard: React.FC<ConversationalWizardProps> = ({
  onProjectCreated,
  onCancel,
}) => {
  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: "Welcome! Let's build your professional website. Tell me your business name or simply describe your idea, and I'll help you create the right website.",
      options: [
        'Pepsi - Refreshing beverage & soda brand',
        'Arcline Studio - Architecture & Interior Design',
        'HealthFirst - Modern Dental & Wellness Clinic',
        'Lumina - Cloud Analytics SaaS Platform',
      ],
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [currentStep, setCurrentStep] = useState<string>('business_name');
  const [collectedData, setCollectedData] = useState<Record<string, any>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [currentStep, isLoading]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = (textToSend || inputValue).trim();
    if (!text || isLoading) return;

    setError(null);
    setInputValue('');

    // Add user message
    const userMsgId = `user-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text },
    ]);

    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        user_message: text,
        current_step: currentStep,
        collected_data: collectedData,
      });

      // Update state
      setCurrentStep(response.next_step);
      setCollectedData(response.updated_data || collectedData);

      // Add assistant response
      const botMsgId = `assistant-${Date.now()}`;
      setMessages((prev) => [
        ...prev,
        {
          id: botMsgId,
          sender: 'assistant',
          text: response.assistant_message,
          options: response.suggested_options,
          isComplete: response.is_complete,
        },
      ]);
    } catch (err: any) {
      setError(err.message || 'Failed to communicate with conversational assistant.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLaunchProject = async () => {
    setIsSubmitting(true);
    setError(null);
    try {
      // 1. Create project record from conversational specification
      const newProject = await api.createProjectFromChat(collectedData);

      // 2. Trigger multi-agent pipeline immediately in background
      api.generateWebsite(newProject.id).catch((e) => {
        console.error('Initial generation error:', e);
      });

      // 3. Navigate directly to Lovable-style live preview workspace
      onProjectCreated(newProject);
    } catch (err: any) {
      setError(err.message || 'Failed to create project from specifications.');
      setIsSubmitting(false);
    }
  };

  // Helper step progress percentage calculation (9 steps)
  const stepOrder = [
    'business_name',
    'industry',
    'description',
    'target_audience',
    'website_type',
    'page_selection',
    'design_preferences',
    'technology',
    'review',
    'ready_to_generate',
  ];
  const stepIndex = Math.max(0, stepOrder.indexOf(currentStep));
  const progressPercent = Math.min(100, Math.round(((stepIndex + 1) / stepOrder.length) * 100));

  const isReviewStep = currentStep === 'review' || currentStep === 'ready_to_generate' || messages[messages.length - 1]?.isComplete;

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100 overflow-hidden font-sans">
      {/* Top Navigation */}
      <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between shrink-0 z-20">
        <div className="flex items-center space-x-3">
          <button
            onClick={onCancel}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition"
            title="Return to Dashboard"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
                Conversational AI Builder
                <span className="text-[10px] bg-blue-500/20 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-full font-mono uppercase font-semibold">
                  Guided Workflow
                </span>
              </h1>
              <p className="text-xs text-slate-400">Step {stepIndex + 1} of 9 · 5-Stage Agent Orchestration</p>
            </div>
          </div>
        </div>

        {/* Progress Bar in Header */}
        <div className="hidden md:flex items-center space-x-4">
          <div className="w-48 bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
          <span className="text-xs font-mono text-slate-400">{progressPercent}%</span>
        </div>

        <button
          onClick={onCancel}
          className="text-xs text-slate-400 hover:text-white px-3 py-1.5 rounded-lg border border-slate-800 hover:bg-slate-800 transition"
        >
          Exit to Projects
        </button>
      </header>

      {/* Main Split Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Chat Stream */}
        <div className="flex-1 flex flex-col bg-slate-900 border-r border-slate-800/80">
          {/* Scrollable Messages */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-3.5 max-w-2xl ${
                  msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
                }`}
              >
                {/* Avatar */}
                <div
                  className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 text-sm font-bold shadow-md ${
                    msg.sender === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-800 border border-slate-700 text-indigo-400'
                  }`}
                >
                  {msg.sender === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Bubble & Options */}
                <div className="space-y-3">
                  <div
                    className={`p-4 rounded-2xl text-sm leading-relaxed shadow-sm ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-slate-800/90 border border-slate-700/80 text-slate-200 rounded-tl-none whitespace-pre-line'
                    }`}
                  >
                    {msg.text}
                  </div>

                  {/* Suggestion Chips */}
                  {msg.options && msg.options.length > 0 && msg.id === messages[messages.length - 1]?.id && !isReviewStep && (
                    <div className="flex flex-wrap gap-2 pt-1 animate-fadeIn">
                      {msg.options.map((opt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSendMessage(opt)}
                          disabled={isLoading}
                          className="text-xs px-3.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white transition-all shadow-sm hover:scale-[1.02] flex items-center gap-1.5 active:scale-95 text-left"
                        >
                          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0" />
                          {opt}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Final Review Screen Trigger */}
                  {msg.isComplete && (
                    <div className="p-5 rounded-2xl bg-gradient-to-br from-blue-950/60 to-indigo-950/40 border border-blue-500/30 space-y-4 animate-fadeIn">
                      <div className="flex items-center gap-2 text-blue-400 font-bold text-sm">
                        <CheckCircle2 className="w-4 h-4" />
                        Website Architecture & Specification Ready
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        Our multi-agent team (Orchestrator, Asset, Design, Backend, Execution) will now code and compile your website with live preview.
                      </p>
                      <button
                        onClick={handleLaunchProject}
                        disabled={isSubmitting}
                        className="w-full py-3.5 px-5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition active:scale-98 disabled:opacity-50"
                      >
                        {isSubmitting ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin" />
                            Launching Agent Pipeline...
                          </>
                        ) : (
                          <>
                            <Sparkles className="w-4 h-4" />
                            Build Website & Open Live Workspace
                            <ArrowRight className="w-4 h-4" />
                          </>
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex items-center gap-3 text-slate-400 text-xs">
                <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400">
                  <Bot className="w-4 h-4" />
                </div>
                <div className="flex items-center gap-1.5 px-3 py-2 bg-slate-800/60 border border-slate-700/60 rounded-xl">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                  <span className="ml-2 text-xs text-slate-400 font-medium">Formulating question...</span>
                </div>
              </div>
            )}

            {error && (
              <div className="p-3.5 rounded-xl bg-rose-950/60 border border-rose-500/40 text-rose-300 text-xs flex items-center justify-between">
                <span>{error}</span>
                <button onClick={() => setError(null)} className="text-rose-400 hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="p-4 bg-slate-950 border-t border-slate-800">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2 max-w-3xl mx-auto"
            >
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  isReviewStep
                    ? 'Type "confirm" or click the button above to launch...'
                    : 'Type your answer or select an option above...'
                }
                disabled={isLoading || isSubmitting}
                className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading || isSubmitting}
                className="px-5 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 disabled:text-slate-600 text-white rounded-xl font-medium text-sm transition flex items-center justify-center shadow-md shadow-blue-600/20"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>
        </div>

        {/* Right: Live Architecture Specification Sidebar */}
        <div className="hidden lg:flex w-96 flex-col bg-slate-950 border-l border-slate-800 overflow-y-auto p-6 space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-blue-400" />
              Live Requirements Spec
            </h2>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              RFC-1035
            </span>
          </div>

          {/* Business Summary Card */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Business Name</span>
              <p className="text-sm font-bold text-white mt-0.5">
                {collectedData.business_name || <span className="text-slate-600 italic">Awaiting answer...</span>}
              </p>
            </div>

            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Industry Sector</span>
              <p className="text-xs font-medium text-slate-300 mt-0.5">
                {collectedData.industry || <span className="text-slate-600 italic">Not specified yet</span>}
              </p>
            </div>

            {collectedData.description && (
              <div>
                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Description</span>
                <p className="text-xs text-slate-400 line-clamp-3 mt-0.5 leading-relaxed">
                  {collectedData.description}
                </p>
              </div>
            )}
          </div>

          {/* Architecture Card */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Architecture</span>
              <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                {collectedData.website_type === 'multi-page' ? 'Multi-Page Website' : 'Single-Page Landing'}
              </span>
            </div>

            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Pages Structure</span>
              <div className="flex flex-wrap gap-1.5 mt-1.5">
                {(collectedData.selected_pages || ['Home']).map((p: string, idx: number) => (
                  <span
                    key={idx}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 font-medium"
                  >
                    {p}
                  </span>
                ))}
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-400 flex items-center gap-1.5">
                <Code2 className="w-3.5 h-3.5 text-indigo-400" />
                Backend Integration
              </span>
              <span className="font-mono text-slate-200 font-semibold">
                React + PHP Backend
              </span>
            </div>
          </div>

          {/* Design & Palette Card */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Design Style</span>
              <span className="text-xs text-slate-300 font-semibold">{collectedData.style || 'Modern & Clean'}</span>
            </div>

            <div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Color Palette</span>
              <div className="flex items-center gap-3 mt-2">
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-5 h-5 rounded-md shadow-sm border border-white/10"
                    style={{ backgroundColor: collectedData.primary_color || '#2563eb' }}
                  />
                  <span className="text-[10px] font-mono text-slate-400">Primary</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <div
                    className="w-5 h-5 rounded-md shadow-sm border border-white/10"
                    style={{ backgroundColor: collectedData.secondary_color || '#0f172a' }}
                  />
                  <span className="text-[10px] font-mono text-slate-400">Secondary</span>
                </div>
              </div>
            </div>
          </div>

          {/* Subdomain Card */}
          <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
              <Globe className="w-3.5 h-3.5 text-emerald-400" />
              Assigned Subdomain Slug
            </span>
            <p className="text-xs font-mono text-emerald-400">
              {collectedData.subdomain ? `${collectedData.subdomain}.local` : (collectedData.business_name ? `${collectedData.business_name.toLowerCase().replace(/[^a-z0-9]/g, '-')}.local` : 'site-draft.local')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
