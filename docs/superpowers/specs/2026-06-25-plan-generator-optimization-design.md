# Plan Generator Response Time Optimization Design

## Goal
Optimize the AI response time in the `PlanGenerator` service. Currently, the system uses a sequential two-step process: querying NotebookLM for RAG context, followed by querying Gemini for the final structured JSON plan. This design eliminates the Gemini step entirely, routing the comprehensive JSON schema prompt directly to NotebookLM to cut response times in half while preserving the Uphill Athlete training intelligence.

## Proposed Changes

### 1. Remove Sequential Pipeline
In `/backend/services/plan_generator.py`, we will bypass the dual-pipeline approach. The existing `nlm_query` string will be removed.

### 2. Single-Step NotebookLM Generation
We will construct the comprehensive `prompt` (which includes all athlete profile data, target race constraints, schedule requirements, and the strict JSON array schema). Instead of sending this prompt to Gemini, we will send it as the direct `query` parameter to `NotebookLmService.query_notebook()`.

Since NotebookLM's knowledge base already contains the RAG grounding documents, it will use its internal retrieval mechanism to generate the plan and format it directly according to the instructions in the prompt.

### 3. Robust JSON Parsing
Because NotebookLM may output markdown formatting (e.g. ````json` fences) around the raw JSON array, we will implement a robust extraction block:
- Attempt `json.loads(response_text)`
- On failure, apply `re.sub(r'```(?:json)?|```', '', response_text).strip()` and attempt parsing again.
- Ensure the result is a Python `list` of `dict` elements.

### 4. Graceful Fallback
If NotebookLM fails to generate a valid JSON array or a network error occurs, the system will continue to catch the exception and fall back to the existing rule-based `PlanGenerator` schedule, ensuring the user always receives a training plan.

## Next Steps
- Implement changes locally in `backend/services/plan_generator.py`.
- Run tests on local dev environment.
- Verify JSON formatting and RAG quality.
- Push and deploy to the SSH server.
