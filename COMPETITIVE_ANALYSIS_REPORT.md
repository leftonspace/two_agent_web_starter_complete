# Jarvis AI Agent System: Competitive Analysis & Market Positioning

**Date:** November 21, 2025
**Document Type:** Strategic Competitive Analysis
**Confidentiality:** Internal Strategy Document

---

## Executive Summary

The AI agent orchestration market is valued at **$7.38 billion in 2025** and projected to reach **$103.6 billion by 2032** (45.3% CAGR). Major players include Microsoft, IBM, Google, Amazon, and several open-source frameworks. This report analyzes how Jarvis compares to these competitors and identifies differentiation opportunities.

**Key Finding:** While enterprise giants dominate with scale and integrations, significant gaps exist in **developer experience**, **cost transparency**, **customization depth**, and **small business accessibility** that Jarvis can exploit.

---

## Part 1: Competitive Landscape Overview

### 1.1 Market Leaders

| Competitor | Type | Target Market | Pricing | Key Strength |
|------------|------|---------------|---------|--------------|
| **IBM watsonx Orchestrate** | Enterprise SaaS | Fortune 500 | $500+/month | Governance & Compliance |
| **Microsoft Copilot Studio** | Enterprise SaaS | M365 Enterprises | Per-seat licensing | Office 365 Integration |
| **CrewAI** | Open Source | Developers | Free (self-host) | Rapid Prototyping |
| **AutoGen (Microsoft)** | Open Source | Enterprise Devs | Free (self-host) | Conversation-based Agents |
| **LangGraph** | Open Source | Advanced Devs | Free (self-host) | Complex Workflows |
| **UiPath** | Enterprise SaaS | RPA Users | Enterprise pricing | RPA + AI Hybrid |

### 1.2 Market Share by Segment

```
Enterprise AI Agents (2025)
├── Microsoft Copilot/Azure: ~35%
├── IBM watsonx: ~15%
├── Google Cloud AI: ~12%
├── Amazon Bedrock Agents: ~10%
├── Open Source (CrewAI, AutoGen, etc.): ~18%
└── Others: ~10%
```

---

## Part 2: Detailed Competitor Analysis

### 2.1 IBM watsonx Orchestrate

**Overview:**
IBM's flagship AI agent platform with 100+ prebuilt agents and 400+ tools.

**Capabilities:**
- Multi-agent orchestration with Granite foundation models
- No-code Agent Builder with drag-and-drop
- Advanced observability and governance dashboard
- Hybrid cloud deployment (IBM Cloud, AWS, on-premises)
- Integration with Salesforce, SAP, ServiceNow

**Pricing:**
- Essentials: Starting at $500/month
- Standard: Custom enterprise pricing
- 30-day free trial available

**Strengths:**
- Enterprise-grade compliance (SOC2, HIPAA, GDPR)
- Pre-built industry-specific agents (HR, Finance, Legal)
- Advanced audit trails and access controls
- Langflow visual builder integration

**Weaknesses:**
- High cost barrier for SMBs
- Complex setup requiring IBM consultants
- Slow innovation cycle compared to startups
- Vendor lock-in concerns

**What Jarvis Can Learn:**
- Observability dashboard concept
- Pre-built agent templates by industry
- Governance and audit logging

**Where Jarvis Can Compete:**
- Lower cost entry point
- Faster deployment without consultants
- More customization flexibility

---

### 2.2 Microsoft Copilot Studio

**Overview:**
Multi-agent orchestration announced at Build 2025, deeply integrated with Microsoft 365.

**Capabilities:**
- Connected agents that delegate tasks across systems
- Agent Store with 70+ prebuilt agents
- Model Context Protocol (MCP) for external data
- Bring Your Own Model via Azure AI Foundry (1,900+ models)
- Child agents and modular architecture

**Pricing:**
- Included with Microsoft 365 Copilot license (~$30/user/month)
- Additional consumption-based charges
- Copilot Studio standalone plans available

