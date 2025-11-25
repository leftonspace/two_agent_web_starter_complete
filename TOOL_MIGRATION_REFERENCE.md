# Tool Name Migration Reference

This document maps old tool names to new standardized names in Claude Code.

## Tool Name Changes

All tools have been updated to use consistent, action-based naming:

| Old Name | New Name | Description |
|----------|----------|-------------|
| `file_read` | `Read` | Read file contents |
| `file_write` | `Write` | Write file contents |
| `file_edit` | `Edit` | Edit file with string replacement |
| `file_glob` | `Glob` | Find files matching pattern |
| `file_grep` | `Grep` | Search file contents with regex |
| `execute_command` | `Bash` | Execute bash command |
| `create_file` | `Write` | Create new file |
| `modify_file` | `Edit` | Modify existing file |

## Current Tool Set

JARVIS now uses these standardized tools:

### File Operations
- **Read**: Read file contents
- **Write**: Write/create files
- **Edit**: Modify files with string replacement
- **Glob**: Find files by pattern
- **Grep**: Search file contents

### Code Operations
- **Bash**: Execute shell commands
- **Task**: Launch specialized agents
- **Skill**: Execute specialized skills

### Advanced Tools
- **WebFetch**: Fetch web content
- **WebSearch**: Search the web
- **NotebookEdit**: Edit Jupyter notebooks

## Migration Impact

### Code Changes
All tool calls in the codebase have been updated to use new names. No action required for existing code.

### Documentation Updates
Documentation has been updated to reflect new tool names. Some historical references may remain for context.

### API Compatibility
The new tool names are part of Claude Code's standard toolkit and are used throughout the system.

## Usage Examples

The new tool names are used by the AI assistant within tool calls (not as Python functions).

### Claude Code Tool Call Format

When JARVIS or Claude Code uses tools, they appear in the conversation as structured tool calls:

```
# Reading a file
Tool: Read
Parameters: {"file_path": "/path/to/example.py"}

# Writing a file
Tool: Write
Parameters: {"file_path": "/path/to/output.txt", "content": "file content here"}

# Editing a file
Tool: Edit
Parameters: {"file_path": "/path/to/config.py", "old_string": "old text", "new_string": "new text"}

# Executing a command
Tool: Bash
Parameters: {"command": "ls -la"}
```

### Python Code (Agent Internals)

Within JARVIS agent code, tools are accessed through the tools registry:

```python
from agent.jarvis_tools import JarvisTools

tools = JarvisTools(workspace="/path/to/workspace")

# Read file
content = await tools.read("/path/to/file.py")

# Write file
await tools.write("/path/to/output.txt", "content here")

# Edit file
await tools.edit("/path/to/config.py", "old_text", "new_text")

# Execute command
result = await tools.bash("ls -la", timeout=30)
```

## References

- All tools follow Claude Code standard naming conventions
- Tools use PascalCase for consistency
- Action-based naming (what the tool does)
- No prefixes (file_, execute_, etc.)

## Related Documentation

- Tool usage guide: See project documentation
- API reference: Check docs/JARVIS_2_0_API_REFERENCE.md
- Developer guide: DEVELOPER_GUIDE.md
