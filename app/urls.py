from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import *


urlpatterns = [
    path('register', UserRegistrationView.as_view(), name='register'),
    path('login', CustomTokenObtainPairView.as_view(), name='login'),
    path('token-refresh', CustomTokenRefreshView.as_view(), name='token-refresh'),
    path('verify-otp', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp', ResendOTPView.as_view(), name='resend-otp'),
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('module-progress', UserModuleProgressView.as_view(), name='module-progress'),
    path('module/<int:module_id>', GetModuleView.as_view(), name='get-module'),
    path('module/<int:module_id>/complete', MarkModuleAsCompletedView.as_view(), name='mark-module-as-completed'),
    path('module/<int:module_id>/quiz', GetModuleQuizView.as_view(), name='get-module-quiz'),
    path('quiz', FinalQuizView.as_view(), name='final-quiz'),
    path('certificate', CertificateView.as_view(), name='certificate'),
    path('certificate/<str:certificate_id>/download', CertificateDownloadView.as_view(), name='certificate-download'),
    path('session', CheckUserSessionView.as_view(), name='check-user-session'),
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('swagger', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("webhooks/mux", mux_webhook, name="mux-webhook"),
]
