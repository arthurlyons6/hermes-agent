"""Regression tests for the Lyons Command Center [PERSON_NAME] self-identity rule.

These tests verify the three identity-routing scenarios Arthur specified:

1. "Get Marcus involved" → assistant recognizes itself as [PERSON_NAME], does
   NOT delegate.
2. "Commander, review the current state…" → assistant answers directly as
   Commander and Chief of Staff, does NOT ask which agent is meant.
3. "Have Evelyn verify the facts and Grant evaluate the transaction." →
   [PERSON_NAME] acknowledges command and delegates to the right specialists.
"""

from types import SimpleNamespace
from unittest.mock import patch

from agent.prompt_builder import MARCUS_SELF_IDENTITY_RULE, DEFAULT_AGENT_IDENTITY
from agent.system_prompt import build_system_prompt_parts


def _make_agent(**overrides):
    base = dict(
        load_soul_identity=False,
        skip_context_files=False,
        _task_completion_guidance=False,
        _tool_use_enforcement="",
        _parallel_tool_call_guidance=False,
        _environment_probe=False,
        _kanban_worker_guidance="",
        _memory_store=None,
        _memory_manager=None,
        model="",
        provider="",
        platform="",
        pass_session_id=False,
        session_id="",
        valid_tool_names=[],
        context_compressor=None,
        reasoning_config=None,
        _platform_hint_overrides=None,
        tools=[],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _stable_prompt(agent):
    """Build the stable tier with SOUL.md and context files mocked out."""
    with (
        patch("run_agent.load_soul_md", return_value=""),
        patch("run_agent.build_nous_subscription_prompt", return_value=""),
        patch("run_agent.build_environment_hints", return_value=""),
        patch("run_agent.build_context_files_prompt", return_value=""),
    ):
        return build_system_prompt_parts(agent)["stable"]


class TestMarcusSelfIdentityRule:
    """Verify the [PERSON_NAME] self-identity rule is injected into the system prompt."""

    def test_rule_is_present_in_stable_prompt(self):
        """The MARCUS_SELF_IDENTITY_RULE string must be in the stable tier."""
        stable = _stable_prompt(_make_agent())
        assert "LYONS COMMAND CENTER — IDENTITY RULE" in stable
        assert "active primary assistant IS Marcus" in stable

    def test_rule_present_even_when_soul_md_loads(self):
        """The rule must be injected even when SOUL.md loads successfully,
        so it can't be overridden by a stale SOUL.md."""
        with (
            patch("run_agent.load_soul_md", return_value="You are a test identity."),
            patch("run_agent.build_nous_subscription_prompt", return_value=""),
            patch("run_agent.build_environment_hints", return_value=""),
            patch("run_agent.build_context_files_prompt", return_value=""),
        ):
            stable = build_system_prompt_parts(_make_agent())["stable"]
        assert "LYONS COMMAND CENTER — IDENTITY RULE" in stable
        assert "You are a test identity." in stable

    def test_rule_instructs_not_to_delegate_marcus(self):
        """The rule must explicitly say NOT to delegate to [PERSON_NAME]."""
        rule_text = MARCUS_SELF_IDENTITY_RULE
        assert "MUST NOT attempt to delegate to Marcus" in rule_text
        assert "It IS Marcus" in rule_text

    def test_rule_lists_workforce_agents(self):
        """The rule must list the authorized workforce agents [PERSON_NAME] can delegate to."""
        rule_text = MARCUS_SELF_IDENTITY_RULE
        for name in [
            "Evelyn",
            "Miles",
            "Victor",
            "Sophia",
            "Julian",
            "Elijah",
            "David",
            "Grant",
            "Caleb",
            "Naomi",
            "Olivia",
            "Grace",
            "Jordan",
            "Malcolm",
        ]:
            assert name in rule_text, f"Workforce agent {name} missing from rule"

    def test_rule_never_delegate_marcus_role(self):
        """The rule must state that the role of [PERSON_NAME] is never delegated."""
        rule_text = MARCUS_SELF_IDENTITY_RULE
        assert "NEVER delegate the role of Marcus" in rule_text

    def test_rule_uses_conversation_context(self):
        """The rule must instruct the assistant to use conversation context
        instead of restarting the interaction."""
        rule_text = MARCUS_SELF_IDENTITY_RULE
        assert "Use the active conversation context" in rule_text
        assert "resolve the reference from" in rule_text


class TestMarcusIdentityScenarios:
    """The three test scenarios from Arthur's directive.

    These verify the system prompt contains the right instructions so that
    the model, when given the test inputs, would respond correctly. We test
    the prompt content because we can't run the actual LLM in a unit test.
    """

    def _full_prompt(self):
        """Get the full system prompt with SOUL.md loaded (the [PERSON_NAME] identity)."""
        with (
            patch("run_agent.load_soul_md", return_value="You are Marcus, Commander."),
            patch("run_agent.build_nous_subscription_prompt", return_value=""),
            patch("run_agent.build_environment_hints", return_value=""),
            patch("run_agent.build_context_files_prompt", return_value=""),
        ):
            return build_system_prompt_parts(_make_agent())

    def test_scenario_1_get_marcus_involved(self):
        """Test 1: 'Get Marcus involved.' → respond as [PERSON_NAME], don't delegate."""
        prompt = self._full_prompt()
        # The prompt must contain the identity rule
        assert "LYONS COMMAND CENTER — IDENTITY RULE" in prompt["stable"]
        # The rule must say NOT to delegate when [PERSON_NAME] is requested
        assert "MUST NOT attempt to delegate to Marcus" in prompt["stable"]
        # The rule must include the example response
        assert "Marcus is here. I am assuming command" in prompt["stable"]

    def test_scenario_2_commander_review(self):
        """Test 2: 'Commander, review…' → answer directly, don't ask which agent."""
        prompt = self._full_prompt()
        # The rule must cover "Commander" as a trigger
        assert "Commander" in prompt["stable"]
        # The rule must say not to ask which agent is meant
        assert "MUST NOT attempt to delegate" in prompt["stable"]

    def test_scenario_3_delegate_to_specialists(self):
        """Test 3: 'Have Evelyn verify and Grant evaluate…' → [PERSON_NAME] delegates."""
        prompt = self._full_prompt()
        # The rule must list both Evelyn and Grant as delegatable agents
        assert "Evelyn" in prompt["stable"]
        assert "Grant" in prompt["stable"]
        # The rule must say [PERSON_NAME] MAY delegate to the workforce
        assert "may delegate" in prompt["stable"].lower()
        # But must NEVER delegate the role of [PERSON_NAME] itself
        assert "NEVER delegate the role of Marcus" in prompt["stable"]
