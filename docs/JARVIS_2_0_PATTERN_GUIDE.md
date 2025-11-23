# JARVIS 2.0 Pattern Selection Guide

**Version:** 2.0.0
**Date:** November 23, 2025

This guide helps you choose the right orchestration pattern for your multi-agent tasks. The pattern determines how agents coordinate, communicate, and make decisions.

---

## Table of Contents

1. [Overview](#overview)
2. [Available Patterns](#available-patterns)
3. [Pattern Selection Matrix](#pattern-selection-matrix)
4. [Detailed Pattern Descriptions](#detailed-pattern-descriptions)
5. [Auto-Selection](#auto-selection)
6. [Custom Patterns](#custom-patterns)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)

---

## Overview

JARVIS 2.0 provides five orchestration patterns inspired by industry leaders like CrewAI and AG2 (AutoGen). Each pattern offers a different approach to agent coordination:

| Pattern | Coordination Style | Best For |
|---------|-------------------|----------|
| **Sequential** | Linear, one-by-one | Simple, predictable tasks |
| **Hierarchical** | Top-down delegation | Complex, multi-level projects |
| **AutoSelect** | AI-driven selection | Flexible, dynamic collaboration |
| **RoundRobin** | Rotating turns | Review cycles, feedback loops |
| **Manual** | Human-directed | Critical operations, debugging |

---

## Available Patterns

### 1. Sequential Pattern

```
Agent A → Agent B → Agent C → Done
```

Agents execute in a predefined order, each taking exactly one turn per round.

**Characteristics:**
- Predictable execution order
- Clear handoff points
- Minimal coordination overhead
- Fast execution for simple tasks

**Example Use Case:**
```
1. Developer writes code
2. Reviewer reviews code
3. Tester runs tests
4. Deployer deploys
```

### 2. Hierarchical Pattern

```
        Manager
       /   |   \
  Supervisor  Supervisor
     |           |
   Worker      Worker
```

Manager delegates to supervisors who delegate to workers. Results flow back up.

**Characteristics:**
- Clear chain of command
- Escalation paths
- Structured decision-making
- Good for complex projects

**Example Use Case:**
```
1. Project Manager breaks down epic
2. Tech Lead assigns to developers
3. Developers implement features
4. Results aggregate back to PM
```

### 3. AutoSelect Pattern

```
Current Context → LLM Selection → Best Agent
```

An LLM analyzes the current context and selects the most appropriate next speaker.

**Characteristics:**
- Dynamic, context-aware selection
- Adapts to changing requirements
- Higher token usage (LLM calls)
- Most flexible coordination

**Example Use Case:**
```
Task: "Design and implement user dashboard"
→ LLM selects Designer first
→ After mockups, LLM selects Frontend Dev
→ When API needed, LLM selects Backend Dev
```

### 4. RoundRobin Pattern

```
A → B → C → A → B → C → ...
```

Agents take turns in fixed rotation, ensuring equal participation.

**Characteristics:**
- Fair participation
- Iterative refinement
- Good for convergence
- Multiple feedback cycles

**Example Use Case:**
```
Round 1: Author → Reviewer1 → Reviewer2
Round 2: Author (revises) → Reviewer1 → Reviewer2
Round 3: Final approval
```

### 5. Manual Pattern

```
Task → [Human selects agent] → Agent executes → Repeat
```

Human operator selects each agent, maintaining full control.

**Characteristics:**
- Maximum control
- Human oversight
- Slower execution
- Best for critical/risky operations

**Example Use Case:**
```
1. Human reviews situation
2. Human selects "Security Auditor"
3. Security Auditor analyzes
4. Human reviews, selects "Deployer"
5. Deployer proceeds with human watching
```

---

## Pattern Selection Matrix

Use this matrix to choose the right pattern:

| Criteria | Sequential | Hierarchical | AutoSelect | RoundRobin | Manual |
|----------|:----------:|:------------:|:----------:|:----------:|:------:|
| **Task Complexity** |||||
| Simple | ✅ Best | ⚠️ Overkill | ⚠️ Expensive | ⚠️ Slow | ⚠️ Slow |
| Medium | ✅ Good | ✅ Good | ✅ Best | ✅ Good | ⚠️ Slow |
| Complex | ⚠️ May miss | ✅ Best | ✅ Good | ⚠️ May diverge | ⚠️ Tedious |
| **Task Type** |||||
| Linear workflow | ✅ Best | ✅ Good | ✅ Good | ⚠️ Slow | ⚠️ Slow |
| Review/Feedback | ⚠️ Single pass | ✅ Good | ✅ Good | ✅ Best | ✅ Good |
| Creative/Open-ended | ⚠️ Rigid | ⚠️ Rigid | ✅ Best | ✅ Good | ✅ Good |
| Security-critical | ⚠️ Limited | ✅ Good | ⚠️ Unpredictable | ⚠️ Limited | ✅ Best |
| **Constraints** |||||
| Time-sensitive | ✅ Fast | ⚠️ Medium | ⚠️ Medium | ⚠️ Slow | ❌ Slowest |
| Cost-sensitive | ✅ Cheapest | ✅ Low | ❌ Highest | ✅ Low | ✅ Low |
| Audit required | ✅ Clear trail | ✅ Clear trail | ⚠️ Dynamic | ✅ Clear trail | ✅ Best |

### Quick Decision Tree

```
Start
  │
  ├── Is this a simple, linear task?
  │   └── Yes → Sequential
  │
  ├── Does it require multiple review cycles?
  │   └── Yes → RoundRobin
  │
  ├── Is it security-critical or high-risk?
  │   └── Yes → Manual
  │
  ├── Does it have multiple management levels?
  │   └── Yes → Hierarchical
  │
  └── Otherwise → AutoSelect
```

---

## Detailed Pattern Descriptions

### Sequential Pattern

**Configuration:**
```yaml
patterns:
  sequential:
    config:
      max_rounds: 3
      allow_repeat: false
      order:
        - developer
        - reviewer
        - tester
```

**Execution Flow:**
```python
# Round 1
developer.execute(task)   # Step 1
reviewer.execute(result)  # Step 2
tester.execute(result)    # Step 3
# Done (or Round 2 if max_rounds > 1)
```

**When to Use:**
- CI/CD pipelines
- Document processing workflows
- ETL operations
- Well-defined multi-step procedures

**When to Avoid:**
- Tasks requiring iteration/refinement
- Open-ended exploration
- Tasks where agent order isn't obvious

---

### Hierarchical Pattern

**Configuration:**
```yaml
patterns:
  hierarchical:
    config:
      max_rounds: 5
      hierarchy_levels:
        - manager
        - supervisor
        - worker
      escalation_enabled: true
      aggregation_strategy: merge  # or: vote, first, last
```

**Execution Flow:**
```python
# Manager decomposes
subtasks = manager.decompose(task)

# Supervisors distribute
for subtask in subtasks:
    supervisor = select_supervisor(subtask)
    workers = supervisor.assign(subtask)

    # Workers execute
    results = [worker.execute(assignment) for assignment in workers]

    # Supervisor aggregates
    supervisor_result = supervisor.aggregate(results)

# Manager finalizes
final_result = manager.finalize(supervisor_results)
```

**When to Use:**
- Large projects with multiple components
- Tasks requiring different expertise levels
- When clear accountability is needed
- Parallel workstreams that need coordination

**When to Avoid:**
- Small, simple tasks
- Time-critical operations
- When hierarchy adds unnecessary overhead

---

### AutoSelect Pattern

**Configuration:**
```yaml
patterns:
  auto_select:
    config:
      max_rounds: 10
      selection_model: claude-3-haiku  # Use cheap model for selection
      selection_prompt: |
        Given the current task state and available agents,
        select the most appropriate next speaker.
        Consider: expertise, workload, recent contributions.
      confidence_threshold: 0.7
      fallback_pattern: round_robin
```

**Execution Flow:**
```python
while not complete and rounds < max_rounds:
    # LLM analyzes context
    context = build_context(task, history, agents)

    # LLM selects next speaker
    selection = await llm.select_speaker(context, agents)

    if selection.confidence < threshold:
        # Fall back to simpler pattern
        return fallback_pattern.execute()

    # Selected agent executes
    result = await selection.agent.execute(task)
    history.append(result)

    # Check completion
    complete = await llm.is_complete(result)
```

**When to Use:**
- Dynamic, evolving tasks
- Creative or exploratory work
- When optimal agent order isn't known
- Complex debugging or investigation

**When to Avoid:**
- Cost-sensitive operations
- Tasks requiring predictable execution
- When audit trails must be deterministic

---

### RoundRobin Pattern

**Configuration:**
```yaml
patterns:
  round_robin:
    config:
      max_rounds: 5
      agents:
        - author
        - reviewer1
        - reviewer2
      skip_on_no_contribution: true
      convergence_check: true
      convergence_threshold: 0.95  # Stop if 95% agreement
```

**Execution Flow:**
```python
for round_num in range(max_rounds):
    for agent in agents:
        # Agent reviews current state
        contribution = await agent.contribute(state)

        if contribution.is_empty and skip_on_no_contribution:
            continue

        state.update(contribution)

    # Check for convergence
    if check_convergence(state):
        break
```

**When to Use:**
- Code reviews (multiple reviewers)
- Document editing with multiple editors
- Consensus building
- Iterative refinement tasks

**When to Avoid:**
- Single-pass tasks
- When agents have very different roles
- Time-critical operations

---

### Manual Pattern

**Configuration:**
```yaml
patterns:
  manual:
    config:
      prompt_timeout_seconds: 300
      default_on_timeout: sequential
      show_recommendations: true
      allow_skip: false
      confirmation_required: true
```

**Execution Flow:**
```python
while not complete:
    # Show current state to human
    display_state(task, history)

    # Show agent recommendations (optional)
    if show_recommendations:
        recommendations = get_recommendations(context)
        display_recommendations(recommendations)

    # Wait for human selection
    selection = await prompt_human(
        "Select next agent:",
        options=available_agents,
        timeout=timeout
    )

    if selection is None:  # Timeout
        return default_pattern.execute()

    # Execute selected agent
    result = await selection.agent.execute(task)

    # Human confirms or reverts
    if confirmation_required:
        confirmed = await prompt_human("Accept result?")
        if not confirmed:
            continue

    history.append(result)
```

**When to Use:**
- Production deployments
- Security-sensitive operations
- Learning/training scenarios
- Debugging agent behavior
- Critical business decisions

**When to Avoid:**
- High-volume automated tasks
- Real-time systems
- When human availability is limited

---

## Auto-Selection

JARVIS 2.0 can automatically select patterns based on task analysis:

```yaml
patterns:
  auto_selection:
    enabled: true
    analyzer_model: claude-3-haiku
    rules:
      # Rule-based selection (checked first)
      - condition: "task.type == 'code_review'"
        pattern: round_robin
        confidence: 0.95

      - condition: "task.priority == 'critical'"
        pattern: manual
        confidence: 0.99

      - condition: "len(task.agents) <= 2"
        pattern: sequential
        confidence: 0.9

      # LLM-based selection (fallback)
      - condition: "default"
        use_llm: true
        prompt: |
          Analyze this task and recommend an orchestration pattern:
          Task: {task.description}
          Agents: {task.agents}
          Constraints: {task.constraints}
```

**Usage:**
```python
from agent.pattern_selector import PatternSelector

selector = PatternSelector(config)
recommendation = await selector.recommend(task, agents)

print(f"Recommended: {recommendation.pattern}")
print(f"Confidence: {recommendation.confidence}")
print(f"Reasoning: {recommendation.reasoning}")
```

---

## Custom Patterns

Create custom patterns by extending the base class:

```python
from agent.patterns import OrchestrationPattern, PatternConfig

class PriorityPattern(OrchestrationPattern):
    """Select agents based on priority scores."""

    async def select_next_speaker(
        self,
        agents: List[Agent],
        context: OrchestrationContext
    ) -> Optional[Agent]:
        # Custom selection logic
        available = [a for a in agents if not a.busy]

        if not available:
            return None

        # Select highest priority agent
        return max(available, key=lambda a: a.priority_score)

    async def should_continue(
        self,
        context: OrchestrationContext
    ) -> bool:
        return (
            context.round < self.config.max_rounds and
            not context.task_complete
        )
```

**Register custom pattern:**
```python
from agent.patterns import PatternRegistry

registry = PatternRegistry()
registry.register("priority", PriorityPattern)

# Use in config
patterns:
  priority:
    config:
      max_rounds: 5
```

---

## Best Practices

### 1. Start Simple, Evolve as Needed

```
Sequential → RoundRobin → AutoSelect → Custom
```

Don't over-engineer. Start with Sequential for new workflows.

### 2. Match Pattern to Team Structure

| Team Structure | Recommended Pattern |
|---------------|-------------------|
| Flat team | Sequential or RoundRobin |
| Hierarchical org | Hierarchical |
| Cross-functional | AutoSelect |
| External stakeholders | Manual |

### 3. Consider Token Costs

| Pattern | Relative Cost | Notes |
|---------|--------------|-------|
| Sequential | $ | Lowest cost |
| Hierarchical | $$ | Moderate |
| RoundRobin | $$ | Moderate |
| AutoSelect | $$$$ | LLM selection calls |
| Manual | $ | Minimal LLM usage |

### 4. Set Appropriate Limits

```yaml
# Prevent runaway executions
config:
  max_rounds: 10        # Absolute maximum
  timeout_seconds: 300  # 5 minute timeout
  max_tokens: 100000    # Token budget
```

### 5. Monitor and Adjust

Track metrics to optimize pattern selection:
- Task completion rate by pattern
- Average time to completion
- Token usage by pattern
- Human intervention frequency

---

## Troubleshooting

### Pattern Not Completing

**Symptoms:** Task runs indefinitely or hits max rounds without resolution.

**Solutions:**
1. Lower `max_rounds` to force earlier termination
2. Add explicit completion conditions
3. Use `convergence_check` in RoundRobin
4. Switch to Manual for debugging

### Agents Not Contributing

**Symptoms:** Same agent selected repeatedly, others never participate.

**Solutions:**
1. In AutoSelect, improve selection prompt
2. In RoundRobin, disable `skip_on_no_contribution`
3. Check agent availability and workload
4. Review agent specializations

### High Token Usage

**Symptoms:** AutoSelect costing too much.

**Solutions:**
1. Use cheaper model for selection (e.g., Haiku)
2. Cache selection decisions for similar contexts
3. Switch to rule-based selection where possible
4. Use Sequential for predictable workflows

### Inconsistent Results

**Symptoms:** Same task produces different results.

**Solutions:**
1. Lower temperature in AutoSelect
2. Use Sequential for reproducibility
3. Add explicit agent instructions
4. Enable audit logging

---

## Pattern Comparison Summary

| Aspect | Sequential | Hierarchical | AutoSelect | RoundRobin | Manual |
|--------|:----------:|:------------:|:----------:|:----------:|:------:|
| Predictability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Flexibility | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Cost | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Complexity | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |
| Auditability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

*Pattern Selection Guide - JARVIS 2.0*
