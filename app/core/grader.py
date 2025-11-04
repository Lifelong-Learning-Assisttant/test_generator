"""
Answer grading module for automated exam checking.
"""
from typing import List, Dict
from app.models.schemas import (
    Exam, GradeRequest, GradeResponse,
    QuestionResult, GradeSummary, Question
)


class Grader:
    """Handles grading of student answers against exam answer keys."""

    def grade(
        self,
        exam: Exam,
        request: GradeRequest,
        partial_credit: bool = True
    ) -> GradeResponse:
        """
        Grade student answers against exam answer keys.

        Args:
            exam: The exam with questions and correct answers
            request: Student answers to grade
            partial_credit: Whether to award partial credit for multiple choice

        Returns:
            GradeResponse with summary and per-question results

        Raises:
            ValueError: If request has no answers or invalid question IDs
        """
        if not request.answers:
            raise ValueError("GradeRequest must contain at least one answer")

        # Build question lookup
        questions_map: Dict[str, Question] = {q.id: q for q in exam.questions}

        # Validate all question IDs exist
        for answer in request.answers:
            if answer.question_id not in questions_map:
                raise ValueError(f"Question ID '{answer.question_id}' not found in exam")

        # Grade each answer
        results: List[QuestionResult] = []
        total_credit = 0.0

        for student_answer in request.answers:
            question = questions_map[student_answer.question_id]
            result = self._grade_question(
                question,
                student_answer.choice,
                partial_credit
            )
            results.append(result)
            total_credit += result.partial_credit

        # Calculate summary
        total_questions = len(results)
        correct_count = sum(1 for r in results if r.is_correct)
        score_percent = (total_credit / total_questions * 100.0) if total_questions > 0 else 0.0

        summary = GradeSummary(
            total=total_questions,
            correct=correct_count,
            score_percent=round(score_percent, 2)
        )

        return GradeResponse(
            exam_id=request.exam_id,
            summary=summary,
            per_question=results
        )

    def _grade_question(
        self,
        question: Question,
        given: List[int],
        partial_credit: bool
    ) -> QuestionResult:
        """
        Grade a single question.

        Args:
            question: The question being graded
            given: Student's answer choices (indices)
            partial_credit: Whether to calculate partial credit

        Returns:
            QuestionResult with grading details
        """
        expected = question.correct

        # For single_choice, simple exact match
        if question.type == "single_choice":
            is_correct = given == expected
            credit = 1.0 if is_correct else 0.0

        # For multiple_choice
        else:
            # Sort for comparison
            expected_sorted = sorted(expected)
            given_sorted = sorted(given)

            # Check if fully correct
            is_correct = expected_sorted == given_sorted

            # Calculate credit
            if is_correct:
                credit = 1.0
            elif partial_credit:
                credit = self.calculate_partial_credit(expected, given)
            else:
                credit = 0.0

        return QuestionResult(
            question_id=question.id,
            is_correct=is_correct,
            expected=expected,
            given=given,
            partial_credit=round(credit, 4)
        )

    def calculate_partial_credit(
        self,
        expected: List[int],
        given: List[int]
    ) -> float:
        """
        Calculate partial credit for multiple choice questions.

        Formula: (correct_selected - wrong_selected) / total_expected
        Credit is clamped to [0.0, 1.0]

        Args:
            expected: List of correct answer indices
            given: List of student's answer indices

        Returns:
            Partial credit score between 0.0 and 1.0
        """
        expected_set = set(expected)
        given_set = set(given)

        # Count correct selections (intersection)
        correct_selected = len(expected_set & given_set)

        # Count wrong selections (given but not expected)
        wrong_selected = len(given_set - expected_set)

        # Total correct answers expected
        total_expected = len(expected_set)

        if total_expected == 0:
            return 0.0

        # Calculate credit: reward correct, penalize wrong
        credit = (correct_selected - wrong_selected) / total_expected

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, credit))
