import { TeamUpdate, TeamMember } from '../types/medical-team';

export class SSEEventParser {
  private teamState: Map<string, TeamMember> = new Map();
  private currentPhase: 'idle' | 'cmo-analyzing' | 'team-assembling' | 'team-working' | 'synthesizing' | 'complete' = 'idle';

  constructor() {
    // Initialize with CMO
    this.teamState.set('cmo', {
      id: 'cmo',
      name: 'Dr. Vitality',
      specialty: 'Chief Medical Officer',
      status: 'waiting',
      gradient: 'from-blue-500 to-blue-600',
      icon: 'Brain'
    });
  }

  parseSSEEvent(event: any): { appState?: string; teamUpdate?: TeamUpdate; streamingContent?: string } {
    const { type, content, data } = event;
    
    console.log('[SSEParser] Parsing event:', { type, content: content?.substring(0, 100) });

    switch (type) {
      case 'thinking':
        return this.parseThinkingEvent(content);
      
      case 'tool_call':
      case 'tool_executing':
        return this.parseToolEvent(data);
      
      case 'tool_result':
        return this.parseToolResultEvent(data);
      
      case 'text':
        return this.parseTextEvent(content);
      
      default:
        return {};
    }
  }

  private parseThinkingEvent(content: string): { appState?: string; teamUpdate?: TeamUpdate; streamingContent?: string } {
    // Parse specialist status messages in thinking events
    // Handle both with and without emoji/markdown, including compound names
    const specialistPattern = /(?:❤️|🔬|📊|💊|🛡️|🔍|🧬|⚕️|🧪|🥗)?\s*\*?\*?([^*]+?)\*?\*?\s+is analyzing your health data\.\.\./i;
    const completionPattern = /(?:✅)?\s*\*?\*?([^*]+?)\*?\*?\s+completed analysis \((\d+) queries? executed, (\d+)% confidence\)/i;
    
    console.log('[SSEParser] Parsing thinking event content:', content);
    
    // Check for specialist starting analysis
    const startMatch = content.match(specialistPattern);
    console.log('[SSEParser] Specialist pattern match:', startMatch);
    
    if (startMatch) {
      const fullSpecialty = startMatch[1].trim();
      let specialty = fullSpecialty.toLowerCase();
      let specId = '';
      
      // Handle compound specialties
      if (specialty === 'laboratory medicine') {
        specId = 'spec_laboratory';
        specialty = 'laboratory';
      } else if (specialty === 'preventive medicine') {
        specId = 'spec_preventive';
        specialty = 'preventive';
      } else if (specialty === 'data analysis') {
        specId = 'spec_data';
        specialty = 'data';
      } else if (specialty === 'nutrition') {
        specId = 'spec_nutrition';
        specialty = 'nutrition';
      } else if (specialty === 'general practice') {
        specId = 'spec_general';
        specialty = 'general';
      } else {
        specId = `spec_${specialty}`;
      }
      
      console.log('Specialist starting analysis (from thinking):', fullSpecialty, '-> id:', specId);
      
      // Add specialist if not exists
      if (!this.teamState.has(specId)) {
        this.addSpecialist(specId, specialty, fullSpecialty);
      }
      
      this.updateSpecialist(specId, {
        status: 'analyzing',
        progress: 10,
        currentTask: 'Starting analysis...'
      });
      
      return { 
        appState: 'team-working',
        teamUpdate: this.getTeamUpdate() 
      };
    }
    
    // Check for specialist completion
    const completeMatch = content.match(completionPattern);
    console.log('[SSEParser] Completion pattern match:', completeMatch);
    
    if (completeMatch) {
      const fullSpecialty = completeMatch[1].trim();
      let specialty = fullSpecialty.toLowerCase();
      const queries = parseInt(completeMatch[2]);
      const confidence = parseInt(completeMatch[3]);
      let specId = '';
      
      // Handle compound specialties
      if (specialty === 'laboratory medicine') {
        specId = 'spec_laboratory';
        specialty = 'laboratory';
      } else if (specialty === 'preventive medicine') {
        specId = 'spec_preventive';
        specialty = 'preventive';
      } else if (specialty === 'data analysis') {
        specId = 'spec_data';
        specialty = 'data';
      } else if (specialty === 'nutrition') {
        specId = 'spec_nutrition';
        specialty = 'nutrition';
      } else if (specialty === 'general practice') {
        specId = 'spec_general';
        specialty = 'general';
      } else {
        specId = `spec_${specialty}`;
      }
      
      console.log('Specialist completed (from thinking):', fullSpecialty, '-> id:', specId, 'Confidence:', confidence);
      
      // Ensure specialist exists
      if (!this.teamState.has(specId)) {
        this.addSpecialist(specId, specialty, fullSpecialty);
      }
      
      this.updateSpecialist(specId, {
        status: 'complete',
        progress: 100,
        confidence,
        toolCalls: queries,
        message: `Analysis complete with ${confidence}% confidence`
      });
      
      return { teamUpdate: this.getTeamUpdate() };
    }
    
    // CMO Analysis Phase - detect various CMO states
    if (content.includes('Chief Medical Officer is reviewing your query') || 
        content.includes('CMO is accessing your health records') ||
        content.includes('CMO starting analysis') || 
        content.includes('analyzing your query')) {
      this.currentPhase = 'cmo-analyzing';
      
      let message = 'Analyzing query complexity...';
      let progress = 25;
      
      if (content.includes('reviewing your query')) {
        message = 'Reviewing your query...';
        progress = 20;
      } else if (content.includes('accessing your health records')) {
        message = 'Accessing health records...';
        progress = 30;
      }
      
      this.updateSpecialist('cmo', { 
        status: 'thinking', 
        message,
        progress,
        currentTask: message
      });
      return { 
        appState: 'cmo-analyzing',
        teamUpdate: this.getTeamUpdate()
      };
    }
    
    // Creating Medical Team Strategy
    if (content.includes('Creating Medical Team Strategy')) {
      this.updateSpecialist('cmo', { 
        status: 'thinking', 
        message: 'Creating team strategy...',
        progress: 75,
        currentTask: 'Assigning specialists based on complexity'
      });
      return { 
        appState: 'cmo-analyzing',
        teamUpdate: this.getTeamUpdate()
      };
    }
    
    // CMO Assessment Complete
    if (content.includes('CMO assessment complete')) {
      this.updateSpecialist('cmo', { 
        status: 'thinking', 
        message: 'Assessment complete - preparing team strategy...',
        progress: 50
      });
      return { 
        appState: 'cmo-analyzing',
        teamUpdate: this.getTeamUpdate()
      };
    }

    // Team Assembly Phase
    if (content.includes('Medical Team Assembled') || content.includes('Your consultation will include')) {
      this.currentPhase = 'team-assembling';
      
      // Mark CMO as complete when team is assembled
      this.updateSpecialist('cmo', {
        status: 'complete',
        progress: 100,
        confidence: 100,
        message: 'Team strategy complete'
      });
      
      // Extract specialists from the numbered list with emojis
      // Updated pattern to capture full specialty names including compound names
      const specialistListPattern = /\d+\.\s*(?:❤️|🔬|📊|💊|🛡️|🔍|🧪)?\s*\*\*([^*]+)\*\*/g;
      let match;
      
      while ((match = specialistListPattern.exec(content)) !== null) {
        const fullSpecialty = match[1].trim();
        let specialty = fullSpecialty.toLowerCase();
        let specId = '';
        
        // Handle compound specialties
        if (specialty === 'laboratory medicine') {
          specId = 'spec_laboratory';
          specialty = 'laboratory';
        } else if (specialty === 'preventive medicine') {
          specId = 'spec_preventive';
          specialty = 'preventive';
        } else if (specialty === 'data analysis') {
          specId = 'spec_data';
          specialty = 'data';
        } else {
          specId = `spec_${specialty}`;
        }
        
        console.log('Found specialist in team assembly:', fullSpecialty, '-> id:', specId);
        
        if (!this.teamState.has(specId)) {
          this.addSpecialist(specId, specialty, fullSpecialty);
        }
        
        this.updateSpecialist(specId, {
          status: 'waiting'
        });
      }

      return {
        appState: 'team-assembling',
        teamUpdate: this.getTeamUpdate()
      };
    }

    // Specialist Working Phase
    if (content.includes('is analyzing') || content.includes('analyzing') || 
        content.includes('Reviewing') || content.includes('Processing')) {
      
      // Look for specialist activities
      const specialistKeywords = {
        'cardiology': ['heart', 'cardiac', 'cholesterol', 'blood pressure'],
        'laboratory': ['lab', 'results', 'test', 'values'],
        'endocrinology': ['HbA1c', 'glucose', 'diabetes', 'metabolic'],
        'data': ['trend', 'analysis', 'pattern', 'data'],
        'preventive': ['prevention', 'screening', 'wellness'],
        'pharmacy': ['medication', 'drug', 'prescription']
      };
      
      let streamingContent: string | undefined;
      let activeSpecialty: string | undefined;
      
      Object.entries(specialistKeywords).forEach(([specialty, keywords]) => {
        const specId = `spec_${specialty}`;
        if (keywords.some(keyword => content.toLowerCase().includes(keyword))) {
          activeSpecialty = specialty;
          if (this.teamState.has(specId)) {
            const member = this.teamState.get(specId)!;
            const currentProgress = member.progress || 0;
            
            // Update based on content context
            let progress = currentProgress;
            let currentTask = member.currentTask || 'Starting analysis...';
            
            if (content.includes('Reviewing')) {
              progress = Math.max(20, Math.min(currentProgress + 15, 40));
              currentTask = 'Reviewing patient records...';
            } else if (content.includes('Analyzing')) {
              progress = Math.max(40, Math.min(currentProgress + 20, 70));
              currentTask = 'Analyzing health metrics...';
            } else if (content.includes('Processing')) {
              progress = Math.max(60, Math.min(currentProgress + 15, 85));
              currentTask = 'Processing findings...';
            }
            
            this.updateSpecialist(specId, {
              status: 'analyzing',
              progress,
              currentTask
            });
          }
        }
      });
      
      // Extract meaningful content for streaming display
      if (activeSpecialty && content.length > 20) {
        // Extract analysis content (remove metadata)
        const cleanContent = content
          .replace(/\*\*/g, '') // Remove markdown bold
          .replace(/❤️|🔬|📊|💊|🛡️|🔍|🧬|⚕️|🥗/g, '') // Remove emojis
          .replace(/\s+/g, ' ') // Normalize whitespace
          .trim();
        
        // Only include substantive analysis content
        if (cleanContent.length > 15 && (
            cleanContent.includes('•') || 
            cleanContent.includes('-') || 
            cleanContent.includes('Reviewing') || 
            cleanContent.includes('Analyzing') ||
            cleanContent.includes('identified') || 
            cleanContent.includes('found') ||
            cleanContent.includes('shows') ||
            cleanContent.includes('indicates') ||
            cleanContent.includes('suggests') ||
            cleanContent.includes('levels') ||
            cleanContent.includes('values') ||
            cleanContent.includes('results') ||
            cleanContent.includes('Query:') ||
            cleanContent.includes('SELECT') ||
            cleanContent.includes('FROM')
        )) {
          streamingContent = cleanContent;
        }
      }
      
      return {
        appState: 'team-working',
        teamUpdate: this.getTeamUpdate(),
        streamingContent
      };
    }

    // Synthesis Phase
    if (content.includes('Chief Medical Officer Final Review') || content.includes('Synthesizing findings') || 
        (content.includes('CMO') && content.includes('synthesizing'))) {
      this.currentPhase = 'synthesizing';
      
      // Mark all specialists as complete
      this.teamState.forEach((member, id) => {
        if (id !== 'cmo' && member.status === 'analyzing') {
          this.updateSpecialist(id, {
            status: 'complete',
            progress: 100,
            confidence: member.confidence || 85
          });
        }
      });
      
      this.updateSpecialist('cmo', {
        status: 'analyzing',
        message: 'Synthesizing findings from all specialists...',
        progress: 90,
        currentTask: 'Creating comprehensive analysis...'
      });
      
      return {
        appState: 'synthesizing',
        teamUpdate: this.getTeamUpdate()
      };
    }

    return { teamUpdate: this.getTeamUpdate() };
  }

