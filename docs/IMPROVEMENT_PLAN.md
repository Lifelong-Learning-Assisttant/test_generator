# LLM Tester Improvement Plan

## Goals
- Unify generation, grading, and evaluation as provider-agnostic services (OpenAI, Yandex, local/stub) with clear boundaries.
- Strengthen safety: path sanitization, auth-ready API, prompt/response validation, logging, and rate limits.
- Support research workflows: import custom exams, run model benchmarks, and evaluate grading consistency.
- Ship reproducible ops: Docker packaging, seeded runs, and observable metrics.

## Workstreams and Steps
1) **Core architecture**
   - Introduce an `LLMProvider` interface + factory (openai, yandex, local/stub) with timeouts/retries.
   - Inject provider into generator/grader/answer tester; support `provider`/`model_name` in `ExamConfig`.
   - Add validation/grounding stage for generated questions (schema checks, source coverage, duplicates).
2) **API & flows**
   - Extend generate/grade endpoints to accept provider/model and optional imported exams.
   - Add endpoint to submit custom exams and to trigger evaluation runs.
   - Return metadata (source hash, seed, provider, model) with artifacts.
3) **Safety**
   - Path sanitization for uploads/exams; restrict CORS/auth hooks/rate limits.
   - Prompt/response validation, JSON schema enforcement, redaction of secrets in logs.
   - Basic abuse protections (payload limits, timeout defaults).
4) **Research & evaluation**
   - Wire evaluation scripts into services; store comparison/eval artifacts with metadata.
   - Add metrics: answerability/coherence/grounding, grading consistency, AI pass rate by type.
5) **Docs, tests, ops**
   - Update README/API docs, add examples for provider selection and validation workflow.
   - Expand tests: provider factory, count-based config, path sanitization, stub LLM deterministic output.
   - Docker/Compose for API + worker; healthchecks and config validation on startup.

## Near-Term Deliverables (current sprint)
- Provider factory + stub client; config support for provider/model; generator/grader refactor to use it.
- Path sanitization for uploads/exams; defensive defaults for missing API keys.
- Documentation updates for new config options and safety notes.
