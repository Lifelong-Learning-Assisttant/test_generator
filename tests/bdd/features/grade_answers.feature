Feature: Grade student answers
  As a teacher
  I want to automatically grade student answers
  So that I can quickly assess exam results

  Background:
    Given a test exam with 3 questions exists
    And the exam contains single choice and multiple choice questions

  Scenario: Grade perfect score
    Given a student answers all questions correctly
    When I submit answers for grading
    Then the grading summary shows 100% score
    And all questions are marked as correct
    And the results are saved to file

  Scenario: Grade partial score with some incorrect answers
    Given a student answers 2 out of 3 questions correctly
    When I submit answers for grading
    Then the grading summary shows approximately 67% score
    And exactly 2 questions are marked as correct
    And 1 question is marked as incorrect

  Scenario: Grade with partial credit for multiple choice
    Given a student partially answers a multiple choice question
    When I submit answers for grading with partial credit enabled
    Then the question receives partial credit
    And the score is between 0% and 100%

  Scenario: Attempt to grade non-existent exam
    Given no exam exists with ID "invalid-exam"
    When I submit answers for the non-existent exam
    Then I receive a 404 error
    And the error message indicates exam not found

  Scenario: Grade answers for subset of questions
    Given a student answers only 2 out of 3 questions
    When I submit the partial answers for grading
    Then only the answered questions are graded
    And the summary reflects the number of answered questions
