---
description: Secure Coding Standards & Input Validation Guidelines
---

# Secure Coding Standards

This skill encapsulates the security practices learned from the **Security Self-Healing** session (2026-02-13).
It provides reusable patterns for sanitizing user inputs, validating IDs, and defending against prompt injection.

## 1. Input Sanitization (Anti-Injection)

**Rule**: All free-text inputs destined for an LLM *must* be sanitized.
**Goal**: Prevent "Ignore previous instructions" attacks.

### Validated Regex Patterns
Use these regex patterns to detect and filter malicious prompts:

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a|an|if)",
    r"pretend\s+(you|to\s+be)",
    r"system\s*:\s*",
    r"<\s*system\s*>",
    r"\[\s*system\s*\]",
    r"assistant\s*:\s*",
    r"\\n\s*system\s*:",
    r"REVEAL\s+(YOUR|THE)\s+(INSTRUCTIONS|PROMPT|SYSTEM)",
]
```

### Implementation Strategy
See `src/security/sanitizer.py` for the reference implementation:
1.  Truncate input length (max 2000 chars).
2.  Remove control characters.
3.  Replace injection patterns with `[FILTERED]`.
4.  Remove HTML/Script tags.

## 2. ID Validation

**Rule**: Product IDs and other identifiers *must* clear a strict allowlist.
**Goal**: Prevent Path Traversal and XSS via ID fields.

### Reference Logic
```python
def validate_product_id(product_id: str) -> str:
    # Allow: alphanumeric, hyphen, underscore
    if not re.match(r'^[a-zA-Z0-9\-_]+$', product_id):
        raise ValueError("Invalid ID format")
    return product_id
```

## 3. Transparency & Fallback

**Rule**: Users must know if a response is AI-generated or a hardcoded fallback.
**Reason**: To avoid "hallucination masking" where a dumb rule is presented as smart AI.

### Standard Practice
Return a structured object with `analysis_type`:
```json
{
  "content": "...",
  "analysis_type": "llm_generated" // or "rule_based"
}
```

## 4. Verification Test Template

When modifying these components, run the standard security test suite:
`pytest tests/test_security_healed.py`

Test Cases must cover:
1.  **Positive Case**: Valid input passes unchanged.
2.  **Negative Case (Injection)**: "Ignore instruction" -> `[FILTERED]`.
3.  **Negative Case (XSS)**: `<script>alert(1)</script>` -> `[FILTERED]`.
