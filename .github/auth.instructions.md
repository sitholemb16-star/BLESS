---
applyTo: "{src/auth/**/*.ts,auth/**/*.ts}"
---

# Auth Path Instructions

- Only BARUK is authorized to request or approve auth data pulls.
- Ensure all auth keys and tokens are handled only via environment variables or GitHub secrets.
- Reject unpinned dependencies and mutable tags.
- Enforce strict linting, type checks, and security checks on all auth code.
- Never log credentials, tokens, session IDs, or personally identifiable auth payloads.
- Require tests for all auth logic changes (success, failure, and edge cases).
