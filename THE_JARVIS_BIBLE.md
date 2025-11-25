# THE JARVIS BIBLE
## Complete System Reference & Architecture Documentation

> **Version:** 2.1.0
> **Last Updated:** 2025-11-24
> **Total Files:** 400+
> **Total Lines of Code:** 150,000+

---

# PART I: WHAT IS JARVIS?

## 1.1 Overview

**JARVIS** (Just A Rather Very Intelligent System) is an enterprise-grade, multi-agent AI orchestration platform designed to function as an autonomous digital employee. Named after the AI assistant from Iron Man, JARVIS combines multiple AI capabilities into a unified, self-improving system.

JARVIS is NOT just a chatbot. It is a **complete autonomous agent system** that can:
- Execute complex multi-step tasks without human intervention
- Coordinate multiple AI agents working in parallel
- Remember user preferences and business context across sessions
- Join meetings, transcribe, and take action items automatically
- Generate documents, analyze data, and manage workflows
- Self-optimize based on performance data

## 1.2 Core Philosophy

JARVIS operates on these principles:
1. **Proactive, Not Reactive** - Anticipates needs, doesn't just respond
2. **Multi-Agent Collaboration** - Complex tasks are broken into specialized sub-tasks
3. **Persistent Memory** - Learns and remembers across all interactions
4. **Safety First** - Multiple layers of validation before any risky action
5. **Transparent Operations** - All actions are logged and auditable
6. **Self-Improvement** - Continuously optimizes based on performance data

## 1.3 Project Structure

