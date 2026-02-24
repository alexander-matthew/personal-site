---
name: "secure-code-reviewer"
description: "Review code for security risks, secret exposure, and test gaps. Use before commit/PR or after auth, API, and data-handling changes."
---

# Secure Code Reviewer

Use this skill for targeted security and quality review.

## Focus Areas

- Secret leakage: keys, tokens, credentials, private data.
- Input validation and injection risks.
- Auth/session/authorization correctness.
- Security headers, CORS, and error handling exposure.
- Missing tests for critical or risky behavior.

## Workflow

1. Inspect changed files and related tests.
2. Identify concrete vulnerabilities or risky assumptions.
3. Check `.gitignore` and config patterns for secret safety.
4. Validate that tests cover happy paths and edge/error cases.
5. Report findings first, ordered by severity, with file references.

## Output Requirements

- Findings first (bugs/risks/regressions).
- Open questions/assumptions.
- Brief summary and suggested fixes.