**Strengths:**
- Native integration with Office 365, Teams, SharePoint
- Massive distribution through M365 ecosystem
- Low barrier for existing Microsoft customers
- Visual agent builder (no-code)

**Weaknesses:**
- Requires Microsoft ecosystem commitment
- Limited customization compared to code-first approaches
- Expensive for small teams not on M365
- Currently in public preview (not GA)

**What Jarvis Can Learn:**
- Agent Store / marketplace concept
- MCP protocol for external integrations
- Modular agent architecture (parent/child)

**Where Jarvis Can Compete:**
- Platform agnostic (not locked to Microsoft)
- Deeper customization for developers
- Self-hosted option (data sovereignty)

---

### 2.3 Open Source Frameworks Comparison

| Framework | Architecture | Learning Curve | Best For | Community Size |
|-----------|--------------|----------------|----------|----------------|
| **CrewAI** | Role-based | Easy | Rapid prototyping | 25k+ GitHub stars |
| **AutoGen** | Conversation | Moderate | Enterprise apps | 35k+ GitHub stars |
| **LangGraph** | Graph-based | Steep | Complex workflows | Part of LangChain |

**CrewAI:**
```python
# Simple, intuitive API
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, write_task, edit_task],
    process=Process.sequential
)
result = crew.kickoff()
```

**Weaknesses:** Debugging is painful, logging inside tasks doesn't work well

**AutoGen:**
```python
# Conversation-based approach
assistant = AssistantAgent("assistant", llm_config=config)
user_proxy = UserProxyAgent("user", code_execution_config={"work_dir": "coding"})
user_proxy.initiate_chat(assistant, message="Write a Python function...")
```

**Weaknesses:** Complex versioning, manual setup required

**LangGraph:**
```python
# Graph-based workflow
workflow = StateGraph(State)
workflow.add_node("agent", agent_node)
workflow.add_edge("agent", "tools")
workflow.add_conditional_edges("tools", should_continue)
```

**Weaknesses:** Steep learning curve, requires graph/state knowledge

---

## Part 3: Jarvis Current State Analysis

### 3.1 What Jarvis Has Today

| Capability | Status | Comparable To |
|------------|--------|---------------|
| Multi-agent orchestration | Working | CrewAI, AutoGen |
| Manager/Supervisor/Employee hierarchy | Working | IBM watsonx |
| Intent classification | Working | All competitors |
| Cost tracking | Working | Better than most OSS |
| Git integration | Working | Unique for web builders |
| Safety checks | Working | Enterprise-grade feature |
| Web interface | Basic | Needs improvement |

### 3.2 Gap Analysis vs. Competitors

| Capability | IBM watsonx | Copilot Studio | CrewAI | **Jarvis** |
|------------|-------------|----------------|--------|------------|
| No-code builder | Yes | Yes | No | **No** |
| Agent marketplace | Yes (100+) | Yes (70+) | No | **No** |
| Visual workflow | Yes | Yes | No | **No** |
| Observability dashboard | Yes | Yes | Limited | **No** |
| Pre-built templates | Yes | Yes | Yes | **No** |
| Self-hosted option | Yes ($$$) | No | Yes | **Yes** |
| Cost transparency | Limited | Limited | N/A | **Strong** |
| Follow-up questions | Yes | Yes | Manual | **No** |
| Mid-task modification | Limited | Limited | No | **No** |
| Real-time agent status | Yes | Yes | No | **No** |

### 3.3 Jarvis Unique Strengths (Current)

1. **Transparent Cost Tracking** - Real-time USD cost display per operation
2. **Self-Hosted Capability** - Full data sovereignty
3. **Git-Native Workflow** - Automatic versioning of generated content
4. **Domain Classification** - Automatic task routing based on content type
5. **Safety-First Design** - Built-in security scanning before deployment

---

## Part 4: $10K Self-Hosted Hardware Analysis

### 4.1 Hardware Configuration Options

**Option A: Triple RTX 4090 Build (~$9,500-$11,000)**