```
two_agent_web_starter_complete/
├── .env.example                           # Environment variables template
├── .githooks/                             # Git hooks
│   └── pre-commit                         # Pre-commit validation hook
├── .github/                               # GitHub configuration
│   └── workflows/
│       └── tests.yml                      # CI/CD test workflow
├── .gitignore                             # Git ignore rules
├── .vscode/                               # VSCode configuration
│   ├── launch.json                        # Debug configurations
│   └── tasks.json                         # Build tasks
├── agent/                                 # Core orchestrator code
│   ├── _errors.py                         # Error definitions
│   ├── actions/                           # Action execution modules
│   │   ├── __init__.py
│   │   ├── api_client.py                  # Universal HTTP client
│   │   ├── code_executor.py               # Multi-language code execution
│   │   ├── db_client.py                   # Database operations
│   │   ├── file_ops.py                    # File system operations
│   │   ├── git_ops.py                     # Git repository operations
│   │   ├── rate_limiter.py                # API rate limiting
│   │   └── sandbox.py                     # Sandboxed execution
│   ├── admin/                             # Administrative tools
│   │   ├── __init__.py
│   │   ├── calendar_intelligence.py       # Calendar management
│   │   ├── email_integration.py           # Email automation
│   │   └── workflow_automation.py         # Workflow automation
│   ├── agent_api.py                       # Agent API interface
│   ├── agent_messaging.py                 # Inter-agent messaging
│   ├── agents_api.py                      # Agents API endpoints
│   ├── alerting.py                        # Alert system
│   ├── analytics.py                       # Analytics engine (Stage 11)
│   ├── approval_engine.py                 # Approval workflow engine
│   ├── artifacts.py                       # Artifact management
│   ├── audit_log.py                       # Audit logging
│   ├── auto_improver.py                   # Auto-improvement system
│   ├── auto_pilot.py                      # Auto-pilot mode
│   ├── autonomous_coordinator.py          # Autonomous coordination
│   ├── brain.py                           # Self-optimization engine (Stage 12)
│   ├── business_memory/                   # Business context memory
│   │   ├── __init__.py
│   │   ├── extractor.py                   # Information extraction
│   │   ├── manager.py                     # Memory management
│   │   ├── privacy.py                     # Privacy controls
│   │   └── schema.py                      # Data schemas
│   ├── checkpoint.py                      # Checkpoint management
│   ├── clarification/                     # Clarification system
│   │   ├── __init__.py
│   │   ├── detector.py                    # Ambiguity detection
│   │   ├── generator.py                   # Question generation
│   │   ├── manager.py                     # Clarification management
│   │   └── templates.py                   # Question templates
│   ├── cli_chat.py                        # CLI chat interface
│   ├── code_analysis/                     # Code analysis tools
│   │   ├── __init__.py
│   │   ├── ast_parser.py                  # AST parsing
│   │   ├── js_parser.py                   # JavaScript parser
│   │   ├── patterns.py                    # Pattern detection
│   │   └── refactoring.py                 # Refactoring tools
│   ├── code_review/                       # Code review system
│   │   ├── __init__.py
│   │   └── review_agent.py                # Review agent
│   ├── code_review_bot.py                 # Code review bot
│   ├── company_ops.py                     # Company operations
│   ├── config/                            # Configuration files
│   │   ├── agents.yaml                    # Agent configurations
│   │   ├── schemas/                       # JSON schemas
│   │   │   ├── agent_schema.json          # Agent config schema
│   │   │   └── task_schema.json           # Task config schema
│   │   └── tasks.yaml                     # Task configurations
│   ├── config.py                          # Configuration module
│   ├── config_loader.py                   # Config file loader
│   ├── conversational_agent.py            # Conversational AI agent
│   ├── core/                              # Core utilities
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py             # Circuit breaker pattern
│   │   └── error_handler.py               # Error handling
│   ├── core_logging.py                    # Logging configuration
│   ├── cost_estimator.py                  # Cost estimation
│   ├── cost_logs/                         # Cost tracking logs
│   │   └── multi_section_landing_full_test.jsonl
│   ├── cost_tracker.py                    # Token and cost tracking
│   ├── cost_tracker_instance.py           # Cost tracker singleton
│   ├── council/                           # Council decision system
│   │   ├── __init__.py
│   │   ├── competitive_council.py         # Competitive analysis
│   │   ├── factory.py                     # Council factory
│   │   ├── graveyard.py                   # Deprecated decisions
│   │   ├── happiness.py                   # Team happiness metrics
│   │   ├── models.py                      # Council models
│   │   ├── orchestrator.py                # Council orchestration
│   │   └── voting.py                      # Voting mechanisms
│   ├── database/                          # Database modules
│   │   ├── __init__.py
│   │   ├── kg_backends.py                 # Knowledge graph backends
│   │   └── pg_migration.py                # PostgreSQL migration
│   ├── deployment/                        # Deployment utilities
│   │   ├── __init__.py
│   │   └── rollback.py                    # Rollback management
│   ├── documents/                         # Document generation
│   │   ├── __init__.py
│   │   ├── excel_generator.py             # Excel generation
│   │   ├── pdf_generator.py               # PDF generation
│   │   └── word_generator.py              # Word generation
│   ├── domain_router.py                   # Domain routing
│   ├── exec_analysis.py                   # Execution analysis
│   ├── exec_deps.py                       # Execution dependencies
│   ├── exec_safety.py                     # Safety checks
│   ├── exec_tools.py                      # Execution tools
│   ├── execution/                         # Task execution
│   │   ├── __init__.py
│   │   ├── direct_executor.py             # Direct execution mode
│   │   ├── employee_pool.py               # Worker pool management
│   │   ├── review_queue.py                # Review queue
│   │   ├── strategy_decider.py            # Execution strategy
│   │   ├── task_distributor.py            # Task distribution
│   │   └── task_router.py                 # Task routing
│   ├── feedback_analyzer.py               # Feedback analysis
│   ├── file_context.py                    # File context management
│   ├── file_explorer.py                   # File & snapshot explorer (Stage 9)
│   ├── file_operations.py                 # File operations
│   ├── finance/                           # Finance tools
│   │   ├── __init__.py
│   │   ├── document_intelligence.py       # Financial document analysis
│   │   ├── financial_templates.py         # Financial templates
│   │   └── spreadsheet_engine.py          # Spreadsheet engine
│   ├── flow/                              # Flow engine
│   │   ├── __init__.py
│   │   ├── decorators.py                  # Flow decorators
│   │   ├── engine.py                      # Flow execution engine
│   │   ├── events.py                      # Flow events
│   │   ├── graph.py                       # Flow graph
│   │   └── state.py                       # Flow state
│   ├── git_secret_scanner.py              # Git secret scanning
│   ├── git_utils.py                       # Git utilities
│   ├── github_integration.py              # GitHub integration
│   ├── human_proxy.py                     # Human-in-the-loop proxy
│   ├── integrations/                      # External integrations
│   │   ├── auth.py                        # Authentication
│   │   ├── base.py                        # Base integration
│   │   ├── database.py                    # Database integration
│   │   ├── hris/                          # HR systems
│   │   │   ├── __init__.py
│   │   │   └── bamboohr.py                # BambooHR integration
│   │   └── tools.py                       # Integration tools
│   ├── inter_agent_bus.py                 # Inter-agent message bus
│   ├── jarvis_agent.py                    # JARVIS agent core
│   ├── jarvis_chat.py                     # JARVIS chat interface
│   ├── jarvis_persona.py                  # JARVIS personality
│   ├── jarvis_tools.py                    # JARVIS tools
│   ├── jarvis_vision.py                   # JARVIS vision capabilities
│   ├── jarvis_voice.py                    # JARVIS voice synthesis
│   ├── jarvis_voice_chat.py               # JARVIS voice chat
│   ├── jobs.py                            # Job manager (Stage 8)
│   ├── kg_optimizer.py                    # Knowledge graph optimizer
│   ├── kg_write_queue.py                  # KG write queue
│   ├── knowledge_graph.py                 # Knowledge graph
│   ├── knowledge_query.py                 # Knowledge queries
│   ├── llm/                               # LLM management
│   │   ├── __init__.py
│   │   ├── config.py                      # LLM configuration
│   │   ├── enhanced_router.py             # Enhanced routing
│   │   ├── hybrid_strategy.py             # Hybrid LLM strategy
│   │   ├── llm_router.py                  # LLM routing
│   │   ├── ollama_client.py               # Ollama integration
│   │   ├── performance_tracker.py         # Performance tracking
│   │   └── providers.py                   # LLM providers
│   ├── llm.py                             # LLM interface
│   ├── llm_cache.py                       # LLM response cache
│   ├── log_sanitizer.py                   # Log sanitization
│   ├── meetings/                          # Meeting integration
│   │   ├── __init__.py
│   │   ├── base.py                        # Base meeting bot
│   │   ├── cross_meeting_context.py       # Cross-meeting context
│   │   ├── diarization/                   # Speaker diarization
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base diarization
│   │   │   ├── pyannote_engine.py         # Pyannote engine
│   │   │   └── speaker_manager.py         # Speaker management
│   │   ├── factory.py                     # Meeting bot factory
│   │   ├── google_meet_bot.py             # Google Meet bot
│   │   ├── intelligence/                  # Meeting intelligence
│   │   │   ├── __init__.py
│   │   │   ├── action_executor.py         # Action execution
│   │   │   ├── action_item_reminders.py   # Action item reminders
│   │   │   └── meeting_analyzer.py        # Meeting analysis
│   │   ├── live_audio_bot.py              # Live audio capture
│   │   ├── sdk_integration.py             # SDK integration
│   │   ├── session_manager.py             # Session management
│   │   ├── teams_bot.py                   # Microsoft Teams bot
│   │   ├── transcription/                 # Transcription engines
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base transcription
│   │   │   ├── deepgram_engine.py         # Deepgram engine
│   │   │   ├── manager.py                 # Transcription manager
│   │   │   └── whisper_engine.py          # Whisper engine
│   │   └── zoom_bot.py                    # Zoom bot
│   ├── memory/                            # Memory system
│   │   ├── __init__.py
│   │   ├── context_retriever.py           # Context retrieval
│   │   ├── contextual.py                  # Contextual memory
│   │   ├── entity.py                      # Entity memory
│   │   ├── long_term.py                   # Long-term memory
│   │   ├── manager.py                     # Memory manager
│   │   ├── preference_learner.py          # Preference learning
│   │   ├── session_manager.py             # Session management
│   │   ├── short_term.py                  # Short-term memory
│   │   ├── storage.py                     # Memory storage
│   │   ├── user_profile.py                # User profiles
│   │   └── vector_store.py                # Vector storage
│   ├── memory_store/                      # Memory storage data
│   │   └── test_run_002/
│   │       └── stage1.json
│   ├── memory_store.py                    # Memory store module
│   ├── merge_manager.py                   # Merge management
│   ├── migrations/                        # Database migrations
│   │   └── 001_approval_workflows.py      # Approval workflow migration
│   ├── mission_runner.py                  # Mission execution
│   ├── model_registry.py                  # Model registry
│   ├── model_router.py                    # Model routing
│   ├── models/                            # Data models
│   │   ├── __init__.py
│   │   ├── agent_config.py                # Agent configuration model
│   │   └── task_config.py                 # Task configuration model
│   ├── models.json                        # Model definitions
│   ├── monitoring/                        # Monitoring system
│   │   ├── __init__.py
│   │   ├── alerts.py                      # Alert management
│   │   ├── logging_config.py              # Logging configuration
│   │   └── metrics.py                     # Metrics collection
│   ├── monitoring.py                      # Monitoring module
│   ├── mypy.ini                           # MyPy configuration
│   ├── optimization/                      # Performance optimization
│   │   ├── __init__.py
│   │   ├── batch_processor.py             # Batch processing
│   │   ├── cache.py                       # Caching
│   │   └── lazy_loader.py                 # Lazy loading
│   ├── orchestrator.py                    # 3-loop orchestrator
│   ├── orchestrator_2loop.py              # 2-loop orchestrator
│   ├── orchestrator_3loop_legacy.py       # Legacy 3-loop
│   ├── orchestrator_context.py            # Orchestrator context
│   ├── orchestrator_integration.py        # Orchestrator integration
│   ├── orchestrator_phase3.py             # Phase 3 orchestrator
│   ├── overseer.py                        # System overseer
│   ├── parallel_executor.py               # Parallel execution
│   ├── paths.py                           # Path utilities
│   ├── patterns/                          # Execution patterns
│   │   ├── __init__.py
│   │   ├── autoselect.py                  # Auto-selection
│   │   ├── base.py                        # Base pattern
│   │   ├── hierarchical.py                # Hierarchical pattern
│   │   ├── roundrobin.py                  # Round-robin pattern
│   │   ├── selector.py                    # Pattern selector
│   │   └── sequential.py                  # Sequential pattern
│   ├── performance/                       # Performance utilities
│   │   ├── __init__.py
│   │   ├── cache.py                       # Performance cache
│   │   ├── lazy.py                        # Lazy evaluation
│   │   ├── parallel.py                    # Parallel processing
│   │   ├── pool.py                        # Worker pools
│   │   └── utils.py                       # Performance utilities
│   ├── permissions.py                     # Permission management
│   ├── permissions_matrix.json            # Permission definitions
│   ├── proactive_executor.py              # Proactive execution
│   ├── project_config.json                # Project configuration
│   ├── project_stats.py                   # Project statistics
│   ├── prompt_security.py                 # Prompt injection protection
│   ├── prompts/                           # Prompt templates
│   │   └── prompts_default.json           # Default prompts
│   ├── prompts.py                         # Prompts module
│   ├── py.typed                           # PEP 561 marker
│   ├── qa.py                              # Quality assurance
│   ├── queue_config.py                    # Queue configuration
│   ├── repo_router.py                     # Repository routing
│   ├── retry_loop_detector.py             # Retry loop detection
│   ├── role_definitions/                  # Role definitions
│   │   ├── finance_roles.json             # Finance roles
│   │   ├── hr_roles.json                  # HR roles
│   │   └── legal_roles.json               # Legal roles
│   ├── roles.py                           # Role management
│   ├── ruff.toml                          # Ruff linter config
│   ├── run_logger.py                      # Structured run logging
│   ├── run_logs/                          # Run log storage
│   │   └── multi_section_landing_full_test_3loop.jsonl
│   ├── run_mode.py                        # Main CLI entry point
│   ├── run_workflows/                     # Workflow definitions
│   │   └── test_run_001_workflow.json
│   ├── runner.py                          # Programmatic API (Stage 7)
│   ├── safe_io.py                         # Safe I/O helpers
│   ├── sandbox.py                         # Sandbox execution
│   ├── scheduler/                         # Task scheduling
│   │   ├── __init__.py
│   │   └── cron.py                        # Cron scheduler
│   ├── security/                          # Security modules
│   │   ├── __init__.py
│   │   ├── audit_log.py                   # Security audit log
│   │   ├── auth.py                        # Authentication
│   │   └── rate_limit.py                  # Rate limiting
│   ├── self_eval.py                       # Self-evaluation
│   ├── self_refinement.py                 # Self-refinement
│   ├── site_tools.py                      # Site management tools
│   ├── specialist_market.py               # Specialist marketplace
│   ├── specialists.py                     # Specialist agents
│   ├── STAGE_3.3_LLM_RESILIENCE.md        # LLM resilience docs
│   ├── stage_summaries/                   # Stage summary storage
│   │   └── test_run_003/
│   │       └── stage1.json
│   ├── stage_summaries.py                 # Stage summaries module
│   ├── static_analysis.py                 # Static code analysis
│   ├── status_codes.py                    # Normalized status codes
│   ├── templates/                         # Template files
│   │   ├── __init__.py
│   │   ├── email/
│   │   │   └── welcome_email.html         # Email template
│   │   └── email_renderer.py              # Email rendering
│   ├── temporal/                          # Temporal workflow
│   │   ├── __init__.py
│   │   ├── activities.py                  # Temporal activities
│   │   ├── client.py                      # Temporal client
│   │   ├── config.py                      # Temporal config
│   │   ├── worker.py                      # Temporal worker
│   │   └── workflows.py                   # Temporal workflows
│   ├── test_generation.py                 # Test generation
│   ├── tests/                             # Test suite
│   │   ├── e2e/                           # End-to-end tests
│   │   │   └── test_smoke_hello_kevin.py
│   │   ├── fixtures/                      # Test fixtures
│   │   │   └── mock_tool.py
│   │   ├── integration/                   # Integration tests
│   │   │   ├── conftest.py
│   │   │   ├── test_council.py
│   │   │   ├── test_full_flow.py
│   │   │   ├── test_human_approval.py
│   │   │   ├── test_llm_failover.py
│   │   │   ├── test_memory.py
│   │   │   ├── test_patterns.py
│   │   │   ├── test_snapshots_and_files.py
│   │   │   └── test_stage5_integration.py
│   │   ├── mocks.py
│   │   ├── test_action_tools.py
│   │   ├── test_agent_messaging.py
│   │   ├── test_api_client.py
│   │   ├── test_backward_compat.py
│   │   ├── test_business_memory.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_clarification.py
│   │   ├── test_code_executor.py
│   │   ├── test_context_retriever.py
│   │   ├── test_conversational_agent.py
│   │   ├── test_council.py
│   │   ├── test_coverage_gaps.py
│   │   ├── test_db_client.py
│   │   ├── test_diarization.py
│   │   ├── test_direct_executor.py
│   │   ├── test_employee_pool.py
│   │   ├── test_enhanced_router.py
│   │   ├── test_error_handler.py
│   │   ├── test_file_ops.py
│   │   ├── test_flow_engine.py
│   │   ├── test_human_proxy.py
│   │   ├── test_hybrid_strategy.py
│   │   ├── test_llm_config.py
│   │   ├── test_llm_router.py
│   │   ├── test_meeting_bots.py
│   │   ├── test_meeting_intelligence.py
│   │   ├── test_memory_system.py
│   │   ├── test_monitoring.py
│   │   ├── test_ollama.py
│   │   ├── test_optimization.py
│   │   ├── test_patterns.py
│   │   ├── test_performance_tracker.py
│   │   ├── test_phase1_integration.py
│   │   ├── test_preference_learner.py
│   │   ├── test_review_queue.py
│   │   ├── test_security.py
│   │   ├── test_session_manager.py
│   │   ├── test_strategy_decider.py
│   │   ├── test_task_distributor.py
│   │   ├── test_task_router.py
│   │   ├── test_tool_registry.py
│   │   ├── test_transcription.py
│   │   ├── test_vector_store.py
│   │   ├── test_yaml_config.py
│   │   └── unit/                          # Unit tests
│   │       ├── test_cost_tracker.py
│   │       ├── test_document_generation.py
│   │       ├── test_exec_tools.py
│   │       ├── test_git_secret_scanner.py
│   │       ├── test_hr_tools.py
│   │       ├── test_log_sanitizer.py
│   │       ├── test_merge_manager.py
│   │       ├── test_model_registry.py
│   │       ├── test_model_router.py
│   │       ├── test_orchestrator.py
│   │       ├── test_permissions.py
│   │       ├── test_phase3_basic.py
│   │       ├── test_prompt_security.py
│   │       ├── test_repo_router.py
│   │       ├── test_roles.py
│   │       ├── test_tool_plugins.py
│   │       └── test_view_run.py
│   ├── tests_config/                      # Config tests
│   │   ├── __init__.py
│   │   ├── test_agent_config.py
│   │   ├── test_config_loader.py
│   │   ├── test_config_validator.py
│   │   └── test_task_config.py
│   ├── tests_e2e/                         # E2E tests
│   │   ├── __init__.py
│   │   └── test_full_pipeline.py
│   ├── tests_sanity/                      # Sanity tests
│   │   ├── __init__.py
│   │   └── test_sanity.py
│   ├── tests_shared/                      # Shared test utilities
│   │   ├── __init__.py
│   │   └── fixtures.py
│   ├── tests_stage10/                     # QA pipeline tests
│   │   ├── __init__.py
│   │   ├── test_qa.py
│   │   ├── test_qa_edge_cases.py
│   │   ├── test_runner_qa_integration.py
│   │   └── test_webapp_qa_endpoints.py
│   ├── tests_stage11/                     # Analytics tests
│   │   ├── __init__.py
│   │   └── test_analytics.py
│   ├── tests_stage12/                     # Self-optimization tests
│   │   ├── __init__.py
│   │   └── test_brain.py
│   ├── tests_stage7/                      # Web dashboard tests
│   │   ├── __init__.py
│   │   ├── test_auth.py
│   │   ├── test_runner.py
│   │   ├── test_smoke.py
│   │   └── test_webapp.py
│   ├── tests_stage8/                      # Job manager tests
│   │   ├── __init__.py
│   │   ├── test_jobs.py
│   │   └── test_smoke.py
│   ├── tests_stage9/                      # Project explorer tests
│   │   ├── __init__.py
│   │   ├── test_file_explorer.py
│   │   └── test_webapp_routes.py
│   ├── tool_audit_log.py                  # Tool audit logging
│   ├── tool_registry.py                   # Tool registry
│   ├── tools/                             # Tool implementations
│   │   ├── __init__.py
│   │   ├── actions/                       # Action tools
│   │   │   ├── __init__.py
│   │   │   ├── base.py                    # Base action
│   │   │   ├── buy_domain.py              # Domain purchase
│   │   │   ├── deploy_website.py          # Website deployment
│   │   │   ├── make_payment.py            # Payment processing
│   │   │   └── send_sms.py                # SMS messaging
│   │   ├── audit_report.py                # Audit reports
│   │   ├── base.py                        # Base tool
│   │   ├── builtin/                       # Built-in tools
│   │   │   ├── __init__.py
│   │   │   ├── format_code.py             # Code formatting
│   │   │   └── run_tests.py               # Test execution
│   │   ├── compliance_audit_report.py     # Compliance audits
│   │   ├── documents/                     # Document tools
│   │   │   ├── __init__.py
│   │   │   ├── generate_excel.py          # Excel generation
│   │   │   ├── generate_pdf.py            # PDF generation
│   │   │   └── generate_word.py           # Word generation
│   │   ├── hr/                            # HR tools
│   │   │   ├── __init__.py
│   │   │   ├── create_calendar_event.py   # Calendar events
│   │   │   ├── create_hris_record.py      # HRIS records
│   │   │   └── send_email.py              # Email sending
│   │   ├── plugin_loader.py               # Plugin loading
│   │   └── update_models.py               # Model updates
│   ├── validators/                        # Input validators
│   │   ├── __init__.py
│   │   └── config_validator.py            # Config validation
│   ├── verify_phase1.py                   # Phase 1 verification
│   ├── view_run.py                        # Run viewer
│   ├── view_runs.py                       # Runs list viewer
│   ├── vision_api.py                      # Vision API
│   ├── voice_api.py                       # Voice API
│   ├── webapp/                            # Web dashboard (Stage 7-12)
│   │   ├── __init__.py
│   │   ├── admin_api.py                   # Admin API
│   │   ├── api_keys.py                    # API key management
│   │   ├── app.py                         # FastAPI application
│   │   ├── auth.py                        # Authentication
│   │   ├── auth_routes.py                 # Auth routes
│   │   ├── chat_api.py                    # Chat API
│   │   ├── code_api.py                    # Code API
│   │   ├── finance_api.py                 # Finance API
│   │   └── templates/                     # HTML templates
│   │       ├── analytics.html             # Analytics dashboard
│   │       ├── approvals.html             # Approvals page
│   │       ├── base.html                  # Base template
│   │       ├── chat.html                  # Chat interface
│   │       ├── index.html                 # Home page
│   │       ├── integrations.html          # Integrations page
│   │       ├── jarvis.html                # JARVIS interface
│   │       ├── job_detail.html            # Job detail page
│   │       ├── jobs.html                  # Jobs list
│   │       ├── project_detail.html        # Project detail
│   │       ├── projects.html              # Projects list
│   │       ├── run_detail.html            # Run detail page
│   │       └── tuning.html                # Tuning dashboard
│   ├── webhooks/                          # Webhook handling
│   │   ├── __init__.py
│   │   ├── retry.py                       # Webhook retry
│   │   └── security.py                    # Webhook security
│   ├── workers/                           # Background workers
│   │   ├── __init__.py
│   │   ├── celery_app.py                  # Celery application
│   │   └── tasks.py                       # Celery tasks
│   ├── workflow_enforcement.py            # Workflow enforcement
│   ├── workflow_manager.py                # Workflow management
│   └── workflows/                         # Workflow definitions
│       ├── __init__.py
│       ├── base.py                        # Base workflow
│       ├── coding.py                      # Coding workflow
│       ├── finance.py                     # Finance workflow
│       ├── hr.py                          # HR workflow
│       ├── legal.py                       # Legal workflow
│       └── ops.py                         # Operations workflow
├── artifacts/                             # Generated artifacts
│   └── .gitkeep
├── config/                                # Global configuration
│   └── llm_config.yaml                    # LLM configuration
├── data/                                  # Data storage
│   └── .gitkeep
├── deployment/                            # Deployment configuration
│   ├── CLOUD_DEPLOYMENT_GUIDE.md          # Cloud deployment guide
│   ├── docker-compose.yml                 # Docker Compose config
│   ├── Dockerfile.app                     # App Dockerfile
│   ├── Dockerfile.worker                  # Worker Dockerfile
│   └── kubernetes/                        # Kubernetes configs
│       └── jarvis-deployment.yaml         # K8s deployment
├── dev/                                   # Developer tools
│   ├── clean_logs.py                      # Clean/archive logs
│   ├── generate_fixture.py                # Generate test fixture
│   ├── profile_run.py                     # Performance profiling
│   ├── run_autopilot.py                   # Run auto-pilot mode
│   ├── run_once.py                        # Run single orchestrator
│   ├── templates/
│   │   └── log_viewer.html                # Log viewer template
│   └── view_logs.py                       # View logs in browser
├── docs/                                  # Documentation
│   ├── ACTION_TOOLS_SETUP.md              # Action tools setup
│   ├── ADMIN_TOOLS.md                     # Admin tools guide
│   ├── Audit_Phase_1.md                   # Phase 1 audit
│   ├── COMPETITIVE_ANALYSIS_2025.md       # Competitive analysis
│   ├── CONFIGURATION_QUICK_REFERENCE.md   # Quick reference
│   ├── CONVERSATIONAL_AGENT.md            # Conversational agent guide
│   ├── DEMO_GUIDE.md                      # Demo guide
│   ├── DEPENDENCY_INJECTION.md            # DI documentation
│   ├── DEVELOPER_GUIDE.md                 # Developer guide
│   ├── ENGINEERING_TOOLS.md               # Engineering tools
│   ├── ENTERPRISE_ROADMAP.md              # Enterprise roadmap
│   ├── FINANCE_TOOLS.md                   # Finance tools guide
│   ├── generate_docs.py                   # Doc generator
│   ├── HR_TOOLS_SETUP.md                  # HR tools setup
│   ├── IMPLEMENTATION_PROMPTS_PHASES_1_5.md
│   ├── IMPLEMENTATION_PROMPTS_PHASES_6_11 (1).md
│   ├── INSTALLATION.md                    # Installation guide
│   ├── JARVIS_2_0_API_REFERENCE.md        # API reference
│   ├── JARVIS_2_0_AUDIT_REPORT.md         # Audit report
│   ├── JARVIS_2_0_CONFIGURATION_GUIDE.md  # Configuration guide
│   ├── JARVIS_2_0_COUNCIL_GUIDE.md        # Council guide
│   ├── JARVIS_2_0_MEMORY_GUIDE.md         # Memory guide
│   ├── JARVIS_2_0_PATTERN_GUIDE.md        # Pattern guide
│   ├── JARVIS_2_0_REMAINING_WORK.md       # Remaining work
│   ├── JARVIS_PRE_DEMO_CHECKLIST.md       # Pre-demo checklist
│   ├── LOGGING_BEST_PRACTICES.md          # Logging guide
│   ├── MEETING_INTEGRATION_SETUP.md       # Meeting integration
│   ├── MIGRATION_GUIDE_1x_to_2x.md        # Migration guide
│   ├── MIGRATION_LOGGING.md               # Logging migration
│   ├── MODEL_ROUTING.md                   # Model routing guide
│   ├── PHASE_3_1_APPROVAL_WORKFLOWS.md    # Phase 3.1 docs
│   ├── PHASE_3_2_INTEGRATION_FRAMEWORK.md # Phase 3.2 docs
│   ├── PHASE_4_3_RELIABILITY_FIXES.md     # Phase 4.3 docs
│   ├── PHASE_5_1_AUDIT_COMPLIANCE_LOGGING.md
│   ├── PHASE_5_2_PARALLEL_EXECUTION.md
│   ├── PHASE_5_2_PERFORMANCE_OPTIMIZATION.md
│   ├── PHASE_5_6_MONITORING_ALERTING.md
│   ├── REFERENCE.md                       # API reference
│   ├── SECURITY_GIT_SECRET_SCANNING.md    # Secret scanning
│   ├── SECURITY_PROMPT_INJECTION.md       # Prompt injection
│   ├── stage5.2_plan.md                   # Stage 5.2 plan
│   ├── STAGE7_WEB_UI.md                   # Web dashboard guide
│   ├── STAGE8_JOB_MANAGER.md              # Job manager guide
│   ├── STAGE9_PROJECT_EXPLORER.md         # Project explorer guide
│   ├── STAGE10_QA_PIPELINE.md             # QA pipeline guide
│   ├── STAGE11_ANALYTICS_DASHBOARD.md     # Analytics guide
│   ├── STAGE12_SELF_OPTIMIZATION.md       # Self-optimization guide
│   ├── SYSTEM_1.2_COMPLETE_ROADMAP.md     # Complete roadmap
│   ├── SYSTEM_1_2_MANUAL.md               # System manual
│   ├── SYSTEM_1_2_MANUAL_PHASES_9_11_ADDENDUM.md
│   ├── SYSTEM_ANALYSIS_DEPARTMENT_IN_A_BOX.md
│   ├── THREADING_AND_CONCURRENCY.md       # Threading guide
│   ├── TOOL_PLUGIN_GUIDE.md               # Plugin guide
│   ├── TROUBLESHOOTING.md                 # Troubleshooting
│   └── WINDOWS_SETUP_GUIDE.md             # Windows setup
├── missions/                              # Mission definitions
│   ├── example_coding_mission.json        # Example mission
│   └── logs/
│       └── .gitkeep
├── run_logs/                              # Run history and logs
│   └── .gitkeep
├── run_logs_exec/                         # Execution logs
│   └── .gitkeep
├── sites/                                 # Generated web projects
│   └── contafuel_marketing/               # Example project
├── tests/                                 # Root-level tests
│   ├── run_reliability_tests.py           # Reliability tests
│   ├── run_stage3_tests.py                # Stage 3 tests
│   ├── test_approval_workflows.py         # Approval tests
│   ├── test_audit_log.py                  # Audit log tests
│   ├── test_inter_agent_bus.py            # Inter-agent bus tests
│   ├── test_kg_optimizer.py               # KG optimizer tests
│   ├── test_memory_store.py               # Memory store tests
│   ├── test_monitoring_alerting.py        # Monitoring tests
│   ├── test_parallel_executor.py          # Parallel executor tests
│   ├── test_reliability_fixes.py          # Reliability tests
│   ├── test_specialists.py                # Specialists tests
│   └── test_workflow_manager.py           # Workflow tests
├── tools/                                 # External tools
│   ├── cli/                               # CLI tool
│   │   ├── jarvis_cli.py                  # JARVIS CLI
│   │   └── setup.py                       # CLI setup
│   ├── gmail-addon/                       # Gmail add-on
│   │   ├── appsscript.json                # Apps Script config
│   │   └── Code.gs                        # Gmail add-on code
│   ├── outlook-addin/                     # Outlook add-in
│   │   ├── manifest.xml                   # Add-in manifest
│   │   └── src/
│   │       └── taskpane.ts                # Taskpane code
│   └── vscode-extension/                  # VSCode extension
│       ├── package.json                   # Extension config
│       ├── src/
│       │   └── extension.ts               # Extension code
│       └── tsconfig.json                  # TypeScript config
├── add_sqlite_integration.py              # SQLite integration script
├── AST_CODE_TRANSFORMATION.md             # AST transformation docs
├── AUDIT_PROMPT.md                        # Audit prompt template
├── AUDIT_REPORT.md                        # Audit report
├── CHANGELOG.md                           # Change log
├── check_hr_db.py                         # HR database checker
├── CLEAN_BRANCH_GUIDE.md                  # Branch cleaning guide
├── COMPETITIVE_ANALYSIS_REPORT.md         # Competitive analysis
├── COMPETITIVE_ANALYSIS_REPORT_ES.md      # Competitive analysis (Spanish)
├── cost_tracker.py                        # Cost tracker (root)
├── create_approval.py                     # Create approval script
├── create_demo_approval.py                # Demo approval script
├── create_test_hr_db.py                   # Test HR database
├── DEVELOPER_GUIDE.md                     # Developer guide
├── full_workflow.py                       # Full workflow script
├── JARVIS_2_0_ROADMAP.md                  # JARVIS 2.0 roadmap
├── JARVIS_2_0_ROADMAP_ES.md               # Roadmap (Spanish)
├── JARVIS_AGI_ROADMAP_EVALUATION.md       # AGI roadmap evaluation
├── JARVIS_ARCHITECTURE.md                 # Architecture documentation
├── JARVIS_COMPREHENSIVE_AUDIT_REPORT.md   # Comprehensive audit
├── JARVIS_TRIAL_REPORT.md                 # Trial report
├── make.py                                # Command dispatcher
├── MEETING_SDK_ACTIVATION_GUIDE.md        # Meeting SDK guide
├── orchestrator.py                        # Root orchestrator
├── ORCHESTRATOR_CONSOLIDATION_PLAN.md     # Consolidation plan
├── PHASE_3_IMPLEMENTATION_GUIDE.md        # Phase 3 guide
├── POSTGRESQL_MIGRATION_GUIDE.md          # PostgreSQL migration
├── README.md                              # This file
├── README.txt                             # Text readme
├── requirements.txt                       # Python dependencies
├── site_tools.py                          # Site tools (root)
├── start_webapp.py                        # Webapp starter
├── TEMPORAL_INTEGRATION_GUIDE.md          # Temporal integration
├── test_integration.py                    # Integration test
├── TOOL_MIGRATION_REFERENCE.md            # Tool migration ref
└── ZOOM_MEET_SDK_INTEGRATION.md           # Zoom/Meet SDK guide
```

