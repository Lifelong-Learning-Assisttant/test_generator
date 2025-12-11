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
  - `generator.py` — builds questions via provider-agnostic LLM layer (OpenAI/Yandex/local stub), supports counts or ratios, deterministic with `seed`, validates grounding/deduplication.
  - `grader.py` — grades choice questions locally, open-ended via LLM rubric, partial credit for multiple choice.
  - `evaluator.py` — quality/consistency metrics, model comparison helpers.
  - `retriever.py` — placeholder RAG retriever (not wired into generation yet).
- `app/models/schemas.py` — Pydantic v2 models for API contracts (Exam, Question, ExamConfig, GradeRequest/Response).
- `app/services/` — LLM client wrappers and evaluation tools:
  - `openai_client.py` — OpenAI API wrapper (question generation, answering, grading).
  - `yandex_client.py` — YandexGPT API wrapper (same capabilities as OpenAI).
  - `model_answer_tester.py` — Service for testing how well models answer exam questions.
  - `llm_provider.py` — Provider factory and local stub for offline/testing.
- `static/` — prebuilt frontend served from `/`.
- `data/` — runtime root
  - `uploads/` — user Markdown uploads
  - `out/` — generated exams and grading outputs
  - `results/` — model answer evaluation results
- `scripts/` — CLI utilities:
  - `evaluate_models.py` — Benchmark question generation quality across LLMs.
  - `test_model_answers.py` — Test and compare how well models answer exam questions.
- `examples/notebooks/` — Jupyter-friendly examples:
  - `01_question_generation.py` — Generate questions from content.
  - `02_model_evaluation.py` — Test models on exams.

## REST API (current behavior)
- `GET /health` → `{status, version}`.
- `POST /api/generate`
  - Body: `{"markdown_content": "...", "config": ExamConfig?}`. `ExamConfig` supports either explicit counts or ratios (missing `open_ended_ratio` auto-filled), plus `total_questions`, `difficulty` (`easy|medium|hard|mixed`), `language` (`en|ru`), `provider`, `model_name`, and optional `seed`.
  - Flow: parse Markdown → generate questions with OpenAI → save to `data/out/exam_<id>.json` → return `Exam`.
  - Errors: 400 on invalid input/config, 500 on generation failures.
- `POST /api/grade`
  - Body: `{"exam_id": "...", "answers": [StudentAnswer...]}` where `StudentAnswer.choice` (indices) or `.text_answer` is provided.
  - Flow: load exam from `data/out/exam_<id>.json` → grade locally; open-ended uses LLM rubric scoring → save `data/out/grade_<id>.json` → return `GradeResponse`.
  - Errors: 404 if exam missing, 400 for invalid payload, 500 if grading fails.
- `POST /api/upload` — accepts `.md` file, stores in `data/uploads/`, returns metadata; rejects non-Markdown.
- `GET /api/files` — list uploaded Markdown files; `GET /api/files/{filename}` — read file contents.
- `GET /api/exams` — list saved exams in `data/out/` with sorting/pagination; `GET /api/exams/{exam_id}` — return stored exam JSON.
- Docs: Swagger at `/docs`, ReDoc at `/redoc`, OpenAPI at `/openapi.json`.

## Data Contracts (selected)
- **Question**: `{id, type: "single_choice"|"multiple_choice"|"open_ended", stem, options?, correct?, reference_answer?, rubric?, source_refs[], meta{difficulty,tags[]}}`.
- **Exam**: `{exam_id, questions[], config_used}`.
- **GradeRequest**: `{exam_id, answers: [{question_id, choice?, text_answer?}]}`.
- **GradeResponse**: `{exam_id, summary{total, correct, score_percent}, per_question: [QuestionResult...]}` with `partial_credit` always present.

## Runtime & Configuration
- Environment (`app/config.py` via `.env`):
  - **OpenAI**: `OPENAI_API_KEY` (required for OpenAI models), `OPENAI_MODEL` (default `gpt-4o-mini`), `OPENAI_BASE_URL` (optional).
  - **Yandex Cloud** (optional): `YANDEX_CLOUD_API_KEY`, `YANDEX_CLOUD_API_KEY_IDENTIFIER`, `YANDEX_FOLDER_ID`, `YANDEX_MODEL` (default `yandexgpt-lite`).
  - **Generation defaults**: `DEFAULT_TOTAL_QUESTIONS`, `DEFAULT_SINGLE_CHOICE_RATIO`, `DEFAULT_MULTIPLE_CHOICE_RATIO`.
  - **Paths**: `DATA_DIR` (default `data`), `OUTPUT_DIR` (default under `data/out`), `UPLOADS_DIR` (default under `data/uploads`).
- Directories created on startup: `data/out/` for exams/grades, `data/uploads/` for uploaded Markdown, `data/results/` for evaluation results.
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

### Two Evaluation Systems

**1. Question Generation Quality** (`scripts/evaluate_models.py`)
- Evaluates how well models **generate** questions from content
- Metrics: answerability, coherence, difficulty distribution, grading consistency
- Output: `data/out/evaluations/evaluation_*.json`
- Usage: `python scripts/evaluate_models.py --models gpt-4o-mini,gpt-4o --content examples/medical_content.md`

**2. Model Answer Evaluation** (`scripts/test_model_answers.py`)
- Tests how well models **answer** existing exam questions
- Metrics: accuracy, AI-pass rate, per-question breakdown
- Supports: OpenAI GPT (gpt-4o, gpt-4o-mini) and YandexGPT (yandexgpt, yandexgpt-lite)
- Output: `data/results/model_test_*.json` and `model_comparison_*.json`
- Usage:
  - Single model: `python scripts/test_model_answers.py --exam data/out/exam_ex-123.json --model gpt-4o-mini --provider openai`
  - Compare models: `python scripts/test_model_answers.py --exam data/out/exam_ex-123.json --compare`

### Jupyter-Friendly Workflows
See `examples/notebooks/` for research-oriented examples:
- `01_question_generation.py` - Generate and save exams from content
- `02_model_evaluation.py` - Test models and compare results

### Automated Tests
Tests (pytest + behave) live under `tests/unit`, `tests/integration`, and `tests/bdd`; they cover schema validation, parsing, generation, grading, API health, evaluation metrics, and new YandexGPT integration. Run them with `pytest` or `behave` from the repo root.

## Limitations & Notes
- OpenAI or Yandex API key required depending on which provider you use.
- Both providers support: question generation, answering questions, and grading open-ended responses.
- RAG retriever is a placeholder and is not used in the current generation flow.
- Exams, grading results, and evaluation outputs are stored locally; cleanup/rotation is manual.
- Wide-open CORS and lack of auth are acceptable for local/demo use only.
- For detailed evaluation workflows, see `docs/EVALUATION.md`.

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
