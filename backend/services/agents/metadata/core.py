"""
Agent Metadata Core Classes

This module contains the core metadata classes used by agents to describe
themselves and their prompts. This is pure agent metadata without any
evaluation-specific concepts.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class PromptMetadata:
    """Metadata for a single prompt file used by an agent"""
    filename: str
    description: str
    purpose: str  # "initial_analysis", "task_creation", "synthesis", etc.
    version: str = "1.0"
    
    @property
    def relative_path(self) -> str:
        """Get relative path for display purposes"""
        return f"prompts/{self.filename}"


@dataclass  
class AgentMetadata:
    """
    Core metadata for an agent - contains descriptive data about the agent's
    identity, capabilities, and configuration.
    """
    agent_type: str  # "cmo", "cardiology", "visualization", etc.
    agent_class: str  # Full class path e.g., "services.agents.cmo.CMOAgent"
    description: str
    
    # Prompts used by this agent
    prompts: List[PromptMetadata]
    
    # Agent capabilities and configuration
    capabilities: List[str] = field(default_factory=list)  # e.g., ["orchestration", "medical_analysis"]
    supported_tools: List[str] = field(default_factory=list)  # e.g., ["execute_health_query_v2"]
    config: Dict[str, Any] = field(default_factory=dict)  # Agent-specific configuration
    
    def get_prompts_by_purpose(self, purpose: str) -> List[PromptMetadata]:
        """Get all prompts for a specific purpose"""
        return [p for p in self.prompts if p.purpose == purpose]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary format"""
        return {
            "agent_type": self.agent_type,
            "agent_class": self.agent_class,
            "description": self.description,
            "prompts": [
                {
                    "filename": p.filename,
                    "description": p.description,
                    "purpose": p.purpose,
                    "version": p.version
                }
                for p in self.prompts
            ],
            "capabilities": self.capabilities,
            "supported_tools": self.supported_tools,
            "config": self.config
        }