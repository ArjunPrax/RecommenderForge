# Collaboration

`main` is the integrated working state. Avoid direct feature development on it. Use a readable, coherent-task branch such as `arjun/<task>` or `teammate/<task>`; do not hard-code the teammate's name until known.

Normal flow: task -> branch -> implementation -> local validation -> documentation/log updates -> push -> PR -> review -> merge. PRs should state what changed, why, testing, requirement/task, experiment/result, and known limitations. Each human should review the other's meaningful PRs where practical.

The branch owner remains responsible for correctness, understanding, testing, security, performance claims, and PR quality even when Codex assists. Agree ownership before overlapping work, communicate interface changes early, and avoid concurrent edits to central files where practical. Keep process lightweight.
