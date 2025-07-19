import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from app.models import Module, UserModuleProgress, FinalQuiz, Certificate, UserProfile, QuizSession

User = get_user_model()

@pytest.mark.django_db
class TestViewsEndpoints:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="viewtest@example.com", password="testpass123")
        # Explicitly create the UserProfile
        self.profile = UserProfile.objects.create(
            user=self.user,
            first_name="View",
            last_name="Test",
            is_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "modules" in data["data"]
        assert "completed_modules" in data["data"]
        assert "total_modules" in data["data"]
        assert "percentage_completed" in data["data"]

    def test_get_module_view(self):
        module = Module.objects.create(name="Test Module", description="desc", module_type="video", google_drive_file_id="1234567890")
        response = self.client.get(reverse('get-module', kwargs={"module_id": module.id}))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "module" in data["data"]

    def test_mark_module_as_completed_view(self):
        module = Module.objects.create(name="Test Module", description="desc", module_type="video", google_drive_file_id="1234567890")
        response = self.client.post(reverse('mark-module-as-completed', kwargs={"module_id": module.id}))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert data["data"]["completed"] is True

    def test_user_module_progress_view(self):
        module = Module.objects.create(name="Test Module", description="desc", module_type="video", google_drive_file_id="1234567890")
        UserModuleProgress.objects.create(user=self.user, module=module, completed=True)
        response = self.client.get(reverse('module-progress'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert isinstance(data["data"], list)

    def test_get_module_quiz_view(self):
        module = Module.objects.create(name="Test Module", description="desc", module_type="video", google_drive_file_id="1234567890")
        response = self.client.get(reverse('get-module-quiz', kwargs={"module_id": module.id}))
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_final_quiz_get_view(self):
        response = self.client.get(reverse('final-quiz'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert all("question" in item for item in data["data"])

    def test_final_quiz_post_view(self):
        # This assumes at least one FinalQuiz exists
        quiz = FinalQuiz.objects.create(question="Q1", options=["A", "B", "C"], correct_answer="A")
        # Send answers as a list directly, not wrapped in "answers" key
        answers = [{"question": quiz.question, "selected_option": "A"}]
        response = self.client.post(reverse('final-quiz'), answers, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "score" in data["data"]
        assert "passed" in data["data"]

    def test_certificate_view(self):
        # Create a quiz session first
        quiz_session = QuizSession.objects.create(
            user=self.user,
            attempt_number=1,
            score=100,
            passed=True
        )
        # Create a valid certificate for the user with quiz_session
        cert = Certificate.objects.create(
            user=self.user,
            quiz_session=quiz_session,
            score=100,
            is_valid=True
        )
        response = self.client.get(reverse('certificate'))
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "certificate_id" in data["data"]

    def test_certificate_download_view(self):
        # Create a quiz session first
        quiz_session = QuizSession.objects.create(
            user=self.user,
            attempt_number=1,
            score=100,
            passed=True
        )
        # Create a valid certificate for the user with quiz_session
        cert = Certificate.objects.create(
            user=self.user,
            quiz_session=quiz_session,
            score=100,
            is_valid=True
        )
        response = self.client.get(reverse('certificate-download', kwargs={"certificate_id": cert.certificate_id}))
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

def run_views_tests():
    import pytest
    pytest.main([__file__]) 