# Architecture (concise)

- FastAPI app (`app/main.py`), static UI served from `/`.
- Core flow: Markdown → parse → LLM generation → validation (grounding/dedup) → persist exam → grading (choice locally, open-ended via LLM).
- Providers: factory (`llm_provider.py`) selects OpenAI/Yandex/local stub; shared prompts; validation soft by default with logging.
- Storage: filesystem `data/` (`out/` exams/grades, `uploads/` sources, `results/` evaluations). Sorting/pagination for exams API.
- Deployment: Docker + Compose (`PORT`/`HOST` configurable); logs to stdout.

```
Client/UI → /api/generate → parse → LLM → validate → exam.json
          → /api/grade    → load exam → score → grade.json
          → /api/exams    → list (sort/paginate)
          → /api/exams/import → save provided exam
```
