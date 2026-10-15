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
  website_type: 'single-page' | 'multi-page';
  selected_pages?: string[];
  tech_stack: string;
  subdomain?: string;
  custom_domain?: string;
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
  requirements_spec?: any;
  submissions_count: number;
  checkpoints_count: number;
  pending_approvals_count: number;
}

export interface WebsitePage {
  id: number | string;
  project_id: string;
  slug: string;
  title: string;
  description?: string;
  file_path: string;
  is_home: boolean;
  nav_order?: number;
  order_index?: number;
}

export interface ChatMessage {
  id: number | string;
  project_id?: string;
  sender: 'user' | 'assistant' | 'system';
  step?: string;
  content: string;
  message_metadata?: {
    suggested_options?: string[];
    updated_data?: Record<string, any>;
    is_complete?: boolean;
  };
  created_at?: string;
}

export interface ConversationalStepRequest {
  project_id?: string;
  user_message: string;
  current_step?: string;
  collected_data?: Record<string, any>;
}

export interface ConversationalStepResponse {
  assistant_message: string;
  next_step: string;
  suggested_options: string[];
  updated_data: Record<string, any>;
  is_complete: boolean;
  review_summary?: Record<string, any>;
  structured_specification?: Record<string, any>;
}

export interface SubdomainCheckResponse {
  available: boolean;
  slug: string;
  message: string;
  suggested_alternatives: string[];
  preview_url?: string;
}

export interface SubdomainAssignResponse {
  project_id: string;
  subdomain: string;
  full_url: string;
  message: string;
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
