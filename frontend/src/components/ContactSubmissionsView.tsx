import React, { useState } from 'react';
import { ContactSubmission } from '../types';
import { MessageSquare, Mail, Phone, Calendar, CheckCircle2, Inbox } from 'lucide-react';

interface ContactSubmissionsViewProps {
  submissions: ContactSubmission[];
  projectName: string;
  onUpdateStatus: (id: number, status: 'read' | 'archived') => Promise<void>;
}

export const ContactSubmissionsView: React.FC<ContactSubmissionsViewProps> = ({
  submissions,
  projectName,
  onUpdateStatus,
}) => {
  const [selectedSubmission, setSelectedSubmission] = useState<ContactSubmission | null>(null);

  const unreadCount = submissions.filter((s) => s.status === 'unread').length;

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold text-slate-900">Contact Inquiries & Leads</h1>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-700">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real messages received through the contact form on <strong>{projectName}</strong>
          </p>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {submissions.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center mx-auto mb-3">
              <Inbox className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-800 mb-1">No contact inquiries yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              When visitors or you submit inquiries via the website's contact form, they will appear here in real time.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {submissions.map((sub) => (
              <div
                key={sub.id}
                onClick={() => setSelectedSubmission(sub)}
                className={`p-5 hover:bg-slate-50/70 cursor-pointer transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  sub.status === 'unread' ? 'bg-blue-50/20' : ''
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold text-slate-900">{sub.name}</span>
                    {sub.status === 'unread' && (
                      <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                    )}
                    <span className="text-xs text-slate-500">• {sub.email}</span>
                  </div>
                  <p className="text-xs font-semibold text-slate-700">
                    {sub.subject || 'Website Inquiry'}
                  </p>
                  <p className="text-xs text-slate-600 line-clamp-1 max-w-2xl">
                    {sub.message}
                  </p>
                </div>

                <div className="flex items-center space-x-3 text-xs text-slate-400 flex-shrink-0">
                  <span>{new Date(sub.created_at).toLocaleString()}</span>
                  {sub.status === 'unread' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onUpdateStatus(sub.id, 'read');
                      }}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Message Inspection Modal */}
      {selectedSubmission && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <h3 className="text-sm font-bold text-slate-900">Inquiry Details</h3>
              <button
                onClick={() => setSelectedSubmission(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4 text-xs text-slate-600 bg-slate-50 p-4 rounded-xl">
                <div>
                  <span className="block text-[10px] uppercase font-bold text-slate-400">From</span>
                  <span className="font-semibold text-slate-900">{selectedSubmission.name}</span>
                </div>
                <div>
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Email</span>
                  <span className="font-semibold text-slate-900">{selectedSubmission.email}</span>
                </div>
                {selectedSubmission.phone && (
                  <div>
                    <span className="block text-[10px] uppercase font-bold text-slate-400">Phone</span>
                    <span>{selectedSubmission.phone}</span>
                  </div>
                )}
                <div>
                  <span className="block text-[10px] uppercase font-bold text-slate-400">Received</span>
                  <span>{new Date(selectedSubmission.created_at).toLocaleString()}</span>
                </div>
              </div>

              <div>
                <span className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Subject</span>
                <p className="text-xs font-bold text-slate-900">{selectedSubmission.subject || 'Website Inquiry'}</p>
              </div>

              <div>
                <span className="block text-[10px] uppercase font-bold text-slate-400 mb-1">Message</span>
                <p className="text-xs text-slate-800 leading-relaxed bg-white border border-slate-200 p-3.5 rounded-xl whitespace-pre-wrap">
                  {selectedSubmission.message}
                </p>
              </div>

              <div className="pt-2 flex justify-end">
                {selectedSubmission.status === 'unread' && (
                  <button
                    onClick={() => {
                      onUpdateStatus(selectedSubmission.id, 'read');
                      setSelectedSubmission(null);
                    }}
                    className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Mark as Read & Close
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
