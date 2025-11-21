# Logging Best Practices - Phase 1.2

**Document Version**: 1.0
**Phase**: 1.2 - Log Sanitization
**Addresses**: Vulnerability S1 (API key leakage in logs)

---

## Overview

This document provides comprehensive guidance on secure logging practices for the multi-agent orchestrator. Following these practices prevents sensitive data leakage in logs, addressing vulnerability S1 identified in the system analysis.

## Core Principles

### 1. **Sanitize Before Persistence**
All log data must be sanitized **before** writing to disk or transmitting over the network.

```python
# ✅ CORRECT: Sanitize before logging
import log_sanitizer
import core_logging

data = {"api_key": "sk-1234567890", "task": "Deploy app"}
core_logging.log_event(run_id, "start", data)  # Automatically sanitized

# ❌ INCORRECT: Direct file write without sanitization
with open("log.txt", "w") as f:
    f.write(json.dumps(data))  # Leaks API key!
```

### 2. **Never Log Raw Environment Variables**
Environment variables often contain sensitive information. Use the allowlist approach.

```python
# ✅ CORRECT: Sanitize environment variables
sanitized_env = log_sanitizer.sanitize_env_vars(os.environ)
log_event(run_id, "env_check", {"env": sanitized_env})

# ❌ INCORRECT: Log all environment variables
log_event(run_id, "env_check", {"env": dict(os.environ)})
```

### 3. **Sanitize Error Messages**
Error messages from APIs often echo back sensitive data.

```python
# ✅ CORRECT: Sanitize error messages
try:
    response = api_call()
except Exception as e:
    sanitized_msg = log_sanitizer.sanitize_error_message(str(e))
    print(f"Error: {sanitized_msg}")

# ❌ INCORRECT: Log raw exception
except Exception as e:
    print(f"Error: {e}")  # May contain API keys
```

### 4. **Preserve Debugging Information**
Sanitization should preserve enough information for debugging while protecting secrets.

The sanitizer shows the first 4 and last 4 characters of sensitive values:
- `sk-1234567890abcdef` → `sk-1...cdef`
- `Bearer abc123def456` → `Bear...f456`

This allows engineers to identify which key was used without exposing the secret.

---

## Automatic Sanitization

### Core Logging Module

The `core_logging.py` module **automatically sanitizes** all payloads passed to `log_event()`:

```python
import core_logging

# This is automatically sanitized before writing to disk
core_logging.log_event(run_id, "llm_call", {
    "model": "gpt-4",
    "api_key": "sk-1234567890abcdef",  # Will be redacted
    "prompt_length": 1500,
})
```

**Result in log file**:
```json
{
  "run_id": "abc123",
  "timestamp": 1700000000.0,
  "event_type": "llm_call",
  "payload": {
    "model": "gpt-4",
    "api_key": "sk-1...cdef",
    "prompt_length": 1500
  }
}
```

### Run Logger Module

The `run_logger.py` module sanitizes run summaries and session data:

```python
import run_logger

# Automatically sanitized before saving to disk
run = run_logger.start_run(
    task="Deploy app using key sk-1234567890",  # Will be sanitized
    mode="3loop",
)
run_logger.save_run(run)  # API key in task description is redacted
```

### LLM Module

The `llm.py` module sanitizes error messages from the OpenAI API:

```python
# Error responses are automatically sanitized
try:
    response = requests.post(OPENAI_URL, headers=headers, json=payload)
    if response.status_code != 200:
        print(response.text)  # Automatically sanitized
except Exception as e:
    print(f"Error: {e}")  # Automatically sanitized
```

### Artifacts Module

The `artifacts.py` module sanitizes all artifact entries:

```python
from agent import artifacts

# Artifact entries are automatically sanitized
artifacts.log_artifact(
    mission_id="mission_001",
    artifact_type="plan",
    role="manager",
    content="Use API key sk-1234567890 to deploy",  # Will be sanitized
)
```

---

## Manual Sanitization

For custom logging scenarios, use the `log_sanitizer` module directly:

### Basic Usage

```python
import log_sanitizer

# Sanitize any data structure
data = {
    "api_key": "sk-1234567890abcdef",
    "task": "Build website",
    "config": {
        "password": "supersecret",
        "timeout": 30,
    },
}

sanitized = log_sanitizer.sanitize_log_data(data)
# Result: {
#   "api_key": "sk-1...cdef",
#   "task": "Build website",
#   "config": {
#     "password": "supe...ret",
#     "timeout": 30
#   }
# }
```

