# Security policy

AI Farm Agent is an experimental desktop automation application. It operates with the permissions of the current Windows user and is intended for supervised experimentation in a dedicated environment.

## Reporting a vulnerability

Use the repository's **Security → Report a vulnerability** option if private reporting is enabled. If it is unavailable, open a public issue requesting a private reporting channel without including exploit details, credentials, private files or personal information. Do not assume a response-time guarantee.

Provide the affected commit, relevant module, a minimal reproduction using synthetic data, expected/actual behavior and impact. Do not test against other people's machines or accounts.

## Trust boundaries

- Model output is untrusted. JSON parsing and plan validation cover selected invariants; they do not establish complete action authorization.
- Websites, files and vault notes can influence model context. Prompt instructions and keyword-based injection checks are not an isolation boundary.
- Generated Python runs through `exec` with normal process permissions. Shell actions use `shell=True`. The current engine has no isolated sandbox or universal path/command allowlist.
- Missing Python libraries can be installed automatically. Dependencies are not locked with hashes, and this review did not perform a dependency vulnerability audit.
- Browser and desktop actions can use active user sessions. Login/CAPTCHA detection and selected safety rules do not guarantee that every consequential action is gated.
- Cancellation is cooperative. In-process Python cannot be forcibly stopped by the run-token mechanism.
- Simulation is handler-dependent. Generic filesystem handlers do not all check the dry-run flag, so simulation is not a universal side-effect barrier.

## Data handling

Prompts, relevant retrieved content and screenshots may be transmitted to Anthropic. The app stores task history, action parameters, reports, captures, route descriptions and execution notes locally. Selected vault and memory fields use pattern-based redaction; history, logs and screenshots are not comprehensively anonymized or encrypted.

Keep `.env`, learned routes, logs, reports, screenshots, generated vault notes and dated journals out of version control. Inspect screenshot content before sharing. A `.gitignore` rule does not remove already tracked files or Git history.

## Historical credential exposure

The review on 2026-09-28 found earlier `.env` blobs containing apparent API credentials and application secrets in reachable Git history. These values were not reproduced in documentation or tool output. Their validity and revocation status were not verified. The present tree does not track `.env`.

Treat exposed values as compromised: revoke or replace them through the relevant provider, review usage and dependent integrations, and coordinate any history cleanup with repository collaborators. History cleanup alone does not revoke a credential or remove forks and cached copies.

## Operational guidance

Use an unprivileged test account or isolated Windows environment with synthetic files and dedicated application accounts. Inspect plans with simulation before execution, avoid sensitive browser sessions and review API usage and local records. Simulation can still call the model and write history.

## References

- [GitHub secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [GitHub: removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: LLM prompt injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

See [docs/security-review.md](docs/security-review.md) for the repository-specific findings and scope.
