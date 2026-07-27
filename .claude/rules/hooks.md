---
paths:
  - ".claude/hooks/**"
  - "scripts/*.sh"
---

# Hook and shell-script rules

- Before committing a hook script, pipe fixture JSON through it and assert exit code and output for the pass, fail, and repeat cases. (L-001)
