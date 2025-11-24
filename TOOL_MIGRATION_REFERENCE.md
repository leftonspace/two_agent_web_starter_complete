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

### Before (Old Names)
```python
# Old tool names (deprecated)
file_read("example.py")
file_write("output.txt", content)
file_edit("config.py", old_str, new_str)
execute_command("ls -la")
```

### After (New Names)
```python
# New standardized tool names
Read("example.py")
Write("output.txt", content)
Edit("config.py", old_str, new_str)
Bash("ls -la")
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
