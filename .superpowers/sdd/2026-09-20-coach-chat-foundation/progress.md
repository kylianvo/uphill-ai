# SDD ledger — plan: docs/superpowers/plans/2026-09-20-coach-chat-foundation.md

Task F1: starting from 09862fd (main merge commit).
Worktree: .claude/worktrees/coach-chat-foundation on branch codex/coach-chat-foundation.
Superpowers skills announced and activated:
- superpowers:using-git-worktrees
- superpowers:executing-plans
- superpowers:test-driven-development
- superpowers:requesting-code-review
- superpowers:receiving-code-review
- superpowers:verification-before-completion
- superpowers:finishing-a-development-branch
- db-migration
- uphill-ai-vietnamese-copy
- ui-screenshot-evidence
- langfuse

Task F1: isolated athlete chat routing into routers/coach_chat.py, created provider-neutral CoachModel protocol and GeminiCoachModel adapter in services/coach_model.py, created coach_prompts.py, pinned langgraph==1.2.11 and langchain-google-genai==4.4.0 in requirements.txt, added test_coach_model.py. Unit tests verify protocol satisfaction, Vietnamese chunk assembly, thinking block exclusion, tool call rejection, single canonical generation wrapping, and error normalization. Review clean. Task F1 complete.