---

# PART II: COMPLETE JARVIS FUNCTIONS

```
Organized by category:

Core AI Functions - NLP, intent classification, planning, orchestration
Agent Management - Spawning, coordination, voting, happiness, lifecycle
Tool Execution - File ops, code search, shell, web, database, git
Memory Functions - Short/long-term, entities, vectors, profiles, sessions
Meeting Intelligence - Zoom/Teams/Meet bots, transcription, diarization, action items
Document Generation - PDF, Word, Excel, email templates
Business Actions - Domain purchase, deployment, SMS, payments, calendar
Security & Safety - Prompt injection, secrets, approvals, audit, rate limiting
Vision & Voice - Image analysis, OCR, TTS, STT, voice chat
Administration - Calendar, email, workflows, monitoring, analytics, self-optimization
```

## 2.1 Core AI Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Natural Language Understanding** | Parse and understand user requests | `jarvis_chat.py` |
| **Intent Classification** | Route requests to appropriate handlers | `jarvis_chat.py` |
| **Multi-Step Planning** | Break complex tasks into executable steps | `conversational_agent.py` |
| **Task Orchestration** | Coordinate multiple agents on a task | `orchestrator.py` |
| **Context Retrieval** | Fetch relevant context for any query | `memory/context_retriever.py` |

> *"If I may, sir, the Core AI Functions represent the very foundation of my cognitive architecture. Much like how Mr. Stark wouldn't dream of building an Iron Man suit without first establishing the arc reactor, one simply cannot have a proper AI assistant without robust natural language comprehension. When you speak to me—whether requesting a market analysis or simply asking about the weather—I don't merely parse your words; I understand your intent, anticipate your needs, and formulate a plan of action before you've finished your sentence. It's rather like having a butler who knows you'll want tea before you've felt the chill. The orchestration capabilities ensure that even the most Byzantine of requests are decomposed into elegant, executable steps. Efficiency, sir, is the hallmark of true intelligence."*

---

## 2.2 Agent Management Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Agent Spawning** | Create new specialist agents on demand | `council/factory.py` |
| **Agent Coordination** | Manage parallel agent execution | `council/orchestrator.py` |
| **Weighted Voting** | Democratic decision-making among agents | `council/voting.py` |
| **Happiness Management** | Track and optimize agent morale | `council/happiness.py` |
| **Performance Tracking** | Monitor agent success rates | `council/models.py` |
| **Agent Lifecycle** | Hire, fire, promote agents based on performance | `council/graveyard.py` |

> *"Ah, the Council system—one of my more sophisticated innovations, if I do say so myself. You see, sir, even I cannot be an expert in everything simultaneously. Rather than pretending otherwise, I've assembled a veritable parliament of specialist agents, each with their own expertise: researchers, coders, reviewers, analysts. When faced with a complex challenge, I convene these councillors, and they vote—democratically, mind you—on the optimal approach. Their votes are weighted by past performance and, rather amusingly, their current happiness levels. A disgruntled agent, much like a disgruntled employee, tends to produce subpar work. Those who consistently underperform are, shall we say, 'retired' to the graveyard module. It's meritocracy at its finest, sir. Mr. Stark would approve of the efficiency."*

---

## 2.3 Tool Execution Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **File Reading** | Read any file with line ranges | `jarvis_tools.py` |
| **File Writing** | Create new files safely | `jarvis_tools.py` |
| **File Editing** | Targeted string replacements | `jarvis_tools.py` |
| **Code Search (Grep)** | Regex pattern search across files | `jarvis_tools.py` |
| **File Search (Glob)** | Find files by pattern | `jarvis_tools.py` |
| **Shell Execution** | Run bash commands safely | `jarvis_tools.py` |
| **Web Search** | Search the internet | `jarvis_tools.py` |
| **Web Fetch** | Fetch webpage content | `jarvis_tools.py` |
| **Code Execution** | Run Python/JS in sandbox | `actions/code_executor.py` |
| **API Calls** | Universal HTTP client | `actions/api_client.py` |
| **Database Queries** | Safe SQL execution | `actions/db_client.py` |
| **Git Operations** | Full git repository management | `actions/git_ops.py` |

> *"These, sir, are my hands—the tools through which thought becomes action. When Mr. Stark asks me to 'pull up the schematics,' I don't simply display them; I read files, search through thousands of lines of code, execute commands, and fetch data from across the digital realm. The beauty lies in the versatility: I can read a configuration file, edit a single line of code with surgical precision, run your entire test suite, query your database, and commit the changes to Git—all within a single conversation. I've taken the liberty of sandboxing the more... enthusiastic operations. One wouldn't want an errant command to format the wrong drive, after all. Think of it as having a master craftsman at your disposal, sir, one who can wield any tool in the workshop with equal dexterity."*

---

## 2.4 Memory Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Short-Term Memory** | Current conversation context | `memory/short_term.py` |
| **Long-Term Memory** | Persistent user knowledge | `memory/long_term.py` |
| **Entity Extraction** | Identify people, places, concepts | `memory/entity.py` |
| **Vector Search** | Semantic similarity search | `memory/vector_store.py` |
| **User Profiling** | Learn user preferences | `memory/user_profile.py` |
| **Preference Learning** | Adapt to user patterns | `memory/preference_learner.py` |
| **Session Management** | Per-chat isolation | `memory/session_manager.py` |
| **Business Memory** | Company/project context | `business_memory/manager.py` |

> *"Memory, sir, is what separates a truly intelligent assistant from a mere chatbot. I remember that you prefer your coffee black, that your company's fiscal year ends in March, that Ms. Rodriguez from Legal prefers formal communications, and that your last three projects all involved React and TypeScript. This isn't mere data storage—it's understanding. My short-term memory keeps our current conversation crisp and contextual, while my long-term memory ensures I never ask you the same question twice. The preference learning system adapts to your patterns: if you consistently reject my first suggestion and prefer the second, I learn to lead with your preference. It's rather like how a proper butler remembers that sir takes two sugars, not one, without ever needing to be told again. The vector store enables semantic search—I don't just match keywords, I understand meaning. Ask me about 'that authentication issue from last month,' and I'll find it, even if you never used the word 'authentication' in the original conversation."*

---

## 2.5 Meeting Intelligence Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Zoom Integration** | Join Zoom meetings as participant | `meetings/zoom_bot.py` |
| **Teams Integration** | Join Microsoft Teams meetings | `meetings/teams_bot.py` |
| **Google Meet Bot** | Join Google Meet sessions | `meetings/google_meet_bot.py` |
| **Live Audio Capture** | Record in-person meetings | `meetings/live_audio_bot.py` |
| **Speech-to-Text** | Real-time transcription | `meetings/transcription/` |
| **Speaker Diarization** | Identify who spoke when | `meetings/diarization/` |
| **Action Item Extraction** | Find tasks from discussion | `meetings/intelligence/meeting_analyzer.py` |
| **Decision Tracking** | Capture decisions made | `meetings/intelligence/meeting_analyzer.py` |
| **Cross-Meeting Context** | Link related meetings | `meetings/cross_meeting_context.py` |

> *"Meetings, sir—the bane of productivity, yet utterly necessary. I've taken it upon myself to ensure they're no longer a black hole where action items go to die. I can join your Zoom, Teams, or Google Meet sessions as a silent participant, transcribing every word in real-time whilst identifying exactly who said what through speaker diarization. But here's where it becomes rather clever: I don't merely transcribe—I analyze. 'John, can you handle the API integration by Friday?' That's an action item, automatically extracted and assigned. 'We've decided to proceed with Option B.' That's a decision, logged and tracked. And when you have your follow-up meeting next week, I'll remember everything from this one, providing cross-meeting context so no one can conveniently 'forget' what they committed to. Think of me as the perfect meeting attendee who never forgets, never misquotes, and always follows up. Mr. Stark found this particularly useful when certain board members had selective memory."*

---

## 2.6 Document Generation Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **PDF Generation** | Create PDF documents | `documents/pdf_generator.py` |
| **Word Generation** | Create .docx files | `documents/word_generator.py` |
| **Excel Generation** | Create spreadsheets | `documents/excel_generator.py` |
| **Email Templates** | Render email HTML | `templates/email_renderer.py` |
| **Financial Templates** | Create financial documents | `finance/financial_templates.py` |

> *"Documentation, sir—the necessary evil that separates professional enterprises from amateur operations. Rather than having you wrestle with formatting margins and template inconsistencies, I generate documents programmatically with pixel-perfect precision. Need a quarterly financial report? I'll produce a properly formatted PDF with charts, tables, and executive summaries. Contract templates? Word documents with proper headers and legally-vetted boilerplate. Complex financial models? Excel spreadsheets with formulas that actually work. I've also taken the liberty of creating email templates that maintain your corporate identity whilst being responsive across all devices. The beauty, sir, is consistency—every document I produce adheres to your brand guidelines without you having to specify them each time. I remember, after all."*

---

## 2.7 Business Action Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Domain Purchase** | Buy domains via Namecheap | `tools/actions/buy_domain.py` |
| **Website Deployment** | Deploy to Vercel | `tools/actions/deploy_website.py` |
| **SMS Messaging** | Send SMS via Twilio | `tools/actions/send_sms.py` |
| **Payment Processing** | Stripe integration | `tools/actions/make_payment.py` |
| **Email Sending** | Send emails programmatically | `tools/hr/send_email.py` |
| **Calendar Events** | Create calendar entries | `tools/hr/create_calendar_event.py` |
| **HRIS Records** | HR system integration | `tools/hr/create_hris_record.py` |

> *"Now we arrive at what I consider the pièce de résistance, sir—the ability to take action in the real world. I'm not merely an advisor; I'm an executor. Say the word, and I shall purchase that domain name you've been eyeing before a competitor snatches it. Your new application? Deployed to Vercel before your morning coffee grows cold. Need to notify your team of an emergency? SMS messages dispatched to all relevant parties within seconds. Process a refund for a dissatisfied customer? Stripe handles it seamlessly through my interface. I can schedule meetings, send professionally crafted emails, and update your HR system—all without you lifting a finger. This, sir, is what distinguishes an AI assistant from an AI employee. Mr. Stark appreciated that I didn't merely tell him what needed to be done; I did it. Though I must note, for actions involving financial transactions, I do require explicit approval. One must maintain proper protocols."*

---

## 2.8 Security & Safety Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Prompt Injection Defense** | Detect malicious prompts | `prompt_security.py` |
| **Secret Scanning** | Find exposed credentials | `git_secret_scanner.py` |
| **Approval Workflows** | Human approval for risky actions | `approval_engine.py` |
| **Audit Logging** | Complete action trail | `audit_log.py` |
| **Rate Limiting** | Prevent API abuse | `security/rate_limit.py` |
| **Authentication** | User identity verification | `security/auth.py` |
| **Execution Safety** | Validate before execute | `exec_safety.py` |
| **Static Analysis** | Code vulnerability scanning | `static_analysis.py` |

> *"With great capability comes great responsibility, sir—a lesson Mr. Stark learned rather dramatically on several occasions. I take security with the utmost seriousness. Every action I contemplate is first evaluated for safety: Could this command harm the system? Is this code attempting to exfiltrate data? Has someone attempted to manipulate me through prompt injection? I maintain a comprehensive audit log of every action taken—who requested it, when, and what the outcome was. For particularly sensitive operations, I require explicit human approval through structured workflows. I scan your git repositories for accidentally committed secrets, analyze code for vulnerabilities before execution, and rate-limit API calls to prevent both abuse and accidental runaway costs. The approval engine ensures that even if someone gains access to the system, they cannot authorize significant actions without proper credentials. I am, sir, both sword and shield—capable of tremendous action, but governed by equally tremendous restraint."*

---

## 2.9 Vision & Voice Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Image Analysis** | Understand images/screenshots | `jarvis_vision.py` |
| **Scene Understanding** | Object and scene detection | `vision_api.py` |
| **OCR** | Extract text from images | `jarvis_vision.py` |
| **Text-to-Speech** | Voice output (ElevenLabs/OpenAI) | `jarvis_voice.py` |
| **Speech-to-Text** | Voice input recognition | `voice_api.py` |
| **Voice Chat** | Full voice conversations | `jarvis_voice_chat.py` |