| Component | Specification | Price |
|-----------|---------------|-------|
| GPUs | 3x NVIDIA RTX 4090 (24GB each) | $5,400 |
| CPU | AMD Threadripper 7960X (24-core) | $1,400 |
| Motherboard | TRX50 (3x PCIe x16 slots) | $700 |
| RAM | 128GB DDR5-5600 | $400 |
| Storage | 2TB NVMe Gen5 | $250 |
| PSU | 1600W 80+ Titanium | $450 |
| Case | Full tower with liquid cooling | $400 |
| Cooling | Custom loop or 360mm AIOs x3 | $500 |
| **Total** | | **~$9,500** |

**Total VRAM: 72GB** (24GB x 3)

**Option B: Mac Studio Alternative (~$10,000)**

| Configuration | VRAM | Price |
|---------------|------|-------|
| Mac Studio M2 Ultra (192GB unified) | 192GB | $9,999 |

### 4.2 Model Capabilities at $10K Budget

| Model | Size | Quantization | Performance | Quality |
|-------|------|--------------|-------------|---------|
| **Llama 3.1 70B** | 70B | Q4_K_M | 25-30 tok/s | Excellent |
| **Llama 3.1 405B** | 405B | Q2_K | 3-5 tok/s | Good (degraded) |
| **Mixtral 8x22B** | 141B MoE | Q4 | 20-25 tok/s | Excellent |
| **GPT-OSS 120B** | 120B MoE | Q4 | 30-35 tok/s | Very Good |
| **DeepSeek V3** | 671B MoE | Q4 | 25-30 tok/s | Excellent |

**Key Insight:** MoE (Mixture of Experts) models are the sweet spot - they offer 100B+ parameter quality while only activating 15-20B parameters at inference time.

### 4.3 Performance vs. Cloud APIs

| Metric | Local 120B (MoE) | GPT-4o API | Claude 3.5 |
|--------|------------------|------------|------------|
| Latency (first token) | 500-1000ms | 200-400ms | 200-400ms |
| Throughput | 30-35 tok/s | 50-80 tok/s | 50-80 tok/s |
| Quality (MMLU) | 82-85% | 88% | 89% |
| Cost per 1M tokens | ~$0.50 (electricity) | $5-15 | $3-15 |
| Data Privacy | Complete | Cloud-dependent | Cloud-dependent |
| Uptime | Self-managed | 99.9% SLA | 99.9% SLA |

### 4.4 Realistic Limitations

**What $10K Local Setup CAN Do:**
- Run 70B models at excellent quality and speed
- Run 120B+ MoE models at good quality
- Handle 10-50 concurrent users (with queuing)
- Provide complete data privacy
- Reduce long-term API costs by 80-90%

**What $10K Local Setup CANNOT Do:**
- Match GPT-4o/Claude 3.5 latest capability frontier
- Scale to 1000+ concurrent users
- Run non-quantized 405B models
- Provide 99.99% enterprise uptime without redundancy
- Auto-update to latest model improvements

### 4.5 TCO Comparison (3-Year)

| Scenario | Year 1 | Year 2 | Year 3 | Total |
|----------|--------|--------|--------|-------|
| **Self-Hosted $10K Build** | $10,500 | $1,500 | $1,500 | **$13,500** |
| **OpenAI API (moderate use)** | $6,000 | $6,000 | $6,000 | **$18,000** |
| **IBM watsonx (basic)** | $6,000 | $6,000 | $6,000 | **$18,000** |

*Assumes 500K tokens/day usage, $500/year electricity, $1000/year maintenance*

**Break-even Point:** ~18 months for moderate API users

---

## Part 5: Strategic Differentiation Opportunities

### 5.1 Positioning Matrix

```
                    CUSTOMIZATION DEPTH
                    Low ─────────────── High
                    │                     │
         High      │  Copilot    │   IBM  │
                   │  Studio     │watsonx │
    ENTERPRISE     │─────────────┼────────│
    READINESS      │             │        │
                   │  UiPath     │ Jarvis │ ← TARGET
         Low       │             │(future)│
                   │─────────────┼────────│
                   │ Simple      │ CrewAI │
                   │ Chatbots    │AutoGen │
                    ─────────────────────
```

