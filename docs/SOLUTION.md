# Solution Snapshot

- Exam generation: supports counts/ratios, difficulty, language (en/ru), provider/model selection; local stub available for offline use.
- Validation: schema + source refs + dedup + grounding heuristics (soft by default, logged).
- Grading: choice scored locally with partial credit; open-ended via LLM rubric; `GradeResponse` persisted.
- Exams API: upload/list files, generate, grade, import exams; exams listing has sorting/pagination.
- Frontend: provider/model selectors, count controls, exam table with pagination, in-app import; gov-inspired palette.
- Ops: Docker + Compose with configurable `PORT`/`HOST`, data volume mount, stdout logs.
