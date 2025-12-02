"""
Jupyter-friendly manual for evaluating model answers.

This script demonstrates how to test different LLM models on exam questions
and compare their performance.

Run in Jupyter:
    %run examples/notebooks/02_model_evaluation.py

Or use as a library:
    from examples.notebooks.model_evaluation import test_model, compare_models
"""
import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.model_answer_tester import ModelAnswerTester, ModelTestResult
from app.models.schemas import Exam


def load_exam(exam_file: str) -> Exam:
    """
    Load an exam from JSON file.

    Args:
        exam_file: Path to exam JSON file

    Returns:
        Exam object

    Example:
        >>> exam = load_exam("data/out/exam_ex-123.json")
        >>> print(f"Loaded exam with {len(exam.questions)} questions")
    """
    tester = ModelAnswerTester()
    return tester.load_exam(exam_file)


def test_model(
    exam_file: str,
    model_name: str,
    provider: str = "openai",
    language: str = "en",
    save_results: bool = True
) -> ModelTestResult:
    """
    Test a model on an exam.

    Args:
        exam_file: Path to exam JSON file
        model_name: Name of model (e.g., "gpt-4o-mini", "yandexgpt-lite")
        provider: "openai" or "yandex"
        language: "en" or "ru"
        save_results: Whether to save results to file

    Returns:
        ModelTestResult with accuracy and details

    Example:
        >>> result = test_model(
        ...     "data/out/exam_ex-123.json",
        ...     "gpt-4o-mini",
        ...     provider="openai"
        ... )
        >>> print(f"Accuracy: {result.accuracy:.2%}")
        >>> print(f"Correct: {result.correct_count}/{result.total_questions}")
    """
    tester = ModelAnswerTester()
    exam = tester.load_exam(exam_file)

    result = tester.test_model_on_exam(
        exam=exam,
        model_name=model_name,
        provider=provider,
        output_dir="data/results" if save_results else None,
        language=language
    )

    return result


def compare_models(
    exam_file: str,
    models: list[dict],
    language: str = "en",
    save_results: bool = True
) -> dict:
    """
    Compare multiple models on the same exam.

    Args:
        exam_file: Path to exam JSON file
        models: List of dicts with "model_name" and "provider" keys
        language: "en" or "ru"
        save_results: Whether to save comparison to file

    Returns:
        Comparison dict with analysis

    Example:
        >>> comparison = compare_models(
        ...     "data/out/exam_ex-123.json",
        ...     [
        ...         {"model_name": "gpt-4o-mini", "provider": "openai"},
        ...         {"model_name": "yandexgpt-lite", "provider": "yandex"}
        ...     ]
        ... )
        >>> print(f"Best model: {comparison['best_model']}")
        >>> print(f"Best accuracy: {comparison['best_accuracy']:.2%}")
    """
    tester = ModelAnswerTester()
    exam = tester.load_exam(exam_file)

    results = tester.batch_test_models(
        exam=exam,
        models=models,
        output_dir="data/results" if save_results else None,
        language=language
    )

    comparison = tester.compare_models(
        results,
        output_dir="data/results" if save_results else None
    )

    return comparison


def analyze_result(result: ModelTestResult):
    """
    Print detailed analysis of test result.

    Args:
        result: ModelTestResult to analyze

    Example:
        >>> result = test_model("exam.json", "gpt-4o-mini")
        >>> analyze_result(result)
    """
    print("=" * 70)
    print(f"Model: {result.model_name} ({result.provider})")
    print(f"Exam: {result.exam_id}")
    print("=" * 70)

    # Overall stats
    print(f"\nOverall Performance:")
    print(f"  Total Questions: {result.total_questions}")
    print(f"  Correct Answers: {result.correct_count}")
    print(f"  Accuracy: {result.accuracy:.2%}")
    print(f"  AI Pass Rate: {result.accuracy:.2%}")

    # Breakdown by question type
    type_stats = {}
    for q_result in result.per_question_results:
        q_type = q_result.get("question_type", "unknown")
        if q_type not in type_stats:
            type_stats[q_type] = {"total": 0, "correct": 0}

        type_stats[q_type]["total"] += 1
        if q_result.get("correct", False):
            type_stats[q_type]["correct"] += 1

    print(f"\nBreakdown by Question Type:")
    for q_type, stats in type_stats.items():
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        print(f"  {q_type:15} {stats['correct']:2}/{stats['total']:2} ({accuracy:6.2%})")

    # Failed questions
    failed = [q for q in result.per_question_results if not q.get("correct", False)]
    if failed:
        print(f"\nFailed Questions ({len(failed)}):")
        for q_result in failed[:5]:  # Show first 5
            print(f"  - {q_result['question_id']} ({q_result.get('question_type', 'unknown')})")
            if "error" in q_result:
                print(f"    Error: {q_result['error']}")
            elif q_result.get("question_type") == "open_ended":
                print(f"    Score: {q_result.get('grading_score', 0):.2%}")
            else:
                print(f"    Expected: {q_result.get('expected_answer')}")
                print(f"    Got: {q_result.get('model_answer')}")

        if len(failed) > 5:
            print(f"  ... and {len(failed) - 5} more")


