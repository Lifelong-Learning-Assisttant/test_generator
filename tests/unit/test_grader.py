"""
Unit tests for answer grading module (TDD - RED phase).

Tests written BEFORE implementation.
"""
import pytest
from app.core.grader import Grader
from app.models.schemas import (
    Question, Exam, ExamConfig, GradeRequest,
    StudentAnswer, GradeResponse
)


class TestGrader:
    """Tests for grading functionality."""

    @pytest.fixture
    def grader(self):
        return Grader()

    @pytest.fixture
    def sample_exam(self):
        """Create a sample exam with mixed question types."""
        q1 = Question(
            id="q1",
            type="single_choice",
            stem="What is 2+2?",
            options=["3", "4", "5", "6"],
            correct=[1]
        )
        q2 = Question(
            id="q2",
            type="single_choice",
            stem="Capital of France?",
            options=["London", "Paris", "Berlin"],
            correct=[1]
        )
        q3 = Question(
            id="q3",
            type="multiple_choice",
            stem="Select all even numbers:",
            options=["1", "2", "3", "4", "5", "6"],
            correct=[1, 3, 5]  # 2, 4, 6
        )
        q4 = Question(
            id="q4",
            type="multiple_choice",
            stem="Select all vowels:",
            options=["A", "B", "C", "E", "I"],
            correct=[0, 3, 4]  # A, E, I
        )

        return Exam(
            exam_id="exam1",
            questions=[q1, q2, q3, q4],
            config_used=ExamConfig()
        )

    def test_grader_initialization(self, grader):
        """Test that grader can be initialized."""
        assert grader is not None

    def test_grade_single_choice_correct(self, grader, sample_exam):
        """Test grading correct single choice answer."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q1", choice=[1])]
        )
        response = grader.grade(sample_exam, request)

        assert response.exam_id == "exam1"
        assert len(response.per_question) == 1
        result = response.per_question[0]
        assert result.is_correct is True
        assert result.question_id == "q1"
        assert result.partial_credit == 1.0

    def test_grade_single_choice_incorrect(self, grader, sample_exam):
        """Test grading incorrect single choice answer."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q1", choice=[0])]  # Wrong answer
        )
        response = grader.grade(sample_exam, request)

        result = response.per_question[0]
        assert result.is_correct is False
        assert result.partial_credit == 0.0
        assert result.expected == [1]
        assert result.given == [0]

    def test_grade_multiple_choice_all_correct(self, grader, sample_exam):
        """Test grading fully correct multiple choice answer."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q3", choice=[1, 3, 5])]
        )
        response = grader.grade(sample_exam, request)

        result = response.per_question[0]
        assert result.is_correct is True
        assert result.partial_credit == 1.0

    def test_grade_multiple_choice_partial_correct(self, grader, sample_exam):
        """Test partial credit for multiple choice (some correct answers)."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q3", choice=[1, 3])]  # 2/3 correct
        )
        response = grader.grade(sample_exam, request, partial_credit=True)

        result = response.per_question[0]
        # Partial credit calculation: correct answers / total correct expected
        # But should also penalize wrong selections
        assert result.partial_credit > 0.0
        assert result.partial_credit < 1.0

    def test_grade_multiple_choice_with_wrong_selections(self, grader, sample_exam):
        """Test partial credit when student selects some wrong options."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q3", choice=[0, 1, 3])]  # 2 correct, 1 wrong
        )
        response = grader.grade(sample_exam, request, partial_credit=True)

        result = response.per_question[0]
        # Should have reduced credit due to wrong selection
        assert result.partial_credit > 0.0
        assert result.partial_credit < 1.0

    def test_grade_multiple_choice_no_partial_credit(self, grader, sample_exam):
        """Test multiple choice without partial credit (all-or-nothing)."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="q3", choice=[1, 3])]  # Incomplete
        )
        response = grader.grade(sample_exam, request, partial_credit=False)

        result = response.per_question[0]
        assert result.is_correct is False
        assert result.partial_credit == 0.0

    def test_grade_summary_all_correct(self, grader, sample_exam):
        """Test summary when all answers are correct."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[
                StudentAnswer(question_id="q1", choice=[1]),
                StudentAnswer(question_id="q2", choice=[1]),
                StudentAnswer(question_id="q3", choice=[1, 3, 5]),
                StudentAnswer(question_id="q4", choice=[0, 3, 4]),
            ]
        )
        response = grader.grade(sample_exam, request)

        assert response.summary.total == 4
        assert response.summary.correct == 4
        assert response.summary.score_percent == 100.0

    def test_grade_summary_mixed_results(self, grader, sample_exam):
        """Test summary with mixed correct/incorrect answers."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[
                StudentAnswer(question_id="q1", choice=[1]),  # Correct - 1.0
                StudentAnswer(question_id="q2", choice=[0]),  # Wrong - 0.0
                StudentAnswer(question_id="q3", choice=[1, 3, 5]),  # Correct - 1.0
                StudentAnswer(question_id="q4", choice=[0]),  # Incomplete - partial credit ~0.33
            ]
        )
        response = grader.grade(sample_exam, request)

        assert response.summary.total == 4
        assert response.summary.correct == 2
        # With partial credit: (1.0 + 0.0 + 1.0 + ~0.33) / 4 * 100 ≈ 58.33%
        assert 55.0 <= response.summary.score_percent <= 60.0

    def test_grade_partial_answers_only(self, grader, sample_exam):
        """Test grading when not all questions are answered."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[
                StudentAnswer(question_id="q1", choice=[1]),
                StudentAnswer(question_id="q3", choice=[1, 3, 5]),
            ]
        )
        response = grader.grade(sample_exam, request)

        # Should only grade answered questions
        assert len(response.per_question) == 2
        assert response.summary.total == 2

    def test_grade_with_partial_credit_in_summary(self, grader, sample_exam):
        """Test that partial credit is reflected in summary score."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[
                StudentAnswer(question_id="q1", choice=[1]),  # 1.0 credit
                StudentAnswer(question_id="q3", choice=[1, 3]),  # Partial credit
            ]
        )
        response = grader.grade(sample_exam, request, partial_credit=True)

        # Total score should be between 50% and 100%
        assert 50.0 < response.summary.score_percent < 100.0

    def test_grade_invalid_question_id_raises_error(self, grader, sample_exam):
        """Test that grading with invalid question ID raises error."""
        request = GradeRequest(
            exam_id="exam1",
            answers=[StudentAnswer(question_id="invalid_id", choice=[0])]
        )

        with pytest.raises((ValueError, KeyError)):
            grader.grade(sample_exam, request)

    def test_grade_empty_answers(self, grader, sample_exam):
        """Test grading with no answers."""
        # Pydantic validates that answers list is not empty
        with pytest.raises(ValueError):
            GradeRequest(exam_id="exam1", answers=[])


