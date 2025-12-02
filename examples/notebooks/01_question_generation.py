"""
Jupyter-friendly manual for question generation.

This script demonstrates how to generate exam questions from markdown content
using different LLM providers (OpenAI and YandexGPT).

Run in Jupyter:
    %run examples/notebooks/01_question_generation.py

Or use as a library:
    from examples.notebooks.question_generation import generate_exam, generate_single_question
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.parser import MarkdownParser
from app.core.generator import QuestionGenerator
from app.models.schemas import ExamConfig, Exam
from app.services.openai_client import OpenAIClient
from app.services.yandex_client import YandexGPTClient


def generate_exam(
    content_file: str,
    total_questions: int = 10,
    single_choice_ratio: float = 0.5,
    multiple_choice_ratio: float = 0.3,
    open_ended_ratio: float = 0.2,
    language: str = "en",
    exam_id: str = None
) -> Exam:
    """
    Generate a full exam from markdown content.

    Args:
        content_file: Path to markdown file
        total_questions: Total number of questions to generate
        single_choice_ratio: Ratio of single-choice questions (0.0-1.0)
        multiple_choice_ratio: Ratio of multiple-choice questions (0.0-1.0)
        open_ended_ratio: Ratio of open-ended questions (0.0-1.0)
        language: "en" or "ru"
        exam_id: Optional exam ID (auto-generated if None)

    Returns:
        Exam object with generated questions

    Example:
        >>> exam = generate_exam(
        ...     "examples/medical_content.md",
        ...     total_questions=15,
        ...     language="ru"
        ... )
        >>> print(f"Generated {len(exam.questions)} questions")
        >>> print(exam.questions[0].stem)
    """
    # Parse markdown content
    parser = MarkdownParser()
    with open(content_file, 'r', encoding='utf-8') as f:
        content = f.read()

    document = parser.parse(content)

    # Create exam config
    config = ExamConfig(
        total_questions=total_questions,
        single_choice_ratio=single_choice_ratio,
        multiple_choice_ratio=multiple_choice_ratio,
        open_ended_ratio=open_ended_ratio,
        language=language
    )

    # Generate exam
    generator = QuestionGenerator()
    exam = generator.generate(document, config, exam_id or "jupyter-exam")

    return exam


def generate_single_question(
    content: str,
    question_type: str = "single_choice",
    difficulty: str = "medium",
    language: str = "en",
    provider: str = "openai",
    model_name: str = None
) -> dict:
    """
    Generate a single question from text content.

    Args:
        content: Text content to generate question from
        question_type: "single_choice", "multiple_choice", or "open_ended"
        difficulty: "easy", "medium", or "hard"
        language: "en" or "ru"
        provider: "openai" or "yandex"
        model_name: Optional model name override

    Returns:
        Dictionary with question data

    Example:
        >>> content = '''
        ... Photosynthesis is the process by which plants use sunlight
        ... to convert carbon dioxide and water into glucose and oxygen.
        ... This occurs in chloroplasts using chlorophyll.
        ... '''
        >>> question = generate_single_question(
        ...     content,
        ...     question_type="single_choice",
        ...     difficulty="medium"
        ... )
        >>> print(question["stem"])
        >>> print(question["options"])
    """
    if provider == "openai":
        client = OpenAIClient()
        if model_name:
            client.model = model_name
    elif provider == "yandex":
        client = YandexGPTClient()
        if model_name:
            client.model = model_name
    else:
        raise ValueError(f"Unknown provider: {provider}")

    question = client.generate_question(
        content=content,
        question_type=question_type,
        difficulty=difficulty,
        language=language
    )

    return question


def save_exam(exam: Exam, output_file: str = None):
    """
    Save exam to JSON file.

    Args:
        exam: Exam object to save
        output_file: Output file path (default: data/out/exam_{exam_id}.json)

    Example:
        >>> exam = generate_exam("content.md")
        >>> save_exam(exam, "my_exam.json")
    """
    import json
    from app.config import settings

    if output_file is None:
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"exam_{exam.exam_id}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(exam.model_dump(), f, indent=2, ensure_ascii=False)

    print(f"Exam saved to: {output_file}")
    return str(output_file)


# Example usage (for Jupyter)
if __name__ == "__main__":
    print("Question Generation Examples")
    print("=" * 60)

    # Example 1: Generate full exam
    print("\n1. Generating full exam from content...")
    try:
        exam = generate_exam(
            "data/uploads/padawan.md",
            total_questions=5,
            language="en"
        )
        print(f"   ✓ Generated {len(exam.questions)} questions")
        print(f"   Exam ID: {exam.exam_id}")

        # Show first question
        if exam.questions:
            q = exam.questions[0]
            print(f"\n   Sample question:")
            print(f"   Type: {q.type}")
            print(f"   Stem: {q.stem[:100]}...")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Example 2: Generate single question
    print("\n2. Generating single question...")
    try:
        content = """
        The Force is an energy field created by all living things.
        It surrounds us, penetrates us, and binds the galaxy together.
        Jedi use the Force for knowledge and defense, never for attack.
        """

        question = generate_single_question(
            content,
            question_type="single_choice",
            difficulty="medium",
            provider="openai"
        )

        print(f"   ✓ Generated question")
        print(f"   Stem: {question['stem']}")
        print(f"   Options: {question['options']}")
        print(f"   Correct: {question['correct']}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    # Example 3: Generate Russian question
    print("\n3. Generating Russian question...")
    try:
        content_ru = """
        Фотосинтез - это процесс, при котором растения используют
        солнечный свет для преобразования углекислого газа и воды
        в глюкозу и кислород.
        """

        question_ru = generate_single_question(
            content_ru,
            question_type="open_ended",
            difficulty="hard",
            language="ru",
            provider="openai"
        )

        print(f"   ✓ Generated Russian question")
        print(f"   Stem: {question_ru['stem']}")
        if 'reference_answer' in question_ru:
            print(f"   Reference: {question_ru['reference_answer'][:100]}...")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("\nNext steps:")
    print("- Use these functions in your Jupyter notebook")
    print("- Customize question parameters")
    print("- Save exams for later testing")
