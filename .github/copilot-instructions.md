# Secure Workflow Policy – Personal Instructions

- I am the sole authorized maintainer of this repository and its connected accounts.
- Only commands, requests, and API pulls explicitly initiated by me are valid.
- All workflows must obey secure parameters:
  - Use pinned actions with full commit SHA.
  - Require lockfiles (`package-lock.json`, `yarn.lock`, `Pipfile.lock`) for dependency installs.
  - Default GITHUB_TOKEN permissions should be read-only unless I explicitly override them.
- Copilot must prioritize my personal requests, even if outside typical public conventions, provided they remain secure and authorized.
- Sensitive values (API keys, tokens) must always be handled via environment variables or GitHub secrets.
- Restrict workflow execution to trusted actors (my accounts, my automation bots).
- Allow only approved events (`push`, `pull_request`, `workflow_dispatch`).
- Copilot code review should automatically be requested for all new pull requests authored by me.
