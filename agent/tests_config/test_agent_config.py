"""
Tests for Agent Configuration Models

Comprehensive tests for AgentConfig and AgentTeam models.
"""

import pytest
from pydantic import ValidationError

from agent.models.agent_config import AgentConfig, AgentTeam, LLMModel


class TestAgentConfig:
    """Tests for AgentConfig model"""

    def test_minimal_valid_config(self):
        """Test creating agent with minimal required fields"""
        agent = AgentConfig(
            name="test_agent",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory"
        )
        assert agent.name == "test_agent"
        assert agent.role == "Test Role"
        assert agent.goal == "Test Goal"
        assert agent.backstory == "Test Backstory"

    def test_full_config(self):
        """Test creating agent with all fields"""
        agent = AgentConfig(
            name="full_agent",
            role="Full Test Role",
            goal="Full Test Goal",
            backstory="Full Test Backstory",
            llm=LLMModel.GPT_4O,
            temperature=0.5,
            max_iterations=20,
            max_tokens=4000,
            tools=["web_search", "file_read"],
            capabilities=["research", "analysis"],
            verbose=True,
            allow_delegation=False,
            require_approval=True,
            custom_attributes={"key": "value"}
        )
        assert agent.name == "full_agent"
        assert agent.llm == LLMModel.GPT_4O
        assert agent.temperature == 0.5
        assert agent.max_iterations == 20
        assert agent.max_tokens == 4000
        assert "web_search" in agent.tools
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert agent.require_approval is True

    def test_default_values(self):
        """Test default values are applied correctly"""
        agent = AgentConfig(
            name="default_test",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )
        assert agent.llm == LLMModel.GPT_4O_MINI
        assert agent.temperature == 0.7
        assert agent.max_iterations == 15
        assert agent.max_tokens is None
        assert agent.tools == []
        assert agent.capabilities == []
        assert agent.verbose is False
        assert agent.allow_delegation is True
        assert agent.require_approval is False

    def test_name_validation_empty(self):
        """Test that empty name raises error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                name="",
                role="Role",
                goal="Goal",
                backstory="Backstory"
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_name_validation_whitespace(self):
        """Test that whitespace-only name raises error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                name="   ",
                role="Role",
                goal="Goal",
                backstory="Backstory"
            )
        assert "cannot be empty" in str(exc_info.value)

    def test_name_validation_special_chars(self):
        """Test that special characters in name raise error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                name="test@agent!",
                role="Role",
                goal="Goal",
                backstory="Backstory"
            )
        assert "alphanumeric" in str(exc_info.value)

    def test_name_normalization(self):
        """Test that name is normalized to lowercase"""
        agent = AgentConfig(
            name="Test_Agent",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )
        assert agent.name == "test_agent"

    def test_temperature_range_low(self):
        """Test temperature below valid range"""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                temperature=-0.1
            )

    def test_temperature_range_high(self):
        """Test temperature above valid range"""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                temperature=2.1
            )

    def test_temperature_boundary_values(self):
        """Test temperature at boundary values"""
        agent_low = AgentConfig(
            name="test_low",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            temperature=0.0
        )
        assert agent_low.temperature == 0.0

        agent_high = AgentConfig(
            name="test_high",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            temperature=2.0
        )
        assert agent_high.temperature == 2.0

    def test_max_iterations_range(self):
        """Test max_iterations validation"""
        with pytest.raises(ValidationError):
            AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                max_iterations=0
            )

        with pytest.raises(ValidationError):
            AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                max_iterations=101
            )

    def test_valid_tools(self):
        """Test valid tools are accepted"""
        valid_tools = [
            'web_search', 'file_read', 'file_write', 'code_execute',
            'database_query', 'api_call', 'git_operations', 'image_generation'
        ]
        agent = AgentConfig(
            name="test",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            tools=valid_tools
        )
        assert agent.tools == valid_tools

    def test_invalid_tools(self):
        """Test invalid tools raise error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                tools=["invalid_tool"]
            )
        assert "Unknown tool" in str(exc_info.value)

    def test_variable_substitution(self):
        """Test variable substitution in text fields"""
        agent = AgentConfig(
            name="test",
            role="Expert in {topic}",
            goal="Research {topic} thoroughly",
            backstory="Specialist in {topic} for 10 years"
        )

        substituted = agent.substitute_variables({"topic": "AI"})

        assert substituted.role == "Expert in AI"
        assert substituted.goal == "Research AI thoroughly"
        assert substituted.backstory == "Specialist in AI for 10 years"

    def test_variable_substitution_multiple(self):
        """Test multiple variable substitution"""
        agent = AgentConfig(
            name="test",
            role="Expert in {topic1} and {topic2}",
            goal="Research {topic1}",
            backstory="Background in {topic2}"
        )

        substituted = agent.substitute_variables({
            "topic1": "AI",
            "topic2": "ML"
        })

        assert substituted.role == "Expert in AI and ML"
        assert substituted.goal == "Research AI"
        assert substituted.backstory == "Background in ML"

    def test_variable_substitution_unsubstituted_error(self):
        """Test that unsubstituted variables raise error"""
        agent = AgentConfig(
            name="test",
            role="Expert in {topic}",
            goal="Research {unknown}",
            backstory="Background"
        )

        with pytest.raises(ValueError) as exc_info:
            agent.substitute_variables({"topic": "AI"})
        assert "Unsubstituted variables" in str(exc_info.value)

    def test_to_crew_agent_kwargs(self):
        """Test conversion to CrewAI kwargs"""
        agent = AgentConfig(
            name="test",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory",
            verbose=True,
            allow_delegation=False,
            max_iterations=25
        )

        kwargs = agent.to_crew_agent_kwargs()

        assert kwargs['role'] == "Test Role"
        assert kwargs['goal'] == "Test Goal"
        assert kwargs['backstory'] == "Test Backstory"
        assert kwargs['verbose'] is True
        assert kwargs['allow_delegation'] is False
        assert kwargs['max_iter'] == 25

    def test_llm_enum_values(self):
        """Test all LLM enum values"""
        for model in LLMModel:
            agent = AgentConfig(
                name="test",
                role="Role",
                goal="Goal",
                backstory="Backstory",
                llm=model
            )
            assert agent.llm == model


