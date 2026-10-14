import React, { useState } from 'react';
import { X, ShieldAlert, CheckCircle, XCircle, Play, Terminal } from 'lucide-react';
import { CommandApproval } from '../types';

interface CommandApprovalModalProps {
  approvals: CommandApproval[];
  isOpen: boolean;
  onClose: () => void;
  onDecide: (approvalId: number, decision: 'approve' | 'reject') => Promise<void>;
  onExecute: (approvalId: number) => Promise<void>;
}

export const CommandApprovalModal: React.FC<CommandApprovalModalProps> = ({
  approvals,
  isOpen,
  onClose,
  onDecide,
  onExecute,
}) => {
  const [processingId, setProcessingId] = useState<number | null>(null);

  if (!isOpen) return null;

  const handleDecision = async (id: number, decision: 'approve' | 'reject') => {
    try {
      setProcessingId(id);
      await onDecide(id, decision);
      if (decision === 'approve') {
        await onExecute(id);
      }
    } finally {
      setProcessingId(null);
    }
  };

  const pendingList = approvals.filter((a) => a.status === 'pending');
  const pastList = approvals.filter((a) => a.status !== 'pending');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-2xl overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-amber-50">
          <div>
            <h2 className="text-base font-bold text-amber-950 flex items-center">
              <ShieldAlert className="w-5 h-5 mr-2 text-amber-600" />
              Execution Agent Command Authorization
            </h2>
            <p className="text-xs text-amber-800">Review and authorize terminal commands before execution</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 max-h-[550px] overflow-y-auto space-y-6">
          {/* Pending Approvals */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              Pending Requests ({pendingList.length})
            </h3>
            {pendingList.length === 0 ? (
              <p className="text-xs text-slate-500 italic bg-slate-50 p-4 rounded-xl border border-slate-200">
                No commands pending authorization. The Execution Agent will register commands here when permission is required.
              </p>
            ) : (
              <div className="space-y-4">
                {pendingList.map((appr) => (
                  <div key={appr.id} className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{appr.purpose}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">
                        Risk: {appr.risk_level}
                      </span>
                    </div>

                    <div className="bg-slate-900 text-emerald-400 font-mono text-xs p-3 rounded-lg flex items-center space-x-2">
                      <Terminal className="w-4 h-4 text-slate-500 flex-shrink-0" />
                      <span className="break-all">{appr.command}</span>
                    </div>

                    <p className="text-[11px] text-slate-500">
                      Target Directory: <code className="bg-slate-100 px-1 py-0.5 rounded">{appr.working_directory}</code>
                    </p>

                    <div className="flex justify-end space-x-2 pt-2 border-t border-amber-200/60">
                      <button
                        onClick={() => handleDecision(appr.id, 'reject')}
                        disabled={processingId === appr.id}
                        className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => handleDecision(appr.id, 'approve')}
                        disabled={processingId === appr.id}
                        className="inline-flex items-center px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-sm"
                      >
                        <Play className="w-3 h-3 mr-1 fill-current" />
                        <span>{processingId === appr.id ? 'Executing...' : 'Approve & Execute'}</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Past Executions */}
          {pastList.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Execution History
              </h3>
              <div className="space-y-3">
                {pastList.map((appr) => (
                  <div key={appr.id} className="p-3.5 rounded-xl border border-slate-200 bg-white space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {appr.status === 'executed' ? (
                          <CheckCircle className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-600" />
                        )}
                        <span className="text-xs font-semibold text-slate-900">{appr.purpose}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 capitalize">{appr.status}</span>
                    </div>
                    <code className="block bg-slate-50 text-slate-700 p-2 rounded text-[11px] font-mono">
                      {appr.command}
                    </code>
                    {appr.execution_output && (
                      <pre className="bg-slate-900 text-slate-300 p-2.5 rounded text-[10px] font-mono max-h-24 overflow-y-auto whitespace-pre-wrap">
                        {appr.execution_output}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
