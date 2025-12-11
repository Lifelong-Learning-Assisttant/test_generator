# Plan (including evaluation)

- Stabilize flows: keep soft validation but surface metrics (grounded ratio, coverage) in responses/UI; add simple retries with clearer logs.
- Research/evaluation: benchmark generation quality and model answers across providers; track grounding, answerability, coherence, grading consistency, and cost. Provide comparison reports and hooks for export.
- API/UI polish: expose validation metrics, model comparison results; allow downloading/importing exams/grades; ensure pagination and sorting are robust.
- Security/safety: path sanitization (done), provider allowlist, rate-limit hooks, safer error messaging; optional auth when moving beyond demo.
- Ops: add basic health/log dashboards; keep Docker/Compose single service with configurable ports/paths.
- Docs/examples: maintain minimal doc set (Architecture, Solution, Plan); keep examples defaulting to local provider, plus one notebook showcasing generation; keep Postman collection aligned with current endpoints/payloads.
