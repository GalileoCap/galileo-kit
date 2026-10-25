---
id: G3
source: owner
status: stated 2026-10-24
---

# G3 Consistent quality, reviewing what matters

In the owner's words:

> I want the produced code and documents to be of consistent quality while I only review the actually relevant parts.
>
> My philosophy (even pre-AI) is that it's best to split pieces of projects into independent subsystems that are then wired together
>
> - This way they can be worked on, tested, optimized, or even completely rewritten, and as long as the API/contract is the same the rest of the code "doesn't care"
> - I am mostly concerned with the general architecture and the integration surface (API between subsystems and with external users and the subsystems)
>
> This is why we check for LLM-isms
>
> This is why we enforce lints, formatters, and custom scripts over the code
