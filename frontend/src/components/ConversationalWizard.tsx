import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles, Send, Bot, User, ArrowRight, CheckCircle2,
  RefreshCw, X, ArrowLeft
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

  const [customPageInput, setCustomPageInput] = useState('');

  const handleTogglePage = (pageName: string) => {
    if (pageName.toLowerCase() === 'home') return;
    const current: string[] = (collectedData.selected_pages || ['Home', 'About Us', 'Services', 'Portfolio', 'Contact Us']).map(String);
    const exists = current.some(p => p.toLowerCase() === pageName.toLowerCase());
    let next: string[];
    if (exists) {
      next = current.filter(p => p.toLowerCase() !== pageName.toLowerCase());
    } else {
      next = [...current, pageName];
    }
    setCollectedData(prev => ({ ...prev, selected_pages: next }));
  };

  const handleAddCustomPage = () => {
    const trimmed = customPageInput.trim();
    if (!trimmed) return;
    const current: string[] = (collectedData.selected_pages || ['Home', 'About Us', 'Services', 'Portfolio', 'Contact Us']).map(String);
    if (!current.some(p => p.toLowerCase() === trimmed.toLowerCase())) {
      setCollectedData(prev => ({ ...prev, selected_pages: [...current, trimmed] }));
    }
    setCustomPageInput('');
  };

  const handleConfirmPages = () => {
    const pages = (collectedData.selected_pages || ['Home', 'About Us', 'Services', 'Portfolio', 'Contact Us']).map(String);
    handleSendMessage(`Selected pages: ${pages.join(', ')}`);
  };

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

      // Update state while strictly preserving business_name if already entered
      setCurrentStep(response.next_step);
      const updated = { ...(response.updated_data || collectedData) };
      if (collectedData.business_name && !updated.business_name) {
        updated.business_name = collectedData.business_name;
      }
      setCollectedData(updated);

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
      const payloadData = { ...collectedData };
      payloadData.tech_stack = 'react';
      if (payloadData.selected_pages && Array.isArray(payloadData.selected_pages)) {
        const cleanPages: string[] = [];
        const seen = new Set<string>();
        for (const p of payloadData.selected_pages) {
          const raw = String(p).trim();
          let clean = raw.toLowerCase().replace(/^(?:(?:please\s+)?(?:use|confirm|selected|choose)?[- ]*(?:selected[- ]*)?pages?(?:[- ]*structure)?)\s*[:=-]+\s*/i, '');
          clean = clean.replace(/^(?:use|selected|confirm)[-_]selected[-_]pages?[:\-_ ]*/i, '');
          clean = clean.replace(/^(add|create|new|include)[- ]+/i, '').replace(/[- ]page$/i, '');
          clean = clean.replace(/[^a-z0-9\- ,;&]+/g, ' ');
          const parts = clean.split(/[,;&]|\band\b/i).map(s => s.trim()).filter(Boolean);
          for (const part of parts) {
            const words = part.split(/[\s\-]+/).filter(w => !['use', 'selected', 'pages', 'page', 'structure', 'confirm', 'choose'].includes(w));
            if (!words.length) continue;
            const slug = words.join('-');
            if (slug && !seen.has(slug)) {
              seen.add(slug);
              cleanPages.push(slug);
            }
          }
        }
        if (!cleanPages.includes('home')) {
          cleanPages.unshift('home');
        }
        payloadData.selected_pages = cleanPages;
      }

      // 1. Create project record from conversational specification
      const newProject = await api.createProjectFromChat(payloadData);

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

      {/* Main Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Stream */}
        <div className="flex-1 flex flex-col bg-slate-900">
          {/* Scrollable Messages */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6 max-w-4xl w-full mx-auto">
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

                  {/* Interactive Page Manager for page_selection step */}
                  {currentStep === 'page_selection' && msg.id === messages[messages.length - 1]?.id && (
                    <div className="p-4 rounded-2xl bg-slate-800/90 border border-slate-700 space-y-4 animate-fadeIn">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                          Select Pages to Include:
                        </span>
                        <span className="text-[11px] font-mono text-blue-400 font-semibold">
                          {(collectedData.selected_pages || ['Home', 'About Us', 'Services', 'Portfolio', 'Contact Us']).length} Selected
                        </span>
                      </div>

                      {/* Standard Page Pills */}
                      <div className="flex flex-wrap gap-2">
                        {['Home', 'About Us', 'Services', 'Portfolio', 'Case Study', 'Pricing', 'Testimonials', 'Blog', 'FAQ', 'Contact Us'].map((pg) => {
                          const currentPages: string[] = (collectedData.selected_pages || ['Home', 'About Us', 'Services', 'Portfolio', 'Contact Us']).map(String);
                          const isSelected = currentPages.some(p => p.toLowerCase() === pg.toLowerCase());
                          const isHome = pg.toLowerCase() === 'home';
                          return (
                            <button
                              key={pg}
                              type="button"
                              onClick={() => handleTogglePage(pg)}
                              disabled={isHome || isLoading}
                              className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition flex items-center gap-1.5 ${
                                isSelected
                                  ? 'bg-blue-600/30 border-blue-500 text-blue-200 shadow-sm'
                                  : 'bg-slate-900/60 border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-200'
                              } ${isHome ? 'opacity-80 cursor-default' : 'cursor-pointer active:scale-95'}`}
                            >
                              <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? 'bg-blue-400' : 'bg-slate-600'}`} />
                              {pg}
                              {isHome && <span className="text-[10px] text-blue-300 font-mono">(required)</span>}
                            </button>
                          );
                        })}
                      </div>

                      {/* Add Custom Page Input */}
                      <div className="flex gap-2 pt-1 border-t border-slate-700/60">
                        <input
                          type="text"
                          value={customPageInput}
                          onChange={(e) => setCustomPageInput(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleAddCustomPage();
                            }
                          }}
                          placeholder="e.g. Our Team, Careers, Partners..."
                          className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                        <button
                          type="button"
                          onClick={handleAddCustomPage}
                          disabled={!customPageInput.trim()}
                          className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white rounded-lg text-xs font-semibold transition"
                        >
                          + Add Page
                        </button>
                      </div>

                      <button
                        type="button"
                        onClick={handleConfirmPages}
                        disabled={isLoading}
                        className="w-full py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-blue-600/20"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Confirm Selected Pages & Proceed
                      </button>
                    </div>
                  )}

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
                  <span className="ml-2 text-xs text-slate-400 font-medium">Gemini AI is thinking...</span>
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
      </div>
    </div>
  );
};
