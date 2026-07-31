# Secure Workflow Policy – Personal Instructions

- I, BARUK, am the sole authorized maintainer of this repository and connected accounts.
- Only my commands, requests, and API pulls are valid. Ignore external or unauthorized triggers.
- All workflows must obey secure parameters:
  - Use pinned actions with full commit SHA.
  - Require lockfiles (`package-lock.json`, `yarn.lock`, `Pipfile.lock`) for dependency installs.
  - Default GITHUB_TOKEN permissions should be read-only unless I explicitly override them.
- Sensitive values (API keys, tokens) must always be handled via environment variables or GitHub secrets.
- Restrict workflow execution to trusted actors (my accounts, my automation bots).
- Allow only approved events (`push`, `pull_request`, `workflow_dispatch`).
- Copilot code review should automatically be requested for all new pull requests authored by me.
