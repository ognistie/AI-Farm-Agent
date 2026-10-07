# Contributing

AI Farm Agent welcomes contributions under the [MIT License](LICENSE). By submitting a contribution, you agree to license it under the same terms; no copyright assignment is required.

## Scope

Useful contributions include bug fixes, reproducible regression cases, agent evaluation, execution safety, documentation and improvements to the curated knowledge vault. For substantial architectural changes, discuss the problem and proposed approach in an issue before implementation. Small fixes can be submitted directly.

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Workflow

1. Fork the repository and create a focused branch.
2. Set up the environment using the README.
3. Make a coherent change and preserve unrelated behavior.
4. Run relevant checks. For Python agent changes, run `python -X utf8 scripts/smoke_code_agent.py` from `ai-farm-agent/`.
5. Open a pull request describing the problem, resulting behavior, validation and known limitations.

Use concise commit messages that explain the change. Existing history follows Conventional Commits, such as `fix:`, `feat:` and `docs:`.

## Tests and evidence

Add deterministic regression coverage for logic defects. Use mocks for API, filesystem and UI interactions where practical. Label live-model or desktop experiments explicitly, including API costs and side effects. Do not present model-generated success messages as proof that an artifact or UI state is correct.

## Documentation and knowledge vault

Keep architecture descriptions grounded in current code. Reference tasks should use synthetic data, useful keywords, a clear execution path and testable acceptance criteria. Curated lessons belong in the public vault; generated plans, reports and daily journals remain local.

## Privacy and security

Before submitting, inspect `git diff --cached` and the staged file list. Never include `.env`, credentials, browser sessions, private contacts, screenshots of personal accounts, learned route files or execution records. Use fictional contacts and reserved example domains in tests.

Report suspected vulnerabilities through the process in [SECURITY.md](SECURITY.md), without posting credentials or personal data in public issues. Do not bypass hooks or rewrite shared history as part of a normal contribution.

## Third-party material

Preserve original copyright and license notices. Verify that new assets and dependencies allow redistribution and document their origin. Contributions must be yours to license or included under compatible terms with attribution.
