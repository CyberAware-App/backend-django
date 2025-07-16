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
from django.http import Http404, HttpResponse
from utils.certificate_generator import CertificateGenerator

User = get_user_model()

@extend_schema_view(
    post=extend_schema(
        summary="User Registration",
        description="Register a new user",
        request=UserProfileSerializer,
        responses={201: UserProfileSerializer}, 
        tags = ['Register']
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
            return self.error_response(
                self.format_serializer_errors(serializer.errors),
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
        responses={200: CustomTokenObtainPairSerializer},
        tags = ['Login']
    )
)
class CustomTokenObtainPairView(TokenObtainPairView, ResponseMixin):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    self.format_serializer_errors(serializer.errors),
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
                self.format_serializer_errors(serializer.errors),
                message=str(e),
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return self.error_response(
                str(e),
                message="Login failed",
                status_code=status.HTTP_401_UNAUTHORIZED
            )
        
        
@extend_schema_view(
    post=extend_schema(
        summary="Token Refresh",
        description="Refresh a JWT token",
        request=CustomTokenRefreshSerializer,
        responses={200: CustomTokenRefreshSerializer},
        tags = ['Token Refresh']
    )
)
class CustomTokenRefreshView(TokenRefreshView, ResponseMixin):
    serializer_class = CustomTokenRefreshSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return self.error_response(
                    self.format_serializer_errors(serializer.errors),
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
        description="Verify a user's OTP and automatically log them in",
        request=VerifyOTPSerializer,
        responses={200: VerifyOTPResponseSerializer},
        tags = ['OTP']
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
                self.format_serializer_errors(serializer.errors),
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
        
        # Auto-login after successful verification
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Check if this is the user's first login
        first_login = user_profile.first_login
        if first_login:
            user_profile.first_login = False
            user_profile.save()
        
        return self.success_response(
            {
                "email": email, 
                "first_name": user_profile.first_name, 
                "verified": True,
                "access": access_token,
                "refresh": refresh_token,
                "first_login": first_login
            },
            message="OTP verified successfully. You are now logged in!",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    post=extend_schema(
        summary="Resend OTP",
        description="Resend an OTP to a user",
        request=ResendOTPSerializer,
        responses={200: ResendOTPSerializer},
        tags = ['OTP']
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
                self.format_serializer_errors(serializer.errors),
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
        responses={200: ForgotPasswordSerializer},
        tags = ['Password']
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
                self.format_serializer_errors(serializer.errors),
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
        responses={200: ResetPasswordSerializer},
        tags = ['Password']
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
                self.format_serializer_errors(serializer.errors),
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
        responses={200: ChangePasswordSerializer},
        tags = ['Password']
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
                self.format_serializer_errors(serializer.errors),
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
        responses={200: DashboardSerializer},
        tags = ['Dashboard']
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
        percentage_completed = (completed_modules / total_modules) * 100 if total_modules > 0 else 0
        return self.success_response(
            {
                "modules": ModuleSerializer(modules, many=True).data,
                "completed_modules": completed_modules,
                "total_modules": total_modules,
                "percentage_completed": percentage_completed
            },
            message="Dashboard data fetched successfully.",
            status_code=status.HTTP_200_OK
        )
        

@extend_schema_view(
    get=extend_schema(
        summary="Get Module",
        description="Get a module",
        responses={200: ModuleSerializer},
        tags = ['Module']
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
        responses={200: MarkModuleAsCompletedSerializer},
        tags = ['Module']
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
        responses={200: UserModuleProgressSerializer},
        tags = ['Module']
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
        responses={200: ModuleQuizSerializer},
        tags = ['Module']
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
        

@extend_schema_view(
    get=extend_schema(
        summary="Get Final Quiz",
        description="Get final quiz questions",
        responses={200: FinalQuizSerializer}
    ),
    post=extend_schema(
        summary="Submit Final Quiz",
        description="Submit final quiz answers and get results",
        request=FinalQuizSubmissionSerializer,
        responses={200: FinalQuizResultSerializer}
    )
)
class FinalQuizView(APIView, ResponseMixin):
    """
    Final Quiz View - Optimized for performance
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get Final Quiz Questions
        Args:
            request: The request object
        Returns:
            Response: The response object
        """
        try:
            quiz_session = QuizSession.objects.get(user=request.user)
            if quiz_session.attempt_number >= 5:
                return self.error_response(
                    None,
                    message="You have reached the maximum number of attempts (5).",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except QuizSession.DoesNotExist:
            pass
        final_quiz = FinalQuiz.objects.all().order_by('id')
        serializer = FinalQuizSerializer(final_quiz, many=True)
        
        return self.success_response(
            serializer.data,
            message="Final quiz fetched successfully.",
            status_code=status.HTTP_200_OK
        )
    
    
    def post(self, request, *args, **kwargs):
        """
        Submit Final Quiz Answers
        Args:
            request: The request object with quiz answers
        Returns:
            Response: The response object with score and result
        """
        user = request.user
        answers_data = request.data
        if not answers_data:
            return self.error_response(
                None,
                message="No answers provided.",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        try:
            quiz_session, created = QuizSession.objects.get_or_create(
                user=user,
                defaults={'attempt_number': 1, 'passed': False}
            )
            if not created:
                quiz_session.attempt_number += 1
                quiz_session.save(update_fields=['attempt_number'])
            
            correct_answers_dict = {
                quiz.question: quiz.correct_answer 
                for quiz in FinalQuiz.objects.all()
            }
            correct_count = 0
            user_answers_to_create = []
            
            for data in answers_data:
                question_text = data.get('question')
                selected_option = data.get('selected_option')
                
                # Find the FinalQuiz object by question text
                try:
                    final_quiz_obj = FinalQuiz.objects.get(question=question_text)
                    is_correct = final_quiz_obj.correct_answer == selected_option
                    if is_correct:
                        correct_count += 1
                        
                    user_answers_to_create.append(
                        UserQuizAnswer(
                            session=quiz_session,
                            question=final_quiz_obj,
                            selected_option=selected_option,
                            is_correct=is_correct
                        )
                    )
                except FinalQuiz.DoesNotExist:
                    # Skip questions that don't exist in the database
                    continue
            
            if user_answers_to_create:
                UserQuizAnswer.objects.bulk_create(user_answers_to_create)
            
            total_questions = len(answers_data)
            score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            passed = score >= 80
            quiz_session.passed = passed
            quiz_session.save(update_fields=['passed'])
            
            # Auto-generate certificate if passed
            certificate_data = None
            if passed:
                try:
                    if not Certificate.objects.filter(user=user, is_valid=True).exists():
                        certificate = Certificate.objects.create(
                            user=user,
                            quiz_session=quiz_session,
                            score=score
                        )
                        certificate_data = CertificateSerializer(certificate, context={'request': request}).data
                except Exception as e:
                    print(f"Certificate generation failed: {e}")
            
            response_data = {
                "score": f"{score:.1f}%",
                "passed": passed,
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "attempt_number": quiz_session.attempt_number
            }
            
            if certificate_data:
                response_data["certificate"] = certificate_data
            
            return self.success_response(
                response_data,
                message="Final Exam submitted successfully." + (" Certificate generated!" if passed else ""),
                status_code=status.HTTP_200_OK
            )
        except Exception as e:
            return self.error_response(
                None,
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )


@extend_schema_view(
    get=extend_schema(
        summary="Get User Certificate",
        description="Get the current user's certificate if they have passed the final quiz",
        responses={200: CertificateSerializer, 404: "Certificate not found"},
        tags=['Certificate']
    )
)
class CertificateView(APIView, ResponseMixin):
    """
    Certificate View - Retrieve user certificates (auto-generated when quiz passed)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Get user's certificate
        Args:
            request: The request object
        Returns:
            Response: The response object with certificate data
        """
        try:
            certificate = Certificate.objects.get(user=request.user, is_valid=True)
            serializer = CertificateSerializer(certificate, context={'request': request})
            return self.success_response(
                serializer.data,
                message="Certificate retrieved successfully.",
                status_code=status.HTTP_200_OK
            )
        except Certificate.DoesNotExist:
            return self.error_response(
                None,
                message="Certificate not found. You may not have passed the final quiz yet.",
                status_code=status.HTTP_404_NOT_FOUND
            )


@extend_schema_view(
    get=extend_schema(
        summary="Download Certificate",
        description="Download certificate as PDF",
        responses={200: "PDF file", 404: "Certificate not found"},
        tags=['Certificate']
    )
)
class CertificateDownloadView(APIView):
    """
    Certificate Download View - Returns actual PDF file
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Download certificate as PDF
        Args:
            request: The request object
        Returns:
            HttpResponse: PDF file response
        """
        certificate_id = kwargs.get('certificate_id')
        
        try:
            certificate = Certificate.objects.get(
                certificate_id=certificate_id,
                user=request.user,
                is_valid=True
            )
        except Certificate.DoesNotExist:
            return HttpResponse(
                "Certificate not found or invalid.",
                status=404,
                content_type='text/plain'
            )
        
        try:
            generator = CertificateGenerator()
            certificate_data = {
                'user_name': f"{certificate.user.user_profile.first_name} {certificate.user.user_profile.last_name}",
                'user_email': certificate.user.email,
                'score': f"{certificate.score}",
                'issued_date': certificate.issued_date.strftime('%B %d, %Y'),
                'certificate_id': certificate.certificate_id
            }
            
            pdf_content = generator.generate_certificate_pdf(certificate_data)
            response = HttpResponse(
                pdf_content,
                content_type='application/pdf'
            )
            response['Content-Disposition'] = f'attachment; filename="certificate_{certificate_id}.pdf"'
            return response
            
        except Exception as e:
            return HttpResponse(
                f"Error generating certificate: {str(e)}",
                status=500,
                content_type='text/plain'
            )
            
        