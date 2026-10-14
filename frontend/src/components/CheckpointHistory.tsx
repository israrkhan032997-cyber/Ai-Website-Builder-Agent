import React, { useState } from 'react';
import { X, History, GitCommit, RotateCcw, CheckCircle2 } from 'lucide-react';
import { Checkpoint, Project } from '../types';

interface CheckpointHistoryProps {
  project: Project;
  checkpoints: Checkpoint[];
  isOpen: boolean;
  onClose: () => void;
  onRollback: (commitHash: string) => Promise<void>;
}

export const CheckpointHistory: React.FC<CheckpointHistoryProps> = ({
  project,
  checkpoints,
  isOpen,
  onClose,
  onRollback,
}) => {
  const [rollingBackHash, setRollingBackHash] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRollback = async (hash: string) => {
    if (confirm(`Are you sure you want to revert workspace files to checkpoint ${hash.substring(0, 8)}?`)) {
      try {
        setRollingBackHash(hash);
        await onRollback(hash);
      } finally {
        setRollingBackHash(null);
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm overflow-y-auto">
      <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-xl overflow-hidden my-8 animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center">
              <History className="w-4 h-4 mr-2 text-blue-600" />
              Git Version Checkpoints
            </h2>
            <p className="text-xs text-slate-500">Atomic checkpoints recorded after approved generation & edits</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="p-6 max-h-[500px] overflow-y-auto space-y-4">
          {checkpoints.length === 0 ? (
            <p className="text-center text-xs text-slate-500 py-8">
              No checkpoints committed yet. Checkpoints are automatically generated when websites are created or refined.
            </p>
          ) : (
            checkpoints.map((chk, index) => {
              const isCurrentHead = project.active_checkpoint_hash === chk.commit_hash || index === 0;
              return (
                <div
                  key={chk.commit_hash}
                  className={`p-4 rounded-xl border transition-all ${
                    isCurrentHead
                      ? 'border-blue-300 bg-blue-50/40'
                      : 'border-slate-200 bg-white hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <GitCommit className="w-4 h-4 text-blue-600" />
                      <span className="font-mono text-xs font-bold text-slate-900">
                        {chk.commit_hash.substring(0, 8)}
                      </span>
                      {isCurrentHead && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-100 text-blue-700">
                          Active HEAD
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {new Date(chk.created_at).toLocaleString()}
                    </span>
                  </div>

                  <p className="text-xs font-semibold text-slate-800 mb-1">{chk.message}</p>
                  <p className="text-[11px] text-slate-500 mb-3">Committed by {chk.author}</p>

                  {!isCurrentHead && (
                    <button
                      onClick={() => handleRollback(chk.commit_hash)}
                      disabled={rollingBackHash === chk.commit_hash}
                      className="inline-flex items-center px-3 py-1 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
                    >
                      <RotateCcw className="w-3 h-3 mr-1" />
                      <span>{rollingBackHash === chk.commit_hash ? 'Reverting...' : 'Rollback to this version'}</span>
                    </button>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
