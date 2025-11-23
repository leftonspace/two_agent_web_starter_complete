"""
Code API endpoints for JARVIS VS Code extension and CLI.
Provides code analysis, completion, review, and security scanning.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import re

router = APIRouter(prefix="/api/code", tags=["code"])


# Request/Response Models
class CodeActionRequest(BaseModel):
    action: str
    code: str
    language: str = "unknown"
    file_name: Optional[str] = None
    question: Optional[str] = None


class CodeCompleteRequest(BaseModel):
    prefix: str
    suffix: str = ""
    language: str = "unknown"
    file_name: Optional[str] = None
    max_tokens: int = 150


class CommitMessageRequest(BaseModel):
    diff: str


class IndexRequest(BaseModel):
    workspace: str
    files: List[Dict[str, str]]


class PRReviewRequest(BaseModel):
    files: List[Dict[str, Any]]
    title: str = ""
    description: str = ""


class AnalyzeRequest(BaseModel):
    code: str
    type: str = "general"
    language: str = "auto"


class QuickScanRequest(BaseModel):
    code: str
    language: str = "unknown"


# Import the JARVIS chat handler for LLM access
def get_llm_response(prompt: str, max_tokens: int = 2000) -> str:
    """Get response from LLM."""
    try:
        from jarvis_chat import JarvisChat
        jarvis = JarvisChat()
        response = jarvis.handle_simple_query(prompt)
        return response
    except Exception as e:
        return f"Error: {str(e)}"


@router.post("/action")
async def code_action(request: CodeActionRequest):
    """
    Handle various code actions: explain, improve, generate_tests, review, ask, security_scan
    """
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")

    # Build prompt based on action
    prompts = {
        'explain': f"""Explain the following {request.language} code in detail.
Break down what each part does and explain the overall purpose.

```{request.language}
{request.code}
```

Provide a clear, educational explanation suitable for developers.""",

        'improve': f"""Review and improve the following {request.language} code.
Suggest improvements for:
- Code quality and readability
- Performance optimizations
- Best practices
- Potential bugs

```{request.language}
{request.code}
```

Provide the improved code with explanations for each change.""",

        'generate_tests': f"""Generate comprehensive unit tests for the following {request.language} code.
Include tests for:
- Normal cases
- Edge cases
- Error handling

```{request.language}
{request.code}
```

Use appropriate testing framework for {request.language} (pytest for Python, Jest for JavaScript, etc.).""",

        'review': f"""Perform a thorough code review of the following {request.language} file{f' ({request.file_name})' if request.file_name else ''}.

Review for:
1. Code quality and maintainability
2. Potential bugs or issues
3. Security vulnerabilities
4. Performance concerns
5. Best practices compliance

```{request.language}
{request.code}
```

Provide actionable feedback with specific line references where applicable.""",

        'ask': f"""Answer the following question about this {request.language} code:

Question: {request.question}

```{request.language}
{request.code}
```

Provide a detailed, helpful answer.""",

        'security_scan': f"""Perform a security audit of the following {request.language} code{f' ({request.file_name})' if request.file_name else ''}.

Check for:
1. OWASP Top 10 vulnerabilities
2. Injection vulnerabilities (SQL, command, XSS)
3. Authentication/Authorization issues
4. Sensitive data exposure
5. Security misconfigurations
6. Insecure dependencies patterns

```{request.language}
{request.code}
```

Report findings with severity levels (Critical, High, Medium, Low) and remediation suggestions."""
    }

    prompt = prompts.get(request.action)
    if not prompt:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")

    result = get_llm_response(prompt)

    return {
        "action": request.action,
        "result": result,
        "language": request.language
    }


@router.post("/complete")
async def code_complete(request: CodeCompleteRequest):
    """
    Provide inline code completion suggestions.
    """
    if not request.prefix:
        return {"completion": ""}

    prompt = f"""Complete the following {request.language} code. Only provide the completion, no explanation.
The code before cursor:
```{request.language}
{request.prefix}
```

The code after cursor:
```{request.language}
{request.suffix}
```

Provide ONLY the code that should be inserted at the cursor position. Keep it concise and contextually appropriate.
Do not include markdown code blocks or explanations, just the raw code completion."""

    completion = get_llm_response(prompt, max_tokens=request.max_tokens)

    # Clean up completion - remove markdown formatting if present
    completion = re.sub(r'^```\w*\n?', '', completion)
    completion = re.sub(r'\n?```$', '', completion)
    completion = completion.strip()

    return {
        "completion": completion,
        "language": request.language
    }


@router.post("/commit-message")
async def generate_commit_message(request: CommitMessageRequest):
    """
    Generate a commit message from git diff.
    """
    if not request.diff:
        raise HTTPException(status_code=400, detail="No diff provided")

    prompt = f"""Generate a concise, conventional commit message for the following git diff.