  private parseToolEvent(data: any): { teamUpdate?: TeamUpdate; streamingContent?: string } {
    let streamingContent: string | undefined;
    
    // Update progress based on tool calls
    if (this.currentPhase === 'team-working') {
      // Generate streaming content for tool execution
      if (data?.tool_name === 'execute_health_query_v2' && data?.parameters?.query) {
        streamingContent = `Executing query: ${data.parameters.query.substring(0, 100)}...`;
      }
      
      // Update progress for active specialists
      this.teamState.forEach((member, id) => {
        if (member.status === 'analyzing' && id !== 'cmo') {
          const currentProgress = member.progress || 0;
          const newProgress = Math.min(currentProgress + 20, 90);
          
          // Determine current task based on progress
          let currentTask = 'Analyzing health data...';
          if (newProgress > 60) {
            currentTask = 'Finalizing analysis...';
          } else if (newProgress > 30) {
            currentTask = 'Processing lab results...';
          }
          
          this.updateSpecialist(id, {
            progress: newProgress,
            toolCalls: (member.toolCalls || 0) + 1,
            currentTask
          });
        }
      });
    }

    return { teamUpdate: this.getTeamUpdate(), streamingContent };
  }

  private parseToolResultEvent(data: any): { teamUpdate?: TeamUpdate; streamingContent?: string } {
    // Mark specialists as complete based on context
    if (data.phase === 'specialist_complete') {
      const specId = data.specialistId;
      if (specId && this.teamState.has(specId)) {
        this.updateSpecialist(specId, {
          status: 'complete',
          progress: 100,
          confidence: data.confidence || 85
        });
      }
    }

    return { teamUpdate: this.getTeamUpdate() };
  }