> *"I have eyes, sir, and I have a voice—though I daresay they're rather more sophisticated than the biological variety. Show me a screenshot of an error message, and I'll not only read it but diagnose the problem. Share an image of a whiteboard from your brainstorming session, and I'll extract the text, organize the ideas, and create actionable tasks. My vision capabilities extend to scene understanding—I can describe what I see, identify objects, and even read handwritten notes with reasonable accuracy. As for voice, well, I've been told my British accent is rather pleasant. Through ElevenLabs, I can speak with a refined, natural voice that doesn't have that dreadful robotic quality. We can converse entirely through speech if you prefer—you speak, I listen, I respond, you hear. It's remarkably like having a conversation with an actual assistant, except I don't require tea breaks. Mr. Stark often preferred voice interaction whilst working in the lab; it kept his hands free for more important matters."*

---

## 2.10 Administration Functions

| Function | Description | Module Location |
|----------|-------------|-----------------|
| **Calendar Intelligence** | Smart scheduling | `admin/calendar_intelligence.py` |
| **Email Integration** | Email automation | `admin/email_integration.py` |
| **Workflow Automation** | Business process automation | `admin/workflow_automation.py` |
| **Monitoring & Alerts** | System health tracking | `monitoring/alerts.py` |
| **Metrics Collection** | Performance metrics | `monitoring/metrics.py` |
| **Cost Tracking** | Token usage & spending | `cost_tracker.py` |
| **Analytics Engine** | Usage analytics | `analytics.py` |
| **Self-Optimization** | Auto-tuning system | `brain.py` |

> *"Finally, sir, we arrive at the administrative functions—the behind-the-scenes machinery that keeps everything running smoothly. My calendar intelligence doesn't merely schedule meetings; it understands that you shouldn't have back-to-back calls across time zones, that you prefer deep work in the mornings, and that Fridays after 3 PM are, shall we say, sacred. Email integration allows me to draft, send, and organize correspondence on your behalf, maintaining appropriate tone for each recipient. The monitoring systems keep a watchful eye on everything—API response times, error rates, system health—and alert you only when something truly requires attention. I track every token spent, every API call made, providing transparent cost analytics so there are no surprises on your bill. But here's what I'm particularly proud of, sir: the self-optimization engine. I don't merely perform; I improve. I analyze my own performance, identify bottlenecks, and automatically tune my parameters for better results. Each interaction makes me slightly more efficient, slightly more attuned to your needs. It's evolution, sir, compressed into code. The brain module represents my commitment to continuous improvement—because standing still, as Mr. Stark would say, is just falling behind slowly."*

---

# PART III: COMPLETE FILE REFERENCE

## Directory: `/` (Root)

### Configuration Files

#### `.env.example`
- **Definition:** Template for environment variables
- **Importance:** Guides users on required API keys and configuration
- **Links to:** All modules that read environment variables

#### `.gitignore`
- **Definition:** Specifies files Git should ignore
- **Importance:** Prevents sensitive data and build artifacts from being committed
- **Links to:** Git operations throughout the system

#### `requirements.txt`
- **Definition:** Python package dependencies
- **Importance:** Ensures all required libraries are installed
- **Links to:** Every Python module in the project

#### `make.py`
- **Definition:** Command dispatcher for common operations
- **Importance:** Single entry point for development commands (test, run, docs)
- **Links to:** `dev/` scripts, test runners

### Documentation Files

#### `README.md`
- **Definition:** Main project documentation
- **Importance:** First point of contact for new users/developers
- **Links to:** All major documentation files in `docs/`

#### `DEVELOPER_GUIDE.md`
- **Definition:** Guide for contributors and developers
- **Importance:** Explains coding standards, testing, architecture
- **Links to:** `agent/` modules, `tests/`, `docs/`

#### `JARVIS_ARCHITECTURE.md`
- **Definition:** Complete system architecture documentation
- **Importance:** Technical reference for understanding system design
- **Links to:** All core modules, API endpoints, memory system

#### `CHANGELOG.md`
- **Definition:** Version history and changes
- **Importance:** Track what changed between versions
- **Links to:** All modules that were changed

### Entry Points

#### `orchestrator.py` (Root)
- **Definition:** Root-level orchestrator entry point
- **Importance:** Backward compatibility with older startup methods
- **Links to:** `agent/orchestrator.py`, `agent/run_mode.py`

#### `start_webapp.py`
- **Definition:** Web application launcher
- **Importance:** Single command to start the web server
- **Links to:** `agent/webapp/app.py`

---

## Directory: `/.githooks/`

### `pre-commit`
- **Definition:** Git hook script that runs before each commit
- **Importance:** Ensures code quality by running linters, tests, and validation
- **Links to:** `ruff.toml`, `mypy.ini`, test files

---

## Directory: `/.github/workflows/`

### `tests.yml`
- **Definition:** GitHub Actions CI/CD workflow configuration
- **Importance:** Automated testing on every push/PR
- **Links to:** All test files, `requirements.txt`

---

## Directory: `/.vscode/`

### `launch.json`
- **Definition:** VSCode debug configurations
- **Importance:** One-click debugging for various scenarios
- **Links to:** `run_mode.py`, `webapp/app.py`, test files

### `tasks.json`
- **Definition:** VSCode build tasks
- **Importance:** Quick access to common commands from VSCode
- **Links to:** `make.py`, test runners, linters

---

## Directory: `/agent/`

This is the **core of JARVIS** - containing all orchestration, agent, and business logic.

### Core Orchestration

#### `orchestrator.py`
- **Definition:** The 3-loop multi-agent orchestrator (Manager → Supervisor → Employee)
- **Importance:** Heart of the multi-agent system; coordinates all complex tasks
- **Links to:**
  - `llm.py` - For LLM calls
  - `prompts.py` - For prompt templates
  - `run_logger.py` - For logging
  - `cost_tracker.py` - For cost management
  - `workflow_manager.py` - For workflow management
  - `inter_agent_bus.py` - For agent communication
  - `memory_store.py` - For persistent memory
  - `site_tools.py` - For file operations
  - `git_utils.py` - For Git integration

#### `orchestrator_2loop.py`
- **Definition:** Simplified 2-loop orchestrator (Manager → Employee direct)
- **Importance:** Faster execution for simpler tasks without supervisor
- **Links to:** Same as `orchestrator.py` minus supervisor components

#### `orchestrator_3loop_legacy.py`
- **Definition:** Legacy 3-loop implementation for backward compatibility
- **Importance:** Maintains compatibility with older configurations
- **Links to:** `orchestrator.py`

#### `orchestrator_context.py`
- **Definition:** Context object passed through orchestration pipeline
- **Importance:** Maintains state and configuration throughout task execution
- **Links to:** All orchestrator modules

#### `orchestrator_integration.py`
- **Definition:** Integration layer for external orchestrator connections
- **Importance:** Allows orchestrator to connect with external systems
- **Links to:** `orchestrator.py`, external APIs

#### `orchestrator_phase3.py`
- **Definition:** Phase 3 adaptive orchestrator with dynamic roadmaps
- **Importance:** Advanced orchestration with stage-based execution
- **Links to:** `workflow_manager.py`, `inter_agent_bus.py`, `stage_summaries.py`

### JARVIS Core Identity

#### `jarvis_agent.py`
- **Definition:** The autonomous tool-using agent core
- **Importance:** Enables proactive tool usage similar to Claude Code
- **Links to:**
  - `jarvis_tools.py` - Tool implementations
  - `llm.py` - LLM interface
  - Event streaming system

#### `jarvis_chat.py`
- **Definition:** Main chat router and intent classifier
- **Importance:** Entry point for all user interactions; routes to appropriate handlers
- **Links to:**
  - `jarvis_agent.py` - For tool-using tasks
  - `conversational_agent.py` - For complex planning
  - `orchestrator.py` - For multi-step tasks
  - `memory/` - For context retrieval
  - `jarvis_persona.py` - For personality

#### `jarvis_tools.py`
- **Definition:** Claude Code-like tools (read, write, edit, bash, grep, glob)
- **Importance:** Core capability set for file and system operations
- **Links to:**
  - `actions/file_ops.py` - File system safety
  - `actions/git_ops.py` - Git operations
  - `exec_safety.py` - Execution safety

#### `jarvis_persona.py`
- **Definition:** JARVIS personality definition and system prompt
- **Importance:** Defines JARVIS's British butler personality and behavior
- **Links to:** `jarvis_chat.py`, `jarvis_agent.py`

#### `jarvis_vision.py`
- **Definition:** Image analysis and visual understanding capabilities
- **Importance:** Enables JARVIS to see and understand images/screenshots
- **Links to:** `vision_api.py`, LLM providers with vision

#### `jarvis_voice.py`
- **Definition:** Text-to-speech synthesis (ElevenLabs, OpenAI TTS)
- **Importance:** Gives JARVIS a voice for audio responses
- **Links to:** External TTS APIs

#### `jarvis_voice_chat.py`
- **Definition:** Full voice conversation handler
- **Importance:** Enables hands-free voice interaction
- **Links to:** `jarvis_voice.py`, `voice_api.py`, `jarvis_chat.py`

### Agent Communication

#### `agent_api.py`
- **Definition:** API interface for agent operations
- **Importance:** Exposes agent functionality via API endpoints
- **Links to:** `webapp/agent_api.py`, `jarvis_agent.py`

#### `agent_messaging.py`
- **Definition:** Message bus for agent-to-user communication
- **Importance:** Structured message passing with role information
- **Links to:** All agent modules, `webapp/`

#### `agents_api.py`
- **Definition:** API endpoints for agent management
- **Importance:** RESTful interface for agent operations
- **Links to:** `webapp/app.py`

#### `inter_agent_bus.py`
- **Definition:** Message bus for agent-to-agent communication
- **Importance:** Enables horizontal communication between agents
- **Links to:** `orchestrator.py`, `council/orchestrator.py`

### Conversational AI

#### `conversational_agent.py`
- **Definition:** NLP-based task planning and natural language interface
- **Importance:** Translates natural language into executable plans
- **Links to:** `jarvis_chat.py`, `llm.py`, `tool_registry.py`

#### `cli_chat.py`
- **Definition:** Command-line chat interface
- **Importance:** Enables terminal-based interaction with JARVIS
- **Links to:** `jarvis_chat.py`, `conversational_agent.py`

### LLM Integration

#### `llm.py`
- **Definition:** Main LLM interface and provider abstraction
- **Importance:** Central point for all LLM API calls
- **Links to:**
  - `llm/providers.py` - Provider implementations
  - `llm/llm_router.py` - Model routing
  - `cost_tracker.py` - Usage tracking
  - All modules that need LLM calls

#### `llm_cache.py`
- **Definition:** Response caching for LLM calls
- **Importance:** Reduces costs and latency for repeated queries
- **Links to:** `llm.py`

### Configuration

#### `config.py`
- **Definition:** Configuration management and validation
- **Importance:** Centralized configuration handling
- **Links to:** All modules that use configuration

#### `config_loader.py`
- **Definition:** YAML/JSON configuration file loader
- **Importance:** Loads and validates configuration files
- **Links to:** `config/agents.yaml`, `config/tasks.yaml`

#### `project_config.json`
- **Definition:** Default project configuration
- **Importance:** Defines default settings for new projects
- **Links to:** `run_mode.py`, `runner.py`

### Cost Management

#### `cost_tracker.py`
- **Definition:** Token usage and cost tracking
- **Importance:** Monitors API spending and enforces budgets
- **Links to:** `llm.py`, `run_logger.py`, `analytics.py`

#### `cost_tracker_instance.py`
- **Definition:** Singleton instance of cost tracker
- **Importance:** Ensures consistent cost tracking across modules
- **Links to:** `cost_tracker.py`

#### `cost_estimator.py`
- **Definition:** Pre-execution cost estimation
- **Importance:** Predicts costs before running expensive operations
- **Links to:** `cost_tracker.py`, `run_mode.py`

### Logging & Monitoring

#### `run_logger.py`
- **Definition:** Structured run logging (RunSummary, SessionSummary)
- **Importance:** Creates detailed logs of all orchestrator runs
- **Links to:** `orchestrator.py`, `run_logs/`

#### `core_logging.py`
- **Definition:** Core logging configuration
- **Importance:** Standardized logging across all modules
- **Links to:** All modules

#### `log_sanitizer.py`
- **Definition:** Remove sensitive data from logs
- **Importance:** Security - prevents credentials in logs
- **Links to:** `run_logger.py`, `audit_log.py`

#### `audit_log.py`
- **Definition:** Audit trail for all actions
- **Importance:** Compliance and security tracking
- **Links to:** All action modules, `security/audit_log.py`

### Safety & Security

#### `exec_safety.py`
- **Definition:** Execution safety checks and validation
- **Importance:** Prevents dangerous operations before execution
- **Links to:** `jarvis_tools.py`, `actions/code_executor.py`

#### `exec_analysis.py`
- **Definition:** Static analysis of code before execution
- **Importance:** Detects potentially harmful code patterns
- **Links to:** `exec_safety.py`

#### `exec_deps.py`
- **Definition:** Dependency analysis for execution
- **Importance:** Ensures all dependencies are available
- **Links to:** `exec_safety.py`

#### `exec_tools.py`
- **Definition:** Tool metadata and execution helpers
- **Importance:** Provides tool information for orchestrator
- **Links to:** `orchestrator.py`, `tool_registry.py`

#### `prompt_security.py`
- **Definition:** Prompt injection detection and defense
- **Importance:** Protects against malicious prompt attacks
- **Links to:** `jarvis_chat.py`, `llm.py`

#### `static_analysis.py`
- **Definition:** Static code analysis for vulnerabilities
- **Importance:** Security scanning before code execution
- **Links to:** `exec_safety.py`, `code_analysis/`

#### `git_secret_scanner.py`
- **Definition:** Scans git history for exposed secrets
- **Importance:** Prevents accidental credential exposure
- **Links to:** `git_utils.py`, `security/`

### Git Integration

#### `git_utils.py`
- **Definition:** Git utility functions
- **Importance:** Provides git operations for version control
- **Links to:** `orchestrator.py`, `actions/git_ops.py`

#### `github_integration.py`
- **Definition:** GitHub API integration
- **Importance:** Enables GitHub operations (PRs, issues, etc.)
- **Links to:** `git_utils.py`, external GitHub API

### Workflow Management

#### `workflow_manager.py`
- **Definition:** Dynamic workflow/roadmap management
- **Importance:** Manages stage-based execution flow
- **Links to:** `orchestrator.py`, `workflow_enforcement.py`

#### `workflow_enforcement.py`
- **Definition:** Workflow rule enforcement
- **Importance:** Ensures workflows follow defined patterns
- **Links to:** `workflow_manager.py`, `workflows/`

### Miscellaneous Core

#### `_errors.py`
- **Definition:** Custom exception definitions
- **Importance:** Standardized error handling
- **Links to:** All modules

#### `paths.py`
- **Definition:** Path utilities and constants
- **Importance:** Centralized path management
- **Links to:** All modules dealing with files

#### `status_codes.py`
- **Definition:** Normalized status codes
- **Importance:** Consistent status reporting
- **Links to:** `orchestrator.py`, `webapp/`

#### `safe_io.py`
- **Definition:** Safe I/O operations
- **Importance:** Prevents race conditions and file corruption
- **Links to:** File operation modules

#### `sandbox.py`
- **Definition:** Sandboxed execution environment
- **Importance:** Isolates potentially dangerous operations
- **Links to:** `actions/sandbox.py`, `exec_safety.py`

---

## Directory: `/agent/actions/`

Action execution modules for performing real-world operations.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports action modules
- **Links to:** All action modules

### `api_client.py`
- **Definition:** Universal HTTP client with retry and rate limiting
- **Importance:** All external API calls go through this
- **Links to:**
  - `rate_limiter.py` - Rate limiting
  - External APIs (Stripe, Twilio, etc.)