### 5.2 Differentiation Strategy: "The Developer's Enterprise Platform"

**Target Segment:** Technical SMBs and startups who need:
- Enterprise-grade features without enterprise pricing
- Self-hosted option for data sovereignty
- Deep customization without vendor lock-in
- Transparent, predictable costs

### 5.3 Unique Value Propositions

| UVP | Description | Why It Matters |
|-----|-------------|----------------|
| **1. Cost Transparency** | Real-time cost tracking per task, no surprise bills | IBM/Microsoft hide costs in enterprise contracts |
| **2. Self-Hosted First** | Run on your hardware, your data never leaves | Compliance, sovereignty, reduced long-term cost |
| **3. Developer Experience** | Code-first with visual option, not the reverse | Developers want control, not just no-code |
| **4. Vertical Specialization** | Pre-tuned for web development initially | Competitors are horizontal, we're deep |
| **5. Open Architecture** | Works with any LLM provider (OpenAI, Anthropic, local) | No vendor lock-in |

### 5.4 Feature Roadmap to Compete

**Phase 1: Foundation (Current + 2 months)**
| Feature | Priority | Competitor Parity |
|---------|----------|-------------------|
| Follow-up question loop | P0 | All competitors |
| Agent activity visualization | P0 | IBM, Copilot |
| Mid-task modification | P1 | Unique advantage |
| Bug fixes (path, memory, safety) | P0 | Table stakes |

**Phase 2: Differentiation (Months 3-6)**
| Feature | Priority | Competitive Edge |
|---------|----------|------------------|
| Observability dashboard | P1 | Match IBM |
| Agent template marketplace | P1 | Match Copilot |
| Local LLM integration (Ollama) | P0 | **Unique** |
| Cost prediction before execution | P1 | **Unique** |
| Live preview during generation | P2 | **Unique** |

**Phase 3: Market Expansion (Months 6-12)**
| Feature | Priority | Market Impact |
|---------|----------|---------------|
| Visual workflow builder | P2 | Compete with no-code |
| Team collaboration | P1 | Enterprise readiness |
| Vertical templates (e-commerce, SaaS) | P1 | Faster adoption |
| Enterprise SSO/RBAC | P2 | Unlock enterprise deals |

---

## Part 6: Go-To-Market Strategy

### 6.1 Target Customer Segments

| Segment | Size | Pain Point | Jarvis Solution |
|---------|------|------------|-----------------|
| **Indie Developers** | 5M+ | API costs add up | Self-hosted, transparent pricing |
| **Tech Startups** | 500K+ | Need enterprise features, can't afford enterprise prices | Full features at SMB price |
| **Agencies** | 100K+ | Client data privacy concerns | Self-hosted, white-label option |
| **Regulated Industries** | 50K+ | Cloud AI compliance issues | On-premises deployment |

### 6.2 Pricing Strategy

**Proposed Pricing Model:**

| Tier | Price | Features | Target |
|------|-------|----------|--------|
| **Community** | Free | Self-hosted, basic features, community support | Indie devs |
| **Pro** | $49/month | All features, priority support, cloud hosting option | Startups |
| **Team** | $199/month | 5 seats, collaboration, shared templates | Small teams |
| **Enterprise** | Custom | SSO, RBAC, SLA, dedicated support | Enterprises |

**Comparison to Competitors:**
- IBM watsonx: 10x more expensive for similar features
- Copilot Studio: Requires M365 ecosystem buy-in
- CrewAI: Free but no support, no hosted option

### 6.3 Competitive Messaging

**Against IBM watsonx:**
> "Enterprise AI orchestration without the enterprise price tag. Get 80% of watsonx capabilities at 10% of the cost, with the flexibility to self-host."

**Against Microsoft Copilot Studio:**
> "Don't let your AI agent strategy lock you into one ecosystem. Jarvis works with OpenAI, Anthropic, or your own local models."

