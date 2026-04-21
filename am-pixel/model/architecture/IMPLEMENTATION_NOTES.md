# Architecture Implementation Notes

**Status:** Template — OpenClaw fills this after implementing `model/architecture/*.py`.

Required content (OPENCLAW_PROMPT Rule 9 / CHANGE-020):

- How **2D positional encodings** are implemented (learned X/Y embeddings vs canvas coords).
- How **DNA conditioning tokens** are constructed, masked, and prepended.
- How the **causal mask** interacts with structure-aware token ordering.
- Any deviations from SPEC with justification.

Do not start training until a human reviews this file and the code.
