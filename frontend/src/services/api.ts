import { Project, ProjectDetail, AgentLog, Checkpoint, ContactSubmission, CommandApproval, SettingsData } from '../types';

const API_BASE = '/api/v1';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    try {
      const errorData = await res.json();
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail;
      } else if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail
          .map((item: any) => item.msg || (item.loc ? `${item.loc.join('.')}: ${item.msg}` : JSON.stringify(item)))
          .join(', ');
      } else if (errorData.message && typeof errorData.message === 'string') {
        errorMessage = errorData.message;
      } else if (errorData.detail) {
        errorMessage = typeof errorData.detail === 'object' ? JSON.stringify(errorData.detail) : String(errorData.detail);
      }
    } catch {
      errorMessage = res.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

export const api = {
  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    return handleResponse<Project[]>(res);
  },

  async getProject(id: string): Promise<ProjectDetail> {
    const res = await fetch(`${API_BASE}/projects/${id}`);
    return handleResponse<ProjectDetail>(res);
  },

  async createProject(data: Partial<Project>): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Project>(res);
  },

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<Project>(res);
  },

  async deleteProject(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/projects/${id}`, {
      method: 'DELETE',
    });
    return handleResponse<void>(res);
  },

  async getProjectFiles(id: string): Promise<{ project_id: string; files: any[] }> {
    const res = await fetch(`${API_BASE}/projects/${id}/files`);
    return handleResponse<{ project_id: string; files: any[] }>(res);
  },

  // Agent Pipeline
  async generateWebsite(id: string): Promise<{ status: string; project_id: string; preview_url: string; commit_hash?: string; validation_score: number }> {
    const res = await fetch(`${API_BASE}/projects/${id}/generate`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  async editWebsite(id: string, instruction: string, section_id?: string): Promise<{ status: string; message: string; commit_hash?: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction, section_id }),
    });
    return handleResponse(res);
  },

  async getAgentLogs(id: string): Promise<AgentLog[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/logs`);
    return handleResponse<AgentLog[]>(res);
  },

  async getCheckpoints(id: string): Promise<Checkpoint[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/checkpoints`);
    return handleResponse<Checkpoint[]>(res);
  },

  async rollbackCheckpoint(id: string, commit_hash: string): Promise<{ status: string; message: string; commit_hash: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/rollback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ commit_hash }),
    });
    return handleResponse(res);
  },

  // Contact Submissions
  async getContactSubmissions(id: string): Promise<ContactSubmission[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/contact`);
    return handleResponse<ContactSubmission[]>(res);
  },

  async updateContactStatus(id: string, submissionId: number, status: 'read' | 'archived'): Promise<ContactSubmission> {
    const res = await fetch(`${API_BASE}/projects/${id}/contact/${submissionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
    });
    return handleResponse<ContactSubmission>(res);
  },

  // Command Approvals
  async getCommandApprovals(id: string): Promise<CommandApproval[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/approvals`);
    return handleResponse<CommandApproval[]>(res);
  },

  async decideCommandApproval(approvalId: number, decision: 'approve' | 'reject', reason?: string): Promise<CommandApproval> {
    const res = await fetch(`${API_BASE}/approvals/${approvalId}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, reason }),
    });
    return handleResponse<CommandApproval>(res);
  },

  async executeApprovedCommand(approvalId: number): Promise<{ status: string; output: string; commit_hash?: string }> {
    const res = await fetch(`${API_BASE}/approvals/${approvalId}/execute`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  // Deployment
  async getDeploymentStatus(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${id}/deployment-status`);
    return handleResponse(res);
  },

  async deployWebsite(id: string, provider: 'local' | 'netlify' | 'vercel' = 'local', customDomain?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/projects/${id}/deploy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, custom_domain: customDomain, confirm: true }),
    });
    return handleResponse(res);
  },

  // Settings
  async getSettings(): Promise<SettingsData> {
    const res = await fetch(`${API_BASE}/settings`);
    return handleResponse<SettingsData>(res);
  },

  async updateSettings(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async testGemini(): Promise<{ valid: boolean; message: string; model?: string }> {
    const res = await fetch(`${API_BASE}/settings/test-gemini`, {
      method: 'POST',
    });
    return handleResponse(res);
  },

  // Multi-page Support & Code Viewing
  async getProjectPages(id: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/projects/${id}/pages`);
    return handleResponse<any[]>(res);
  },

  async getFileContent(id: string, path: string): Promise<{ path: string; content: string }> {
    const res = await fetch(`${API_BASE}/projects/${id}/files/content?path=${encodeURIComponent(path)}`);
    return handleResponse<{ path: string; content: string }>(res);
  },

  // Conversational Onboarding Chatbot
  async sendChatMessage(payload: { project_id?: string; user_message: string; current_step?: string; collected_data?: Record<string, any> }): Promise<any> {
    const res = await fetch(`${API_BASE}/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse<any>(res);
  },

  async getChatHistory(id: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/chat/${id}/history`);
    return handleResponse<any[]>(res);
  },

  async createProjectFromChat(collectedData: Record<string, any>): Promise<Project> {
    const res = await fetch(`${API_BASE}/chat/create-project`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ collected_data: collectedData }),
    });
    return handleResponse<Project>(res);
  },

  // Subdomains
  async checkSubdomain(slug: string, projectId?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/subdomains/check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug, project_id: projectId }),
    });
    return handleResponse<any>(res);
  },

  async assignSubdomain(projectId: string, subdomain: string): Promise<any> {
    const res = await fetch(`${API_BASE}/subdomains/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_id: projectId, subdomain }),
    });
    return handleResponse<any>(res);
  }
};

