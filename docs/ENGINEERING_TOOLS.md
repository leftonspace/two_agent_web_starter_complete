# JARVIS Engineering Tools

This document describes the engineering tools available in JARVIS for developers, including the VS Code extension, CLI tool, and Code Review Agent.

## Table of Contents

1. [VS Code Extension](#vs-code-extension)
2. [CLI Tool](#cli-tool)
3. [Code API](#code-api)
4. [Code Review Agent](#code-review-agent)

---

## VS Code Extension

The JARVIS VS Code extension provides AI-powered coding assistance directly in your IDE.

### Installation

```bash
cd tools/vscode-extension
npm install
npm run compile
```

To install in VS Code:
1. Run `npm run package` to create a `.vsix` file
2. In VS Code, go to Extensions > Install from VSIX
3. Select the generated `.vsix` file

### Features

#### 1. Chat Sidebar
- Open with `Ctrl+Shift+J` (Mac: `Cmd+Shift+J`)
- Ask questions about code
- Get help with programming concepts
- Selected code is automatically included as context

#### 2. Inline Code Completion
- Trigger with `Ctrl+Shift+Space` (Mac: `Cmd+Shift+Space`)
- Automatic suggestions while typing (configurable delay)
- Context-aware completions based on surrounding code

#### 3. Code Actions (Right-click menu)
- **Explain Code**: Get detailed explanations of selected code
- **Improve Code**: Suggestions for code quality improvements
- **Generate Tests**: Auto-generate unit tests
- **Ask About Code**: Ask specific questions about code

#### 4. Commands (Command Palette)
| Command | Description |
|---------|-------------|
| `JARVIS: Open Chat` | Open chat sidebar |
| `JARVIS: Explain Selected Code` | Explain highlighted code |
| `JARVIS: Improve Selected Code` | Get improvement suggestions |
| `JARVIS: Generate Tests` | Generate unit tests |
| `JARVIS: Review Current File` | Full code review |
| `JARVIS: Generate Commit Message` | Generate git commit message |
| `JARVIS: Security Scan` | Security vulnerability scan |
| `JARVIS: Index Workspace` | Index codebase for better context |

### Configuration

Settings available in VS Code settings:

```json
{
  "jarvis.serverUrl": "http://localhost:8000",
  "jarvis.enableInlineCompletion": true,
  "jarvis.completionDelay": 500,
  "jarvis.maxCompletionTokens": 150,
  "jarvis.enableCodeLens": true,
  "jarvis.autoIndexWorkspace": false
}
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+J` | Open JARVIS Chat |
| `Ctrl+Shift+Space` | Trigger inline completion |
| `Ctrl+Shift+E` | Explain selected code |

---

## CLI Tool

The JARVIS CLI provides command-line access to all JARVIS features.

### Installation

```bash
cd tools/cli
pip install -e .
```

Or use directly:
```bash
python tools/cli/jarvis_cli.py
```

### Environment Variables

```bash
export JARVIS_SERVER="http://localhost:8000"
```

### Commands

#### Chat
```bash
jarvis chat "How do I implement a binary search in Python?"
```

#### Analyze Code
```bash
# Analyze a file
jarvis analyze file.py

# Analyze from stdin
cat file.py | jarvis analyze --stdin

# Specify analysis type
jarvis analyze file.py --type complexity
jarvis analyze file.py --type dependencies
```

#### Code Review
```bash
jarvis review src/main.py
jarvis review --stdin < file.py
```

#### Security Scan
```bash
# Quick regex-based scan
jarvis security app.py

# Full LLM-based security analysis
jarvis security app.py --full
```

#### Generate Commit Message
```bash
# From current git diff
jarvis commit-msg

# From piped diff
git diff | jarvis commit-msg --stdin

# Copy to clipboard
jarvis commit-msg --copy

# Apply commit directly
jarvis commit-msg --apply
```

#### Explain Code
```bash
jarvis explain file.py
```

#### Improve Code
```bash
jarvis improve file.py
```

#### Generate Tests
```bash
jarvis tests file.py
```

#### Ask About Code
```bash
jarvis ask "What does this function do?" file.py
```

### Pipe Support

The CLI supports Unix pipes for integration with other tools:

```bash
# Analyze clipboard content (Linux)
xclip -o | jarvis analyze --stdin

# Generate commit message from staged changes
git diff --staged | jarvis commit-msg --stdin

# Review a specific function
sed -n '10,50p' file.py | jarvis review --stdin --language python
```

---

## Code API

The Code API provides HTTP endpoints for IDE extensions and tools.

### Base URL
```
http://localhost:8000/api/code
```

### Endpoints

#### POST /api/code/action
Perform various code actions.

**Request:**
```json
{
  "action": "explain|improve|generate_tests|review|ask|security_scan",
  "code": "your code here",
  "language": "python",
  "file_name": "optional_filename.py",
  "question": "optional question for 'ask' action"
}
```

**Response:**
```json
{
  "action": "explain",
  "result": "Code explanation...",
  "language": "python"
}
```

#### POST /api/code/complete
Get inline code completions.

**Request:**
```json
{
  "prefix": "code before cursor",
  "suffix": "code after cursor",
  "language": "python",
  "max_tokens": 150
}
```

**Response:**
```json
{
  "completion": "suggested code",
  "language": "python"
}
```

#### POST /api/code/commit-message
Generate commit message from diff.

**Request:**
```json
{
  "diff": "git diff content"
}
```

**Response:**
```json
{
  "message": "feat(auth): add user authentication..."
}
```

#### POST /api/code/index
Index workspace for codebase-aware responses.

**Request:**
```json
{
  "workspace": "/path/to/project",
  "files": [
    {"path": "file.py", "content": "...", "language": "python"}
  ]
}
```

#### POST /api/code/review-pr
Review a pull request.

**Request:**
```json
{
  "files": [
    {"path": "file.py", "content": "...", "diff": "..."}
  ],
  "title": "PR Title",
  "description": "PR Description"
}
```

#### POST /api/code/analyze
General code analysis.

**Request:**
```json
{
  "code": "your code",
  "type": "general|complexity|dependencies",
  "language": "python"
}
```

#### POST /api/code/quick-scan
Quick regex-based security scan.

**Request:**
```json
{
  "code": "your code",
  "language": "python"
}
```

**Response:**
```json
{
  "findings": [
    {
      "category": "sql_injection",
      "line": 42,
      "match": "cursor.execute(query + user_input)",
      "severity": "high"
    }
  ],
  "total_issues": 1
}
```

---

## Code Review Agent

The Code Review Agent provides automated code review with security scanning, best practices enforcement, and complexity analysis.

### Python API

```python
from agent.code_review import CodeReviewAgent, get_review_agent

# Get singleton instance
agent = get_review_agent()

# Review code string
report = agent.review(
    code="your code here",
    language="python",
    file_path="optional/path.py"
)

# Review a file
report = agent.review_file("/path/to/file.py")

# Review multiple files (PR review)
pr_report = agent.review_pr([
    {"path": "file1.py", "content": "...", "language": "python"},
    {"path": "file2.js", "content": "...", "language": "javascript"},
])

# Get report in different formats
print(report.to_json())
print(report.to_markdown())
```

### Review Report Structure

```python
ReviewReport:
  - file_path: str
  - language: str
  - issues: List[ReviewIssue]
  - summary: str
  - score: int (0-100)
  - passed: bool

ReviewIssue:
  - category: IssueCategory (security, performance, maintainability, bug_risk, style, best_practice)
  - severity: Severity (critical, high, medium, low, info)
  - title: str
  - description: str
  - file_path: str
  - line_number: int
  - code_snippet: str
  - suggestion: str
  - cwe_id: str (for security issues)
```

### Security Patterns Detected

#### Python
- SQL Injection (CWE-89)
- Command Injection (CWE-78)
- Code Injection via eval/exec (CWE-94)
- Hardcoded Secrets (CWE-798)
- Insecure Random (CWE-330)
- Path Traversal (CWE-22)
- Unsafe Pickle Deserialization (CWE-502)
- Unsafe YAML Load (CWE-502)

#### JavaScript
- XSS via innerHTML/document.write (CWE-79)
- Code Injection via eval (CWE-94)
- Hardcoded Secrets (CWE-798)
- Prototype Pollution (CWE-1321)

### Best Practices Checked

#### Python
- Bare except clauses
- Mutable default arguments
- Print statements (should use logging)
- TODO/FIXME comments
- Long functions (>50 lines)
- Too many function arguments (>5)
- Deep nesting (>4 levels)
- Large classes (>20 methods)

#### JavaScript
- Use of `var` (should use let/const)
- Loose equality `==` (should use `===`)
- Console statements in production code

---

## Integration Examples

### Git Hooks

#### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run security scan on staged Python files
for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    result=$(jarvis security "$file" 2>&1)
    if echo "$result" | grep -q "HIGH\|CRITICAL"; then
        echo "Security issues found in $file"
        echo "$result"
        exit 1
    fi
done
```

#### Prepare-commit-msg Hook
```bash
#!/bin/bash
# .git/hooks/prepare-commit-msg

# Auto-generate commit message
if [ -z "$(cat $1)" ]; then
    jarvis commit-msg > "$1"
fi
```

### CI/CD Integration

#### GitHub Actions
```yaml
name: Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install JARVIS CLI
        run: pip install -e tools/cli
      - name: Security Scan
        run: |
          for file in $(git diff --name-only origin/main | grep '\.py$'); do
            jarvis security "$file" --full
          done
```

---

## Troubleshooting

### VS Code Extension

**Extension not connecting:**
1. Ensure JARVIS server is running: `python start_webapp.py`
2. Check server URL in VS Code settings
3. Verify firewall allows connections

**Completions not appearing:**
1. Check `jarvis.enableInlineCompletion` setting
2. Increase `jarvis.completionDelay` if network is slow
3. Check VS Code output panel for errors

### CLI Tool

**Connection refused:**
```bash
# Check if server is running
curl http://localhost:8000/health

# Start server if not running
python start_webapp.py
```

**Timeout errors:**
- The server may be processing a large request
- Increase timeout in jarvis_cli.py if needed

---

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  VS Code Ext    │────▶│   Code API       │────▶│  JARVIS Chat    │
└─────────────────┘     │  (/api/code/*)   │     │  (LLM Backend)  │
                        └──────────────────┘     └─────────────────┘
┌─────────────────┐            │
│   CLI Tool      │────────────┘
└─────────────────┘            │
                               ▼
                        ┌──────────────────┐
                        │  Code Review     │
                        │  Agent           │
                        │  - Security Scan │
                        │  - Best Practices│
                        │  - Complexity    │
                        └──────────────────┘
```

---

*Last Updated: November 2025*
