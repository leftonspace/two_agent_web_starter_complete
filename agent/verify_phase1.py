#!/usr/bin/env python3
"""
Phase 1 Verification Script
Run this to verify all Phase 1 components are properly installed and working.

Usage:
    python -m agent.verify_phase1
    # or from agent directory:
    python verify_phase1.py
"""

import sys
import asyncio
from pathlib import Path
from typing import Tuple

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_status(component: str, status: bool, message: str = ""):
    """Print component status with color"""
    symbol = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
    status_text = f"{GREEN}PASS{RESET}" if status else f"{RED}FAIL{RESET}"
    print(f"  {symbol} {component}: {status_text}")
    if message:
        print(f"    {YELLOW}{message}{RESET}")


def print_section(title: str):
    """Print section header"""
    print(f"\n{BLUE}{BOLD}{title}{RESET}")


async def verify_phase1() -> Tuple[int, int]:
    """Verify all Phase 1 components"""
    passed = 0
    failed = 0

    print("\n" + "=" * 60)
    print(f"{BOLD}PHASE 1 VERIFICATION - JARVIS Foundation{RESET}")
    print("=" * 60)

    # 1. YAML Configuration System
    print_section("1. YAML Configuration System")
    try:
        from agent.config_loader import ConfigLoader, ConfigValidationError
        from agent.models.agent_config import AgentConfig, AgentTeam
        from agent.models.task_config import TaskConfig, TaskGraph

        # Test model creation
        test_agent = AgentConfig(
            name="test",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Story"
        )
        print_status("Agent model creation", True)
        passed += 1

        test_task = TaskConfig(
            id="test",
            name="Test Task",
            description="Test",
            expected_output="Test",
            agent="test"
        )
        print_status("Task model creation", True)
        passed += 1

        # Test loader initialization
        loader = ConfigLoader()
        print_status("ConfigLoader initialization", True)
        passed += 1

        # Check if example configs exist and can be loaded
        config_dir = Path("agent/config")
        if (config_dir / "agents.yaml").exists():
            try:
                agents = loader.load_agents()
                print_status("Agent config loading", True, f"Loaded {len(agents)} agents")
                passed += 1
            except Exception as e:
                print_status("Agent config loading", False, str(e))
                failed += 1
        else:
            print_status("Agent config loading", True, "No agents.yaml (optional)")
            passed += 1

        if (config_dir / "tasks.yaml").exists():
            try:
                tasks = loader.load_tasks()
                print_status("Task config loading", True, f"Loaded {len(tasks)} tasks")
                passed += 1
            except Exception as e:
                print_status("Task config loading", False, str(e))
                failed += 1
        else:
            print_status("Task config loading", True, "No tasks.yaml (optional)")
            passed += 1

    except ImportError as e:
        print_status("YAML Configuration imports", False, str(e))
        failed += 5
    except Exception as e:
        print_status("YAML Configuration", False, str(e))
        failed += 5

    # 2. Flow Engine
    print_section("2. Flow Engine with Router")
    try:
        from agent.flow import (
            Flow, start, listen, router,
            FlowState, FlowStatus, FlowGraph,
            FlowExecutionError
        )

        # Test flow creation and execution
        class TestFlow(Flow):
            @start()
            async def begin(self):
                return "test_value"

            @listen("begin")
            async def process(self, data):
                return f"processed_{data}"

        flow = TestFlow()
        result = await flow.run()

        expected = "processed_test_value"
        print_status("Flow execution", result == expected, f"Result: {result}")
        if result == expected:
            passed += 1
        else:
            failed += 1

        # Test graph building
        try:
            graph = flow._build_graph()
            node_count = len(graph.nodes) if hasattr(graph, 'nodes') else 0
            print_status("Graph construction", node_count > 0, f"{node_count} nodes")
            if node_count > 0:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_status("Graph construction", False, str(e))
            failed += 1

        # Test visualization
        try:
            viz = flow.visualize()
            has_content = "begin" in viz.lower() or len(viz) > 10
            print_status("Flow visualization", has_content)
            if has_content:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_status("Flow visualization", False, str(e))
            failed += 1

        # Test router decorator
        class RouterFlow(Flow):
            @start()
            async def begin(self):
                return "route_a"

            @router("begin")
            async def route(self, data):
                if data == "route_a":
                    return "path_a"
                return "path_b"

            @listen("path_a")
            async def handle_a(self):
                return "result_a"

            @listen("path_b")
            async def handle_b(self):
                return "result_b"

        router_flow = RouterFlow()
        router_result = await router_flow.run()
        print_status("Router functionality", router_result == "result_a")
        if router_result == "result_a":
            passed += 1
        else:
            failed += 1

    except ImportError as e:
        print_status("Flow Engine imports", False, str(e))
        failed += 4
    except Exception as e:
        print_status("Flow Engine", False, str(e))
        failed += 4

    # 3. Clarification Loop System
    print_section("3. Clarification Loop System")
    try:
        from agent.clarification import (
            VagueRequestDetector,
            should_request_clarification,
            QuestionGenerator,
            ClarificationManager,
            ClarityAnalysis,
            RequestClarity,
            RequestType,
            ClarifyingQuestion,
            QuestionType,
            ClarificationPhase,
        )

        # Test vague request detection
        detector = VagueRequestDetector()
        analysis = detector.analyze("make me a website")
        is_vague = analysis.clarity_level in [RequestClarity.VAGUE, RequestClarity.VERY_VAGUE]
        print_status("Vague detection", is_vague, f"Clarity: {analysis.clarity_level.value}")
        if is_vague:
            passed += 1
        else:
            failed += 1

        # Test clear request detection
        clear_analysis = detector.analyze(
            "Create a React portfolio website with 5 pages: Home, About, Projects, "
            "Blog, Contact. Use dark theme with blue accents. Target audience is developers."
        )
        is_clearer = clear_analysis.clarity_level in [RequestClarity.CLEAR, RequestClarity.SOMEWHAT_CLEAR]
        print_status("Clear detection", is_clearer, f"Clarity: {clear_analysis.clarity_level.value}")
        if is_clearer:
            passed += 1
        else:
            failed += 1

        # Test question generation
        generator = QuestionGenerator()
        questions = await generator.generate_questions(analysis, max_questions=5)
        has_questions = len(questions) > 0
        print_status("Question generation", has_questions, f"Generated {len(questions)} questions")
        if has_questions:
            passed += 1
        else:
            failed += 1

        # Test session management
        manager = ClarificationManager()
        session = manager.start_session("test request", analysis, questions)
        session_created = session is not None and session.phase == ClarificationPhase.ASKING
        print_status("Session creation", session_created)
        if session_created:
            passed += 1
        else:
            failed += 1

        # Test answer processing
        if questions:
            result = manager.process_answer("Test answer", questions[0].id)
            answer_processed = result.get("status") in ["complete", "continue"]
            print_status("Answer processing", answer_processed)
            if answer_processed:
                passed += 1
            else:
                failed += 1
        else:
            print_status("Answer processing", False, "No questions to answer")
            failed += 1

        # Test session completion
        completion = manager.complete_clarification()
        has_enhanced = completion.get("enhanced_request") is not None or session.enhanced_request is not None
        print_status("Session completion", has_enhanced)
        if has_enhanced:
            passed += 1
        else:
            failed += 1

    except ImportError as e:
        print_status("Clarification imports", False, str(e))
        failed += 6
    except Exception as e:
        print_status("Clarification System", False, str(e))
        failed += 6

    # 4. Template System
    print_section("4. Question Templates")
    try:
        from agent.clarification import (
            TemplateLibrary,
            QuestionTemplate,
            TemplateType,
            template_library,
            CORE_TEMPLATES,
            WEBSITE_TEMPLATES,
        )

        # Test template library
        has_templates = len(template_library.templates) > 0
        print_status("Template library", has_templates, f"{len(template_library.templates)} templates")
        if has_templates:
            passed += 1
        else:
            failed += 1

        # Test getting templates by type
        website_templates = template_library.get_templates_for_type(TemplateType.WEBSITE)
        has_website = len(website_templates) > 0
        print_status("Website templates", has_website, f"{len(website_templates)} templates")
        if has_website:
            passed += 1
        else:
            failed += 1

    except ImportError as e:
        print_status("Template imports", False, str(e))
        failed += 2
    except Exception as e:
        print_status("Template System", False, str(e))
        failed += 2

    # 5. Integration Test
    print_section("5. End-to-End Integration")
    try:
        from agent.clarification import should_request_clarification, QuestionGenerator, ClarificationManager
        from agent.flow import Flow, start, listen

        # Test full flow: detection -> clarification -> flow execution
        user_request = "build me something cool"

        # Step 1: Detect if clarification needed
        should_clarify, analysis = should_request_clarification(user_request)

        if should_clarify:
            # Step 2: Generate questions
            generator = QuestionGenerator()
            questions = await generator.generate_questions(analysis, max_questions=3)

            # Step 3: Start session and answer
            manager = ClarificationManager()
            session = manager.start_session(user_request, analysis, questions)

            for q in questions[:2]:  # Answer first 2 questions
                manager.process_answer("Integration test answer", q.id)

            # Step 4: Complete and get enhanced request
            result = manager.complete_clarification()
            enhanced = result.get("enhanced_request") or session.enhanced_request or ""

            # Step 5: Use in flow
            class IntegrationFlow(Flow):
                def __init__(self, request):
                    super().__init__()
                    self.request = request

                @start()
                async def process(self):
                    return f"Processed: {len(self.request)} chars"

            flow = IntegrationFlow(enhanced)
            flow_result = await flow.run()

            integration_ok = "Processed:" in flow_result and len(enhanced) > len(user_request)
            print_status("Full integration", integration_ok, f"Enhanced: {len(enhanced)} chars")
            if integration_ok:
                passed += 1
            else:
                failed += 1
        else:
            print_status("Full integration", False, "Should have triggered clarification")
            failed += 1

    except Exception as e:
        print_status("Integration test", False, str(e))
        failed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"{BOLD}VERIFICATION SUMMARY{RESET}")
    print("=" * 60)
    total = passed + failed
    percentage = (passed / total * 100) if total > 0 else 0

    print(f"  Total Tests: {total}")
    print(f"  Passed: {GREEN}{passed}{RESET}")
    print(f"  Failed: {RED}{failed}{RESET}")
    print(f"  Success Rate: {percentage:.1f}%")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}✓ Phase 1 is fully operational!{RESET}")
        print(f"{GREEN}  All JARVIS foundation components are working correctly.{RESET}")
    elif failed <= 2:
        print(f"\n{YELLOW}{BOLD}⚠ Phase 1 is mostly operational.{RESET}")
        print(f"{YELLOW}  {failed} minor issue(s) detected. Review warnings above.{RESET}")
    else:
        print(f"\n{RED}{BOLD}✗ Phase 1 has {failed} failing component(s).{RESET}")
        print(f"{RED}  Please check the errors above and ensure all dependencies are installed.{RESET}")

    print("=" * 60 + "\n")

    return passed, failed


def main():
    """Main entry point"""
    print(f"\n{BLUE}Starting JARVIS Phase 1 Verification...{RESET}")

    try:
        passed, failed = asyncio.run(verify_phase1())
        sys.exit(0 if failed == 0 else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification interrupted by user.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Verification failed with error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
