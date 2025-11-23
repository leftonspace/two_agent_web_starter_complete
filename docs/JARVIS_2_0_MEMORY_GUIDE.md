# JARVIS 2.0 Memory System Guide

**Version:** 2.0.0
**Date:** November 23, 2025

This guide covers the multi-type memory system in JARVIS 2.0, enabling agents to remember context, learn from past interactions, and build knowledge over time.

---

## Table of Contents

1. [Memory System Overview](#memory-system-overview)
2. [Memory Types](#memory-types)
3. [Short-Term Memory (STM)](#short-term-memory-stm)
4. [Long-Term Memory (LTM)](#long-term-memory-ltm)
5. [Entity Memory](#entity-memory)
6. [Memory Manager](#memory-manager)
7. [Configuration](#configuration)
8. [Usage Examples](#usage-examples)
9. [Performance Optimization](#performance-optimization)
10. [Best Practices](#best-practices)

---

## Memory System Overview

JARVIS 2.0 implements a sophisticated multi-type memory system inspired by human cognition:

```
                    ┌─────────────────────────────────────┐
                    │         Memory Manager              │
                    │  (Unified Interface & Routing)      │
                    └─────────────────┬───────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          │                           │                           │
          ▼                           ▼                           ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Short-Term     │       │   Long-Term     │       │    Entity       │
│    Memory       │       │    Memory       │       │    Memory       │
│                 │       │                 │       │                 │
│ • Current       │       │ • Persistent    │       │ • Knowledge     │
│   conversation  │       │   storage       │       │   graph         │
│ • Working       │       │ • Semantic      │       │ • Relationships │
│   context       │       │   search        │       │ • Attributes    │
│ • Recent        │       │ • Long-term     │       │ • Types         │
│   messages      │       │   retention     │       │                 │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### Why Multiple Memory Types?

| Memory Type | Purpose | Retention | Search Method |
|------------|---------|-----------|---------------|
| **Short-Term** | Current session context | Session/hours | Recency + relevance |
| **Long-Term** | Persistent knowledge | Days/months | Semantic similarity |
| **Entity** | Relationships & facts | Permanent | Graph traversal |

---

## Memory Types

### Comparison Table

| Feature | Short-Term | Long-Term | Entity |
|---------|:----------:|:---------:|:------:|
| **Storage** | In-memory | SQLite/PostgreSQL | Graph DB/NetworkX |
| **Capacity** | ~8K tokens | Unlimited | Unlimited |
| **Persistence** | Session | Permanent | Permanent |
| **Query Type** | Token window | Semantic search | Graph query |
| **Use Case** | Conversation | Experience | Knowledge |
| **Update Frequency** | Every message | Important events | Entity changes |

---

## Short-Term Memory (STM)

STM maintains the current conversation context and recent interactions.

### Features

- **Token-limited window**: Keeps recent messages within token budget
- **Relevance scoring**: Prioritizes relevant content when compressing
- **Automatic compression**: Summarizes older content to fit limits
- **Embedding support**: Semantic relevance matching

### Basic Usage

```python
from agent.memory import ShortTermMemory, STMConfig

# Initialize
stm = ShortTermMemory(config=STMConfig(
    max_tokens=8000,
    relevance_threshold=0.7,
    embedding_model="text-embedding-3-small"
))

# Add messages
await stm.add_message(role="user", content="Hello, I'm working on a Python project")
await stm.add_message(role="assistant", content="Great! What kind of project?")
await stm.add_message(role="user", content="A web scraper for news articles")

# Get conversation history
history = stm.get_messages(limit=10)

# Get relevant context for a query
context = await stm.get_relevant_context(
    query="What is the user building?",
    max_tokens=2000
)
# Returns: Most relevant messages about the Python web scraper
```

### Conversation Buffer

For simple conversation tracking without embeddings:

```python
from agent.memory import ConversationBuffer

buffer = ConversationBuffer(max_messages=100)

buffer.add("user", "Hello")
buffer.add("assistant", "Hi there!")

# Get recent messages
recent = buffer.get_recent(n=10)

# Get messages as string
context_str = buffer.to_string(
    format="role: content",
    separator="\n"
)
```

### Compression

When STM exceeds token limits, it automatically compresses:

```python
# Manual compression
summary = await stm.compress(
    strategy="summarize",  # or "truncate", "relevance"
    target_tokens=4000
)

# Check if compression needed
if stm.token_count > stm.config.max_tokens:
    await stm.compress()
```

**Compression Strategies:**

| Strategy | Description | Best For |
|----------|-------------|----------|
| `truncate` | Remove oldest messages | Simple, fast |
| `summarize` | LLM summarizes old content | Preserve meaning |
| `relevance` | Keep most relevant to current | Focused context |

---

## Long-Term Memory (LTM)

LTM provides persistent storage with semantic search capabilities.

### Features

- **Persistent storage**: SQLite, PostgreSQL, or custom backends
- **Semantic search**: Find memories by meaning, not just keywords
- **Chunking**: Automatically splits large content
- **Metadata**: Tag and filter memories
- **TTL support**: Auto-expire old memories

### Basic Usage

```python
from agent.memory import LongTermMemory, LTMConfig

# Initialize
ltm = LongTermMemory(config=LTMConfig(
    storage_path="./data/memory.db",
    embedding_model="text-embedding-3-small",
    chunk_size=500,
    retention_days=90
))

# Store a memory
await ltm.store(
    content="User John prefers dark mode and uses VS Code",
    metadata={
        "category": "user_preference",
        "user_id": "john_123",
        "confidence": 0.95
    }
)

# Store with custom embedding
await ltm.store(
    content="Important meeting notes from product review",
    embedding=custom_embedding,  # Pre-computed
    metadata={"type": "meeting", "date": "2025-11-23"}
)

# Retrieve by semantic search
memories = await ltm.retrieve(
    query="What editor does John use?",
    limit=5,
    filters={"user_id": "john_123"}
)

for memory in memories:
    print(f"[{memory.score:.2f}] {memory.content}")
# Output: [0.92] User John prefers dark mode and uses VS Code
```

### Advanced Queries

```python
# Retrieve with multiple filters
memories = await ltm.retrieve(
    query="user preferences",
    limit=10,
    filters={
        "category": "user_preference",
        "confidence": {"$gte": 0.8}  # Confidence >= 0.8
    },
    time_range={
        "start": datetime(2025, 1, 1),
        "end": datetime.now()
    }
)

# Get all memories for a user
user_memories = await ltm.get_by_metadata(
    filters={"user_id": "john_123"},
    limit=100
)

# Delete old memories
deleted = await ltm.cleanup(
    older_than_days=90,
    filters={"category": "temporary"}
)
```

### Storage Backends

**SQLite (Default):**
```python
ltm = LongTermMemory(config=LTMConfig(
    storage_type="sqlite",
    storage_path="./data/memory.db"
))
```

**PostgreSQL:**
```python
ltm = LongTermMemory(config=LTMConfig(
    storage_type="postgresql",
    connection_string="postgresql://user:pass@localhost:5432/jarvis"
))
```

**Redis (Fast, volatile):**
```python
ltm = LongTermMemory(config=LTMConfig(
    storage_type="redis",
    connection_string="redis://localhost:6379/0"
))
```

---

## Entity Memory

Entity Memory maintains a knowledge graph of entities and their relationships.

### Features

- **Entity storage**: People, projects, concepts, etc.
- **Relationships**: Typed connections between entities
- **Graph queries**: Find related entities by traversal
- **Attribute tracking**: Entity properties and history

### Basic Usage

```python
from agent.memory import EntityMemory, Entity, Relationship

# Initialize
entity_mem = EntityMemory()

# Add entities
await entity_mem.add_entity(Entity(
    id="user_john",
    type="person",
    name="John Smith",
    attributes={
        "role": "developer",
        "team": "backend",
        "skills": ["python", "postgresql", "docker"]
    }
))

await entity_mem.add_entity(Entity(
    id="project_alpha",
    type="project",
    name="Project Alpha",
    attributes={
        "status": "active",
        "tech_stack": ["python", "react", "postgresql"]
    }
))

# Add relationship
await entity_mem.add_relationship(Relationship(
    source="user_john",
    target="project_alpha",
    type="works_on",
    properties={
        "role": "lead_developer",
        "since": "2025-01-15"
    }
))
```

### Graph Queries

```python
# Find all projects John works on
projects = await entity_mem.get_related(
    entity_id="user_john",
    relationship_type="works_on",
    direction="outgoing"
)

# Find all people on Project Alpha
team = await entity_mem.get_related(
    entity_id="project_alpha",
    relationship_type="works_on",
    direction="incoming"
)

# Multi-hop traversal (depth 2)
# Find colleagues: John → Projects → Other team members
colleagues = await entity_mem.get_related(
    entity_id="user_john",
    relationship_type="works_on",
    depth=2,
    exclude_start=True
)

# Find entities by attributes
python_devs = await entity_mem.find_entities(
    type="person",
    attributes={"skills": {"$contains": "python"}}
)
```

### Entity Updates

```python
# Update entity attributes
await entity_mem.update_entity(
    entity_id="user_john",
    updates={
        "attributes.team": "platform",
        "attributes.skills": ["python", "postgresql", "kubernetes"]
    }
)

# Remove relationship
await entity_mem.remove_relationship(
    source="user_john",
    target="project_alpha",
    type="works_on"
)

# Get entity history
history = await entity_mem.get_entity_history("user_john")
```

### Graph Visualization

```python
# Export graph for visualization
graph_data = entity_mem.export_graph(
    format="json",  # or "graphml", "gexf"
    include_attributes=True
)

# Get graph statistics
stats = entity_mem.get_stats()
# {"entities": 150, "relationships": 320, "types": 5, ...}
```

---

## Memory Manager

The Memory Manager provides a unified interface for all memory types.

### Basic Usage

```python
from agent.memory import MemoryManager, MemoryConfig

# Initialize with all memory types
manager = MemoryManager(config=MemoryConfig(
    stm_config=STMConfig(max_tokens=8000),
    ltm_config=LTMConfig(storage_path="./data/memory.db"),
    entity_config=EntityConfig()
))

# Process a message (auto-routes to appropriate memories)
await manager.process_message(
    message={
        "role": "user",
        "content": "I'm John from the backend team working on Project Alpha"
    },
    extract_entities=True,  # Auto-extract and store entities
    store_ltm=True          # Store in long-term memory
)
```

### Unified Context Retrieval

```python
# Get context from all memory types
context = await manager.get_context(
    query="What projects is John working on?",
    include_stm=True,
    include_ltm=True,
    include_entities=True,
    max_tokens=4000
)

# Returns:
# {
#     "stm": [...recent messages...],
#     "ltm": [...relevant memories...],
#     "entities": [...related entities...],
#     "formatted": "Combined context string for LLM"
# }
```

### Memory Routing

```python
# Configure routing rules
manager.set_routing_rules({
    "user_preferences": "ltm",      # Store preferences in LTM
    "entity_mentions": "entity",     # Detected entities to Entity Memory
    "all_messages": "stm",          # Everything to STM
    "important": "ltm"              # Messages marked important
})

# Process with routing
await manager.process_message(
    message={"role": "user", "content": "..."},
    tags=["user_preferences", "important"]
)
```

---

## Configuration

### Complete Configuration Example

**File:** `config/memory.yaml`

```yaml
version: "2.0"

memory:
  # Enable/disable memory system
  enabled: true

  # Short-Term Memory
  short_term:
    enabled: true
    max_tokens: 8000
    relevance_threshold: 0.65
    compression:
      enabled: true
      strategy: summarize
      target_ratio: 0.5  # Compress to 50% when needed
    embedding:
      model: text-embedding-3-small
      cache_enabled: true
      cache_ttl_seconds: 3600

  # Long-Term Memory
  long_term:
    enabled: true
    storage:
      type: sqlite  # sqlite, postgresql, redis
      path: ./data/memory.db
      # connection_string: postgresql://...
    embedding:
      model: text-embedding-3-small
      dimensions: 1536
    chunking:
      enabled: true
      chunk_size: 500
      chunk_overlap: 50
    retention:
      enabled: true
      default_days: 90
      cleanup_interval_hours: 24
    indexing:
      type: hnsw  # or flat, ivf
      ef_construction: 200
      m: 16

  # Entity Memory
  entity:
    enabled: true
    storage:
      type: networkx  # networkx (in-memory), neo4j, sqlite
      # connection_string: bolt://localhost:7687
    extraction:
      enabled: true
      model: claude-3-haiku
      confidence_threshold: 0.7
    relationship_types:
      - works_on
      - depends_on
      - created_by
      - manages
      - part_of
      - related_to
    max_entities: 10000

  # Context Settings
  context:
    max_tokens: 4000
    include_stm: true
    include_ltm: true
    include_entities: true
    format_template: |
      ## Recent Conversation
      {stm}

      ## Relevant Memories
      {ltm}

      ## Related Knowledge
      {entities}

  # Performance
  performance:
    lazy_loading: true
    cache_embeddings: true
    batch_size: 100
    async_operations: true
```

---

## Usage Examples

### Example 1: Personal Assistant with Memory

```python
from agent.memory import MemoryManager

class PersonalAssistant:
    def __init__(self):
        self.memory = MemoryManager(config_path="config/memory.yaml")

    async def chat(self, user_message: str) -> str:
        # Store user message
        await self.memory.process_message({
            "role": "user",
            "content": user_message
        })

        # Get relevant context
        context = await self.memory.get_context(
            query=user_message,
            max_tokens=4000
        )

        # Generate response with context
        response = await self.llm.generate(
            system="You are a helpful assistant with memory.",
            context=context["formatted"],
            user_message=user_message
        )

        # Store assistant response
        await self.memory.process_message({
            "role": "assistant",
            "content": response
        })

        return response
```

### Example 2: Project Knowledge Base

```python
async def build_project_knowledge(project_docs: List[str]):
    """Build a knowledge base from project documentation."""

    ltm = LongTermMemory(config=LTMConfig(
        storage_path="./data/project_kb.db"
    ))

    for doc in project_docs:
        # Extract sections
        sections = split_into_sections(doc)

        for section in sections:
            await ltm.store(
                content=section.content,
                metadata={
                    "source": doc.filename,
                    "section": section.title,
                    "type": "documentation"
                }
            )

    # Query the knowledge base
    answer = await ltm.retrieve(
        query="How do I deploy the application?",
        limit=5
    )
```

### Example 3: User Preference Learning

```python
async def learn_user_preferences(message: str, user_id: str):
    """Extract and store user preferences."""

    entity_mem = EntityMemory()

    # Use LLM to extract preferences
    preferences = await extract_preferences(message)

    for pref in preferences:
        # Update user entity
        await entity_mem.update_entity(
            entity_id=user_id,
            updates={
                f"attributes.preferences.{pref.category}": pref.value
            }
        )

        # Store in LTM for semantic search
        await ltm.store(
            content=f"User prefers {pref.value} for {pref.category}",
            metadata={
                "user_id": user_id,
                "category": "preference",
                "preference_type": pref.category
            }
        )
```

---

## Performance Optimization

### Lazy Loading

```python
from agent.performance import LazyLoader

# Defer memory initialization
memory_loader = LazyLoader(lambda: MemoryManager(config))

# Memory only initialized when first accessed
context = await memory_loader.get().get_context(query)
```

### Caching

```python
from agent.performance import ResponseCache

# Cache embedding computations
embedding_cache = ResponseCache(config=CacheConfig(
    max_size=10000,
    ttl_seconds=3600
))

@embedding_cache.memoize
async def get_embedding(text: str) -> List[float]:
    return await embedding_model.encode(text)
```

### Batch Operations

```python
# Batch store multiple memories
await ltm.store_batch([
    {"content": "Memory 1", "metadata": {...}},
    {"content": "Memory 2", "metadata": {...}},
    {"content": "Memory 3", "metadata": {...}},
])

# Batch retrieve
results = await ltm.retrieve_batch([
    "Query 1",
    "Query 2",
    "Query 3"
])
```

### Index Optimization

```yaml
# config/memory.yaml
long_term:
  indexing:
    type: hnsw          # Hierarchical Navigable Small World
    ef_construction: 200  # Higher = better recall, slower build
    m: 16                 # Connections per node
    ef_search: 100       # Higher = better recall, slower search
```

---

## Best Practices

### 1. Memory Type Selection

| Information Type | Recommended Memory |
|-----------------|-------------------|
| Current conversation | STM |
| User preferences | LTM + Entity |
| Past decisions | LTM |
| People/Projects | Entity |
| Temporary notes | STM only |
| Long-term facts | LTM |

### 2. Metadata Strategy

```python
# Good: Structured, queryable metadata
await ltm.store(
    content="...",
    metadata={
        "type": "decision",
        "project": "alpha",
        "user_id": "john",
        "importance": "high",
        "tags": ["architecture", "database"]
    }
)

# Bad: Unstructured metadata
await ltm.store(
    content="...",
    metadata={"info": "some decision about architecture for john's project"}
)
```

### 3. Memory Hygiene

```python
# Regular cleanup
async def memory_maintenance():
    # Clean expired LTM entries
    await ltm.cleanup(older_than_days=90)

    # Compress STM if needed
    if stm.token_count > stm.config.max_tokens * 0.9:
        await stm.compress()

    # Remove orphaned entities
    await entity_mem.cleanup_orphans()
```

### 4. Privacy Considerations

```python
# Anonymize sensitive data before storage
content = anonymize_pii(user_message)
await ltm.store(content=content, metadata={"anonymized": True})

# Use encryption for sensitive memories
await ltm.store(
    content=encrypt(sensitive_data),
    metadata={"encrypted": True}
)
```

### 5. Testing Memory

```python
# Unit test memory operations
async def test_memory_retrieval():
    ltm = LongTermMemory(config=LTMConfig(
        storage_type="sqlite",
        storage_path=":memory:"  # In-memory for testing
    ))

    await ltm.store("Test content", {"test": True})
    results = await ltm.retrieve("Test", limit=1)

    assert len(results) == 1
    assert "Test content" in results[0].content
```

---

*Memory System Guide - JARVIS 2.0*