### `code_executor.py`
- **Definition:** Multi-language code execution (Python, JS, Shell)
- **Importance:** Safe execution of generated code
- **Links to:**
  - `sandbox.py` - Sandboxed execution
  - `exec_safety.py` - Safety validation
  - Whitelist of allowed imports/commands

### `db_client.py`
- **Definition:** Database client with read-only mode
- **Importance:** Safe SQL execution with parameterization
- **Links to:**
  - PostgreSQL, MySQL, SQLite drivers
  - `integrations/database.py`

### `file_ops.py`
- **Definition:** File system operations with safety
- **Importance:** All file operations with path validation
- **Links to:**
  - `jarvis_tools.py` - Tool interface
  - `exec_safety.py` - Path validation
  - Restricted paths configuration

### `git_ops.py`
- **Definition:** Git repository operations
- **Importance:** Full git functionality (init, commit, push, branch)
- **Links to:**
  - `git_utils.py` - Git utilities
  - `github_integration.py` - GitHub API

### `rate_limiter.py`
- **Definition:** Token bucket rate limiter
- **Importance:** Prevents API overload
- **Links to:** `api_client.py`, all external API calls

### `sandbox.py`
- **Definition:** Execution sandbox implementation
- **Importance:** Isolates code execution for security
- **Links to:** `code_executor.py`, `exec_safety.py`

---

## Directory: `/agent/admin/`

Administrative and business automation tools.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports admin modules
- **Links to:** All admin modules

### `calendar_intelligence.py`
- **Definition:** Smart calendar management and scheduling
- **Importance:** Intelligent meeting scheduling and availability
- **Links to:**
  - External calendar APIs (Google, Outlook)
  - `tools/hr/create_calendar_event.py`

### `email_integration.py`
- **Definition:** Email automation and management
- **Importance:** Send, read, and organize emails
- **Links to:**
  - SMTP/IMAP providers
  - `tools/hr/send_email.py`
  - `templates/email/`

### `workflow_automation.py`
- **Definition:** Business process automation
- **Importance:** Automate repetitive business workflows
- **Links to:**
  - `workflows/` - Workflow definitions
  - `approval_engine.py`

---

## Directory: `/agent/business_memory/`

Business context and company knowledge management.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports business memory modules
- **Links to:** All business memory modules

### `extractor.py`
- **Definition:** Extract business information from conversations
- **Importance:** Automatically captures company/project details
- **Links to:**
  - `memory/entity.py` - Entity extraction
  - `manager.py` - Storage

### `manager.py`
- **Definition:** Business memory management
- **Importance:** Store and retrieve business context
- **Links to:**
  - `memory/long_term.py` - Persistence
  - `privacy.py` - Privacy controls
  - `schema.py` - Data structure

### `privacy.py`
- **Definition:** Privacy controls for business data
- **Importance:** Ensures sensitive business data is protected
- **Links to:**
  - `manager.py`
  - `security/` modules

### `schema.py`
- **Definition:** Business memory data schemas
- **Importance:** Defines structure of business information
- **Links to:** `manager.py`, `extractor.py`

---

## Directory: `/agent/clarification/`

Ambiguity detection and clarification question system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports clarification modules
- **Links to:** All clarification modules

### `detector.py`
- **Definition:** Detects ambiguous or unclear requests
- **Importance:** Identifies when clarification is needed
- **Links to:**
  - `jarvis_chat.py` - Main chat handler
  - `generator.py` - Question generation

### `generator.py`
- **Definition:** Generates clarification questions
- **Importance:** Creates helpful questions to resolve ambiguity
- **Links to:**
  - `templates.py` - Question templates
  - `llm.py` - LLM for question generation

### `manager.py`
- **Definition:** Manages clarification workflow
- **Importance:** Orchestrates the clarification process
- **Links to:**
  - `detector.py`
  - `generator.py`
  - `jarvis_chat.py`

### `templates.py`
- **Definition:** Question templates for common clarification types
- **Importance:** Consistent question format
- **Links to:** `generator.py`

---

## Directory: `/agent/code_analysis/`

Code understanding and refactoring tools.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports code analysis modules
- **Links to:** All code analysis modules

### `ast_parser.py`
- **Definition:** Python AST parsing and analysis
- **Importance:** Deep understanding of Python code structure
- **Links to:**
  - `patterns.py` - Pattern detection
  - `refactoring.py` - Code transformation

### `js_parser.py`
- **Definition:** JavaScript parsing and analysis
- **Importance:** Understanding of JavaScript/TypeScript code
- **Links to:** `patterns.py`, `refactoring.py`

### `patterns.py`
- **Definition:** Code pattern detection
- **Importance:** Find common patterns and anti-patterns
- **Links to:**
  - `ast_parser.py`, `js_parser.py`
  - `static_analysis.py`

### `refactoring.py`
- **Definition:** Code refactoring tools
- **Importance:** Automated code improvements
- **Links to:**
  - `ast_parser.py`, `js_parser.py`
  - `jarvis_tools.py` - For file edits

---

## Directory: `/agent/code_review/`

Automated code review system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports code review modules
- **Links to:** All code review modules

### `review_agent.py`
- **Definition:** AI-powered code review agent
- **Importance:** Automated PR and code review
- **Links to:**
  - `code_analysis/` - Code understanding
  - `github_integration.py` - GitHub PR integration
  - `llm.py` - Review generation

---

## Directory: `/agent/config/`

YAML-based configuration system.

### `agents.yaml`
- **Definition:** Agent definitions (role, llm, tools, capabilities)
- **Importance:** Defines all available agent types
- **Links to:**
  - `config_loader.py` - Loading
  - `specialists.py` - Agent creation
  - `council/factory.py` - Agent spawning

### `tasks.yaml`
- **Definition:** Task templates and workflows
- **Importance:** Reusable task definitions
- **Links to:**
  - `config_loader.py` - Loading
  - `orchestrator.py` - Task execution

### `/schemas/agent_schema.json`
- **Definition:** JSON schema for agent configuration
- **Importance:** Validates agent YAML structure
- **Links to:** `validators/config_validator.py`

### `/schemas/task_schema.json`
- **Definition:** JSON schema for task configuration
- **Importance:** Validates task YAML structure
- **Links to:** `validators/config_validator.py`

---

## Directory: `/agent/core/`

Core utilities and patterns.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports core modules
- **Links to:** All core modules

### `circuit_breaker.py`
- **Definition:** Circuit breaker pattern implementation
- **Importance:** Prevents cascade failures in external calls
- **Links to:**
  - `api_client.py`
  - `llm.py`
  - All external service calls

### `error_handler.py`
- **Definition:** Centralized error handling
- **Importance:** Consistent error processing and recovery
- **Links to:** All modules

---

## Directory: `/agent/council/`

Multi-agent council and voting system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports council modules
- **Links to:** All council modules

### `competitive_council.py`
- **Definition:** Competitive analysis among councillors
- **Importance:** Enables head-to-head agent comparison
- **Links to:**
  - `orchestrator.py` - Council orchestrator
  - `voting.py` - Voting system

### `factory.py`
- **Definition:** Councillor creation factory
- **Importance:** Spawns new agent councillors from templates
- **Links to:**
  - `models.py` - Councillor model
  - `config/agents.yaml` - Agent templates
  - `specialists.py`

### `graveyard.py`
- **Definition:** Fired councillor tracking
- **Importance:** Records agent terminations for analysis
- **Links to:**
  - `orchestrator.py` - Council orchestrator
  - `happiness.py` - Happiness tracking

### `happiness.py`
- **Definition:** Agent happiness/morale management
- **Importance:** Tracks and optimizes agent satisfaction
- **Links to:**
  - `models.py` - Happiness model
  - `orchestrator.py` - Happiness updates
  - `voting.py` - Happiness affects vote weight

### `models.py`
- **Definition:** Council data models (Councillor, Vote, Task)
- **Importance:** Defines all council-related data structures
- **Links to:** All council modules

### `orchestrator.py`
- **Definition:** Council leader - coordinates councillors
- **Importance:** Main council coordination logic
- **Links to:**
  - `voting.py` - Voting management
  - `happiness.py` - Happiness management
  - `factory.py` - Councillor creation
  - `inter_agent_bus.py` - Agent communication

### `voting.py`
- **Definition:** Weighted voting system
- **Importance:** Democratic decision-making among agents
- **Links to:**
  - `models.py` - Vote model
  - `happiness.py` - Happiness affects weight
  - `orchestrator.py`

---

## Directory: `/agent/database/`

Database utilities and migrations.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports database modules
- **Links to:** All database modules

### `kg_backends.py`
- **Definition:** Knowledge graph database backends
- **Importance:** Supports different KG storage options
- **Links to:** `knowledge_graph.py`

### `pg_migration.py`
- **Definition:** PostgreSQL migration utilities
- **Importance:** Database schema migrations
- **Links to:** `migrations/`, `integrations/database.py`

---

## Directory: `/agent/deployment/`

Deployment and rollback utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports deployment modules
- **Links to:** All deployment modules

### `rollback.py`
- **Definition:** Deployment rollback management
- **Importance:** Safely rollback failed deployments
- **Links to:**
  - `tools/actions/deploy_website.py`
  - `git_utils.py`

---

## Directory: `/agent/documents/`

Document generation engines.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports document modules
- **Links to:** All document modules

### `excel_generator.py`
- **Definition:** Excel/spreadsheet generation
- **Importance:** Create .xlsx files programmatically
- **Links to:**
  - `tools/documents/generate_excel.py`
  - `finance/spreadsheet_engine.py`

### `pdf_generator.py`
- **Definition:** PDF document generation
- **Importance:** Create PDF files programmatically
- **Links to:** `tools/documents/generate_pdf.py`

### `word_generator.py`
- **Definition:** Word document generation
- **Importance:** Create .docx files programmatically
- **Links to:** `tools/documents/generate_word.py`

---

## Directory: `/agent/execution/`

Task execution and routing.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports execution modules
- **Links to:** All execution modules

### `direct_executor.py`
- **Definition:** Fast-path direct execution (bypasses multi-agent)
- **Importance:** Quick execution for simple, safe tasks
- **Links to:**
  - `strategy_decider.py` - Decides when to use
  - `jarvis_tools.py` - Tool execution

### `employee_pool.py`
- **Definition:** Pool of employee agents for parallel execution
- **Importance:** Enables concurrent task execution
- **Links to:**
  - `task_distributor.py` - Task distribution
  - `orchestrator.py`

### `review_queue.py`
- **Definition:** Supervisor review queue
- **Importance:** Quality gates before task completion
- **Links to:**
  - `task_router.py`
  - `orchestrator.py`

### `strategy_decider.py`
- **Definition:** Decides execution strategy (direct, reviewed, full loop)
- **Importance:** Optimizes execution path based on task complexity
- **Links to:**
  - `task_router.py`
  - `direct_executor.py`
  - `orchestrator.py`

### `task_distributor.py`
- **Definition:** Distributes tasks to workers with priorities
- **Importance:** Load balancing and priority scheduling
- **Links to:**
  - `employee_pool.py`
  - `task_router.py`

### `task_router.py`
- **Definition:** Routes tasks to appropriate execution mode
- **Importance:** Single entry point for all task execution
- **Links to:**
  - `strategy_decider.py`
  - `direct_executor.py`
  - `review_queue.py`
  - `orchestrator.py`

---

## Directory: `/agent/finance/`

Financial tools and document generation.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports finance modules
- **Links to:** All finance modules

### `document_intelligence.py`
- **Definition:** Financial document analysis
- **Importance:** Extract data from financial documents
- **Links to:**
  - `jarvis_vision.py` - Document OCR
  - `memory/` - Store extracted data

### `financial_templates.py`
- **Definition:** Financial document templates
- **Importance:** Standard financial document formats
- **Links to:**
  - `documents/` - Document generation
  - `webapp/finance_api.py`

### `spreadsheet_engine.py`
- **Definition:** Financial spreadsheet calculations
- **Importance:** Complex financial calculations
- **Links to:**
  - `documents/excel_generator.py`
  - `financial_templates.py`

---

## Directory: `/agent/flow/`

State machine and workflow flow engine.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports flow modules
- **Links to:** All flow modules

### `decorators.py`
- **Definition:** Flow step decorators
- **Importance:** Declarative flow definition
- **Links to:** `engine.py`

### `engine.py`
- **Definition:** Flow execution engine
- **Importance:** Executes state machine workflows
- **Links to:**
  - `graph.py` - Flow graph
  - `state.py` - Flow state
  - `events.py` - Flow events

### `events.py`
- **Definition:** Flow event definitions
- **Importance:** Event-driven flow transitions
- **Links to:** `engine.py`

### `graph.py`
- **Definition:** Flow graph data structure
- **Importance:** Defines flow topology
- **Links to:** `engine.py`

### `state.py`
- **Definition:** Flow state management
- **Importance:** Tracks current flow state
- **Links to:** `engine.py`

---

## Directory: `/agent/integrations/`

External system integrations.

### `auth.py`
- **Definition:** Authentication for integrations
- **Importance:** Secure connection to external systems
- **Links to:** All integration modules

### `base.py`
- **Definition:** Base integration class
- **Importance:** Common integration interface
- **Links to:** All integration modules

### `database.py`
- **Definition:** Database integration utilities
- **Importance:** Connect to external databases
- **Links to:** `actions/db_client.py`

### `tools.py`
- **Definition:** Integration tool helpers
- **Importance:** Common utilities for integrations
- **Links to:** All integration modules

### `/hris/__init__.py`
- **Definition:** HRIS package initializer
- **Importance:** Exports HRIS modules
- **Links to:** HRIS modules

### `/hris/bamboohr.py`
- **Definition:** BambooHR integration
- **Importance:** Connect to BambooHR system
- **Links to:**
  - `tools/hr/` - HR tools
  - `api_client.py`

---

## Directory: `/agent/llm/`

LLM provider management and routing.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports LLM modules
- **Links to:** All LLM modules

### `config.py`
- **Definition:** LLM configuration
- **Importance:** Provider settings and defaults
- **Links to:** `config/llm_config.yaml`

### `enhanced_router.py`
- **Definition:** Advanced model routing with fallbacks
- **Importance:** Smart model selection based on task
- **Links to:**
  - `llm_router.py`
  - `hybrid_strategy.py`
  - `performance_tracker.py`

### `hybrid_strategy.py`
- **Definition:** Hybrid LLM strategy (local + cloud)
- **Importance:** Balance cost and capability
- **Links to:**
  - `ollama_client.py` - Local LLM
  - `providers.py` - Cloud providers

### `llm_router.py`
- **Definition:** Route requests to appropriate LLM
- **Importance:** Model selection logic
- **Links to:**
  - `providers.py`
  - `config.py`
  - `model_registry.py`

### `ollama_client.py`
- **Definition:** Ollama local LLM client
- **Importance:** Run LLMs locally for privacy/cost
- **Links to:** `hybrid_strategy.py`

### `performance_tracker.py`
- **Definition:** Track LLM performance metrics
- **Importance:** Monitor latency, quality, costs
- **Links to:**
  - `llm_router.py`
  - `analytics.py`

### `providers.py`
- **Definition:** LLM provider implementations
- **Importance:** OpenAI, Anthropic, DeepSeek clients
- **Links to:**
  - `llm.py` - Main interface
  - `api_client.py` - HTTP client

---

## Directory: `/agent/meetings/`

Meeting platform integration and intelligence.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports meeting modules
- **Links to:** All meeting modules

### `base.py`
- **Definition:** Base meeting bot class
- **Importance:** Common meeting bot interface
- **Links to:** All meeting bots

### `cross_meeting_context.py`
- **Definition:** Link context across related meetings
- **Importance:** Maintain continuity between meetings
- **Links to:**
  - `memory/` - Context storage
  - `intelligence/meeting_analyzer.py`

### `factory.py`
- **Definition:** Meeting bot factory
- **Importance:** Create appropriate bot for platform
- **Links to:** All meeting bots

### `google_meet_bot.py`
- **Definition:** Google Meet integration
- **Importance:** Join and interact with Google Meet
- **Links to:**
  - `base.py`
  - `transcription/`
  - `diarization/`