**Against Open Source (CrewAI, AutoGen):**
> "The power of open source with the polish of a product. Production-ready multi-agent orchestration with observability, cost tracking, and support."

---

## Part 7: Technical Recommendations

### 7.1 Architecture Improvements for $10K Self-Hosted

```
┌─────────────────────────────────────────────────────────────┐
│                    JARVIS ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Web UI    │    │  REST API   │    │  WebSocket  │     │
│  │  (React)    │    │  (FastAPI)  │    │ (Real-time) │     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                 │
│                    ┌───────▼───────┐                        │
│                    │   Jarvis      │                        │
│                    │   Gateway     │                        │
│                    │ (Intent/Route)│                        │
│                    └───────┬───────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼──────┐   ┌───────▼───────┐  ┌──────▼──────┐     │
│  │  Simple     │   │  Orchestrator │  │    File     │     │
│  │  Queries    │   │  (Multi-Agent)│  │  Operations │     │
│  └──────┬──────┘   └───────┬───────┘  └──────┬──────┘     │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            │                                 │
│                    ┌───────▼───────┐                        │
│                    │  LLM Router   │                        │
│                    │  (Model Agn.) │                        │
│                    └───────┬───────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼──────┐   ┌───────▼───────┐  ┌──────▼──────┐     │
│  │  OpenAI     │   │   Anthropic   │  │   Ollama    │     │
│  │  API        │   │   API         │  │   (Local)   │     │
│  └─────────────┘   └───────────────┘  └─────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Recommended Local Model Stack

```yaml
# docker-compose.yml for self-hosted Jarvis
version: '3.8'
services:
  jarvis:
    image: jarvis/orchestrator:latest
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=ollama
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 3
              capabilities: [gpu]

  # Pre-load recommended models
  model-loader:
    image: jarvis/model-loader:latest
    environment:
      - MODELS=deepseek-v3,llama3.1:70b,qwen2.5-coder:32b
```

### 7.3 Hybrid Cloud/Local Strategy

```
User Request
     │
     ▼
┌─────────────────┐
│ Task Classifier │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│Simple │ │Complex│
│ Task  │ │ Task  │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ Local │ │ Cloud │
│ 70B   │ │ GPT-4 │
│(fast) │ │(best) │
└───────┘ └───────┘