class TestPartialCreditCalculation:
    """Tests for partial credit calculation logic."""

    @pytest.fixture
    def grader(self):
        return Grader()

    def test_calculate_partial_credit_all_correct(self, grader):
        """Test partial credit when all answers correct."""
        expected = [0, 2, 4]
        given = [0, 2, 4]

        credit = grader.calculate_partial_credit(expected, given)
        assert credit == 1.0

    def test_calculate_partial_credit_subset(self, grader):
        """Test partial credit when student selects subset of correct."""
        expected = [0, 2, 4]
        given = [0, 2]  # 2/3 correct

        credit = grader.calculate_partial_credit(expected, given)
        assert 0.6 <= credit <= 0.7  # Should be around 2/3

    def test_calculate_partial_credit_with_wrong(self, grader):
        """Test partial credit with wrong selections."""
        expected = [0, 2, 4]
        given = [0, 1, 2]  # 2 correct, 1 wrong

        credit = grader.calculate_partial_credit(expected, given)
        # Should penalize for wrong selection
        assert 0.0 < credit < 0.7

    def test_calculate_partial_credit_all_wrong(self, grader):
        """Test partial credit when all selections wrong."""
        expected = [0, 2, 4]
        given = [1, 3, 5]

        credit = grader.calculate_partial_credit(expected, given)
        assert credit == 0.0