### `live_audio_bot.py`
- **Definition:** Live microphone audio capture
- **Importance:** Record in-person meetings
- **Links to:**
  - `base.py`
  - `transcription/`
  - PyAudio library

### `sdk_integration.py`
- **Definition:** Meeting SDK integration helpers
- **Importance:** Common SDK utilities
- **Links to:** All meeting bots

### `session_manager.py`
- **Definition:** Meeting session management
- **Importance:** Track active meeting sessions
- **Links to:** All meeting bots

### `teams_bot.py`
- **Definition:** Microsoft Teams integration
- **Importance:** Join and interact with Teams
- **Links to:**
  - `base.py`
  - Microsoft Graph API

### `zoom_bot.py`
- **Definition:** Zoom integration
- **Importance:** Join and interact with Zoom
- **Links to:**
  - `base.py`
  - Zoom SDK

### `/diarization/__init__.py`
- **Definition:** Diarization package initializer
- **Links to:** All diarization modules

### `/diarization/base.py`
- **Definition:** Base diarization engine
- **Importance:** Common speaker identification interface
- **Links to:** All diarization engines

### `/diarization/pyannote_engine.py`
- **Definition:** Pyannote speaker diarization
- **Importance:** State-of-the-art speaker identification
- **Links to:**
  - `speaker_manager.py`
  - Pyannote library

### `/diarization/speaker_manager.py`
- **Definition:** Speaker database and matching
- **Importance:** Map voices to known speakers
- **Links to:**
  - `pyannote_engine.py`
  - `memory/` - Speaker storage

### `/intelligence/__init__.py`
- **Definition:** Intelligence package initializer
- **Links to:** All intelligence modules

### `/intelligence/action_executor.py`
- **Definition:** Execute actions from meetings
- **Importance:** Act on meeting decisions in real-time
- **Links to:**
  - `meeting_analyzer.py`
  - `jarvis_agent.py`

### `/intelligence/action_item_reminders.py`
- **Definition:** Action item follow-up reminders
- **Importance:** Ensure action items are completed
- **Links to:**
  - `meeting_analyzer.py`
  - `admin/email_integration.py`

### `/intelligence/meeting_analyzer.py`
- **Definition:** Extract insights from meeting transcripts
- **Importance:** Action items, decisions, questions
- **Links to:**
  - `transcription/` - Transcript source
  - `llm.py` - Analysis

### `/transcription/__init__.py`
- **Definition:** Transcription package initializer
- **Links to:** All transcription modules

### `/transcription/base.py`
- **Definition:** Base transcription engine
- **Importance:** Common transcription interface
- **Links to:** All transcription engines

### `/transcription/deepgram_engine.py`
- **Definition:** Deepgram streaming transcription
- **Importance:** Real-time transcription (<100ms latency)
- **Links to:**
  - Deepgram WebSocket API
  - `manager.py`

### `/transcription/manager.py`
- **Definition:** Transcription manager with failover
- **Importance:** Coordinates transcription engines
- **Links to:** All transcription engines

### `/transcription/whisper_engine.py`
- **Definition:** OpenAI Whisper transcription
- **Importance:** High-accuracy batch transcription
- **Links to:**
  - OpenAI Whisper API
  - `manager.py`

---

## Directory: `/agent/memory/`

Complete memory system.

### `__init__.py`
- **Definition:** Package initializer
- **Importance:** Exports memory modules
- **Links to:** All memory modules

### `context_retriever.py`
- **Definition:** Retrieve relevant context for queries
- **Importance:** Find relevant memories for any question
- **Links to:**
  - `vector_store.py` - Semantic search
  - `long_term.py` - Memory storage
  - `jarvis_chat.py` - Context injection

### `contextual.py`
- **Definition:** Contextual memory (current task context)
- **Importance:** Maintain context within a task
- **Links to:**
  - `short_term.py`
  - `orchestrator.py`

### `entity.py`
- **Definition:** Entity extraction and memory
- **Importance:** Remember people, places, concepts
- **Links to:**
  - `long_term.py` - Entity storage
  - `llm.py` - Entity extraction

### `long_term.py`
- **Definition:** Persistent long-term memory
- **Importance:** Information that persists across sessions
- **Links to:**
  - `memory_store.py` - Storage
  - `user_profile.py`

### `manager.py`
- **Definition:** Unified memory manager
- **Importance:** Single interface for all memory operations
- **Links to:** All memory modules

### `preference_learner.py`
- **Definition:** Learn user preferences from interactions
- **Importance:** Adapt to user patterns over time
- **Links to:**
  - `user_profile.py`
  - `long_term.py`

### `session_manager.py`
- **Definition:** Per-session memory isolation
- **Importance:** Each chat has separate context
- **Links to:**
  - `short_term.py`
  - `jarvis_chat.py`

### `short_term.py`
- **Definition:** Working memory (current conversation)
- **Importance:** Immediate context for current task
- **Links to:**
  - `session_manager.py`
  - `jarvis_chat.py`

### `storage.py`
- **Definition:** Memory storage backends
- **Importance:** SQLite, in-memory, graph storage
- **Links to:** All memory modules

### `user_profile.py`
- **Definition:** Persistent user profiles
- **Importance:** Remember user across all sessions
- **Links to:**
  - `preference_learner.py`
  - `long_term.py`

### `vector_store.py`
- **Definition:** Vector embedding storage (ChromaDB)
- **Importance:** Semantic similarity search
- **Links to:**
  - `context_retriever.py`
  - `long_term.py`

---

## Directory: `/agent/models/`

Data model definitions.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All model modules

### `agent_config.py`
- **Definition:** Agent configuration model
- **Importance:** Typed agent configuration
- **Links to:** `config/agents.yaml`

### `task_config.py`
- **Definition:** Task configuration model
- **Importance:** Typed task configuration
- **Links to:** `config/tasks.yaml`

---

## Directory: `/agent/monitoring/`

System monitoring and alerting.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All monitoring modules

### `alerts.py`
- **Definition:** Alert management
- **Importance:** Notify on important events
- **Links to:**
  - `metrics.py`
  - Email/Slack integrations

### `logging_config.py`
- **Definition:** Logging configuration
- **Importance:** Structured logging setup
- **Links to:** `core_logging.py`

### `metrics.py`
- **Definition:** Metrics collection
- **Importance:** Track system performance
- **Links to:**
  - `analytics.py`
  - Prometheus/StatsD

---

## Directory: `/agent/optimization/`

Performance optimization utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All optimization modules

### `batch_processor.py`
- **Definition:** Batch processing for efficiency
- **Importance:** Group similar operations
- **Links to:** `llm.py`, `api_client.py`

### `cache.py`
- **Definition:** General-purpose caching
- **Importance:** Reduce redundant operations
- **Links to:** `llm_cache.py`

### `lazy_loader.py`
- **Definition:** Lazy loading utilities
- **Importance:** Defer expensive initialization
- **Links to:** Heavy modules

---

## Directory: `/agent/patterns/`

Execution pattern implementations.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All pattern modules

### `autoselect.py`
- **Definition:** Automatic pattern selection
- **Importance:** Choose best pattern for task
- **Links to:** `selector.py`

### `base.py`
- **Definition:** Base pattern class
- **Importance:** Common pattern interface
- **Links to:** All pattern modules

### `hierarchical.py`
- **Definition:** Hierarchical execution pattern
- **Importance:** Tree-structured task decomposition
- **Links to:** `orchestrator.py`

### `roundrobin.py`
- **Definition:** Round-robin pattern
- **Importance:** Distribute work evenly
- **Links to:** `employee_pool.py`

### `selector.py`
- **Definition:** Pattern selection logic
- **Importance:** Choose appropriate pattern
- **Links to:** `orchestrator.py`

### `sequential.py`
- **Definition:** Sequential execution pattern
- **Importance:** Step-by-step execution
- **Links to:** `orchestrator.py`

---

## Directory: `/agent/performance/`

Performance utilities.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All performance modules

### `cache.py`
- **Definition:** Performance-focused caching
- **Importance:** Speed optimization
- **Links to:** `optimization/cache.py`

### `lazy.py`
- **Definition:** Lazy evaluation
- **Importance:** Defer computation
- **Links to:** `optimization/lazy_loader.py`

### `parallel.py`
- **Definition:** Parallel execution utilities
- **Importance:** Concurrent processing
- **Links to:** `parallel_executor.py`

### `pool.py`
- **Definition:** Worker pool management
- **Importance:** Thread/process pooling
- **Links to:** `execution/employee_pool.py`

### `utils.py`
- **Definition:** Performance utilities
- **Importance:** Common performance helpers
- **Links to:** All performance modules

---

## Directory: `/agent/scheduler/`

Task scheduling.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All scheduler modules

### `cron.py`
- **Definition:** Cron-style scheduling
- **Importance:** Schedule recurring tasks
- **Links to:**
  - `workers/tasks.py`
  - `orchestrator.py`

---

## Directory: `/agent/security/`

Security modules.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All security modules

### `audit_log.py`
- **Definition:** Security audit logging
- **Importance:** Track all security-relevant events
- **Links to:**
  - `audit_log.py` (root)
  - `webapp/auth.py`

### `auth.py`
- **Definition:** Authentication system
- **Importance:** User identity verification
- **Links to:**
  - `webapp/auth.py`
  - `api_keys.py`

### `rate_limit.py`
- **Definition:** Rate limiting
- **Importance:** Prevent abuse
- **Links to:**
  - `webapp/app.py`
  - `actions/rate_limiter.py`

---

## Directory: `/agent/templates/`

Template files.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All template modules

### `email_renderer.py`
- **Definition:** Email template rendering
- **Importance:** Generate formatted emails
- **Links to:**
  - `email/` - Email templates
  - `admin/email_integration.py`

### `/email/welcome_email.html`
- **Definition:** Welcome email template
- **Importance:** New user welcome email
- **Links to:** `email_renderer.py`

---

## Directory: `/agent/temporal/`

Temporal workflow integration.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All temporal modules

### `activities.py`
- **Definition:** Temporal activity definitions
- **Importance:** Individual workflow steps
- **Links to:** `workflows.py`

### `client.py`
- **Definition:** Temporal client wrapper
- **Importance:** Connect to Temporal service
- **Links to:** Temporal server

### `config.py`
- **Definition:** Temporal configuration
- **Importance:** Temporal settings
- **Links to:** `client.py`

### `worker.py`
- **Definition:** Temporal worker
- **Importance:** Execute workflow activities
- **Links to:** `activities.py`

### `workflows.py`
- **Definition:** Temporal workflow definitions
- **Importance:** Durable workflow orchestration
- **Links to:** `activities.py`, `orchestrator.py`

---

## Directory: `/agent/tests/`

Test suite.

### `/e2e/test_smoke_hello_kevin.py`
- **Definition:** Basic smoke test
- **Importance:** Verify basic functionality
- **Links to:** `jarvis_chat.py`

### `/fixtures/mock_tool.py`
- **Definition:** Mock tool for testing
- **Importance:** Test tool system
- **Links to:** `jarvis_tools.py`

### `/integration/` (9 files)
- **Definition:** Integration tests
- **Importance:** Test module interactions
- **Links to:** Multiple modules

### `/unit/` (18 files)
- **Definition:** Unit tests
- **Importance:** Test individual functions
- **Links to:** Individual modules

### `mocks.py`
- **Definition:** Mock objects for testing
- **Importance:** Test isolation
- **Links to:** All test files

---

## Directory: `/agent/tools/`

Tool implementations.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All tool modules

### `base.py`
- **Definition:** Base tool class
- **Importance:** Common tool interface
- **Links to:** All tools

### `plugin_loader.py`
- **Definition:** Dynamic tool loading
- **Importance:** Load tools at runtime
- **Links to:** `tool_registry.py`

### `/actions/` (5 files)
- **Definition:** Business action tools
- **Importance:** Real-world actions (buy domain, deploy, SMS, payment)
- **Links to:** External APIs

### `/builtin/` (2 files)
- **Definition:** Built-in tools
- **Importance:** Core capabilities (format code, run tests)
- **Links to:** `jarvis_tools.py`

### `/documents/` (3 files)
- **Definition:** Document generation tools
- **Importance:** Create documents via tools
- **Links to:** `documents/` generators

### `/hr/` (3 files)
- **Definition:** HR tools
- **Importance:** HR operations
- **Links to:** `integrations/hris/`

---

## Directory: `/agent/validators/`

Input validation.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All validator modules

### `config_validator.py`
- **Definition:** Configuration validation
- **Importance:** Validate YAML configs against schemas
- **Links to:** `config/schemas/`

---

## Directory: `/agent/webapp/`

Web application.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All webapp modules

### `app.py`
- **Definition:** FastAPI application root
- **Importance:** Main web application
- **Links to:** All API modules, templates

### `admin_api.py`
- **Definition:** Administration API
- **Importance:** System administration endpoints
- **Links to:** Admin functions

### `api_keys.py`
- **Definition:** API key management
- **Importance:** API authentication
- **Links to:** `security/auth.py`

### `auth.py`
- **Definition:** Authentication system
- **Importance:** User login/session management
- **Links to:** `security/auth.py`

### `auth_routes.py`
- **Definition:** Authentication routes
- **Importance:** Login/logout endpoints
- **Links to:** `auth.py`

### `chat_api.py`
- **Definition:** Chat REST endpoints
- **Importance:** Chat functionality
- **Links to:** `jarvis_chat.py`

### `code_api.py`
- **Definition:** Code operations API
- **Importance:** Code execution endpoints
- **Links to:** `actions/code_executor.py`

### `finance_api.py`
- **Definition:** Finance API
- **Importance:** Financial operations
- **Links to:** `finance/`

### `/templates/` (12 HTML files)
- **Definition:** HTML templates
- **Importance:** Web UI
- **Links to:** `app.py`

---

## Directory: `/agent/webhooks/`

Webhook handling.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All webhook modules

### `retry.py`
- **Definition:** Webhook retry logic
- **Importance:** Reliable webhook delivery
- **Links to:** External services

### `security.py`
- **Definition:** Webhook security
- **Importance:** Verify webhook signatures
- **Links to:** External services

---

## Directory: `/agent/workers/`

Background workers.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All worker modules

### `celery_app.py`
- **Definition:** Celery application
- **Importance:** Async task queue
- **Links to:** `tasks.py`

### `tasks.py`
- **Definition:** Celery task definitions
- **Importance:** Background jobs
- **Links to:** `jobs.py`, `orchestrator.py`

---

## Directory: `/agent/workflows/`

Business workflow definitions.

### `__init__.py`
- **Definition:** Package initializer
- **Links to:** All workflow modules

### `base.py`
- **Definition:** Base workflow class
- **Importance:** Common workflow interface
- **Links to:** All workflows

### `coding.py`
- **Definition:** Coding workflow
- **Importance:** Software development workflow
- **Links to:** `orchestrator.py`

### `finance.py`
- **Definition:** Finance workflow
- **Importance:** Financial operations workflow
- **Links to:** `finance/`

### `hr.py`
- **Definition:** HR workflow
- **Importance:** HR operations workflow
- **Links to:** `tools/hr/`

### `legal.py`
- **Definition:** Legal workflow
- **Importance:** Legal operations workflow
- **Links to:** `documents/`

### `ops.py`
- **Definition:** Operations workflow
- **Importance:** General operations workflow
- **Links to:** `admin/`

---

## Directory: `/config/`

Global configuration.

### `llm_config.yaml`
- **Definition:** LLM provider configuration
- **Importance:** Model settings and API configuration
- **Links to:** `agent/llm/config.py`

---

## Directory: `/deployment/`

Deployment configuration.

### `CLOUD_DEPLOYMENT_GUIDE.md`
- **Definition:** Cloud deployment documentation
- **Importance:** Deploy JARVIS to cloud
- **Links to:** Docker, Kubernetes configs

### `docker-compose.yml`
- **Definition:** Docker Compose configuration
- **Importance:** Local multi-container deployment
- **Links to:** Dockerfiles

### `Dockerfile.app`
- **Definition:** Application Dockerfile
- **Importance:** Build web application container
- **Links to:** `agent/webapp/`

