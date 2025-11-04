"""
OpenAI API client wrapper for question generation.
"""
import json
from typing import Dict, Any
from openai import OpenAI
from app.config import settings


class OpenAIClient:
    """Wrapper for OpenAI API calls."""

    def __init__(self):
        """Initialize OpenAI client with API key from settings."""
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url
        )
        self.model = settings.openai_model

    def generate_question(
        self,
        content: str,
        question_type: str,
        difficulty: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generate a single question from content.

        Args:
            content: Source content to generate question from
            question_type: "single_choice" or "multiple_choice"
            difficulty: "easy", "medium", or "hard"

        Returns:
            Dict with question data (stem, options, correct)
        """
        prompt = self._build_prompt(content, question_type, difficulty)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert medical educator creating educational test questions."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # Validate result has required fields
            if not all(k in result for k in ["stem", "options", "correct"]):
                raise ValueError("Invalid response from OpenAI: missing required fields")

            return result

        except Exception as e:
            raise RuntimeError(f"Failed to generate question: {str(e)}")

    def _build_prompt(self, content: str, question_type: str, difficulty: str) -> str:
        """
        Build prompt for question generation.

        Args:
            content: Source content
            question_type: Type of question
            difficulty: Difficulty level

        Returns:
            Formatted prompt string
        """
        if question_type == "single_choice":
            type_instruction = "Create a single-choice question with EXACTLY ONE correct answer."
            correct_format = "The 'correct' field must be a list with exactly ONE index (e.g., [2])."
        else:
            type_instruction = "Create a multiple-choice question with 2-3 correct answers."
            correct_format = "The 'correct' field must be a list with 2-3 indices (e.g., [1, 3])."

        prompt = f"""Based on the following medical content, generate a {difficulty} difficulty test question.

Content:
{content}

Requirements:
- {type_instruction}
- Provide 4-5 answer options
- Options must be plausible but clearly distinguishable
- Question must be answerable from the given content
- Use clear, unambiguous language

Return ONLY a JSON object with this exact structure:
{{
  "stem": "The question text here?",
  "options": ["Option A", "Option B", "Option C", "Option D"],
  "correct": [index_or_indices]
}}

Important:
- {correct_format}
- Indices are 0-based (first option is index 0)
- Do NOT include any additional text, explanations, or markdown
- Return ONLY valid JSON
"""
        return prompt