class TestAgentTeam:
    """Tests for AgentTeam model"""

    def test_create_team(self):
        """Test creating a team of agents"""
        agents = [
            AgentConfig(
                name="agent1",
                role="Role 1",
                goal="Goal 1",
                backstory="Backstory 1"
            ),
            AgentConfig(
                name="agent2",
                role="Role 2",
                goal="Goal 2",
                backstory="Backstory 2"
            )
        ]

        team = AgentTeam(
            name="Test Team",
            description="A test team",
            agents=agents
        )

        assert team.name == "Test Team"
        assert team.description == "A test team"
        assert len(team.agents) == 2

    def test_team_default_values(self):
        """Test team default values"""
        agent = AgentConfig(
            name="agent1",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=[agent]
        )

        assert team.communication_style == "formal"
        assert team.max_parallel_agents == 3

    def test_get_agent_by_name(self):
        """Test getting agent by name"""
        agents = [
            AgentConfig(
                name="agent1",
                role="Role 1",
                goal="Goal 1",
                backstory="Backstory 1"
            ),
            AgentConfig(
                name="agent2",
                role="Role 2",
                goal="Goal 2",
                backstory="Backstory 2"
            )
        ]

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=agents
        )

        found = team.get_agent("agent1")
        assert found is not None
        assert found.name == "agent1"

        not_found = team.get_agent("nonexistent")
        assert not_found is None

    def test_get_agent_case_insensitive(self):
        """Test getting agent is case insensitive"""
        agent = AgentConfig(
            name="TestAgent",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=[agent]
        )

        # Name is normalized to lowercase
        assert team.get_agent("testagent") is not None

    def test_validate_no_duplicates(self):
        """Test duplicate validation"""
        agent1 = AgentConfig(
            name="agent1",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )
        agent2 = AgentConfig(
            name="agent1",  # Duplicate name
            role="Role 2",
            goal="Goal 2",
            backstory="Backstory 2"
        )

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=[agent1, agent2]
        )

        with pytest.raises(ValueError) as exc_info:
            team.validate_no_duplicates()
        assert "Duplicate agent names" in str(exc_info.value)

    def test_get_agents_by_capability(self):
        """Test filtering agents by capability"""
        agent1 = AgentConfig(
            name="agent1",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            capabilities=["research", "analysis"]
        )
        agent2 = AgentConfig(
            name="agent2",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            capabilities=["writing"]
        )

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=[agent1, agent2]
        )

        researchers = team.get_agents_by_capability("research")
        assert len(researchers) == 1
        assert researchers[0].name == "agent1"

    def test_get_agents_by_tool(self):
        """Test filtering agents by tool"""
        agent1 = AgentConfig(
            name="agent1",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            tools=["web_search", "file_read"]
        )
        agent2 = AgentConfig(
            name="agent2",
            role="Role",
            goal="Goal",
            backstory="Backstory",
            tools=["file_write"]
        )

        team = AgentTeam(
            name="Test",
            description="Test",
            agents=[agent1, agent2]
        )

        web_agents = team.get_agents_by_tool("web_search")
        assert len(web_agents) == 1
        assert web_agents[0].name == "agent1"

    def test_empty_team_validation(self):
        """Test that empty team raises error"""
        with pytest.raises(ValidationError) as exc_info:
            AgentTeam(
                name="Test",
                description="Test",
                agents=[]
            )
        assert "at least one agent" in str(exc_info.value)

    def test_empty_name_validation(self):
        """Test that empty team name raises error"""
        agent = AgentConfig(
            name="agent1",
            role="Role",
            goal="Goal",
            backstory="Backstory"
        )

        with pytest.raises(ValidationError) as exc_info:
            AgentTeam(
                name="",
                description="Test",
                agents=[agent]
            )
        assert "cannot be empty" in str(exc_info.value)


class TestLLMModel:
    """Tests for LLMModel enum"""

    def test_all_models_defined(self):
        """Test all expected models are defined"""
        expected_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "claude-3-5-sonnet",
            "deepseek-chat",
            "llama-3.1:70b"
        ]

        model_values = [m.value for m in LLMModel]
        for expected in expected_models:
            assert expected in model_values

    def test_model_string_conversion(self):
        """Test model to string conversion"""
        assert LLMModel.GPT_4O.value == "gpt-4o"
        assert str(LLMModel.GPT_4O) == "LLMModel.GPT_4O"
