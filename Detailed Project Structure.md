***Project Structure***

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
