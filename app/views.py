from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status, permissions, serializers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes, OpenApiResponse, OpenApiExample
from .models import *
from .serializers import *
from utils.response import ResponseMixin
from django.contrib.auth import get_user_model
from utils.email import send_otp, send_reset_password_otp, validate_otp
from rest_framework.views import APIView
from django.http import Http404

User = get_user_model()

@extend_schema_view(
    post=extend_schema(
        summary="User Registration",
        description="Register a new user",
        request=UserProfileSerializer,
        responses={201: UserProfileSerializer}
    )
)
class UserRegistrationView(generics.GenericAPIView, ResponseMixin):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """
        Register a new user
        Args:
            request: The request object
        Returns:
            Response: The response object
        Raises:
            ValidationError: If the request data is invalid
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            error_message = serializer.errors
            return self.error_response(
                error_message,
                message="Registration failed",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user_profile = serializer.save()
        user = user_profile.user
        email_sent, otp_obj = send_otp(user)
        if not email_sent:
            return self.success_response(
                {"email": user.email, "first_name": user_profile.first_name, "last_name": user_profile.last_name, "otp_sent": False},
                message="Registration successful, but failed to send OTP.",
                status_code=status.HTTP_202_ACCEPTED
            )
        return self.success_response(
            {"email": user.email, "first_name": user_profile.first_name, "last_name": user_profile.last_name, "otp_sent": True},
            message="User registered successfully. OTP sent to email.",
            status_code=status.HTTP_201_CREATED
        )
        
        
@extend_schema_view(
    post=extend_schema(
        summary="User Login",
        description="Login a user",
        request=CustomTokenObtainPairSerializer,
        responses={200: CustomTokenObtainPairSerializer}
    )
)
class CustomTokenObtainPairView(TokenObtainPairView, ResponseMixin):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    serializer.errors,
                    message="Login failed",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            data = serializer.validated_data
            user = serializer.user
            first_login = user.user_profile.first_login
            if first_login:
                user.user_profile.first_login = False
                user.user_profile.save()
            data['first_login'] = first_login
            return self.success_response(
                data,
                message="Login successful",
                status_code=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            return self.error_response(
                None,
                message=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return self.error_response(
                None,
                message="Login failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        
@extend_schema_view(
    post=extend_schema(
        summary="Token Refresh",
        description="Refresh a JWT token",
        request=CustomTokenRefreshSerializer,
        responses={200: CustomTokenRefreshSerializer}
    )
)
class CustomTokenRefreshView(TokenRefreshView, ResponseMixin):
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    serializer.errors,
                    message="Token refresh failed",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
            data = serializer.validated_data
            return self.success_response(
                data,
                message="Token refreshed successfully",
                status_code=status.HTTP_200_OK
            )
        except serializers.ValidationError as e:
            return self.error_response(
                None,
                message=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return self.error_response(
                None,
                message="Token refresh failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
    

@extend_schema_view(
    post=extend_schema(
        summary="Verify OTP",
        description="Verify a user's OTP",
        request=VerifyOTPSerializer,
        responses={200: VerifyOTPSerializer}
    )
)
class VerifyOTPView(APIView, ResponseMixin):
    """
    Verify OTP view
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):
        """
        Verify OTP
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        user, otp_obj, error = validate_otp(email, code, require_verified=False)
        if error:
            return self.error_response(
                None,
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        otp_obj.is_used = True
        otp_obj.save()
        user_profile = UserProfile.objects.get(user=user)
        user_profile.is_verified = True
        user_profile.save()
        return self.success_response(
            {"email": email, "first_name": user_profile.first_name, "verified": True},
            message="OTP verified successfully.",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    post=extend_schema(
        summary="Resend OTP",
        description="Resend an OTP to a user",
        request=ResendOTPSerializer,
        responses={200: ResendOTPSerializer}
    )
)
class ResendOTPView(APIView, ResponseMixin):
    """
    Resend OTP view
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ResendOTPSerializer

    def post(self, request, *args, **kwargs):
        """
        Resend OTP
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return self.error_response(
                None,
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        email_sent, otp_obj = send_otp(user)
        if not email_sent:
            return self.success_response(
                {"email": user.email, "otp_resent": False},
                message="OTP created but failed to send email. Please try again later.",
                status_code=status.HTTP_200_OK
            )
        return self.success_response(
            {"email": user.email, "otp_resent": True},
            message="OTP resent successfully.",
            status_code=status.HTTP_200_OK
        )
    

@extend_schema_view(
    post=extend_schema(
        summary="Forgot Password",
        description="Forgot password",
        request=ForgotPasswordSerializer,
        responses={200: ForgotPasswordSerializer}
    )
)
class ForgotPasswordView(APIView, ResponseMixin):
    """
    Forgot password view
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ForgotPasswordSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Forgot password
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return self.error_response(
                None,
                message="User not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        if not user.user_profile.is_verified:
            return self.error_response(
                None,
                message="User is not verified.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        email_sent, otp_obj = send_reset_password_otp(user)
        if not email_sent:
            return self.success_response(
                {"email": user.email, "otp_sent": False},
                message="OTP created but failed to send email. Please try again later.",
                status_code=status.HTTP_200_OK
            )
        return self.success_response(
            {"email": user.email, "otp_sent": True},
            message="OTP sent to email.",
            status_code=status.HTTP_200_OK
        )
        
        
@extend_schema_view(
    post=extend_schema(
        summary="Reset Password",
        description="Reset password",
        request=ResetPasswordSerializer,
        responses={200: ResetPasswordSerializer}
    )
)
class ResetPasswordView(APIView, ResponseMixin):
    """
    Reset password view
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Reset password
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']
        user, otp_obj, error = validate_otp(email, code, require_verified=True)
        if error:
            return self.error_response(
                None,
                message=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        otp_obj.is_used = True
        otp_obj.save()
        user.set_password(new_password)
        user.save()
        return self.success_response(
            {"email": user.email, "password_reset": True},
            message="Password reset successfully.",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    post=extend_schema(
        summary="Change Password",
        description="Change password",
        request=ChangePasswordSerializer,
        responses={200: ChangePasswordSerializer}
    )
)
class ChangePasswordView(APIView, ResponseMixin):
    """
    Change password view
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Change password
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return self.error_response(
                serializer.errors,
                message="Invalid data",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        user = request.user
        if not user.check_password(old_password):
            return self.error_response(
                None,
                message="Old password is incorrect.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return self.success_response(
            {"email": user.email, "password_changed": True},
            message="Password changed successfully.",
            status_code=status.HTTP_200_OK
        )
        
@extend_schema_view(
    get=extend_schema(
        summary="Dashboard",
        description="Get dashboard data",
        responses={200: DashboardSerializer}
    )
)
class DashboardView(APIView, ResponseMixin):
    """
    Dashboard View
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Dashboard View
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        user = request.user
        modules = Module.objects.all().order_by('id')
        try:
            user_progress = UserModuleProgress.objects.filter(user=user)
            completed_modules = user_progress.filter(completed=True).count()
        except UserModuleProgress.DoesNotExist:
            completed_modules = 0
        total_modules = modules.count()
        return self.success_response(
            {
                "modules": ModuleSerializer(modules, many=True).data,
                "completed_modules": completed_modules,
                "total_modules": total_modules
            },
            message="Dashboard data fetched successfully.",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    get=extend_schema(
        summary="Get Module",
        description="Get a module",
        responses={200: ModuleSerializer}
    )
)
class GetModuleView(APIView, ResponseMixin):
    """
    Get Module View
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get Module View
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        module_id = kwargs.get('module_id')
        try:
            module = get_object_or_404(Module, id=module_id)
        except Http404:
            return self.error_response(
                None,
                message="Module not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return self.success_response(
            {"module": ModuleSerializer(module).data},
            message="Module fetched successfully.",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    post=extend_schema(
        summary="Mark Module As Completed",
        description="Mark a module as completed",
        responses={200: MarkModuleAsCompletedSerializer}
    )
)
class MarkModuleAsCompletedView(APIView, ResponseMixin):
    """
    Mark Module As Completed View
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """
        Mark Module As Completed View
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        module_id = kwargs.get('module_id')
        try:
            module = get_object_or_404(Module, id=module_id)
        except Http404:
            return self.error_response(
                None,
                message="Module not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        user = request.user
        user_progress, created = UserModuleProgress.objects.get_or_create(user=user, module=module)
        user_progress.completed = True
        user_progress.save()
        return self.success_response(
            {"module": ModuleSerializer(module).data, "completed": True},
            message="Module marked as completed.",
            status_code=status.HTTP_200_OK
        )
        
@extend_schema_view(
    get=extend_schema(
        summary="User Module Progress",
        description="Get user module progress",
        responses={200: UserModuleProgressSerializer}
    )
)
class UserModuleProgressView(APIView, ResponseMixin):
    """
    User Module Progress View
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        User Module Progress View
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        user = request.user
        try:
            user_progress = UserModuleProgress.objects.filter(user=user).select_related('module')
            serializer = UserModuleProgressSerializer(user_progress, many=True)
        except UserModuleProgress.DoesNotExist:
            return self.error_response(
                None,
                message="User module progress not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        return self.success_response(
            serializer.data,
            message="User module progress fetched successfully.",
            status_code=status.HTTP_200_OK
        )
        
        
@extend_schema_view(
    get=extend_schema(
        summary="Get Module Quiz",
        description="Get a module quiz",
        responses={200: ModuleQuizSerializer}
    )
)
class GetModuleQuizView(APIView, ResponseMixin):
    """
    Get Module Quiz View
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get Module Quiz View
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        module_id = kwargs.get('module_id')
        try:
            module = get_object_or_404(Module, id=module_id)
        except Http404:
            return self.error_response(
                None,
                message="Module not found.",
                status_code=status.HTTP_404_NOT_FOUND
            )
        module_quiz = ModuleQuiz.objects.filter(module=module).order_by('id')
        serializer = ModuleQuizSerializer(module_quiz, many=True)
        return self.success_response(
            serializer.data,
            message="Module quiz fetched successfully.",
            status_code=status.HTTP_200_OK
        )
        
