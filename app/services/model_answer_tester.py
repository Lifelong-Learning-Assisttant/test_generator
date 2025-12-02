"""
Service for testing how well different LLM models answer exam questions.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict

from app.models.schemas import Exam, Question
from app.services.openai_client import OpenAIClient
from app.services.yandex_client import YandexGPTClient
from app.config import settings


@dataclass
class ModelTestResult:
    """Results from testing a model on an exam."""
    model_name: str
    provider: str  # "openai" or "yandex"
    exam_id: str
    total_questions: int
    correct_count: int
    accuracy: float
    per_question_results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ModelAnswerTester:
    """Service for evaluating model performance on answering exam questions."""

    def __init__(self):
        """Initialize the model answer tester."""
        self.results_dir = Path(settings.data_dir) / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

    def test_model_on_exam(
        self,
        exam: Exam,
        model_name: str,
        provider: Literal["openai", "yandex"],
        output_dir: Optional[str] = None,
        language: str = "en"
    ) -> ModelTestResult:
        """
        Test a model on all questions in an exam.

        Args:
            exam: Exam object with questions
            model_name: Name of the model to test
            provider: "openai" or "yandex"
            output_dir: Optional directory to save results
            language: Language for prompts ("en" or "ru")

        Returns:
            ModelTestResult with accuracy and per-question details
        """
        if provider == "openai":
            client = OpenAIClient()
            # Temporarily override model
            original_model = client.model
            client.model = model_name
        elif provider == "yandex":
            client = YandexGPTClient()
            original_model = client.model
            client.model = model_name
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        try:
            per_question_results = []
            correct_count = 0

            for question in exam.questions:
                try:
                    # Get model's answer
                    if question.type == "open_ended":
                        model_answer = client.answer_question(
                            question_stem=question.stem,
                            question_type=question.type,
                            language=language
                        )

                        # Grade the open-ended answer
                        grading_result = client.grade_open_ended(
                            question_stem=question.stem,
                            reference_answer=question.reference_answer,
                            rubric=question.rubric,
                            student_answer=model_answer["text_answer"],
                            language=language
                        )

                        is_correct = grading_result["score"] >= 0.7  # 70% threshold
                        per_question_results.append({
                            "question_id": question.id,
                            "question_type": question.type,
                            "correct": is_correct,
                            "model_answer": model_answer["text_answer"],
                            "expected_answer": question.reference_answer,
                            "grading_score": grading_result["score"],
                            "feedback": grading_result["feedback"],
                            "rubric_scores": grading_result["rubric_scores"]
                        })
                    else:
                        # Choice questions (single or multiple)
                        model_answer = client.answer_question(
                            question_stem=question.stem,
                            question_type=question.type,
                            options=question.options,
                            language=language
                        )

                        is_correct = self._check_answer(question, model_answer)
                        per_question_results.append({
                            "question_id": question.id,
                            "question_type": question.type,
                            "correct": is_correct,
                            "model_answer": model_answer["choice"],
                            "expected_answer": question.correct,
                            "reasoning": model_answer.get("reasoning", "")
                        })

                    if is_correct:
                        correct_count += 1

                except Exception as e:
                    # Log error but continue with other questions
                    per_question_results.append({
                        "question_id": question.id,
                        "question_type": question.type,
                        "correct": False,
                        "error": str(e)
                    })

            accuracy = correct_count / len(exam.questions) if exam.questions else 0.0

            result = ModelTestResult(
                model_name=model_name,
                provider=provider,
                exam_id=exam.exam_id,
                total_questions=len(exam.questions),
                correct_count=correct_count,
                accuracy=round(accuracy, 4),
                per_question_results=per_question_results,
                metadata={
                    "language": language,
                    "exam_config": exam.config_used
                }
            )

            # Save result if output_dir specified
            if output_dir:
                self.save_result(result, output_dir)

            return result

        finally:
            # Restore original model
            client.model = original_model

    def _check_answer(self, question: Question, model_answer: Dict[str, Any]) -> bool:
        """
        Check if model's answer is correct.

        Args:
            question: Question object with correct answer
            model_answer: Model's answer dict

        Returns:
            True if answer is correct
        """
        if question.type == "single_choice":
            # Exact match required for single choice
            return model_answer["choice"] == question.correct

        elif question.type == "multiple_choice":
            # Must match all correct answers (exact set match)
            return set(model_answer["choice"]) == set(question.correct)

        return False

    def load_exam(self, exam_path: str) -> Exam:
        """
        Load an exam from a JSON file.

        Args:
            exam_path: Path to exam JSON file

        Returns:
            Exam object
        """
        with open(exam_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return Exam(**data)

    def save_result(
        self,
        result: ModelTestResult,
        output_dir: Optional[str] = None
    ) -> str:
        """
        Save test result to JSON file.

        Args:
            result: ModelTestResult to save
            output_dir: Directory to save to (defaults to self.results_dir)

        Returns:
            Path to saved file
        """
        if output_dir:
            save_dir = Path(output_dir)
        else:
            save_dir = self.results_dir

        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"model_test_{result.model_name}_{result.exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = save_dir / filename

        # Convert result to dict and handle Pydantic models
        result_dict = asdict(result)

        # Convert ExamConfig to dict if present
        if "metadata" in result_dict and "exam_config" in result_dict["metadata"]:
            from app.models.schemas import ExamConfig
            exam_config = result_dict["metadata"]["exam_config"]
            if isinstance(exam_config, ExamConfig):
                result_dict["metadata"]["exam_config"] = exam_config.model_dump()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False)

        return str(filepath)

    def batch_test_models(
        self,
        exam: Exam,
        models: List[Dict[str, str]],
        output_dir: Optional[str] = None,
        language: str = "en"
    ) -> List[ModelTestResult]:
        """
        Test multiple models on the same exam.

        Args:
            exam: Exam to test on
            models: List of dicts with "model_name" and "provider" keys
            output_dir: Optional directory to save results
            language: Language for prompts

        Returns:
            List of ModelTestResult objects
        """
        results = []

        for model_config in models:
            print(f"\nTesting {model_config['model_name']} ({model_config['provider']})...")
            try:
                result = self.test_model_on_exam(
                    exam=exam,
                    model_name=model_config["model_name"],
                    provider=model_config["provider"],
                    output_dir=output_dir,
                    language=language
                )
                results.append(result)
                print(f"  Accuracy: {result.accuracy:.2%} ({result.correct_count}/{result.total_questions})")
            except Exception as e:
                print(f"  Error testing {model_config['model_name']}: {e}")

        return results

    def compare_models(
        self,
        results: List[ModelTestResult],
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare results from multiple models.

        Args:
            results: List of ModelTestResult objects
            output_dir: Optional directory to save comparison

        Returns:
            Comparison dict with analysis
        """
        if not results:
            return {"error": "No results to compare"}

        comparison = {
            "exam_id": results[0].exam_id,
            "total_questions": results[0].total_questions,
            "models": [],
            "best_model": None,
            "best_accuracy": 0.0,
            "timestamp": datetime.now().isoformat()
        }

        for result in results:
            model_info = {
                "model_name": result.model_name,
                "provider": result.provider,
                "accuracy": result.accuracy,
                "correct_count": result.correct_count,
                "ai_pass_rate": result.accuracy  # Same as accuracy for now
            }
            comparison["models"].append(model_info)

            if result.accuracy > comparison["best_accuracy"]:
                comparison["best_accuracy"] = result.accuracy
                comparison["best_model"] = result.model_name

        # Per-question breakdown
        question_breakdown = {}
        for result in results:
            for q_result in result.per_question_results:
                q_id = q_result["question_id"]
                if q_id not in question_breakdown:
                    question_breakdown[q_id] = {
                        "question_type": q_result.get("question_type", "unknown"),
                        "models_correct": [],
                        "models_incorrect": []
                    }

                if q_result.get("correct", False):
                    question_breakdown[q_id]["models_correct"].append(result.model_name)
                else:
                    question_breakdown[q_id]["models_incorrect"].append(result.model_name)

        comparison["per_question_breakdown"] = question_breakdown

        # Save comparison if output_dir specified
        if output_dir:
            save_dir = Path(output_dir)
            save_dir.mkdir(parents=True, exist_ok=True)
            filename = f"model_comparison_{results[0].exam_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = save_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2, ensure_ascii=False)

            comparison["comparison_file"] = str(filepath)

        return comparison
