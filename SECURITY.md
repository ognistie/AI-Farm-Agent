# Security policy

AI Farm Agent is an experimental desktop automation application. It operates with the permissions of the current Windows user and is intended for supervised experimentation in a dedicated environment.

## Reporting a vulnerability

Use the repository's **Security → Report a vulnerability** option if private reporting is enabled. If it is unavailable, open a public issue requesting a private reporting channel without including exploit details, credentials, private files or personal information. Do not assume a response-time guarantee.

Provide the affected commit, relevant module, a minimal reproduction using synthetic data, expected/actual behavior and impact. Do not test against other people's machines or accounts.

## Trust boundaries

- Model output is untrusted. JSON parsing and plan validation cover selected invariants; they do not establish complete action authorization.
- Websites, files and vault notes can influence model context. Prompt instructions and keyword-based injection checks are not an isolation boundary.
- The public executor rejects `run_python`, `run_command` and `pip_install`. CODE and DATA produce bounded declarative manifests; trusted builders write new project directories and workbooks without executing model text. Generated source remains untrusted and must be reviewed before a person runs it.
- Internal process-runner utilities remain for tests and controlled development. Windows Job Objects bound process lifetime/resources, but do not restrict filesystem or network privileges. These utilities are not a security sandbox and are unavailable through the task dispatcher.
- Execution-time tool ownership is checked outside the model. FILE paths must remain within roots derived from the original request. Project edits use snapshots, backups and conflict detection; undo refuses changed files or altered backups. These controls do not establish complete GUI effect authorization.
- Runtime package installation is disabled. The validated Windows/Python 3.11 environment has a version lock and a repeatable vulnerability audit; the lock does not include package hashes. Zero known advisories in one scan is not proof of vulnerability absence.
- Browser and desktop actions can use active user sessions. Login/CAPTCHA detection and selected safety rules do not guarantee that every consequential action is gated.
- Cancellation retains the execution slot until termination is confirmed. Managed workers terminate descendants through a Job Object; native GUI actions and external applications still require end-to-end cancellation testing.
- Tool simulation is enforced centrally before any handler is invoked. The surrounding planning/conversation flow may still call the model and save local history; simulation is not a privacy or offline mode.

## Data handling

Prompts, relevant retrieved content and screenshots may be transmitted to Anthropic. With `OPENAI_API_KEY` set and the "Conversa em tempo real" option on (default), **Conversa mode sends microphone audio, a summary of the current conversation and task results to OpenAI** while a session is open. While the session is closed, nothing leaves the computer: a local detector only decides when to reopen it. Outside Conversa mode, short reply text is sent for narration and capture and transcription stay local. Turning the option off keeps Conversa local too. GPT-Live has no tools: every spoken request goes through the app's own understanding, Maestro and executor rules, and a delegation event alone never runs anything. `store=false` does not replace the provider's general data policy. Sensitive effects (send, buy, pay, delete, publish, accept terms) pass an app-side gate in `core/action_risk.py`, including inside the browser and app pilots. It starts in `shadow` mode, which only records what would be blocked; `enforce` requires an explicit confirmation in the request. Classification uses the element's label, so an effect behind an unlabeled icon is not recognized. The app stores task history, reports, route descriptions and execution notes locally. Action telemetry omits parameter values and automatic diagnostic screenshots are disabled. Selected vault and memory fields use pattern-based redaction; history and model context are not comprehensively anonymized or encrypted. No universal retention policy or at-rest encryption is implemented.

Keep `.env`, learned routes, logs, reports, screenshots, generated vault notes and dated journals out of version control. Inspect screenshot content before sharing. A `.gitignore` rule does not remove already tracked files or Git history.

## Historical credential exposure

The review on 2026-09-28 found earlier `.env` blobs containing apparent API credentials and application secrets in reachable Git history. These values were not reproduced in documentation or tool output. Their validity and revocation status were not verified. The present tree does not track `.env`.

Treat exposed values as compromised: revoke or replace them through the relevant provider, review usage and dependent integrations, and coordinate any history cleanup with repository collaborators. History cleanup alone does not revoke a credential or remove forks and cached copies.

## Operational guidance

Use an unprivileged test account or isolated Windows environment with synthetic files and dedicated application accounts. Inspect plans with simulation before execution, avoid sensitive browser sessions and review API usage and local records. Do not deploy unattended automation of consequential effects until action-level authorization and representative desktop tests are complete.

## References

- [GitHub secret scanning](https://docs.github.com/en/code-security/concepts/secret-security/secret-scanning)
- [GitHub: removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [OWASP: LLM prompt injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

See [docs/security-review.md](docs/security-review.md) for the repository-specific findings and scope.
See [the current release assessment](docs/research/production-readiness.md) for executed checks and remaining release blockers.
