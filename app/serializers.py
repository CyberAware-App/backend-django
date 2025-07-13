from rest_framework import serializers
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth.password_validation import validate_password
from .models import *
from utils.response import ResponseMixin

User = get_user_model()

class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['email', 'password', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, value):
        """
        Validate the user profile data
        """
        if User.objects.filter(email=value['email']).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value

    def create(self, validated_data):
        """
        Create a new user profile
        """
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password']
        )
        user_profile = UserProfile.objects.create(
            user=user,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user_profile


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom serializer for JWT token authentication
    """
    def validate(self, attrs):
        """
        Validate the user credentials
        """
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        if not self.user.user_profile.is_verified:
            raise serializers.ValidationError("User is not verified.")
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['email'] = self.user.email
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom serializer for JWT token refresh
    """
    def validate(self, attrs):
        """
        Validate the token refresh data
        """
        token = super().validate(attrs)
        return token
    
    
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(max_length=128)
    
    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)
    
    
class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'name', 'description', 'content']


class UserModuleProgressSerializer(serializers.ModelSerializer):
    module = ModuleSerializer()
    class Meta:
        model = UserModuleProgress
        fields = ['module', 'completed']


class ModuleQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleQuiz
        fields = ['id', 'module', 'question', 'options', 'correct_answer']


class DashboardSerializer(serializers.Serializer):
    modules = ModuleSerializer(many=True)
    completed_modules = serializers.IntegerField()
    total_modules = serializers.IntegerField()
    
    
class MarkModuleAsCompletedSerializer(serializers.Serializer):
    module = ModuleSerializer()
    completed = serializers.BooleanField()
    
    
    