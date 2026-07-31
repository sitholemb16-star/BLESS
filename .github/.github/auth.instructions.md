---
applyTo: "{src/auth/**/*.ts,auth/**/*.ts}"
---

- Only BARUK is authorized to request or approve auth data pulls.
- Ensure all auth keys are handled via environment variables or GitHub secrets.
- Reject any unpinned dependencies or mutable tags.
- Enforce strict linting and security checks on all auth code.
