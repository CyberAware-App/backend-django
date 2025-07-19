from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user__email', 'first_name', 'last_name', 'is_verified']
    list_filter = ['user__email', 'is_verified']
    search_fields = ['user__email']


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user__email', 'code', 'is_used', 'expires_at']
    list_filter = ['user__email', 'is_used']
    search_fields = ['user__email']
    
    
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'module_type']
    search_fields = ['name']
    
    
@admin.register(UserModuleProgress)
class UserModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['user__email', 'module__name', 'completed']
    list_filter = ['user__email', 'module__name', 'completed']
    search_fields = ['user__email', 'module__name']
    
    
@admin.register(ModuleQuiz)
class ModuleQuizAdmin(admin.ModelAdmin):
    list_display = ['module__name', 'question']
    list_filter = ['module__name']
    search_fields = ['module__name', 'question']
    
@admin.register(FinalQuiz)
class FinalQuizAdmin(admin.ModelAdmin):
    list_display = ['question']
    search_fields = ['question']
    
    
@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = ['user__email', 'attempt_number', 'score', 'passed']
    list_filter = ['user__email', 'passed']
    search_fields = ['user__email']
    

@admin.register(UserQuizAnswer)
class UserQuizAnswerAdmin(admin.ModelAdmin):
    list_display = ['session__user__email', 'question__question', 'selected_option', 'is_correct']
    list_filter = ['session__user__email', 'is_correct']
    search_fields = ['session__user__email', 'question__question']
    
    
