import React, { useState, useRef } from 'react';
import { Project } from '../types';
import { Monitor, Tablet, Smartphone, RefreshCw, ExternalLink, Edit3, Rocket, AlertCircle } from 'lucide-react';

interface LivePreviewProps {
  project: Project;
  onOpenEdit: () => void;
  onOpenDeploy: () => void;
}

export const LivePreview: React.FC<LivePreviewProps> = ({
  project,
  onOpenEdit,
  onOpenDeploy,
}) => {
  const [viewport, setViewport] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [iframeKey, setIframeKey] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const previewUrl = `/api/v1/preview/${project.id}/index.html`;

  const handleRefresh = () => {
    setIframeKey((prev) => prev + 1);
  };

  const getViewportWidth = () => {
    switch (viewport) {
      case 'mobile':
        return '375px';
      case 'tablet':
        return '768px';
      default:
        return '100%';
    }
  };

  return (
    <div className="space-y-4">
      {/* Control bar */}
      <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-3">
        {/* Device Viewport Switchers */}
        <div className="flex items-center space-x-1.5 bg-slate-100 p-1 rounded-xl">
          <button
            onClick={() => setViewport('desktop')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              viewport === 'desktop'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Monitor className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Desktop</span>
          </button>

          <button
            onClick={() => setViewport('tablet')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              viewport === 'tablet'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Tablet className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Tablet (768px)</span>
          </button>

          <button
            onClick={() => setViewport('mobile')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
              viewport === 'mobile'
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Mobile (375px)</span>
          </button>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2 w-full sm:w-auto justify-end">
          <button
            onClick={handleRefresh}
            className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Reload preview"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Open website in new browser tab"
          >
            <ExternalLink className="w-4 h-4" />
          </a>

          <button
            onClick={onOpenEdit}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-bold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1" />
            <span>Ask for Changes</span>
          </button>

          <button
            onClick={onOpenDeploy}
            className="inline-flex items-center px-4 py-1.5 rounded-xl text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 shadow-sm transition-colors"
          >
            <Rocket className="w-3.5 h-3.5 mr-1" />
            <span>Deploy Website</span>
          </button>
        </div>
      </div>

      {/* Interactive Notice */}
      <div className="px-4 py-2 bg-blue-50/70 border border-blue-200/60 rounded-xl text-[11px] text-blue-800 flex items-center justify-between">
        <span>
          💡 <strong>Live Functional Website:</strong> Links, mobile navigation, and contact forms submit to the backend database in real time.
        </span>
        {project.active_checkpoint_hash && (
          <span className="font-mono text-[10px] text-blue-600">
            Git HEAD: {project.active_checkpoint_hash.substring(0, 8)}
          </span>
        )}
      </div>

      {/* Frame Container */}
      <div className="bg-slate-200 p-4 sm:p-6 rounded-2xl border border-slate-300 min-h-[700px] flex items-center justify-center overflow-auto shadow-inner">
        <div
          className="bg-white rounded-xl shadow-2xl overflow-hidden border border-slate-300 transition-all duration-300 ease-out"
          style={{ width: getViewportWidth(), height: '780px' }}
        >
          <iframe
            key={iframeKey}
            ref={iframeRef}
            src={previewUrl}
            title={`${project.name} Live Preview`}
            className="w-full h-full border-none"
            sandbox="allow-scripts allow-forms allow-same-origin"
          />
        </div>
      </div>
    </div>
  );
};