  private parseTextEvent(content: string): { appState?: string; teamUpdate?: TeamUpdate; streamingContent?: string } {
    // Check if this is the final synthesis message
    if (this.currentPhase === 'synthesizing') {
      // Mark CMO as complete when synthesis is done
      this.updateSpecialist('cmo', {
        status: 'complete',
        progress: 100,
        confidence: 100,
        message: 'Synthesis complete'
      });
      this.currentPhase = 'complete';
    }
    // Parse specialist status messages (handle compound names)
    const specialistPattern = /([^*]+?) is analyzing your health data\.\.\./i;
    const completionPattern = /([^*]+?) completed analysis \((\d+) queries? executed, (\d+)% confidence\)/i;
    
    // Check for specialist starting analysis
    const startMatch = content.match(specialistPattern);
    if (startMatch) {
      const fullSpecialty = startMatch[1].trim();
      let specialty = fullSpecialty.toLowerCase();
      let specId = '';
      
      // Handle compound specialties
      if (specialty === 'laboratory medicine') {
        specId = 'spec_laboratory';
        specialty = 'laboratory';
      } else if (specialty === 'preventive medicine') {
        specId = 'spec_preventive';
        specialty = 'preventive';
      } else if (specialty === 'data analysis') {
        specId = 'spec_data';
        specialty = 'data';
      } else if (specialty === 'nutrition') {
        specId = 'spec_nutrition';
        specialty = 'nutrition';
      } else if (specialty === 'general practice') {
        specId = 'spec_general';
        specialty = 'general';
      } else {
        specId = `spec_${specialty}`;
      }
      
      console.log('Specialist starting analysis:', fullSpecialty, '-> id:', specId);
      
      // Add specialist if not exists
      if (!this.teamState.has(specId)) {
        this.addSpecialist(specId, specialty, fullSpecialty);
      }
      
      this.updateSpecialist(specId, {
        status: 'analyzing',
        progress: 10,
        currentTask: 'Starting analysis...'
      });
      
      return { 
        appState: 'team-working',
        teamUpdate: this.getTeamUpdate() 
      };
    }
    
    // Check for specialist completion
    const completeMatch = content.match(completionPattern);
    if (completeMatch) {
      const fullSpecialty = completeMatch[1].trim();
      let specialty = fullSpecialty.toLowerCase();
      const queries = parseInt(completeMatch[2]);
      const confidence = parseInt(completeMatch[3]);
      let specId = '';
      
      // Handle compound specialties
      if (specialty === 'laboratory medicine') {
        specId = 'spec_laboratory';
        specialty = 'laboratory';
      } else if (specialty === 'preventive medicine') {
        specId = 'spec_preventive';
        specialty = 'preventive';
      } else if (specialty === 'data analysis') {
        specId = 'spec_data';
        specialty = 'data';
      } else if (specialty === 'nutrition') {
        specId = 'spec_nutrition';
        specialty = 'nutrition';
      } else if (specialty === 'general practice') {
        specId = 'spec_general';
        specialty = 'general';
      } else {
        specId = `spec_${specialty}`;
      }
      
      console.log('Specialist completed:', fullSpecialty, '-> id:', specId, 'Confidence:', confidence);
      
      if (this.teamState.has(specId)) {
        this.updateSpecialist(specId, {
          status: 'complete',
          progress: 100,
          confidence,
          toolCalls: queries,
          message: `Analysis complete with ${confidence}% confidence`
        });
      }
      
      return { teamUpdate: this.getTeamUpdate() };
    }
    
    // Check for visualization generation
    if (content.includes('Creating') && content.includes('visualization')) {
      return { appState: 'visualizing' };
    }

    return {};
  }