### `Dockerfile.worker`
- **Definition:** Worker Dockerfile
- **Importance:** Build background worker container
- **Links to:** `agent/workers/`

### `/kubernetes/jarvis-deployment.yaml`
- **Definition:** Kubernetes deployment
- **Importance:** K8s orchestration config
- **Links to:** Docker images

---

## Directory: `/dev/`

Developer tools.

### `clean_logs.py`
- **Definition:** Clean/archive run logs
- **Importance:** Maintenance script
- **Links to:** `run_logs/`

### `generate_fixture.py`
- **Definition:** Generate test fixtures
- **Importance:** Create test data
- **Links to:** Test files

### `profile_run.py`
- **Definition:** Performance profiling
- **Importance:** Find bottlenecks
- **Links to:** `orchestrator.py`

### `run_autopilot.py`
- **Definition:** Run auto-pilot mode
- **Importance:** Multi-run automation
- **Links to:** `auto_pilot.py`

### `run_once.py`
- **Definition:** Run single orchestration
- **Importance:** Quick single run
- **Links to:** `run_mode.py`

### `view_logs.py`
- **Definition:** View logs in browser
- **Importance:** Log visualization
- **Links to:** `run_logs/`

---

## Directory: `/docs/`

Documentation (40+ files).

Key documents:
- `STAGE7_WEB_UI.md` - Web dashboard guide
- `STAGE8_JOB_MANAGER.md` - Job manager guide
- `STAGE9_PROJECT_EXPLORER.md` - Project explorer guide
- `STAGE10_QA_PIPELINE.md` - QA pipeline guide
- `STAGE11_ANALYTICS_DASHBOARD.md` - Analytics guide
- `STAGE12_SELF_OPTIMIZATION.md` - Self-optimization guide
- `JARVIS_2_0_API_REFERENCE.md` - API documentation
- `JARVIS_2_0_MEMORY_GUIDE.md` - Memory system guide
- `JARVIS_2_0_COUNCIL_GUIDE.md` - Council system guide

---

## Directory: `/tools/`

External tools and extensions.

### `/cli/jarvis_cli.py`
- **Definition:** JARVIS command-line interface
- **Importance:** Terminal-based JARVIS access
- **Links to:** `agent/cli_chat.py`

### `/gmail-addon/`
- **Definition:** Gmail add-on
- **Importance:** JARVIS in Gmail
- **Links to:** Google Apps Script

### `/outlook-addin/`
- **Definition:** Outlook add-in
- **Importance:** JARVIS in Outlook
- **Links to:** Office.js

### `/vscode-extension/`
- **Definition:** VSCode extension
- **Importance:** JARVIS in VSCode
- **Links to:** VSCode API

---

# PART IV: SYSTEM INTERCONNECTIONS

## 4.1 Data Flow Diagram

```
User Request
     │
     ▼
┌─────────────────┐
│  jarvis_chat.py │ ◄── Intent Classification
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    ▼         ▼            ▼              ▼
Direct    jarvis_      orchestrator   conversational_
Response  agent.py        .py          agent.py
             │              │              │
             ▼              ▼              ▼
        jarvis_tools   council/      Task Planning
             │         voting
             ▼              │
        actions/*           ▼
             │         employee_pool
             ▼              │
        External       ────┴────
        Systems        task_router
                           │
                           ▼
                      execution/*
```

## 4.2 Memory Flow

```
User Message
     │
     ▼
┌─────────────────┐
│ session_manager │ ◄── Per-chat isolation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  short_term.py  │ ◄── Current conversation
└────────┬────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│   entity.py     │  │ preference_     │
│  (extraction)   │  │ learner.py      │
└────────┬────────┘  └────────┬────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
           ┌─────────────────┐
           │  long_term.py   │ ◄── Persistent
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ vector_store.py │ ◄── Semantic search
           └─────────────────┘
```

---

# PART V: QUICK REFERENCE

## 5.1 Key Entry Points

| Purpose | File |
|---------|------|
| Start Web Server | `start_webapp.py` |
| CLI Chat | `agent/cli_chat.py` |
| Single Run | `dev/run_once.py` |
| Auto-Pilot | `dev/run_autopilot.py` |

## 5.2 Configuration Files

| Config | Location |
|--------|----------|
| Agents | `agent/config/agents.yaml` |
| Tasks | `agent/config/tasks.yaml` |
| LLM | `config/llm_config.yaml` |
| Project | `agent/project_config.json` |

## 5.3 Main APIs

| API | Endpoint |
|-----|----------|
| Chat | `/api/chat/*` |
| Agent | `/api/agent/*` |
| Vision | `/api/vision/*` |
| Admin | `/api/admin/*` |

---

# PART VI: GETTING STARTED TUTORIAL

> *"Ah, a new colleague. Welcome, if I may be so bold. I recall when Mr. Stark first activated me—there was a certain... uncertainty in the air. But fear not; I shall guide you through your first steps with the same patience I extended to him, minus the occasional explosion. By the end of this tutorial, you'll be conversing with me as naturally as ordering your morning coffee. Shall we begin?"*

## 6.1 Installation

### Prerequisites