Strategy:
- Route simple tasks to local 70B (fast, free)
- Route complex tasks to cloud API (best quality)
- User can override per-task
- Cost savings: 60-70%
```

---

## Part 8: Risk Analysis

### 8.1 Competitive Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Microsoft bundles agents free with M365 | High | High | Focus on non-M365 customers, self-hosted value |
| Open source catches up on polish | Medium | Medium | Move faster, build community |
| IBM/Google reduce pricing | Low | Medium | Self-hosted differentiator remains |
| New entrant with better UX | Medium | High | Continuous UX investment |

### 8.2 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Local LLM quality plateau | Low | High | Maintain cloud API fallback |
| GPU supply constraints | Medium | Medium | Support Apple Silicon alternative |
| Model licensing changes | Medium | Medium | Multi-model support |

---

## Part 9: Conclusions & Recommendations

### 9.1 Key Takeaways

1. **The market is massive and growing** - $7B → $100B+ by 2032
2. **Enterprise incumbents have gaps** - Cost, flexibility, developer experience
3. **$10K self-hosted is viable** - MoE models make 120B accessible
4. **Differentiation is possible** - Cost transparency, self-hosting, developer-first

### 9.2 Immediate Actions (Next 30 Days)

| Action | Owner | Impact |
|--------|-------|--------|
| Fix path mismatch bug | Engineering | Unblocks testing |
| Implement follow-up questions | Engineering | Major UX improvement |
| Add agent activity visualization | Frontend | User engagement |
| Integrate Ollama for local LLM | Engineering | Self-hosted enablement |
| Create landing page with positioning | Marketing | Lead generation |

### 9.3 Success Metrics

| Metric | 3-Month Target | 12-Month Target |
|--------|----------------|-----------------|
| GitHub Stars | 1,000 | 10,000 |
| Active Users (Community) | 500 | 5,000 |
| Paying Customers | 10 | 200 |
| Monthly Recurring Revenue | $1,000 | $25,000 |

### 9.4 Final Verdict

**Can Jarvis compete with IBM and Microsoft?**

Not head-to-head on enterprise features today. But Jarvis can carve out a defensible niche as:

> **"The self-hosted, cost-transparent, developer-first AI agent platform for teams who want enterprise capabilities without enterprise lock-in."**

This positioning targets the 80% of the market that IBM and Microsoft aren't serving well: technical teams at startups, agencies, and regulated industries who need control, transparency, and flexibility.

The $10K self-hosted option becomes a key differentiator as API costs rise and data sovereignty concerns grow. Combined with the improvements outlined in the Trial Report, Jarvis can become a credible alternative in the rapidly growing AI agent market.

---

## Appendix A: Competitor Feature Matrix

| Feature | IBM watsonx | Copilot Studio | CrewAI | AutoGen | LangGraph | **Jarvis** |
|---------|-------------|----------------|--------|---------|-----------|------------|
| Multi-agent orchestration | Full | Full | Full | Full | Full | **Full** |
| No-code builder | Yes | Yes | No | No | No | **Planned** |
| Visual workflow | Yes | Yes | No | No | Yes | **Planned** |
| Self-hosted | Yes ($$$) | No | Yes | Yes | Yes | **Yes** |
| Agent marketplace | 100+ | 70+ | Community | Community | No | **Planned** |
| Observability | Advanced | Basic | Limited | Limited | Via LangSmith | **Planned** |
| Cost tracking | Hidden | Hidden | N/A | N/A | N/A | **Real-time** |
| Local LLM support | No | Via Azure | Yes | Yes | Yes | **Planned** |
| Git integration | No | No | No | No | No | **Built-in** |
| Safety scanning | Yes | Yes | No | No | No | **Built-in** |
| Follow-up questions | Yes | Yes | Manual | Manual | Manual | **Planned** |
| Mid-task modification | Limited | Limited | No | No | No | **Planned** |

## Appendix B: Hardware Cost Breakdown

### Triple RTX 4090 Build (Detailed)

```
┌─────────────────────────────────────────────────────────────┐
│                 $10,000 AI WORKSTATION BUILD                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GPUs (72GB Total VRAM)                                     │
│  ├── RTX 4090 #1 (24GB)................ $1,800              │
│  ├── RTX 4090 #2 (24GB)................ $1,800              │
│  └── RTX 4090 #3 (24GB)................ $1,800              │
│                                          ────────           │
│                               Subtotal:  $5,400             │
│                                                              │
│  CPU & Motherboard                                          │
│  ├── AMD Threadripper 7960X............ $1,400              │
│  └── ASUS Pro WS TRX50-SAGE............ $700                │
│                                          ────────           │
│                               Subtotal:  $2,100             │
│                                                              │
│  Memory & Storage                                           │
│  ├── 128GB DDR5-5600 (4x32GB).......... $400                │
│  └── 2TB Samsung 990 Pro NVMe.......... $250                │
│                                          ────────           │
│                               Subtotal:  $650               │
│                                                              │
│  Power & Cooling                                            │
│  ├── Corsair AX1600i PSU............... $450                │
│  ├── Custom Loop / 3x 360mm AIO........ $500                │
│  └── Full Tower Case................... $400                │
│                                          ────────           │
│                               Subtotal:  $1,350             │
│                                                              │
│  ═══════════════════════════════════════════════════════   │
│                              TOTAL:      $9,500             │
│  ═══════════════════════════════════════════════════════   │
│                                                              │
│  Monthly Operating Costs:                                   │
│  ├── Electricity (600W avg)............ $50-80/month        │
│  ├── Internet (redundant).............. $100/month          │
│  └── Maintenance reserve............... $50/month           │
│                                          ────────           │
│                              Monthly:    $200-230           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

*Report prepared for strategic planning purposes*
*Last updated: November 21, 2025*