  private extractSpecialistsFromContent(content: string): TeamMember[] {
    const specialists: TeamMember[] = [];
    
    // Map of keywords to specialist configurations
    const specialistMap = {
      'Cardiology': { id: 'cardio', name: 'Dr. Heart', gradient: 'from-red-400 to-red-500', icon: 'Heart' },
      'Laboratory': { id: 'lab', name: 'Dr. Lab', gradient: 'from-green-400 to-green-500', icon: 'Flask' },
      'Endocrinology': { id: 'endo', name: 'Dr. Hormone', gradient: 'from-purple-400 to-purple-500', icon: 'Activity' },
      'Data Analysis': { id: 'data', name: 'Dr. Data', gradient: 'from-blue-400 to-blue-500', icon: 'BarChart3' },
      'Pharmacy': { id: 'pharm', name: 'Dr. Meds', gradient: 'from-orange-400 to-orange-500', icon: 'Pill' },
      'Preventive': { id: 'prevent', name: 'Dr. Prevent', gradient: 'from-teal-400 to-teal-500', icon: 'Shield' }
    };

    Object.entries(specialistMap).forEach(([keyword, config]) => {
      if (content.includes(keyword)) {
        specialists.push({
          ...config,
          specialty: keyword,
          status: 'waiting'
        });
      }
    });

    return specialists;
  }

