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
    path('schema', SpectacularAPIView.as_view(), name='schema'),
    path('swagger', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