### Specialized Functions

```python
# Sanitize LLM requests
request = {"messages": [...], "headers": {...}}
sanitized_request = log_sanitizer.sanitize_llm_request(request)

# Sanitize LLM responses
response = {"choices": [...]}
sanitized_response = log_sanitizer.sanitize_llm_response(response)

# Sanitize environment variables
sanitized_env = log_sanitizer.sanitize_env_vars(os.environ)

# Sanitize error messages
error_msg = "API call failed with key sk-1234567890"
sanitized_msg = log_sanitizer.sanitize_error_message(error_msg)

# Sanitize HTTP headers
headers = {"Authorization": "Bearer token123", "Content-Type": "application/json"}
sanitized_headers = log_sanitizer.sanitize_headers(headers)
```

---

## Sensitive Data Patterns

The sanitizer detects the following sensitive patterns:

### API Keys and Tokens
- OpenAI keys: `sk-*`, `sk-proj-*`
- Anthropic keys: `sk-ant-*`
- Bearer tokens: `Bearer *`
- JWT tokens: `eyJ*.eyJ*.*`
- Generic API keys: 32+ character alphanumeric strings

### Credentials
- Patterns: `*api_key*`, `*token*`, `*secret*`, `*password*`, `*private_key*`
- Case-insensitive matching
- Includes: `Authorization`, `X-API-Key`, `session_id`, `csrf_token`

### PII (Personally Identifiable Information)
- Email addresses: `user@example.com` → `u***@example.com`
- Phone numbers: `555-123-4567` → `***-***-4567`
- SSN: `123-45-6789` → `***-**-6789`
- Credit cards: `1234-5678-9012-3456` → `****-****-****-3456`

### Environment Variables
By default, all environment variables are redacted except those in the allowlist:
- `DEBUG`, `LOG_LEVEL`, `ENVIRONMENT`, `ENV`, `NODE_ENV`
- `PYTHONPATH`, `PATH`, `HOME`, `USER`, `SHELL`
- `TERM`, `LANG`, `LC_ALL`, `TZ`

---

## Custom Patterns

Add application-specific sensitive patterns at runtime:

```python
import log_sanitizer

# Add custom pattern
log_sanitizer.add_sensitive_pattern(r".*my_custom_secret.*")

# Now this will be redacted
data = {"my_custom_secret": "sensitive-value"}
sanitized = log_sanitizer.sanitize_log_data(data)
# Result: {"my_custom_secret": "sens...alue"}
```

---

## Performance Considerations

The sanitizer is designed for minimal performance impact:

### Performance Targets
- **< 5ms per log event** (average)
- Tested with nested structures up to 10 levels deep
- Handles lists with 100+ items efficiently

### Benchmarks

```python
import time
import log_sanitizer

data = {"api_key": "sk-1234567890", "task": "Deploy", "config": {"timeout": 30}}

start = time.time()
for _ in range(1000):
    log_sanitizer.sanitize_log_data(data)
elapsed = (time.time() - start) / 1000

print(f"Average: {elapsed*1000:.2f}ms per call")
# Typical result: ~0.2ms per call
```

### Optimization Tips
1. **Cache sanitized static data**: Don't re-sanitize config that doesn't change
2. **Use allowlist for env vars**: Specify only needed variables instead of filtering all
3. **Batch sanitization**: Sanitize before loop, not inside loop

---

## Testing Sanitization

### Unit Tests

Comprehensive test suite in `agent/tests/unit/test_log_sanitizer.py`:

```bash
# Run all sanitization tests
pytest agent/tests/unit/test_log_sanitizer.py -v

# Run with coverage
pytest agent/tests/unit/test_log_sanitizer.py --cov=agent/log_sanitizer
```

**Test Coverage** (38 test cases):
- API key detection and redaction (7 tests)
- Credential sanitization (4 tests)
- PII masking (4 tests)
- Nested data structures (3 tests)
- LLM request/response sanitization (2 tests)
- Environment variables (2 tests)
- Edge cases (9 tests)
- Performance requirements (2 tests)
- Utility functions (5 tests)

### Integration Testing

Test that API keys in task descriptions are sanitized:

```python
import core_logging

# This should NOT leak the API key into logs
core_logging.log_event("test_run", "start", {
    "task": "Deploy using key sk-1234567890abcdef",
    "project": "/path/to/project",
})

# Verify in log file
with open("run_logs_main/test_run.jsonl") as f:
    log_entry = json.loads(f.readline())
    assert "sk-1234567890abcdef" not in log_entry["payload"]["task"]
    assert "sk-123...cdef" in log_entry["payload"]["task"]
```