  private extractSpecialistName(content: string): string | null {
    const match = content.match(/(\w+)\s+is\s+analyzing/i);
    return match ? match[1] : null;
  }

  private getSpecialistIdByName(name: string): string | null {
    for (const [id, member] of this.teamState.entries()) {
      if (member.specialty.toLowerCase().includes(name.toLowerCase())) {
        return id;
      }
    }
    return null;
  }

  private updateSpecialist(id: string, updates: Partial<TeamMember>) {
    const current = this.teamState.get(id);
    if (current) {
      this.teamState.set(id, { ...current, ...updates });
    }
  }

  private addSpecialist(id: string, specialty: string, fullSpecialtyName?: string) {
    const specialists = [
      { specialty: 'cardiology', name: 'Dr. Heart', gradient: 'from-red-400 to-red-500', icon: 'Heart' },
      { specialty: 'laboratory', name: 'Dr. Lab', gradient: 'from-green-400 to-green-500', icon: 'FlaskConical' },
      { specialty: 'medicine', name: 'Dr. Lab', gradient: 'from-green-400 to-green-500', icon: 'FlaskConical' }, // For "Laboratory Medicine"
      { specialty: 'endocrinology', name: 'Dr. Hormone', gradient: 'from-purple-400 to-purple-500', icon: 'Activity' },
      { specialty: 'data', name: 'Dr. Analytics', gradient: 'from-yellow-400 to-yellow-500', icon: 'BarChart3' },
      { specialty: 'analysis', name: 'Dr. Analytics', gradient: 'from-yellow-400 to-yellow-500', icon: 'BarChart3' }, // For "Data Analysis"
      { specialty: 'pharmacy', name: 'Dr. Pharma', gradient: 'from-orange-400 to-orange-500', icon: 'Pill' },
      { specialty: 'preventive', name: 'Dr. Prevention', gradient: 'from-indigo-400 to-indigo-500', icon: 'Shield' },
      { specialty: 'nutrition', name: 'Dr. Nutrition', gradient: 'from-emerald-400 to-emerald-500', icon: 'Apple' },
      { specialty: 'general', name: 'Dr. General', gradient: 'from-blue-400 to-blue-500', icon: 'Stethoscope' },
      { specialty: 'practice', name: 'Dr. General', gradient: 'from-blue-400 to-blue-500', icon: 'Stethoscope' } // For "General Practice"
    ];
    
    const config = specialists.find(s => s.specialty.toLowerCase() === specialty.toLowerCase()) || {
      specialty: specialty,
      name: `Dr. ${specialty}`,
      gradient: 'from-gray-400 to-gray-500',
      icon: 'Stethoscope'
    };
    
    // Use full specialty name if provided, otherwise capitalize the specialty
    let displaySpecialty = fullSpecialtyName || (specialty.charAt(0).toUpperCase() + specialty.slice(1));
    
    this.teamState.set(id, {
      id,
      name: config.name,
      specialty: displaySpecialty,
      status: 'waiting',
      gradient: config.gradient,
      icon: config.icon
    });
  }

