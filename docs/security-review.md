# Repository security review

Review date: 2026-09-28. Baseline: commit `b614c94`; documentation and privacy changes were assessed in the working tree.

## Scope and method

The review inspected tracked files, Git exclusions, reachable historical blobs, attached screenshots and the current execution architecture. Pattern searches covered credential formats, email addresses, personal workstation paths and selected personal identifiers. Historical scanning also compared blobs against selected current local secret values without displaying those values. It examined 1,770 reachable blobs at the baseline.

This is a bounded source review, not penetration testing or a guarantee that every secret or personal identifier has been found. Credential validity, remote forks/caches, provider logs, authenticated application state and dependency vulnerability databases were not assessed.

## Findings

| Priority | Finding | Evidence / status |
| --- | --- | --- |
| High | Apparent credentials remain in Git history | Two historical `.env` blobs contained a provider-key format and application secret fields without placeholder markers. Validity is unknown. Revocation and coordinated history cleanup remain external actions. |
| High | Generated code executes with user privileges | `core/automation.py` uses `exec(code, g)` with normal builtins and OS modules; command execution uses `shell=True`. No execution sandbox was found. |
| High | Authorization is incomplete at execution time | Domain-level checks exist, but generic filesystem handlers can write/delete arbitrary resolved paths. The command denylist covers selected strings and cannot constrain arbitrary generated Python. |
| Medium | Operational records were versioned despite ignore rules | Ten generated HTML reports and three dated vault journals were tracked. They are removed from the index while retained locally, and dated journals now have an ignore rule. Prior commits remain reachable. |
| Medium | Sensitive data can persist locally and leave through model context | History retains requests/artifact paths; action logs retain parameter excerpts; capture/model paths can include screen data. Redaction is partial and local storage is not encrypted. |
| Medium | Prompt-injection controls have limited coverage | Page content reaches model context. ContentGuard uses a keyword pattern for selected read actions; browser-pilot instructions do not establish runtime authorization. |
| Medium | Dependencies and automatic installation are not integrity-locked | Requirements include ranges/unpinned packages. Generated-code imports can trigger pip installation without hashes. No dependency vulnerability scan was performed. |
| Medium | Cancellation does not isolate running code | The controller checks run tokens between operations; already executing in-process Python is not forcibly terminated. |
| Medium | Simulation is not enforced centrally | The dispatcher calls handlers even with `dry_run=True`; generic filesystem handlers such as create, write and delete do not all check that flag. Simulation cannot guarantee an unchanged filesystem. |

## Changes included in this review

- Replace the restrictive license with the standard MIT text requested by the owner and align contribution terms.
- Remove the personal contact email from contribution documentation. Keep intentional public copyright attribution and existing author credits.
- Stop tracking generated reports and dated journals without deleting local copies.
- Ignore dated vault journals and legacy learned-route data; repair a malformed glob that broke ripgrep searches.
- Use an explicit non-secret placeholder in `.env.example`.
- Add supplied screenshots as local documentation assets. No credentials, contact details or private workstation paths were visible; the UI screenshot includes generic recent-task labels.
- Document current architectural controls and their limits without claiming a production security guarantee.

## Remaining remediation

1. Revoke or replace historical provider credentials and application secrets; verify provider-side usage. No rotation was performed by this review.
2. Decide whether to rewrite shared history and coordinate a cleanup procedure. No history rewrite or force-push was performed.
3. Introduce an isolated execution worker, restricted capabilities and action-level authorization before expanding autonomous execution.
4. Add stronger data minimization/redaction and explicit retention controls for history, logs, captures and model context.
5. Establish dependency locking, integrity checks and repeatable vulnerability scans.

The MIT text is based on the [Open Source Initiative license reference](https://opensource.org/license/mit). Security references and reporting guidance are in [SECURITY.md](../SECURITY.md).

## Update — 2026-10-07

Re-checked at commit `84bd85d` plus the repository cleanup that followed.

- **Still open (High):** the two historical `.env` blobs still contain Anthropic key formats in reachable history. The key currently configured locally is **not** one of them. The historical keys must be revoked in the Anthropic console; rewriting history is optional and needs coordination with collaborators, because forks and caches keep copies.
- **Fixed since the baseline:**
  - `open_path` refuses network/UNC and `file:` paths before touching them, which prevents NTLM hash leakage.
  - The executable-extension blocklist was expanded (`.msc`, `.jar`, `.url`, `.chm`, `.appinstaller`, `.settingcontent-ms`, disk images, `.dll`).
  - The Start-menu fallback refuses names containing paths, arguments or shell symbols.
  - Voice understanding and conversation resolution treat page/window text as data.

  Negative tests: `test_security_guards_round4` in the smoke suite.
- **Hygiene:**
  - Empty vault notes and IDE settings were removed from version control.
  - Local marketing material is ignored.
  - CI fails if a `.env`, `.pem` or `.key` file is tracked.
