export interface Project {
  id: string;
  name: string;
  industry: string;
  description: string;
  target_audience?: string;
  style?: string;
  primary_color?: string;
  secondary_color?: string;
  accent_color?: string;
  logo_url?: string;
  status: 'draft' | 'planning' | 'generating_assets' | 'generating_design' | 'generating_backend' | 'validating' | 'ready' | 'failed';
  current_agent?: string;
  current_step?: string;
  progress_percentage: string;
  active_checkpoint_hash?: string;
  deployment_status: 'unassigned' | 'preparing' | 'deployed' | 'failed';
  deployment_provider?: string;
  deployment_url?: string;
  live_preview_url?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  website_plan?: any;
  asset_manifest?: any;
  submissions_count: number;
  checkpoints_count: number;
  pending_approvals_count: number;
}

export interface AgentLog {
  id: number;
  project_id: string;
  agent_name: string;
  step_name: string;
  status: 'started' | 'in_progress' | 'success' | 'failed' | 'awaiting_approval';
  message: string;
  input_payload?: any;
  output_payload?: any;
  error_details?: string;
  created_at: string;
}

export interface Checkpoint {
  id: number;
  project_id: string;
  commit_hash: string;
  branch: string;
  message: string;
  author: string;
  changed_files?: string[];
  created_at: string;
}

export interface ContactSubmission {
  id: number;
  project_id: string;
  name: string;
  email: string;
  phone?: string;
  subject?: string;
  message: string;
  status: 'unread' | 'read' | 'archived';
  created_at: string;
}

export interface CommandApproval {
  id: number;
  project_id: string;
  command: string;
  working_directory: string;
  purpose: string;
  risk_level: 'low' | 'medium' | 'high';
  status: 'pending' | 'approved' | 'rejected' | 'executed' | 'failed';
  execution_output?: string;
  created_at: string;
  decided_at?: string;
}

export interface ProviderStatus {
  provider_name: string;
  configured: boolean;
  valid: boolean;
  model?: string;
  message: string;
}

export interface SettingsData {
  settings: {
    gemini_api_key_masked: string;
    gemini_model: string;
    unsplash_access_key_masked: string;
    vercel_token_masked: string;
    netlify_auth_token_masked: string;
    require_command_approval: boolean;
    allowlisted_commands: string;
  };
  providers: ProviderStatus[];
}
