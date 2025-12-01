# LLM Test Generator — Single Overview

Consolidated description of the current solution (backend, REST API, evaluation tooling, and operational notes). This supersedes the split docs in this folder.

## Purpose
- Generate exams from Markdown medical content (single-choice, multiple-choice, open-ended).
- Grade submitted answers with partial credit for multiple choice and LLM-assisted scoring for open-ended responses.
- Provide a simple file workflow (upload Markdown, generate exams, retrieve and grade) via REST API and a static web UI.

## Architecture & Code Map
- `app/main.py` — FastAPI app wiring, CORS, static site at `/`, routers for API.
- `app/api/` — REST endpoints:
  - `generate.py` (`POST /api/generate`) — parse Markdown and create exams.
  - `grade.py` (`POST /api/grade`) — grade submitted answers against saved exams.
  - `files.py` (`POST /api/upload`, `GET /api/files*`, `GET /api/exams*`) — upload/list/read Markdown and generated exams.
  - `health.py` (`GET /health`) — liveness/version.
- `app/core/` — domain logic:
  - `parser.py` — Markdown → `ParsedDocument`/sections.
  - `generator.py` — builds questions via `OpenAIClient`, supports counts or ratios, deterministic with `seed`.
  - `grader.py` — grades choice questions locally, open-ended via LLM rubric, partial credit for multiple choice.
  - `evaluator.py` — quality/consistency metrics, model comparison helpers.
  - `retriever.py` — placeholder RAG retriever (not wired into generation yet).
- `app/models/schemas.py` — Pydantic v2 models for API contracts (Exam, Question, ExamConfig, GradeRequest/Response).
- `app/services/openai_client.py` — OpenAI client wrapper (JSON mode prompts, language-aware).
- `static/` — prebuilt frontend served from `/`.
- `data/` — runtime root
  - `uploads/` — user Markdown uploads
  - `out/` — generated exams and grading outputs
- `scripts/evaluate_models.py` — CLI to benchmark multiple LLMs against the same Markdown source.

## REST API (current behavior)
- `GET /health` → `{status, version}`.
- `POST /api/generate`
  - Body: `{"markdown_content": "...", "config": ExamConfig?}`. `ExamConfig` supports either explicit counts (`single_choice_count`, `multiple_choice_count`, `open_ended_count`) or ratios (`single_choice_ratio`, `multiple_choice_ratio`, `open_ended_ratio`) plus `total_questions`, `difficulty` (`easy|medium|hard|mixed`), `language` (`en|ru`), and optional `seed`.
  - Flow: parse Markdown → generate questions with OpenAI → save to `data/out/exam_<id>.json` → return `Exam`.
  - Errors: 400 on invalid input/config, 500 on generation failures.
- `POST /api/grade`
  - Body: `{"exam_id": "...", "answers": [StudentAnswer...]}` where `StudentAnswer.choice` (indices) or `.text_answer` is provided.
  - Flow: load exam from `data/out/exam_<id>.json` → grade locally; open-ended uses LLM rubric scoring → save `data/out/grade_<id>.json` → return `GradeResponse`.
  - Errors: 404 if exam missing, 400 for invalid payload, 500 if grading fails.
- `POST /api/upload` — accepts `.md` file, stores in `data/uploads/`, returns metadata; rejects non-Markdown.
- `GET /api/files` — list uploaded Markdown files; `GET /api/files/{filename}` — read file contents.
- `GET /api/exams` — list saved exams in `data/out/`; `GET /api/exams/{exam_id}` — return stored exam JSON.
- Docs: Swagger at `/docs`, ReDoc at `/redoc`, OpenAPI at `/openapi.json`.

## Data Contracts (selected)
- **Question**: `{id, type: "single_choice"|"multiple_choice"|"open_ended", stem, options?, correct?, reference_answer?, rubric?, source_refs[], meta{difficulty,tags[]}}`.
- **Exam**: `{exam_id, questions[], config_used}`.
- **GradeRequest**: `{exam_id, answers: [{question_id, choice?, text_answer?}]}`.
- **GradeResponse**: `{exam_id, summary{total, correct, score_percent}, per_question: [QuestionResult...]}` with `partial_credit` always present.

## Runtime & Configuration
- Environment (`app/config.py` via `.env`):
  - `OPENAI_API_KEY` (required), `OPENAI_MODEL` (default `gpt-4o-mini`), `OPENAI_BASE_URL` (optional).
  - `DEFAULT_TOTAL_QUESTIONS`, `DEFAULT_SINGLE_CHOICE_RATIO`, `DEFAULT_MULTIPLE_CHOICE_RATIO`.
  - `DATA_DIR` (default `data`), `OUTPUT_DIR` (default under `data/out`), `UPLOADS_DIR` (default under `data/uploads`).
- Directories created on startup: `data/out/` for exams/grades, `data/uploads/` for uploaded Markdown (both under `data_dir` unless overridden).
- CORS allows `*` (development convenience); add restrictions before production.
- No authentication/authorization; storage is filesystem-only.

## Core Workflows
1) **Generate an exam**
   - Send Markdown via `/api/generate` (or upload then read via `/api/files/{filename}` and pass content).
   - Receive `exam_id` and questions; persisted to `data/out/exam_<id>.json`.
2) **Grade answers**
   - Submit `exam_id` plus answers to `/api/grade`.
   - Receive per-question results, partial credit values, and summary; persisted to `data/out/grade_<id>.json`.
3) **Use the web UI**
   - Navigate to `/` to access the static client (served from `static/`) that walks through upload → generate → take test → grade.

## Evaluation & QA
- `scripts/evaluate_models.py` runs end-to-end generation/grading for one or more models, computes:
  - Question quality (`answerability`, `coherence`, `difficulty_distribution`, `overall`).
  - Grading consistency across repeated runs.
  - Cost-per-question estimates and model rankings.
  - Outputs JSON reports under `data/out/evaluations/`.
- Tests (pytest + behave) live under `tests/unit`, `tests/integration`, and `tests/bdd`; they cover schema validation, parsing, generation, grading, API health, and evaluation metrics. Run them with `pytest` or `behave` from the repo root.

## Limitations & Notes
- OpenAI key is mandatory; generation and open-ended grading will fail without it.
- RAG retriever is a placeholder and is not used in the current generation flow.
- Exams and grading results are stored locally; cleanup/rotation is manual.
- Wide-open CORS and lack of auth are acceptable for local/demo use only.

## Operational Recipes
- Install deps: `pip install -r requirements.txt`
- Run API: `uvicorn app.main:app --reload` (serves API + static UI).
- Generate exam (example):
  ```bash
  curl -X POST http://localhost:8000/api/generate \
    -H "Content-Type: application/json" \
    -d '{"markdown_content": "# Topic\n## Section\nText", "config": {"total_questions": 5, "single_choice_ratio": 0.6, "multiple_choice_ratio": 0.2, "open_ended_ratio": 0.2}}'
  ```
- Grade answers (example):
  ```bash
  curl -X POST http://localhost:8000/api/grade \
    -H "Content-Type: application/json" \
    -d '{"exam_id": "ex-xxxxxx", "answers": [{"question_id": "q-001", "choice": [1]}]}'
  ```
- Evaluate models: `python scripts/evaluate_models.py --models gpt-4o-mini,gpt-4o --content examples/sample_medical.md`
