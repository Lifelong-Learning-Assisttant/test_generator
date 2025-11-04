# LLM Test Generator

AI-powered test generation system for educational materials. Generates and grades multiple-choice exams from Markdown content using OpenAI.

## Features

- 📝 **Question Generation**: Automatically generate single-choice and multiple-choice questions from Markdown content
- ✅ **Automated Grading**: Grade student answers with partial credit support
- 🏥 **Medical Focus**: Optimized for medical education content
- 🔍 **Source Traceability**: Every question links back to source material
- 📊 **Configurable**: Control question counts, difficulty, and type ratios
- 🧪 **Well-Tested**: 82 tests, 91% code coverage, full BDD scenarios

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Run the API Server

```bash
# Start server
python3 -m uvicorn app.main:app --reload

# API available at: http://localhost:8000
# Swagger UI at: http://localhost:8000/docs
```

### 3. Generate an Exam

```bash
curl -X POST "http://localhost:8000/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "markdown_content": "# Disease\n## Symptoms\nFever, cough, headache.\n## Treatment\nRest and hydration.",
    "config": {
      "total_questions": 5,
      "single_choice_ratio": 0.6,
      "multiple_choice_ratio": 0.4
    }
  }'
```

### 4. Grade Answers

```bash
curl -X POST "http://localhost:8000/api/grade" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_id": "ex-abc123",
    "answers": [
      {"question_id": "q-001", "choice": [1]},
      {"question_id": "q-002", "choice": [0, 2]}
    ]
  }'
```

## Architecture

```
llm_tester/
├── app/
│   ├── api/           # FastAPI endpoints
│   │   ├── generate.py    # POST /api/generate
│   │   ├── grade.py       # POST /api/grade
│   │   └── health.py      # GET /health
│   ├── core/          # Business logic
│   │   ├── parser.py      # Markdown parsing
│   │   ├── generator.py   # Question generation
│   │   └── grader.py      # Answer grading
│   ├── models/        # Pydantic schemas
│   │   └── schemas.py
│   ├── services/      # External services
│   │   └── openai_client.py
│   ├── config.py      # Configuration management
│   └── main.py        # FastAPI app
├── tests/
│   ├── unit/          # Unit tests (TDD)
│   ├── integration/   # API integration tests
│   └── bdd/           # Behave BDD scenarios
├── examples/
│   └── sample_medical.md   # Example content
└── out/               # Generated exams and results
```

## API Endpoints

### POST /api/generate
Generate an exam from Markdown content.

**Request:**
```json
{
  "markdown_content": "# Topic\n## Section\nContent here...",
  "config": {
    "total_questions": 20,
    "single_choice_ratio": 0.7,
    "multiple_choice_ratio": 0.3,
    "difficulty": "mixed",
    "seed": 42
  }
}
```

**Response:**
```json
{
  "exam_id": "ex-abc123",
  "questions": [
    {
      "id": "q-001",
      "type": "single_choice",
      "stem": "What is the primary symptom?",
      "options": ["A", "B", "C", "D"],
      "correct": [1],
      "source_refs": [{"file": "...", "heading": "...", "start": 0, "end": 100}],
      "meta": {"difficulty": "medium", "tags": ["Symptoms"]}
    }
  ],
  "config_used": {...}
}
```

### POST /api/grade
Grade student answers.

**Request:**
```json
{
  "exam_id": "ex-abc123",
  "answers": [
    {"question_id": "q-001", "choice": [1]},
    {"question_id": "q-002", "choice": [0, 2]}
  ]
}
```

**Response:**
```json
{
  "exam_id": "ex-abc123",
  "summary": {
    "total": 2,
    "correct": 1,
    "score_percent": 50.0
  },
  "per_question": [
    {
      "question_id": "q-001",
      "is_correct": true,
      "expected": [1],
      "given": [1],
      "partial_credit": 1.0
    }
  ]
}
```

### GET /health
Health check endpoint.

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run BDD scenarios
behave tests/bdd/features/

# Run with coverage
pytest --cov=app --cov-report=html tests/
```

## Development Approach

This project follows **Test-Driven Development (TDD)** and **Behavior-Driven Development (BDD)**:

1. **Tests First**: All features have tests written before implementation
2. **RED → GREEN cycle**: Write failing tests, then make them pass
3. **BDD Scenarios**: User-facing features validated with Gherkin scenarios
4. **High Coverage**: 91% code coverage, 82 tests passing

### Test Structure
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test API endpoints end-to-end
- **BDD Scenarios**: Test complete user workflows

## Configuration

Edit `.env` file:

```env
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini  # or gpt-4, gpt-3.5-turbo

# Generation defaults
DEFAULT_TOTAL_QUESTIONS=20
DEFAULT_SINGLE_CHOICE_RATIO=0.7
DEFAULT_MULTIPLE_CHOICE_RATIO=0.3

# Output
OUTPUT_DIR=out
```

## Example Usage

See `examples/sample_medical.md` for example medical content format.

```bash
# Generate exam from example content
cat examples/sample_medical.md | python3 -c "
import sys, json, requests
content = sys.stdin.read()
resp = requests.post('http://localhost:8000/api/generate',
                     json={'markdown_content': content})
print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
" > out/my_exam.json
```

## Tech Stack

- **Backend**: Python 3.10+, FastAPI, uvicorn
- **AI**: OpenAI API (gpt-4o-mini)
- **Testing**: pytest, behave (BDD), httpx
- **Parsing**: markdown-it-py
- **Validation**: Pydantic v2

## Project Status

✅ **Completed Features:**
- Pydantic schemas with validation
- Markdown parser with chunking
- Question generator with OpenAI
- Answer grading with partial credit
- FastAPI endpoints with Swagger
- Comprehensive test coverage (82 tests)
- BDD scenarios (12 scenarios)

🔄 **Future Enhancements:**
- RAG (Retrieval-Augmented Generation) for better context selection
- Additional question types (true/false, matching, essay)
- Question difficulty calibration
- Batch generation for large content
- Export to various formats (PDF, GIFT, QTI)

## License

Educational project for ITMO University.

## Contributing

This project follows conventional commits and maintains high test coverage.
All features must have:
1. Unit tests (TDD approach)
2. Integration tests
3. BDD scenarios (if user-facing)
4. Documentation

## Support

- GitHub Issues: https://github.com/TohaRhymes/llm_tester/issues
- Documentation: See `/docs` folder
- API Docs: http://localhost:8000/docs (when server running)
