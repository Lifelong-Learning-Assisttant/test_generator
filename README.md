# LLM Test Generator

FastAPI service that turns Markdown medical content into exams and grades submitted answers (choice and open-ended) with OpenAI.

## Quick Start
- Requirements: Python 3.11+, `pip`, OpenAI API key.
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Configure `.env` (create if missing):
  ```env
  OPENAI_API_KEY=sk-...
  OPENAI_MODEL=gpt-4o-mini     # optional override
  OPENAI_BASE_URL=             # optional, for proxies/self-hosted endpoints
  OUTPUT_DIR=data/out          # where exams/grades are stored (default under data/)
  ```
- Run the API + static UI (creates data folders under `data/`):
  ```bash
  uvicorn app.main:app --reload
  ```
- Open http://localhost:8000 (UI) or http://localhost:8000/docs (Swagger).

## API Overview
- `GET /health` — service liveness.
- `POST /api/generate` — generate an exam from Markdown (`markdown_content` + optional `config` supporting counts or ratios, difficulty, language, seed). Persists to `data/out/exam_<id>.json`.
- `POST /api/grade` — grade answers for an `exam_id`; multiple choice graded locally with partial credit, open-ended graded via LLM. Persists to `data/out/grade_<id>.json`.
- `POST /api/upload` — upload `.md` into `data/uploads/`.
- `GET /api/files` and `GET /api/files/{filename}` — list/read uploaded Markdown.
- `GET /api/exams` and `GET /api/exams/{exam_id}` — list/read generated exams.
- Docs at `/docs`, `/redoc`, OpenAPI at `/openapi.json`.

## Typical Flows
- Generate via API:
  ```bash
  curl -X POST http://localhost:8000/api/generate \
    -H "Content-Type: application/json" \
    -d '{"markdown_content":"# Topic\n## Section\nText", "config":{"total_questions":5,"single_choice_ratio":0.6,"multiple_choice_ratio":0.2,"open_ended_ratio":0.2}}'
  ```
- Grade answers:
  ```bash
  curl -X POST http://localhost:8000/api/grade \
    -H "Content-Type: application/json" \
    -d '{"exam_id":"ex-xxxxxx","answers":[{"question_id":"q-001","choice":[1]}]}'
  ```
- Use the UI: browse to `/` and follow upload → generate → take exam → grade.
- Postman: import `LLM_Test_Generator.postman_collection.json` for a ready-made request set.

## Project Structure
```
app/
  main.py           # FastAPI bootstrap, routers, static mount
  api/              # REST endpoints (generate, grade, files, health)
  core/             # Parser, generator, grader, evaluator, RAG placeholder
  models/           # Pydantic schemas for API contracts
  services/         # OpenAI client wrapper
static/             # Bundled frontend served from /
data/               # Runtime root for generated artifacts
  uploads/          # Uploaded Markdown files
  out/              # Generated exams and grading outputs
scripts/evaluate_models.py  # Model benchmarking CLI
tests/              # unit/integration/Bdd suites
docs/SOLUTION_OVERVIEW.md   # Consolidated solution guide
```

## Testing and Evaluation
- Run automated tests:
  ```bash
  pytest tests/ -v
  behave tests/bdd/features/
  ```
- Coverage HTML reports are written to `data/htmlcov/` (set by pytest addopts and coverage config).
- Benchmark different LLMs:
  ```bash
  python scripts/evaluate_models.py --models gpt-4o-mini,gpt-4o --content examples/sample_medical.md
  ```

## Notes
- OpenAI key is required for question generation and open-ended grading.
- CORS is wide open and there is no authentication; tighten before production.
- Exams/grades are stored on disk; clean up `data/out/` and `data/uploads/` as needed.

For deeper details (architecture, REST behaviors, evaluation metrics), see `docs/SOLUTION_OVERVIEW.md`.
