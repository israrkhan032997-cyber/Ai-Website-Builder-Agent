import React, { useState, useEffect } from 'react';
import { Project, AgentLog, Checkpoint, ContactSubmission, CommandApproval } from './types';
import { api } from './services/api';
import { Navbar } from './components/Navbar';
import { Dashboard } from './components/Dashboard';
import { AgentWorkflowView } from './components/AgentWorkflowView';
import { LivePreview } from './components/LivePreview';
import { ContactSubmissionsView } from './components/ContactSubmissionsView';
import { CreateProjectModal } from './components/CreateProjectModal';
import { EditWebsiteModal } from './components/EditWebsiteModal';
import { CheckpointHistory } from './components/CheckpointHistory';
import { CommandApprovalModal } from './components/CommandApprovalModal';
import { DeploymentModal } from './components/DeploymentModal';
import { SettingsModal } from './components/SettingsModal';
import { ConversationalWizard } from './components/ConversationalWizard';
import { LovableWorkspace } from './components/LovableWorkspace';

export const App: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [activeTab, setActiveTab] = useState<'dashboard' | 'projects' | 'workflow' | 'preview' | 'leads'>('dashboard');

  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [submissions, setSubmissions] = useState<ContactSubmission[]>([]);
  const [approvals, setApprovals] = useState<CommandApproval[]>([]);

  const [isGenerating, setIsGenerating] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Modern Lovable Workspace and Conversational Wizard modes
  const [isConversationalWizardOpen, setIsConversationalWizardOpen] = useState(false);
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false);

  // Classic Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isCheckpointsOpen, setIsCheckpointsOpen] = useState(false);
  const [isApprovalsOpen, setIsApprovalsOpen] = useState(false);
  const [isDeployOpen, setIsDeployOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      loadProjectData(selectedProject.id);
    }
  }, [selectedProject?.id]);

  // Polling during active generation
  useEffect(() => {
    if (!selectedProject || !isGenerating) return;

    const interval = setInterval(async () => {
      try {
        const updated = await api.getProject(selectedProject.id);
        setSelectedProject(updated);
        const newLogs = await api.getAgentLogs(selectedProject.id);
        setLogs(newLogs);
        if (updated.status === 'ready' || updated.status === 'failed') {
          setIsGenerating(false);
          loadProjects();
        }
      } catch (err) {
        // Silent fail during poll
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [selectedProject?.id, isGenerating]);

  const loadProjects = async () => {
    try {
      setIsLoading(true);
      const res = await api.getProjects();
      setProjects(res);
      if (res.length > 0 && !selectedProject) {
        setSelectedProject(res[0]);
      }
    } catch (e) {
      console.error('Failed to load projects:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadProjectData = async (projectId: string) => {
    try {
      const [pLogs, pCheckpoints, pSubs, pApprovals] = await Promise.all([
        api.getAgentLogs(projectId),
        api.getCheckpoints(projectId),
        api.getContactSubmissions(projectId),
        api.getCommandApprovals(projectId),
      ]);
      setLogs(pLogs);
      setCheckpoints(pCheckpoints);
      setSubmissions(pSubs);
      setApprovals(pApprovals);
    } catch (e) {
      console.error('Failed to load project details:', e);
    }
  };

  const handleCreateProject = async (data: Partial<Project>) => {
    const newProject = await api.createProject(data);
    await loadProjects();
    setSelectedProject(newProject);
    setIsWorkspaceOpen(true);
    // Trigger generation pipeline automatically
    handleTriggerGenerate(newProject.id);
  };

  const handleTriggerGenerate = async (projectId?: string) => {
    const id = projectId || selectedProject?.id;
    if (!id) return;

    try {
      setIsGenerating(true);
      await api.generateWebsite(id);
      const updated = await api.getProject(id);
      setSelectedProject(updated);
      await loadProjectData(id);
      await loadProjects();
    } catch (err: any) {
      alert(`Generation pipeline error: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleEditProject = async (instruction: string) => {
    if (!selectedProject) return;
    const urlMatch = instruction.match(/https?:\/\/[^\s<>"')\]}]+/);
    const extractedUrl = urlMatch ? urlMatch[0].replace(/[,.'")\]}]+$/, '') : undefined;
    await api.editWebsite(selectedProject.id, instruction, undefined, extractedUrl);
    const updated = await api.getProject(selectedProject.id);
    setSelectedProject(updated);
    await loadProjectData(selectedProject.id);
    await loadProjects();
  };

  const handleRollbackCheckpoint = async (commitHash: string) => {
    if (!selectedProject) return;
    await api.rollbackCheckpoint(selectedProject.id, commitHash);
    const updated = await api.getProject(selectedProject.id);
    setSelectedProject(updated);
    await loadProjectData(selectedProject.id);
    alert(`Workspace rolled back to ${commitHash.substring(0, 8)}`);
  };

  const handleDecideApproval = async (approvalId: number, decision: 'approve' | 'reject') => {
    await api.decideCommandApproval(approvalId, decision);
    if (selectedProject) {
      await loadProjectData(selectedProject.id);
    }
  };

  const handleExecuteCommand = async (approvalId: number) => {
    await api.executeApprovedCommand(approvalId);
    if (selectedProject) {
      await loadProjectData(selectedProject.id);
    }
  };

  const handleDeploy = async (provider: 'local' | 'netlify' | 'vercel', domain?: string) => {
    if (!selectedProject) return;
    const res = await api.deployWebsite(selectedProject.id, provider, domain);
    const updated = await api.getProject(selectedProject.id);
    setSelectedProject(updated);
    await loadProjects();
    return res;
  };

  const handleDeleteProject = async (id: string) => {
    await api.deleteProject(id);
    if (selectedProject?.id === id) {
      setSelectedProject(null);
      setIsWorkspaceOpen(false);
      setActiveTab('dashboard');
    }
    await loadProjects();
  };

  const handleUpdateContactStatus = async (id: number, status: 'read' | 'archived') => {
    if (!selectedProject) return;
    await api.updateContactStatus(selectedProject.id, id, status);
    const updatedSubs = await api.getContactSubmissions(selectedProject.id);
    setSubmissions(updatedSubs);
  };

  const hasPendingApprovals = approvals.some((a) => a.status === 'pending');

  // 1. If Conversational AI Wizard is active
  if (isConversationalWizardOpen) {
    return (
      <ConversationalWizard
        onProjectCreated={(newProj) => {
          setSelectedProject(newProj);
          setIsConversationalWizardOpen(false);
          setIsWorkspaceOpen(true);
          loadProjects();
        }}
        onCancel={() => setIsConversationalWizardOpen(false)}
      />
    );
  }

  // 2. If Lovable Workspace is active for a selected project
  if (isWorkspaceOpen && selectedProject) {
    return (
      <LovableWorkspace
        project={selectedProject}
        onBackToDashboard={() => setIsWorkspaceOpen(false)}
        onProjectUpdated={(updated) => {
          setSelectedProject(updated);
          loadProjects();
        }}
      />
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenCreate={() => setIsCreateOpen(true)}
        onOpenConversationalWizard={() => setIsConversationalWizardOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        selectedProjectName={selectedProject?.name}
        hasPendingApprovals={hasPendingApprovals}
      />

      <main className="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        {activeTab === 'dashboard' && (
          <Dashboard
            projects={projects}
            onSelectProject={(proj, tab) => {
              setSelectedProject(proj);
              setActiveTab(tab || 'preview');
            }}
            onOpenCreate={() => setIsCreateOpen(true)}
            onOpenConversationalWizard={() => setIsConversationalWizardOpen(true)}
            onOpenWorkspace={(proj) => {
              setSelectedProject(proj);
              setIsWorkspaceOpen(true);
            }}
            onOpenEdit={(proj) => {
              setSelectedProject(proj);
              setIsEditOpen(true);
            }}
            onOpenDeploy={(proj) => {
              setSelectedProject(proj);
              setIsDeployOpen(true);
            }}
            onDeleteProject={handleDeleteProject}
          />
        )}

        {selectedProject && activeTab === 'workflow' && (
          <AgentWorkflowView
            project={selectedProject}
            logs={logs}
            approvals={approvals}
            isGenerating={isGenerating}
            onTriggerGenerate={() => handleTriggerGenerate()}
            onOpenPreview={() => setActiveTab('preview')}
            onOpenApprovals={() => setIsApprovalsOpen(true)}
            onOpenCheckpoints={() => setIsCheckpointsOpen(true)}
          />
        )}

        {selectedProject && activeTab === 'preview' && (
          <LivePreview
            project={selectedProject}
            onOpenEdit={() => setIsEditOpen(true)}
            onOpenDeploy={() => setIsDeployOpen(true)}
          />
        )}

        {selectedProject && activeTab === 'leads' && (
          <ContactSubmissionsView
            submissions={submissions}
            projectName={selectedProject.name}
            onUpdateStatus={handleUpdateContactStatus}
          />
        )}
      </main>

      {/* Global Modals */}
      <CreateProjectModal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        onSubmit={handleCreateProject}
      />

      {selectedProject && (
        <>
          <EditWebsiteModal
            project={selectedProject}
            isOpen={isEditOpen}
            onClose={() => setIsEditOpen(false)}
            onSubmit={handleEditProject}
          />

          <CheckpointHistory
            project={selectedProject}
            checkpoints={checkpoints}
            isOpen={isCheckpointsOpen}
            onClose={() => setIsCheckpointsOpen(false)}
            onRollback={handleRollbackCheckpoint}
          />

          <CommandApprovalModal
            approvals={approvals}
            isOpen={isApprovalsOpen}
            onClose={() => setIsApprovalsOpen(false)}
            onDecide={handleDecideApproval}
            onExecute={handleExecuteCommand}
          />

          <DeploymentModal
            project={selectedProject}
            isOpen={isDeployOpen}
            onClose={() => setIsDeployOpen(false)}
            onDeploy={handleDeploy}
          />
        </>
      )}

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        onSaved={loadProjects}
      />
    </div>
  );
};
