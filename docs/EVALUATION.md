# Evaluation System

This document describes the two evaluation systems in LLM Tester:

1. **Question Generation Quality Evaluation** - Assess how well models generate questions
2. **Model Answer Evaluation** - Test how well models answer existing questions

---

## 1. Question Generation Quality Evaluation

Evaluates the quality of LLM-generated exam questions.

### Purpose
- Compare different models' ability to generate educational questions
- Assess question quality metrics: answerability, coherence, difficulty distribution
- Test grading consistency

### Usage

#### CLI
```bash
python scripts/evaluate_models.py \
    --models gpt-4o-mini,gpt-4o \
    --content examples/medical_content.md \
    --num-questions 10
```

#### Jupyter
```python
from scripts.evaluate_models import ModelEvaluator

evaluator = ModelEvaluator(
    models=["gpt-4o-mini", "gpt-4o"],
    content_path="examples/medical_content.md"
)

report = evaluator.run_evaluation(num_questions=10)
print(f"Best model: {report['recommendations']['recommended_model']}")
```

### Metrics

- **Answerability** (0.0-1.0): Can questions be answered from source material?
- **Coherence** (0.0-1.0): Are questions well-formed and clear?
- **Difficulty Distribution**: Balance of easy/medium/hard questions
- **Grading Consistency** (0.0-1.0): Does grading produce consistent results?
- **Cost per Question**: Estimated API cost

### Output

Results saved to `data/out/evaluations/evaluation_YYYYMMDD_HHMMSS.json`

---

## 2. Model Answer Evaluation

Tests how well different LLM models **answer** exam questions (not generate them).

### Purpose
- Measure AI-pass rate: what percentage of questions can AI solve?
- Compare performance across different models (OpenAI GPT, YandexGPT, etc.)
- Identify question types that are more resistant to AI
- Benchmark for designing AI-resistant assessments

### Supported Models

#### OpenAI
- `gpt-4o` - Most capable (but expensive)
- `gpt-4o-mini` - Best balance
- `gpt-3.5-turbo` - Faster, cheaper

#### Yandex Cloud
- `yandexgpt` - Standard model
- `yandexgpt-lite` - Faster, cheaper variant

### Usage

#### CLI

Test a single model:
```bash
python scripts/test_model_answers.py \
    --exam data/out/exam_ex-123.json \
    --model gpt-4o-mini \
    --provider openai
```

Compare multiple models:
```bash
python scripts/test_model_answers.py \
    --exam data/out/exam_ex-123.json \
    --compare
```

#### Jupyter

See `examples/notebooks/02_model_evaluation.py` for detailed examples.

```python
from examples.notebooks.model_evaluation import test_model, compare_models

result = test_model("data/out/exam_ex-123.json", "gpt-4o-mini", "openai")
print(f"Accuracy: {result.accuracy:.2%}")
```

### Metrics

- **Accuracy**: Percentage of questions answered correctly
- **AI Pass Rate**: Same as accuracy
- **Correct Count**: Number of questions answered correctly
- **Per-question breakdown**: Detailed results for each question

### Output Files

Results saved to `data/results/`:
- `model_test_{model}_{exam_id}_{timestamp}.json` - Individual results
- `model_comparison_{exam_id}_{timestamp}.json` - Comparison across models

---

## Environment Setup

### Required Variables

```bash
# OpenAI (required for OpenAI models)
OPENAI_API_KEY=sk-proj-...

# Yandex Cloud (required for Yandex models)
YANDEX_CLOUD_API_KEY=AQVN...
YANDEX_CLOUD_API_KEY_IDENTIFIER=ajeibu...
YANDEX_FOLDER_ID=b1g...
```

### Getting Yandex Cloud Credentials

1. Go to [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Create or select a folder
3. Note the **Folder ID** from URL or folder info
4. Create API key in IAM → Service accounts
5. Add to `.env`

---

## Workflow Examples

### Generate Exam and Test Models

```bash
# 1. Generate exam
python -m app.main  # Start API
curl -X POST http://localhost:8000/api/generate -d @config.json

# 2. Test models
python scripts/test_model_answers.py --exam data/out/exam_ex-123.json --compare
```

### Jupyter Research Workflow

```python
# Generate questions
from examples.notebooks.question_generation import generate_exam, save_exam

exam = generate_exam("content.md", total_questions=20)
exam_file = save_exam(exam)

# Test models
from examples.notebooks.model_evaluation import compare_models

comparison = compare_models(
    exam_file,
    models=[
        {"model_name": "gpt-4o-mini", "provider": "openai"},
        {"model_name": "yandexgpt-lite", "provider": "yandex"}
    ]
)
```

---

## Best Practices

### For Model Answer Evaluation
1. Test on diverse content types
2. Use representative exams (15-30 questions minimum)
3. Compare same-language models
4. Track which question types resist AI better
5. Set acceptable AI-pass rate thresholds (e.g., <40%)

### Question Design for AI Resistance
Questions that are more resistant to AI:
- Require evidence/citations from source
- Need multi-step reasoning
- Involve application rather than recall
- Use unusual phrasing or obfuscation

---

## Troubleshooting

**Yandex API Errors (401)**
- Check `YANDEX_CLOUD_API_KEY` and `YANDEX_FOLDER_ID` in `.env`

**OpenAI Rate Limits**
- Add delays or use lower-tier model

**JSON Parse Errors**
- Check prompt clarity or lower temperature
