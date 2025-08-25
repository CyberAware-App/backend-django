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

    def validate(self, attrs):
        """
        Validate the user profile data
        """
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                'email': "User with this email already exists"
            })
        return attrs

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
            raise serializers.ValidationError({
                'email': "User is not verified."
            })
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


class VerifyOTPResponseSerializer(serializers.Serializer):
    """Serializer for OTP verification response with authentication tokens"""
    email = serializers.EmailField()
    first_name = serializers.CharField()
    verified = serializers.BooleanField()
    access = serializers.CharField()
    refresh = serializers.CharField()
    first_login = serializers.BooleanField()
    
    
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
    mux_playback_url = serializers.SerializerMethodField()
    mux_playback = serializers.SerializerMethodField()
    class Meta:
        model = Module
        fields = ['id', 'name', 'description', 'module_type', 'mux_playback_url', 'mux_playback']
        
    def get_mux_playback_url(self, obj):
        return obj.mux_playback_url
    
    def get_mux_playback(self, obj):
        return obj.mux_playback

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
    
    
class FinalQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalQuiz
        fields = ['question', 'options']


class FinalQuizSubmissionSerializer(serializers.Serializer):
    question = serializers.CharField()
    selected_option = serializers.CharField()


class FinalQuizResultSerializer(serializers.Serializer):
    score = serializers.CharField()
    passed = serializers.BooleanField()
    correct_answers = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    attempt_number = serializers.IntegerField()


class CertificateSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()
    certificate_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Certificate
        fields = [
            'certificate_id', 'user_name', 'user_email', 'issued_date', 
            'score', 'is_valid', 'certificate_url'
        ]
        read_only_fields = ['certificate_id', 'issued_date', 'is_valid']
    
    def get_user_name(self, obj):
        return f"{obj.user.user_profile.first_name} {obj.user.user_profile.last_name}"
    
    def get_user_email(self, obj):
        return obj.user.email
    
    def get_certificate_url(self, obj):
        # Generate certificate download URL
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(
                f'/api/certificate/{obj.certificate_id}/download'
            )
        return None


class GenerateCertificateSerializer(serializers.Serializer):
    """Serializer for generating a new certificate"""
    pass  # No input fields needed, uses authenticated user