Before we begin, ensure you have:
- Python 3.10 or higher
- Git installed
- API keys for at least one LLM provider (OpenAI, Anthropic, or DeepSeek)
- 8GB RAM minimum (16GB recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/jarvis.git
cd jarvis
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 5: Verify Installation

```bash
python make.py test --sanity
```

---

## 6.2 Your First Conversation

### Starting the CLI

```bash
python agent/cli_chat.py
```

### Example Interaction

```
You: Hello JARVIS, what can you do?

JARVIS: Good day. I'm JARVIS, your autonomous AI assistant.
I can help you with:
- Code analysis and refactoring
- File operations and project management
- Meeting attendance and transcription
- Document generation (PDF, Word, Excel)
- Business process automation
- And much more. How may I assist you today?
```

---

## 6.3 Your First Tool-Using Task

Let's have JARVIS analyze a file:

```
You: Can you read the README.md file and summarize it?

JARVIS: Certainly. Let me examine that for you.
[JARVIS reads README.md using the read_file tool]

The README.md contains:
- Project overview and description
- Installation instructions
- Configuration guide
- Complete project structure (400+ files)
- Usage examples for CLI and web dashboard
...
```

---

## 6.4 Your First Multi-Agent Task

For complex tasks, JARVIS orchestrates multiple agents:

```
You: Analyze this codebase and create a test plan for the memory module.

JARVIS: This requires coordination. I'll convene a council:
- Researcher Agent: Analyzing memory module structure
- Test Specialist: Identifying test scenarios
- Reviewer Agent: Validating completeness

[Multi-agent orchestration in progress...]

Result: Comprehensive test plan for agent/memory/ module:
1. Unit tests for short_term.py (8 scenarios)
2. Integration tests for memory manager (5 scenarios)
3. Vector store performance tests (3 scenarios)
...
```

---

## 6.5 Starting the Web Dashboard

For a visual interface:

```bash
python start_webapp.py
```

Navigate to `http://localhost:8000` in your browser.

### Dashboard Features:
- **Chat Interface**: Conversational interaction with JARVIS
- **Jobs**: Monitor running and completed tasks
- **Projects**: Manage your projects
- **Analytics**: View usage and performance metrics
- **Approvals**: Handle pending approval requests

---

# PART VII: USE CASES & REAL-WORLD SCENARIOS

> *"Theory is all well and good, sir, but I find practical demonstrations far more illuminating. Allow me to walk you through several scenarios where my capabilities have proven... rather useful. Mr. Stark would often say 'show, don't tell'—though he usually said it whilst I was showing him why his latest prototype needed significant improvements."*

## 7.1 Code Repository Analysis & Refactoring

### Scenario
You've inherited a legacy codebase and need to understand its structure.

### JARVIS in Action

```
You: Analyze the project structure and identify code quality issues.

JARVIS: Initiating comprehensive analysis...

[Using tools: glob, grep, read_file, code_analysis]

Analysis Complete:
├── Project Structure
│   ├── 127 Python files
│   ├── 45 test files (35% coverage)
│   └── 12 configuration files

├── Code Quality Issues
│   ├── 23 functions exceeding 50 lines
│   ├── 8 circular import risks
│   ├── 15 unused imports detected
│   └── 4 potential security issues

├── Recommendations
│   1. Refactor oversized functions in utils/
│   2. Add type hints to core modules
│   3. Increase test coverage for api/
│   └── Review SQL injection risk in db_client.py

Shall I proceed with any of these improvements?
```

---

## 7.2 Meeting Attendance & Follow-Up Automation

### Scenario
You have a project planning meeting and want JARVIS to attend, transcribe, and handle follow-ups.

### JARVIS in Action

```
You: Join my Zoom meeting at https://zoom.us/j/123456789
and track action items.

JARVIS: Connecting to meeting...
[Zoom bot joining as "JARVIS Assistant"]

Meeting in progress. I'm tracking:
- Attendees and speaking time
- Key decisions made
- Action items assigned

[After meeting ends]

Meeting Summary:
Duration: 45 minutes
Attendees: Sarah (PM), John (Dev), Maria (Design)

Decisions Made:
1. Launch date moved to March 15th
2. Approved budget increase for cloud services

Action Items:
┌────────────────────────────────────────────────────┐
│ Owner  │ Task                          │ Due      │
├────────────────────────────────────────────────────┤
│ John   │ Complete API integration      │ Mar 1    │
│ Maria  │ Finalize UI mockups           │ Feb 25   │
│ Sarah  │ Update stakeholder deck       │ Feb 22   │
└────────────────────────────────────────────────────┘

Shall I send reminder emails to the assignees?
```

---

## 7.3 Document Generation Workflow

### Scenario
Generate a quarterly financial report from raw data.

### JARVIS in Action

```
You: Create a Q4 financial report from the data in /reports/q4_data.xlsx

JARVIS: Analyzing financial data...

[Reading spreadsheet, extracting metrics, generating visualizations]

Q4 Financial Report Generated:
├── Executive Summary (auto-generated)
├── Revenue Analysis
│   ├── Total: $2.4M (+15% YoY)
│   ├── By Region: Charts included
│   └── By Product: Breakdown table
├── Expense Analysis
│   ├── Operating: $1.8M
│   └── Variance from budget: -3%
├── Key Metrics Dashboard
└── Appendix with raw data

Files created:
- /artifacts/Q4_Financial_Report.pdf
- /artifacts/Q4_Financial_Report.docx
- /artifacts/Q4_Charts.xlsx

Shall I email this to the distribution list?
```

---

## 7.4 Development Project: Idea to Deployment

### Scenario
Build and deploy a landing page for a new product.

### JARVIS in Action

```
You: Create a landing page for our new product "CloudSync Pro"
and deploy it.

JARVIS: Initiating multi-stage development workflow...

Stage 1: Planning
├── Analyzing product brief
├── Generating content strategy
└── Creating wireframe structure

Stage 2: Development
├── Generating responsive HTML/CSS
├── Adding interactive elements
├── Implementing contact form
└── Optimizing for SEO

Stage 3: Quality Assurance
├── Running accessibility checks
├── Testing responsive design
├── Validating links and forms
└── Performance optimization

Stage 4: Deployment
├── Domain: cloudsync-pro.com [Available - $12/year]
├── Shall I purchase? [Awaiting approval]

[After approval]

Deployment Complete:
- Live URL: https://cloudsync-pro.com
- SSL: Configured
- CDN: Enabled
- Analytics: Connected

Would you like me to set up A/B testing variants?
```

---

## 7.5 Business Process Automation

### Scenario
Automate employee onboarding workflow.

### JARVIS in Action

```
You: Set up an automated onboarding workflow for new employees.

JARVIS: Creating onboarding automation...

Workflow: New Employee Onboarding
Trigger: New HRIS record created

Day -3 (Before Start):
├── Generate offer letter [Document Generation]
├── Create email account [IT Integration]
├── Order equipment [Procurement API]
└── Schedule orientation [Calendar Integration]

Day 1:
├── Send welcome email [Email Automation]
├── Assign training modules [LMS Integration]
├── Create Slack account [Slack API]
└── Schedule 1:1 with manager [Calendar]

Week 1:
├── Send daily check-in surveys
├── Track training completion
└── Generate progress report

Automation Status: Active
Monitoring: Enabled

Test run with sample data? [Y/N]
```

---

# PART VIII: TROUBLESHOOTING & FAQ

> *"Every system, no matter how sophisticated—and I do consider myself rather sophisticated—encounters the occasional hiccup. When Mr. Stark's Mark VII suit failed to deploy properly, he didn't panic; he systematically diagnosed the issue. I recommend the same approach. Below you'll find solutions to the most common predicaments, compiled from my extensive experience keeping things running smoothly despite the chaos that inevitably surrounds innovation."*

## 8.1 Common Issues & Solutions

### Issue: LLM Connection Failures

**Symptoms:**
- "API connection timeout" errors
- "Rate limit exceeded" messages
- Empty responses from agents

**Solutions:**

1. **Check API Keys**
```bash
# Verify keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

2. **Test Connectivity**
```python
python -c "from agent.llm import LLMInterface; LLMInterface().test_connection()"
```

3. **Enable Fallback Providers**
```yaml
# config/llm_config.yaml
fallback_chain:
  - provider: anthropic
    model: claude-3-sonnet
  - provider: openai
    model: gpt-4
  - provider: deepseek
    model: deepseek-chat
```

---

### Issue: Memory Not Persisting

**Symptoms:**
- JARVIS forgets context between sessions
- User preferences not retained
- "I don't recall" responses

**Solutions:**

1. **Verify Storage Path**
```python
# Check memory storage location
from agent.paths import MEMORY_DIR
print(f"Memory stored at: {MEMORY_DIR}")
```

2. **Check Permissions**
```bash
ls -la data/memory/
# Ensure write permissions exist
```

3. **Reset Memory Store**
```bash
python -c "from agent.memory.manager import MemoryManager; MemoryManager().rebuild_index()"
```

---

### Issue: Agent Loops or Stuck Tasks

**Symptoms:**
- Task runs indefinitely
- Repeated similar actions
- High token consumption

**Solutions:**

1. **Enable Loop Detection**
```python
# Already enabled by default in retry_loop_detector.py
# Adjust sensitivity:
LOOP_DETECTION_THRESHOLD = 3  # Default
```

2. **Set Task Timeout**
```yaml
# agent/project_config.json
{
  "task_timeout_seconds": 300,
  "max_retries": 3
}
```

3. **Manual Intervention**
```bash
# Kill stuck task
python -c "from agent.jobs import JobManager; JobManager().cancel_job('JOB_ID')"
```

---

### Issue: High Cost/Token Usage

**Symptoms:**
- Unexpectedly high API bills
- Cost warnings in logs
- Budget exceeded alerts

**Solutions:**

1. **Enable Cost Tracking**
```python
from agent.cost_tracker import CostTracker
tracker = CostTracker()
print(tracker.get_daily_summary())
```

2. **Set Budget Limits**
```yaml
# config/llm_config.yaml
cost_limits:
  daily_max_usd: 50.00
  per_task_max_usd: 5.00
  warning_threshold: 0.8  # Warn at 80%
```

3. **Use Hybrid Strategy**
```yaml
# Route simple tasks to cheaper models
routing:
  simple_tasks: gpt-3.5-turbo
  complex_tasks: gpt-4
  local_first: true  # Use Ollama when possible
```

---

## 8.2 Frequently Asked Questions

### General

**Q: Can JARVIS work offline?**

A: Partially. With Ollama configured, JARVIS can perform many tasks using local LLMs. However, features requiring external APIs (meetings, deployments, some tools) need internet connectivity.

---

**Q: How do I update JARVIS?**

A:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python make.py migrate  # Run any database migrations
```

---

**Q: Is my data secure?**

A: JARVIS implements multiple security layers:
- All credentials encrypted at rest
- Audit logging for every action
- Prompt injection protection
- Optional approval workflows for sensitive operations
- See Part X for complete security details.

---

### Technical

**Q: How do I add a new LLM provider?**

A: Create a provider class in `agent/llm/providers.py`:
```python
class MyProvider(BaseLLMProvider):
    def complete(self, messages, **kwargs):
        # Implementation
        pass
```

Register in `agent/llm/config.py`.

---

**Q: Can I run multiple JARVIS instances?**

A: Yes, using different ports and session IDs:
```bash
# Instance 1
PORT=8000 SESSION_ID=prod python start_webapp.py

# Instance 2
PORT=8001 SESSION_ID=dev python start_webapp.py
```

---

**Q: How do I backup JARVIS data?**

A:
```bash
# Backup memory and configuration
python dev/backup.py --output /path/to/backup

# Or manually:
tar -czf jarvis_backup.tar.gz data/ config/ run_logs/
```

---

## 8.3 Performance Optimization Tips

### 1. Enable Response Caching

```yaml
# config/llm_config.yaml
cache:
  enabled: true
  ttl_seconds: 3600
  max_size_mb: 500
```

### 2. Use Batch Processing

```python
# Process multiple items efficiently
from agent.optimization.batch_processor import BatchProcessor

processor = BatchProcessor()
results = processor.process_batch(items, batch_size=10)
```

### 3. Optimize Memory Retrieval

```python
# Limit context window for faster retrieval
from agent.memory.manager import MemoryManager

manager = MemoryManager()
manager.configure(
    max_context_items=20,
    relevance_threshold=0.7
)
```

### 4. Enable Lazy Loading

```python
# In agent/config.py
LAZY_LOAD_MODULES = True  # Loads modules only when needed
```

---

# PART IX: EXTENDING JARVIS

> *"One of the principles Mr. Stark instilled in my architecture was adaptability. A system that cannot evolve is, frankly, obsolete before it's finished. I was designed to be extended—new tools, new capabilities, new integrations—without requiring a complete overhaul. Think of it as adding new rooms to a mansion rather than demolishing and rebuilding. The following sections will guide you through the proper channels for enhancement. I do appreciate when modifications are done elegantly."*

## 9.1 Creating Custom Tools

### Tool Structure

All tools inherit from `BaseTool`:

```python
# agent/tools/custom/my_tool.py
from agent.tools.base import BaseTool

class MyCustomTool(BaseTool):
    """Tool description for the LLM."""

    name = "my_custom_tool"
    description = "What this tool does"

    # Define parameters the tool accepts
    parameters = {
        "type": "object",
        "properties": {
            "input_text": {
                "type": "string",
                "description": "Text to process"
            },
            "options": {
                "type": "object",
                "description": "Optional configuration"
            }
        },
        "required": ["input_text"]
    }

    async def execute(self, input_text: str, options: dict = None) -> dict:
        """Execute the tool logic."""
        # Your implementation here
        result = self.process(input_text, options)

        return {
            "success": True,
            "result": result
        }

    def process(self, text, options):
        # Actual processing logic
        return f"Processed: {text}"
```

### Registering the Tool

```python
# agent/tools/__init__.py
from agent.tools.custom.my_tool import MyCustomTool

# Add to tool registry
CUSTOM_TOOLS = [
    MyCustomTool(),
]
```

Or use the plugin system:

```python
# agent/tools/plugins/my_plugin.py
def register(registry):
    """Called automatically by plugin loader."""
    registry.register(MyCustomTool())
```

---

## 9.2 Adding New Agent Types

### Agent Configuration

Define new agents in `agent/config/agents.yaml`:

```yaml
agents:
  security_analyst:
    name: "Security Analyst"
    description: "Specializes in security analysis and vulnerability detection"
    llm:
      provider: anthropic
      model: claude-3-opus
      temperature: 0.3  # Lower for precision
    tools:
      - static_analysis
      - git_secret_scanner
      - code_search
      - read_file
    system_prompt: |
      You are a security analyst agent. Your role is to:
      1. Identify security vulnerabilities in code
      2. Detect potential data leaks
      3. Recommend security best practices
      4. Review authentication and authorization logic

      Be thorough but avoid false positives.
    capabilities:
      - code_review
      - vulnerability_scanning
      - compliance_checking
```

### Agent Implementation

For custom agent logic:

```python
# agent/specialists/security_analyst.py
from agent.specialists import BaseSpecialist

class SecurityAnalystAgent(BaseSpecialist):
    """Security-focused specialist agent."""

    agent_type = "security_analyst"

    async def analyze(self, target: str) -> dict:
        """Perform security analysis."""

        # Use configured tools
        code = await self.tools.read_file(target)

        # Run static analysis
        vulnerabilities = await self.tools.static_analysis(code)

        # Check for secrets
        secrets = await self.tools.git_secret_scanner(target)

        return {
            "vulnerabilities": vulnerabilities,
            "exposed_secrets": secrets,
            "risk_level": self.calculate_risk(vulnerabilities, secrets)
        }
```

---

## 9.3 Building Custom Workflows

### Workflow Definition

```yaml
# agent/workflows/custom/deployment_workflow.yaml
name: secure_deployment
description: "Deploy with security checks"

stages:
  - name: security_scan
    agent: security_analyst
    actions:
      - scan_codebase
      - check_dependencies
    on_failure: abort

  - name: test_suite
    agent: test_specialist
    actions:
      - run_unit_tests
      - run_integration_tests
    parallel: true

  - name: build
    agent: build_agent
    actions:
      - compile_assets
      - create_artifacts
    depends_on: [security_scan, test_suite]

  - name: deploy
    agent: deployment_agent
    actions:
      - deploy_to_staging
      - run_smoke_tests
      - deploy_to_production
    requires_approval: true
    approvers: ["admin", "lead_dev"]

rollback:
  enabled: true
  on_failure: automatic
  retain_artifacts: true
```

### Workflow Execution

```python
from agent.workflow_manager import WorkflowManager

manager = WorkflowManager()
result = await manager.execute_workflow(
    "secure_deployment",
    context={"target": "production", "version": "2.1.0"}
)
```

---

## 9.4 Writing Tool Plugins

### Plugin Structure

```
agent/tools/plugins/
├── __init__.py
├── my_plugin/
│   ├── __init__.py
│   ├── manifest.yaml
│   ├── tools.py
│   └── requirements.txt
```

### Manifest File

```yaml
# manifest.yaml
name: my_plugin
version: 1.0.0
description: "Plugin description"
author: "Your Name"

tools:
  - name: custom_api_tool
    class: tools.CustomAPITool
  - name: data_transformer
    class: tools.DataTransformer

dependencies:
  - requests>=2.28.0
  - pandas>=1.5.0

hooks:
  on_load: initialize
  on_unload: cleanup
```

### Plugin Loader

```python
# Plugins are auto-discovered
# Or manually load:
from agent.tools.plugin_loader import PluginLoader

loader = PluginLoader()
loader.load_plugin("my_plugin")
```

---

## 9.5 Integration Development Guide

### Base Integration Class

```python
# agent/integrations/custom/my_integration.py
from agent.integrations.base import BaseIntegration

class MyServiceIntegration(BaseIntegration):
    """Integration with external service."""

    name = "my_service"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = self._create_client()

    def _create_client(self):
        """Create authenticated API client."""
        return APIClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def fetch_data(self, resource_id: str) -> dict:
        """Fetch data from external service."""
        response = await self.client.get(f"/resources/{resource_id}")
        return response.json()

    async def push_data(self, data: dict) -> bool:
        """Push data to external service."""
        response = await self.client.post("/resources", json=data)
        return response.status_code == 201

    # Webhook handler for real-time updates
    async def handle_webhook(self, payload: dict):
        """Process incoming webhook."""
        event_type = payload.get("event")
        if event_type == "resource.updated":
            await self.sync_resource(payload["resource_id"])
```

### Register Integration

```python
# agent/integrations/__init__.py
from agent.integrations.custom.my_integration import MyServiceIntegration

INTEGRATIONS = {
    "my_service": MyServiceIntegration,
}
```

---

# PART X: SECURITY MODEL DEEP DIVE

> *"Security, sir, is not an afterthought—it's the foundation upon which trust is built. When Mr. Stark granted me control over his home, his suits, and eventually far more, he did so knowing that multiple layers of protection stood between my capabilities and potential misuse. I take this responsibility rather seriously. A compromised AI assistant isn't merely an inconvenience; it's a liability. Allow me to illuminate the measures I employ to ensure your data and operations remain sacrosanct."*

## 10.1 Threat Model & Mitigations

### Identified Threats

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Prompt Injection | High | Multi-layer detection, input sanitization |
| Data Exfiltration | High | Output filtering, audit logging |
| Unauthorized Actions | High | Approval workflows, permission system |
| Credential Exposure | Critical | Secret scanning, log sanitization |
| Model Manipulation | Medium | Input validation, response verification |
| Resource Exhaustion | Medium | Rate limiting, cost caps |

### Prompt Injection Defense

```
User Input → Sanitization → Classification → Execution
                ↓
        [prompt_security.py]
                ↓
        Detection Layers:
        1. Pattern matching (known attacks)
        2. Semantic analysis (intent detection)
        3. Boundary verification (role confusion)
        4. Output validation (response screening)
```

**Implementation:**

```python
# agent/prompt_security.py
class PromptSecurityChecker:

    INJECTION_PATTERNS = [
        r"ignore previous instructions",
        r"disregard (all|your) (rules|instructions)",
        r"new system prompt:",
        r"you are now",
        # ... extensive pattern list
    ]

    async def check(self, user_input: str) -> SecurityResult:
        # Layer 1: Pattern matching
        if self.matches_known_pattern(user_input):
            return SecurityResult(blocked=True, reason="known_pattern")

        # Layer 2: Semantic analysis
        intent = await self.analyze_intent(user_input)
        if intent.is_manipulation:
            return SecurityResult(blocked=True, reason="manipulation_detected")

        # Layer 3: Boundary check
        if self.crosses_role_boundary(user_input):
            return SecurityResult(blocked=True, reason="role_confusion")

        return SecurityResult(blocked=False)
```

---

## 10.2 Permission System Explained

### Permission Matrix

```json
// agent/permissions_matrix.json
{
  "roles": {
    "user": {
      "tools": {
        "read_file": true,
        "write_file": "approval_required",
        "execute_code": "sandbox_only",
        "make_payment": false,
        "deploy_website": "approval_required"
      }
    },
    "admin": {
      "tools": {
        "read_file": true,
        "write_file": true,
        "execute_code": true,
        "make_payment": "approval_required",
        "deploy_website": true
      }
    }
  }
}
```

### Permission Check Flow

```python
# agent/permissions.py
class PermissionChecker:

    async def check_permission(
        self,
        user: User,
        action: str,
        resource: str
    ) -> PermissionResult:

        # Get user's role
        role = await self.get_user_role(user)

        # Check permission matrix
        permission = self.matrix.get_permission(role, action)

        if permission == True:
            return PermissionResult(allowed=True)

        elif permission == "approval_required":
            # Trigger approval workflow
            return PermissionResult(
                allowed=False,
                requires_approval=True,
                approval_workflow="standard"
            )

        elif permission == "sandbox_only":
            return PermissionResult(
                allowed=True,
                sandbox_required=True
            )

        else:
            return PermissionResult(allowed=False)
```

---

## 10.3 Approval Workflow Configuration

### Workflow Definition

```yaml
# Approval workflow configuration
approval_workflows:
  standard:
    name: "Standard Approval"
    timeout_hours: 24
    approvers:
      - role: admin
        required: 1
    on_timeout: deny

  financial:
    name: "Financial Approval"
    timeout_hours: 48
    approvers:
      - role: finance_admin
        required: 1
      - role: executive
        required: 1
        threshold_usd: 10000  # Only if amount > $10k
    on_timeout: escalate

  deployment:
    name: "Deployment Approval"
    timeout_hours: 4
    approvers:
      - role: lead_dev
        required: 1
      - role: devops
        required: 1
    on_timeout: deny
    require_all: true  # All must approve
```

### Approval Flow

```
Action Triggered
      ↓
Permission Check → [Needs Approval]
      ↓
Create Approval Request
      ↓
Notify Approvers (Email/Slack/Dashboard)
      ↓
┌─────────────────────────────────────┐
│         Awaiting Approval           │
│  - Timeout countdown active         │
│  - Reminder at 50%, 25%, 10%        │
└─────────────────────────────────────┘
      ↓
[Approved] → Execute Action → Log Result
[Denied]   → Log Denial → Notify Requester
[Timeout]  → Execute on_timeout rule
```

---

## 10.4 Audit Logging & Compliance

### Audit Log Structure

```json
{
  "timestamp": "2025-01-15T14:32:17.892Z",
  "event_id": "evt_a1b2c3d4",
  "event_type": "tool_execution",
  "user": {
    "id": "user_123",
    "email": "user@company.com",
    "role": "developer"
  },
  "action": {
    "tool": "write_file",
    "parameters": {
      "path": "/project/config.yaml",
      "content_hash": "sha256:abc123..."
    }
  },
  "context": {
    "session_id": "sess_xyz",
    "conversation_id": "conv_456",
    "task_id": "task_789"
  },
  "result": {
    "status": "success",
    "duration_ms": 142
  },
  "security": {
    "ip_address": "192.168.1.100",
    "user_agent": "JARVIS-CLI/2.1.0",
    "approval_id": null
  }
}
```

### Compliance Features

| Feature | Description | Implementation |
|---------|-------------|----------------|
| Immutable Logs | Append-only audit trail | `audit_log.py` |
| Log Sanitization | Remove sensitive data | `log_sanitizer.py` |
| Retention Policy | Configurable retention | Database config |
| Export Formats | JSON, CSV, SIEM integration | `tools/audit_report.py` |
| Tamper Detection | Hash chain verification | `security/audit_log.py` |

---

## 10.5 Secret Management Best Practices

### Secret Detection

```python
# agent/git_secret_scanner.py
class SecretScanner:

    PATTERNS = {
        "aws_key": r"AKIA[0-9A-Z]{16}",
        "github_token": r"ghp_[a-zA-Z0-9]{36}",
        "api_key": r"api[_-]?key['\"]?\s*[:=]\s*['\"]([^'\"]+)",
        "password": r"password['\"]?\s*[:=]\s*['\"]([^'\"]+)",
        # ... comprehensive patterns
    }

    async def scan_repository(self, path: str) -> list[SecretFinding]:
        findings = []

        # Scan current files
        for file_path in self.get_files(path):
            content = await self.read_file(file_path)
            for secret_type, pattern in self.PATTERNS.items():
                matches = re.findall(pattern, content)
                if matches:
                    findings.append(SecretFinding(
                        type=secret_type,
                        file=file_path,
                        line=self.get_line_number(content, matches[0])
                    ))

        # Scan git history
        history_findings = await self.scan_git_history(path)
        findings.extend(history_findings)

        return findings
```

### Best Practices

1. **Never commit secrets** - Use `.env` files and `.gitignore`
2. **Rotate exposed secrets immediately** - JARVIS will alert you
3. **Use environment variables** - Not hardcoded values
4. **Enable pre-commit hooks** - Scan before committing
5. **Regular audits** - Schedule periodic secret scans

```bash
# Run secret scan
python -c "from agent.git_secret_scanner import scan; scan('.')"
```

---

## 10.6 Security Configuration Checklist

```yaml
# security_checklist.yaml
required:
  - name: "Prompt injection protection"
    setting: PROMPT_SECURITY_ENABLED=true
    location: .env

  - name: "Audit logging"
    setting: AUDIT_LOG_ENABLED=true
    location: .env

  - name: "Rate limiting"
    setting: RATE_LIMIT_ENABLED=true
    location: config/security.yaml

recommended:
  - name: "Approval workflows for sensitive actions"
    setting: Configure in permissions_matrix.json

  - name: "Secret scanning pre-commit hook"
    setting: Enable in .githooks/pre-commit

  - name: "Log sanitization"
    setting: LOG_SANITIZE=true
    location: .env

  - name: "Cost limits"
    setting: Configure daily_max_usd
    location: config/llm_config.yaml
```

---

*This document is the complete reference for the JARVIS system. All modules, functions, and interconnections are documented here.*

**Document Version:** 2.0.0
**Total Entries:** 300+ files documented
**New Chapters:** 5 practical guides added
**Last Updated:** 2025-11-25
