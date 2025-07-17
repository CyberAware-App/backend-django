from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_profile")
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    is_verified = models.BooleanField(default=False)
    first_login = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
  
    
class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField(default=timezone.now() + timedelta(minutes=10))
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()
    


class Module(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    content = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.name
    
    
class UserModuleProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="module_progress")
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('user', 'module')
    
    def __str__(self):
        return f"{self.user.email} - {self.module.name}"
    

class ModuleQuiz(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    question = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.module.name} - {self.question}"
    
    
class FinalQuiz(models.Model):
    question = models.CharField(max_length=255)
    options = models.JSONField()
    correct_answer = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.question}"
    

class QuizSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_sessions")
    attempt_number = models.PositiveIntegerField()
    score = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'attempt_number')
    
    def __str__(self):
        return f"{self.user.email} - Attempt {self.attempt_number}"
    

class UserQuizAnswer(models.Model):
    session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(FinalQuiz, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=255)
    is_correct = models.BooleanField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def save(self, *args, **kwargs):
        self.is_correct = (self.selected_option == self.question.correct_answer)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.session.user.email} - {self.question.question}"
    
    
class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feedback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.user.email} - {self.feedback}"


class Certificate(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="certificate")
    certificate_id = models.CharField(max_length=50, unique=True)
    quiz_session = models.ForeignKey(QuizSession, on_delete=models.CASCADE, related_name="certificate")
    issued_date = models.DateTimeField(default=timezone.now)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    is_valid = models.BooleanField(default=True)
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            # Generate unique certificate ID: CERT-YYYYMMDD-USERID
            date_str = timezone.now().strftime('%Y%m%d')
            self.certificate_id = f"CERT-{date_str}-{self.user.id:06d}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Certificate {self.certificate_id} - {self.user.email}"
    
    class Meta:
        ordering = ['-issued_date']
    
    