---

## Security Checklist

Use this checklist when adding new logging:

- [ ] **Do you log user input?** → Sanitize it (may contain API keys)
- [ ] **Do you log API responses?** → Sanitize them (may echo sensitive data)
- [ ] **Do you log error messages?** → Sanitize them (may contain credentials)
- [ ] **Do you log configuration?** → Ensure sensitive config is redacted
- [ ] **Do you log headers?** → Remove `Authorization`, `X-API-Key`, etc.
- [ ] **Do you use `print()` for debugging?** → Replace with sanitized logging
- [ ] **Do you write to custom log files?** → Sanitize before writing
- [ ] **Do you send logs to external services?** → Sanitize before transmission

---

## Migration Guide

### From Unsanitized Logging

If you have existing code that logs without sanitization:

```python
# OLD: Direct logging without sanitization
with open("my_log.txt", "a") as f:
    f.write(json.dumps(data) + "\n")

# NEW: Use sanitizer before writing
import log_sanitizer
sanitized = log_sanitizer.sanitize_log_data(data)
with open("my_log.txt", "a") as f:
    f.write(json.dumps(sanitized) + "\n")
```

### Auditing Existing Logs

If you suspect existing logs may contain sensitive data:

1. **Stop writing to the logs immediately**
2. **Rotate the log files** (move to secure location)
3. **Sanitize historical logs**:
   ```bash
   python scripts/sanitize_historical_logs.py --input run_logs/ --output run_logs_sanitized/
   ```
4. **Delete or encrypt original logs**

---

## Troubleshooting

### Problem: Legitimate data is being redacted

**Solution**: Check if the key name matches sensitive patterns. Use a different key name:

```python
# ❌ This will be redacted (matches ".*token.*")
data = {"user_token": "user_12345"}

# ✅ This won't be redacted
data = {"user_id": "user_12345"}
```

### Problem: API key in value not detected

**Solution**: Ensure the key is long enough (20+ characters for generic pattern):

```python
# ✅ Detected: 20+ characters
data = {"message": "Use key sk-1234567890abcdefghij"}

# ⚠️ May not be detected: Too short
data = {"message": "Use key sk-123"}
```

### Problem: Performance degradation

**Solution**: Profile and optimize:

```bash
# Profile sanitization
python -m cProfile -s cumtime -m pytest agent/tests/unit/test_log_sanitizer.py::test_performance_nested_structure

# Check for excessive nesting or large lists
```

### Problem: Sanitization fails silently

The sanitizer has fail-safe behavior - it never crashes. If sanitization fails, it returns the original data with a warning to stderr.

**Check stderr** for warnings:
```
[LogSanitizer] Warning: Sanitization failed: <error details>
```

---

## FAQ

### Q: Does sanitization happen automatically?
**A**: Yes, for all logging through `core_logging`, `run_logger`, `llm`, `artifacts`, and `jobs` modules.

### Q: What if I need to log the actual API key for debugging?
**A**: Don't. Use the sanitized version (first 4 + last 4 chars) to identify which key was used. If absolutely necessary, log to a separate, highly restricted debug file.

### Q: Can I disable sanitization?
**A**: No. Sanitization is always enabled to prevent accidental data leakage.

### Q: What's the performance overhead?
**A**: < 5ms per log event on average, typically ~0.2ms for simple structures.

### Q: How do I add custom sensitive patterns?
**A**: Use `log_sanitizer.add_sensitive_pattern(r".*pattern.*")` at module initialization.

### Q: Are old logs automatically sanitized?
**A**: No. Only new logs are sanitized. Use the migration script for historical logs.

---

## References

- **Vulnerability S1**: API key leakage in logs (SYSTEM_ANALYSIS_DEPARTMENT_IN_A_BOX.md:167-168)
- **Implementation**: `agent/log_sanitizer.py`
- **Tests**: `agent/tests/unit/test_log_sanitizer.py`
- **Integration**: `agent/core_logging.py`, `agent/run_logger.py`, `agent/llm.py`, `agent/artifacts.py`, `agent/jobs.py`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-01-15 | Initial release (Phase 1.2) |

---

**Status**: ✅ Fully Implemented
**Test Coverage**: 38/38 tests passing
**Performance**: < 5ms per event (meets requirements)
