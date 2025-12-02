"""
Unit tests for YandexGPT API client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.yandex_client import YandexGPTClient
from app.config import settings


class TestYandexGPTClient:
    """Test suite for YandexGPT client."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Yandex credentials."""
        with patch('app.services.yandex_client.settings') as mock:
            mock.yandex_cloud_api_key = "test-api-key"
            mock.yandex_cloud_api_key_identifier = "test-identifier"
            mock.yandex_folder_id = "test-folder-id"
            mock.yandex_model = "yandexgpt-lite"
            yield mock

    @pytest.fixture
    def client(self, mock_settings):
        """Create YandexGPT client instance."""
        return YandexGPTClient()

    def test_client_initialization(self, mock_settings):
        """Test client initializes with correct settings."""
        client = YandexGPTClient()
        assert client.api_key == "test-api-key"
        assert client.folder_id == "test-folder-id"
        assert client.model == "yandexgpt-lite"

    def test_client_missing_api_key(self):
        """Test client raises error when API key is missing."""
        with patch('app.services.yandex_client.settings') as mock:
            mock.yandex_cloud_api_key = ""
            mock.yandex_folder_id = "test-folder"
            with pytest.raises(ValueError, match="YANDEX_CLOUD_API_KEY not set"):
                YandexGPTClient()

    def test_client_missing_folder_id(self):
        """Test client raises error when folder ID is missing."""
        with patch('app.services.yandex_client.settings') as mock:
            mock.yandex_cloud_api_key = "test-key"
            mock.yandex_folder_id = ""
            with pytest.raises(ValueError, match="YANDEX_FOLDER_ID not set"):
                YandexGPTClient()

    @patch('requests.post')
    def test_generate_single_choice_question(self, mock_post, client):
        """Test generating a single-choice question."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": '{"stem": "Test question?", "options": ["A", "B", "C"], "correct": [1], "rubric": ["Check answer"]}'
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.generate_question(
            content="Test content",
            question_type="single_choice",
            difficulty="medium"
        )

        assert result["stem"] == "Test question?"
        assert result["options"] == ["A", "B", "C"]
        assert result["correct"] == [1]
        assert "rubric" in result

    @patch('requests.post')
    def test_generate_multiple_choice_question(self, mock_post, client):
        """Test generating a multiple-choice question."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": '{"stem": "Test question?", "options": ["A", "B", "C", "D"], "correct": [1, 2], "rubric": ["Check"]}'
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.generate_question(
            content="Test content",
            question_type="multiple_choice",
            difficulty="hard"
        )

        assert result["stem"] == "Test question?"
        assert len(result["correct"]) == 2
        assert set(result["correct"]) == {1, 2}

    @patch('requests.post')
    def test_generate_open_ended_question(self, mock_post, client):
        """Test generating an open-ended question."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": '{"stem": "Explain this?", "reference_answer": "Answer", "rubric": ["Point 1", "Point 2", "Point 3"]}'
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.generate_question(
            content="Test content",
            question_type="open_ended",
            difficulty="hard"
        )

        assert result["stem"] == "Explain this?"
        assert "reference_answer" in result
        assert len(result["rubric"]) == 3

    @patch('requests.post')
    def test_api_error_handling(self, mock_post, client):
        """Test handling of API errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="YandexGPT API error"):
            client.generate_question(
                content="Test content",
                question_type="single_choice"
            )

    @patch('requests.post')
    def test_answer_single_choice_question(self, mock_post, client):
        """Test answering a single-choice question."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": "2"
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.answer_question(
            question_stem="What is 2+2?",
            question_type="single_choice",
            options=["1", "2", "3", "4"]
        )

        assert result["choice"] == [2]
        assert "reasoning" in result

    @patch('requests.post')
    def test_answer_multiple_choice_question(self, mock_post, client):
        """Test answering a multiple-choice question."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": "Options 0 and 2 are correct."
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.answer_question(
            question_stem="Select all even numbers:",
            question_type="multiple_choice",
            options=["2", "3", "4", "5"]
        )

        assert "choice" in result
        assert isinstance(result["choice"], list)

    @patch('requests.post')
    def test_answer_open_ended_question(self, mock_post, client):
        """Test answering an open-ended question."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": "This is a detailed answer to the question."
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.answer_question(
            question_stem="Explain photosynthesis:",
            question_type="open_ended"
        )

        assert result["text_answer"]
        assert len(result["text_answer"]) > 0

    @patch('requests.post')
    def test_grade_open_ended(self, mock_post, client):
        """Test grading an open-ended answer."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "alternatives": [{
                    "message": {
                        "text": '{"rubric_scores": [1, 1, 0], "score": 0.67, "feedback": "Good answer"}'
                    }
                }]
            }
        }
        mock_post.return_value = mock_response

        result = client.grade_open_ended(
            question_stem="Explain X",
            reference_answer="Reference",
            rubric=["Point 1", "Point 2", "Point 3"],
            student_answer="Student answer"
        )

        assert result["score"] == 0.67
        assert len(result["rubric_scores"]) == 3
        assert "feedback" in result
