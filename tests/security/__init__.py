"""
Security Test Suite

Comprehensive tests for JARVIS security components:
- Sandbox filesystem isolation
- Sandbox resource limits
- Network domain validation
- Profile configuration

Run all security tests:
    pytest tests/security/ -v

Run only network tests:
    pytest tests/security/test_network.py -v

Run only sandbox tests:
    pytest tests/security/test_sandbox.py -v

Run excluding slow tests:
    pytest tests/security/ -v -m "not slow"
"""
