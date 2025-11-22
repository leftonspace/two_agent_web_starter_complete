"""
Agent Configuration Models

Pydantic models for agent configuration in the JARVIS system.
Supports YAML-based declarative agent definitions.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
import re


class LLMModel(str, Enum):
    """Supported LLM models for agents"""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_35_SONNET = "claude-3-5-sonnet"
    DEEPSEEK_CHAT = "deepseek-chat"
    LLAMA_31_70B = "llama-3.1:70b"


class AgentConfig(BaseModel):
    """Configuration for a single agent

    Attributes:
        name: Unique agent identifier
        role: Agent's role description
        goal: What the agent aims to achieve
        backstory: Agent's background and expertise
        llm: LLM model to use
        temperature: LLM temperature (0.0 to 2.0)
        max_iterations: Maximum iterations allowed
        max_tokens: Maximum tokens per response
        tools: List of available tools
        capabilities: List of agent capabilities
        verbose: Enable verbose output
        allow_delegation: Can delegate to other agents
        require_approval: Require human approval for actions
        custom_attributes: Custom key-value attributes
        variables: Variables for substitution
    """

    name: str = Field(..., description="Unique agent identifier")
    role: str = Field(..., description="Agent's role description")
    goal: str = Field(..., description="What the agent aims to achieve")
    backstory: str = Field(..., description="Agent's background and expertise")

    # Technical configuration
    llm: LLMModel = Field(LLMModel.GPT_4O_MINI, description="LLM model to use")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_iterations: int = Field(15, ge=1, le=100, description="Max iterations allowed")
    max_tokens: Optional[int] = Field(None, ge=1, le=8000, description="Max tokens per response")

    # Tools and capabilities
    tools: List[str] = Field(default_factory=list, description="Available tools")
    capabilities: List[str] = Field(default_factory=list, description="Agent capabilities")

    # Behavioral flags
    verbose: bool = Field(False, description="Enable verbose output")
    allow_delegation: bool = Field(True, description="Can delegate to other agents")
    require_approval: bool = Field(False, description="Require human approval for actions")

    # Custom attributes
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)

    # Variable substitution support
    variables: Dict[str, str] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True
        extra = "allow"  # Allow extra fields for extensibility

    @validator('name')
    def validate_name(cls, v):
        """Validate agent name format"""
        if not v or not v.strip():
            raise ValueError("Agent name cannot be empty")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Agent name must be alphanumeric with optional _ or -")
        return v.lower().strip()

    @validator('tools')
    def validate_tools(cls, v):
        """Validate that tools are recognized"""
        valid_tools = [
            'web_search', 'file_read', 'file_write', 'code_execute',
            'database_query', 'api_call', 'git_operations', 'image_generation'
        ]
        for tool in v:
            if tool not in valid_tools:
                raise ValueError(f"Unknown tool: {tool}. Valid tools: {valid_tools}")
        return v

    @validator('role', 'goal', 'backstory')
    def validate_not_empty(cls, v, field):
        """Validate that text fields are not empty"""
        if not v or not v.strip():
            raise ValueError(f"{field.name} cannot be empty")
        return v.strip()

    def substitute_variables(self, variables: Dict[str, str]) -> 'AgentConfig':
        """Replace {variable} placeholders in text fields

        Args:
            variables: Dictionary of variable names to values

        Returns:
            New AgentConfig with substituted values

        Raises:
            ValueError: If unsubstituted variables remain
        """
        def substitute(text: str) -> str:
            for key, value in variables.items():
                text = text.replace(f"{{{key}}}", value)
            # Check for unsubstituted variables
            unsubstituted = re.findall(r'\{([^}]+)\}', text)
            if unsubstituted:
                raise ValueError(f"Unsubstituted variables found: {unsubstituted}")
            return text

        # Create a copy and substitute
        config_dict = self.dict()
        config_dict['role'] = substitute(self.role)
        config_dict['goal'] = substitute(self.goal)
        config_dict['backstory'] = substitute(self.backstory)

        return AgentConfig(**config_dict)

    def to_crew_agent_kwargs(self) -> Dict[str, Any]:
        """Convert to kwargs suitable for CrewAI Agent

        Returns:
            Dictionary of kwargs for CrewAI Agent constructor
        """
        return {
            'role': self.role,
            'goal': self.goal,
            'backstory': self.backstory,
            'verbose': self.verbose,
            'allow_delegation': self.allow_delegation,
            'max_iter': self.max_iterations,
        }


class AgentTeam(BaseModel):
    """Configuration for a team of agents

    Attributes:
        name: Team name
        description: Team purpose
        agents: List of team members
        communication_style: How agents communicate
        max_parallel_agents: Maximum concurrent agents
    """

    name: str = Field(..., description="Team name")
    description: str = Field(..., description="Team purpose")
    agents: List[AgentConfig] = Field(..., description="Team members")

    # Team-level settings
    communication_style: str = Field("formal", description="How agents communicate")
    max_parallel_agents: int = Field(3, ge=1, le=10)

    class Config:
        """Pydantic model configuration"""
        extra = "allow"

    @validator('name')
    def validate_name(cls, v):
        """Validate team name"""
        if not v or not v.strip():
            raise ValueError("Team name cannot be empty")
        return v.strip()

    @validator('agents')
    def validate_agents(cls, v):
        """Validate agents list is not empty"""
        if not v:
            raise ValueError("Team must have at least one agent")
        return v

    def get_agent(self, name: str) -> Optional[AgentConfig]:
        """Get agent by name

        Args:
            name: Agent name to find

        Returns:
            AgentConfig if found, None otherwise
        """
        name_lower = name.lower()
        for agent in self.agents:
            if agent.name == name_lower:
                return agent
        return None

    def validate_no_duplicates(self) -> None:
        """Ensure no duplicate agent names

        Raises:
            ValueError: If duplicate names found
        """
        names = [agent.name for agent in self.agents]
        if len(names) != len(set(names)):
            duplicates = [n for n in names if names.count(n) > 1]
            raise ValueError(f"Duplicate agent names found: {set(duplicates)}")

    def get_agents_by_capability(self, capability: str) -> List[AgentConfig]:
        """Get agents with a specific capability

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability
        """
        return [agent for agent in self.agents if capability in agent.capabilities]

    def get_agents_by_tool(self, tool: str) -> List[AgentConfig]:
        """Get agents with access to a specific tool

        Args:
            tool: Tool name to search for

        Returns:
            List of agents with the tool
        """
        return [agent for agent in self.agents if tool in agent.tools]