def print_comparison(comparison: dict):
    """
    Print formatted comparison of models.

    Args:
        comparison: Comparison dict from compare_models()

    Example:
        >>> comparison = compare_models(...)
        >>> print_comparison(comparison)
    """
    print("=" * 70)
    print(f"Model Comparison - Exam: {comparison['exam_id']}")
    print("=" * 70)
    print(f"Total Questions: {comparison['total_questions']}\n")

    # Models summary
    print(f"{'Model':<25} {'Provider':<12} {'Accuracy':<12} {'Correct'}")
    print("-" * 70)
    for model in comparison['models']:
        print(
            f"{model['model_name']:<25} "
            f"{model['provider']:<12} "
            f"{model['accuracy']:>10.2%}  "
            f"{model['correct_count']}/{comparison['total_questions']}"
        )

    print(f"\n{'Best Model:':<25} {comparison['best_model']}")
    print(f"{'Best Accuracy:':<25} {comparison['best_accuracy']:.2%}")

    # Questions where all models failed
    if "per_question_breakdown" in comparison:
        all_failed = []
        for q_id, q_data in comparison["per_question_breakdown"].items():
            if not q_data["models_correct"]:
                all_failed.append((q_id, q_data["question_type"]))

        if all_failed:
            print(f"\nQuestions where ALL models failed ({len(all_failed)}):")
            for q_id, q_type in all_failed[:5]:
                print(f"  - {q_id} ({q_type})")


# Example usage (for Jupyter)
if __name__ == "__main__":
    print("Model Evaluation Examples")
    print("=" * 70)

    # Find available exams
    from pathlib import Path
    exam_files = list(Path("data/out").glob("exam_*.json"))

    if not exam_files:
        print("\nNo exam files found in data/out/")
        print("Please generate an exam first using 01_question_generation.py")
        sys.exit(0)

    # Use first available exam
    exam_file = str(exam_files[0])
    print(f"\nUsing exam: {exam_file}")

    # Example 1: Test single model (OpenAI)
    print("\n" + "=" * 70)
    print("Example 1: Testing GPT-4o-mini")
    print("=" * 70)
    try:
        result_gpt = test_model(
            exam_file,
            model_name="gpt-4o-mini",
            provider="openai",
            language="en"
        )
        analyze_result(result_gpt)
    except Exception as e:
        print(f"Error: {e}")

    # Example 2: Test YandexGPT (if credentials available)
    print("\n" + "=" * 70)
    print("Example 2: Testing YandexGPT")
    print("=" * 70)
    try:
        from app.config import settings
        if settings.yandex_cloud_api_key and settings.yandex_folder_id:
            result_yandex = test_model(
                exam_file,
                model_name="yandexgpt-lite",
                provider="yandex",
                language="en"
            )
            analyze_result(result_yandex)
        else:
            print("YandexGPT credentials not found in .env")
            print("Set YANDEX_CLOUD_API_KEY and YANDEX_FOLDER_ID to test Yandex models")
    except Exception as e:
        print(f"Error: {e}")

    # Example 3: Compare multiple models
    print("\n" + "=" * 70)
    print("Example 3: Comparing Models")
    print("=" * 70)
    try:
        models = [
            {"model_name": "gpt-4o-mini", "provider": "openai"},
        ]

        # Add Yandex if available
        from app.config import settings
        if settings.yandex_cloud_api_key and settings.yandex_folder_id:
            models.append({"model_name": "yandexgpt-lite", "provider": "yandex"})

        comparison = compare_models(
            exam_file,
            models=models,
            language="en"
        )
        print_comparison(comparison)

        if "comparison_file" in comparison:
            print(f"\nComparison saved to: {comparison['comparison_file']}")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("\nNext steps:")
    print("- Customize models and parameters in your notebook")
    print("- Analyze per-question results")
    print("- Compare different prompt strategies")