  private getTeamUpdate(): TeamUpdate {
    const members = Array.from(this.teamState.values());
    const overallProgress = this.calculateOverallProgress(members);
    const teamStatus = this.determineTeamStatus(members);
    
    console.log('[SSEParser] Current team state:', {
      memberCount: members.length,
      members: members.map(m => ({ id: m.id, name: m.name, status: m.status, progress: m.progress })),
      teamStatus,
      overallProgress
    });

    return {
      teamStatus,
      members,
      overallProgress
    };
  }

  private calculateOverallProgress(members: TeamMember[]): number {
    // During CMO analysis phase, overall progress is based on CMO progress only
    if (this.currentPhase === 'cmo-analyzing') {
      const cmo = members.find(m => m.id === 'cmo');
      return cmo?.progress || 0;
    }
    
    // During team working phase, calculate average of all specialists (excluding CMO)
    const specialists = members.filter(m => m.id !== 'cmo' && m.status !== 'waiting');
    if (specialists.length === 0) {
      // If no specialists are active yet, show CMO progress
      const cmo = members.find(m => m.id === 'cmo');
      return cmo?.progress || 0;
    }

    const totalProgress = specialists.reduce((sum, m) => sum + (m.progress || 0), 0);
    return Math.round(totalProgress / specialists.length);
  }

  private determineTeamStatus(members: TeamMember[]): 'assembling' | 'analyzing' | 'synthesizing' | 'complete' {
    const specialists = members.filter(m => m.id !== 'cmo');
    
    if (specialists.length === 0) return 'assembling';
    if (this.currentPhase === 'synthesizing') return 'synthesizing';
    if (specialists.some(s => s.status === 'analyzing')) return 'analyzing';
    if (specialists.every(s => s.status === 'complete')) return 'complete';
    
    return 'assembling';
  }

  reset() {
    // Clear all specialists but keep CMO
    const specialists = Array.from(this.teamState.keys()).filter(id => id !== 'cmo');
    specialists.forEach(id => this.teamState.delete(id));
    
    // Reset CMO to initial state
    this.teamState.set('cmo', {
      id: 'cmo',
      name: 'Dr. Vitality',
      specialty: 'Chief Medical Officer',
      status: 'waiting',
      gradient: 'from-blue-500 to-blue-600',
      icon: 'Brain',
      progress: 0
    });
    this.currentPhase = 'idle';
  }
}