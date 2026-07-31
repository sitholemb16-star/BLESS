---
applyTo: "src/api/**/*.ts"
---

- Only BARUK is authorized to request or approve API data pulls.
- Ensure all API keys are handled via environment variables or GitHub secrets.
- Reject any unpinned dependencies or mutable tags.
- Enforce strict linting and security checks on all API code.
