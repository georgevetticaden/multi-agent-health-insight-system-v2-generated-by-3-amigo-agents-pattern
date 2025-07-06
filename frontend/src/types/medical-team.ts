export interface TeamMember {
  id: string;
  name: string;
  specialty: string;
  status: 'waiting' | 'thinking' | 'analyzing' | 'complete' | 'error';
  progress?: number;
  confidence?: number;
  currentTask?: string;
  toolCalls?: number;
  message?: string;
  gradient?: string;
  icon?: string;
}

export interface TeamUpdate {
  teamStatus: 'assembling' | 'analyzing' | 'synthesizing' | 'complete';
  members: TeamMember[];
  overallProgress: number;
  cmoMessage?: string;
}

export type AppState = 
  | 'welcome'
  | 'idle'
  | 'listening'
  | 'cmo-analyzing'
  | 'team-assembling'
  | 'team-working'
  | 'synthesizing'
  | 'visualizing'
  | 'complete';