Follow these guidelines:
- Use conventional commit format: type(scope): description
- Types: feat, fix, docs, style, refactor, test, chore
- Keep the first line under 72 characters
- Add a brief body if needed for complex changes

Git diff:
```diff
{request.diff[:8000]}
```

Provide ONLY the commit message, no explanation or markdown."""

    message = get_llm_response(prompt, max_tokens=200)

    # Clean up
    message = message.strip()
    message = re.sub(r'^```\w*\n?', '', message)
    message = re.sub(r'\n?```$', '', message)

    return {"message": message.strip()}


@router.post("/index")
async def index_workspace(request: IndexRequest):
    """
    Index workspace files for codebase-aware responses.
    """
    indexed_count = len(request.files)

    # In production, you would:
    # 1. Generate embeddings for each file
    # 2. Store in vector database
    # 3. Use for RAG in code responses

    return {
        "status": "indexed",
        "workspace": request.workspace,
        "files_indexed": indexed_count
    }


@router.post("/review-pr")
async def review_pr(request: PRReviewRequest):
    """
    Review a pull request with multiple file changes.
    """
    if not request.files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Build context from all files
    file_context = ""
    for f in request.files[:10]:  # Limit to 10 files
        file_context += f"\n### {f.get('path', 'unknown')}\n"
        if f.get('diff'):
            file_context += f"```diff\n{f['diff'][:2000]}\n```\n"
        elif f.get('content'):
            file_context += f"```\n{f['content'][:2000]}\n```\n"

    prompt = f"""Review this pull request:

Title: {request.title}
Description: {request.description}

Files changed:
{file_context}

Provide a comprehensive PR review including:
1. Overall assessment
2. Code quality feedback
3. Potential issues or bugs
4. Security concerns
5. Suggestions for improvement
6. Approval recommendation (Approve / Request Changes / Comment)

Be constructive and specific with line references where applicable."""

    result = get_llm_response(prompt)

    return {
        "review": result,
        "files_reviewed": len(request.files)
    }


@router.post("/analyze")
async def analyze_code(request: AnalyzeRequest):
    """
    General code analysis endpoint for CLI.
    """
    if not request.code:
        raise HTTPException(status_code=400, detail="No code provided")

    analysis_prompts = {
        'general': f"""Analyze this code and provide insights on:
1. Purpose and functionality
2. Code structure and organization
3. Potential improvements
4. Notable patterns used

```
{request.code}
```""",

        'complexity': f"""Analyze the complexity of this code:
1. Time complexity of main functions
2. Space complexity
3. Cyclomatic complexity assessment
4. Suggestions for reducing complexity

```
{request.code}
```""",

        'dependencies': f"""Analyze the dependencies and imports in this code:
1. List all external dependencies
2. Identify potential security concerns with dependencies
3. Suggest alternatives if applicable
4. Check for unused imports

```
{request.code}
```"""
    }

    prompt = analysis_prompts.get(request.type, analysis_prompts['general'])
    result = get_llm_response(prompt)

    return {
        "analysis": result,
        "type": request.type,
        "language": request.language
    }


# Security patterns for quick scanning
SECURITY_PATTERNS = {
    'sql_injection': [
        r'execute\s*\(\s*["\'].*%s',
        r'execute\s*\(\s*f["\']',
        r'cursor\.execute\s*\([^,]+\+',
    ],
    'command_injection': [
        r'os\.system\s*\(',
        r'subprocess\.\w+\s*\([^)]*shell\s*=\s*True',
        r'eval\s*\(',
        r'exec\s*\(',
    ],
    'xss': [
        r'innerHTML\s*=',
        r'document\.write\s*\(',
        r'\.html\s*\([^)]*\+',
    ],
    'hardcoded_secrets': [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'AWS_SECRET',
    ],
    'insecure_random': [
        r'random\.\w+\(',
        r'Math\.random\(',
    ]
}


@router.post("/quick-scan")
async def quick_security_scan(request: QuickScanRequest):
    """
    Quick regex-based security scan for common vulnerabilities.
    """
    findings = []

    for category, patterns in SECURITY_PATTERNS.items():
        for pattern in patterns:
            try:
                matches = re.finditer(pattern, request.code, re.IGNORECASE)
                for match in matches:
                    # Find line number
                    line_num = request.code[:match.start()].count('\n') + 1
                    findings.append({
                        'category': category,
                        'pattern': pattern,
                        'line': line_num,
                        'match': match.group()[:100],
                        'severity': 'high' if category in ['sql_injection', 'command_injection'] else 'medium'
                    })
            except re.error:
                continue

    return {
        "findings": findings,
        "total_issues": len(findings),
        "language": request.language
    }
