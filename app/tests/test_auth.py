#!/usr/bin/env python3
"""
Test file for Django authentication endpoints
Tests all authentication functionality including registration, verification, login, and password management
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from app.models import OTP, UserProfile
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    """Test class for Django authentication endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client and data before each test"""
        self.client = APIClient()
        self.test_user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        self.test_user_data2 = {
            "email": "test2@example.com",
            "password": "testpassword456",
            "first_name": "Test2",
            "last_name": "User2"
        }
    
    def test_register_success(self):
        """Test successful user registration"""
        response = self.client.post(reverse('register'), self.test_user_data, format='json')        

        # Handle both success (201) and email failure (202) cases
        assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_202_ACCEPTED]
        data = response.data
        assert data["status"] == "success"
        assert "successful" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert data["data"]["first_name"] == self.test_user_data["first_name"]
        assert data["data"]["last_name"] == self.test_user_data["last_name"]
        assert "otp_sent" in data["data"]
        
        # Verify user was created in database
        user = User.objects.get(email=self.test_user_data["email"])
        assert user.email == self.test_user_data["email"]
        assert user.user_profile.first_name == self.test_user_data["first_name"]
        assert user.user_profile.last_name == self.test_user_data["last_name"]
        assert user.user_profile.is_verified is False
        
        # Verify OTP was created
        otp = OTP.objects.filter(user=user, is_used=False).first()
        assert otp is not None
        assert len(otp.code) == 6
    
    def test_register_duplicate_email(self):
        """Test registration with duplicate email"""
        # Register first user
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        # Try to register with same email
        response = self.client.post(reverse('register'), self.test_user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Registration failed" in data["message"]
        # Check for email error in errors
        assert "email" in data["errors"] or "general" in data["errors"]
    
    def test_register_invalid_data(self):
        """Test registration with invalid data"""
        invalid_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "first_name": "",
            "last_name": ""
        }
        response = self.client.post(reverse('register'), invalid_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Registration failed" in data["message"]
        # Check for field errors
        assert any(field in data["errors"] for field in ["email", "password", "first_name", "last_name", "general"])
    
    def test_verify_otp_success(self):
        """Test successful OTP verification with auto-login"""
        # Register user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        # Get the OTP from database
        user = User.objects.get(email=self.test_user_data["email"])
        otp = OTP.objects.filter(user=user, is_used=False).first()
        
        verify_data = {
            "email": self.test_user_data["email"],
            "code": otp.code
        }
        response = self.client.post(reverse('verify-otp'), verify_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "You are now logged in" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert data["data"]["verified"] is True
        assert "access" in data["data"]
        assert "refresh" in data["data"]
        assert "first_login" in data["data"]
        
        # Verify user is now verified in database
        user.refresh_from_db()
        assert user.user_profile.is_verified is True
        
        # Verify OTP is marked as used
        otp.refresh_from_db()
        assert otp.is_used is True
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code"""
        # Register user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        verify_data = {
            "email": self.test_user_data["email"],
            "code": "000000"
        }
        response = self.client.post(reverse('verify-otp'), verify_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Invalid, expired, or already used OTP" in data["message"]
    
    def test_verify_otp_user_not_found(self):
        """Test OTP verification for non-existent user"""
        verify_data = {
            "email": "nonexistent@example.com",
            "code": "123456"
        }
        response = self.client.post(reverse('verify-otp'), verify_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "User not found" in data["message"]
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired OTP"""
        # Register user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        # Get the OTP and make it expired
        user = User.objects.get(email=self.test_user_data["email"])
        otp = OTP.objects.filter(user=user, is_used=False).first()
        otp.expires_at = timezone.now() - timedelta(minutes=1)
        otp.save()
        
        verify_data = {
            "email": self.test_user_data["email"],
            "code": otp.code
        }
        response = self.client.post(reverse('verify-otp'), verify_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Invalid, expired, or already used OTP" in data["message"]
    
    def test_resend_otp_success(self):
        """Test successful OTP resend"""
        # Register user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        resend_data = {"email": self.test_user_data["email"]}
        response = self.client.post(reverse('resend-otp'), resend_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        # Handle both email success and failure cases
        assert "OTP" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert "otp_resent" in data["data"]
        
        # Verify new OTP was created
        user = User.objects.get(email=self.test_user_data["email"])
        otps = OTP.objects.filter(user=user, is_used=False)
        assert otps.count() >= 1
    
    def test_resend_otp_user_not_found(self):
        """Test OTP resend for non-existent user"""
        resend_data = {"email": "nonexistent@example.com"}
        response = self.client.post(reverse('resend-otp'), resend_data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.data
        assert data["status"] == "error"
        assert "User not found" in data["message"]
    
    def test_login_success(self):
        """Test successful login"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        response = self.client.post(reverse('login'), login_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "Login successful" in data["message"]
        assert "access" in data["data"]
        assert "refresh" in data["data"]
        assert data["data"]["email"] == self.test_user_data["email"]
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        login_data = {
            "email": "wrong@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(reverse('login'), login_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        if hasattr(response, 'data') and isinstance(response.data, dict):
            if 'status' in response.data:
                assert response.data["status"] == "error"
                assert "Login failed" in response.data["message"]
            else:
                # DRF default error response
                assert "detail" in response.data or "non_field_errors" in response.data
    
    def test_login_unverified_user(self):
        """Test login with unverified user"""
        # Register user but don't verify
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        response = self.client.post(reverse('login'), login_data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        if hasattr(response, 'data') and isinstance(response.data, dict):
            if 'status' in response.data:
                assert response.data["status"] == "error"
                assert "Login failed" in response.data["message"]
            else:
                pass
    
    def test_forgot_password_success(self):
        """Test successful forgot password request"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
    
        forgot_data = {"email": self.test_user_data["email"]}
        response = self.client.post(reverse('forgot-password'), forgot_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        # Handle both email success and failure cases
        assert "OTP" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert "otp_sent" in data["data"]
        
        # Verify OTP was created
        otp = OTP.objects.filter(user=user, is_used=False).first()
        assert otp is not None
    
    def test_forgot_password_unverified_user(self):
        """Test forgot password for unverified user"""
        # Register user but don't verify
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        forgot_data = {"email": self.test_user_data["email"]}
        response = self.client.post(reverse('forgot-password'), forgot_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "User is not verified" in data["message"]
    
    def test_forgot_password_user_not_found(self):
        """Test forgot password for non-existent user"""
        forgot_data = {"email": "nonexistent@example.com"}
        response = self.client.post(reverse('forgot-password'), forgot_data, format='json')
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.data
        assert data["status"] == "error"
        assert "User not found" in data["message"]
    
    def test_reset_password_success(self):
        """Test successful password reset"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        # Send forgot password OTP
        self.client.post(reverse('forgot-password'), {"email": self.test_user_data["email"]}, format='json')
        
        # Get the OTP
        otp = OTP.objects.filter(user=user, is_used=False).first()
        
        reset_data = {
            "email": self.test_user_data["email"],
            "code": otp.code,
            "new_password": "newpassword123"
        }
        response = self.client.post(reverse('reset-password'), reset_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "Password reset successfully" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert data["data"]["password_reset"] is True
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password("newpassword123")
        
        # Verify OTP is marked as used
        otp.refresh_from_db()
        assert otp.is_used is True
    
    def test_reset_password_invalid_otp(self):
        """Test password reset with invalid OTP"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        reset_data = {
            "email": self.test_user_data["email"],
            "code": "000000",
            "new_password": "newpassword123"
        }
        response = self.client.post(reverse('reset-password'), reset_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Invalid, expired, or already used OTP" in data["message"]
    
    def test_reset_password_unverified_user(self):
        """Test password reset for unverified user"""
        # Register user but don't verify
        self.client.post(reverse('register'), self.test_user_data, format='json')
        
        reset_data = {
            "email": self.test_user_data["email"],
            "code": "123456",
            "new_password": "newpassword123"
        }
        response = self.client.post(reverse('reset-password'), reset_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "User is not verified" in data["message"]
    
    def test_change_password_success(self):
        """Test successful password change for authenticated user"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        # Login to get token
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        login_response = self.client.post(reverse('login'), login_data, format='json')
        access_token = login_response.data["data"]["access"]
        
        # Change password
        change_data = {
            "old_password": self.test_user_data["password"],
            "new_password": "newpassword123"
        }
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(reverse('change-password'), change_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "Password changed successfully" in data["message"]
        assert data["data"]["email"] == self.test_user_data["email"]
        assert data["data"]["password_changed"] is True
        
        # Verify password was changed
        user.refresh_from_db()
        assert user.check_password("newpassword123")
    
    def test_change_password_wrong_current_password(self):
        """Test change password with wrong current password"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        # Login to get token
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        login_response = self.client.post(reverse('login'), login_data, format='json')
        token = login_response.data["data"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        change_data = {
            "old_password": "wrongpassword",
            "new_password": "newpassword123"
        }
        response = self.client.post(reverse('change-password'), change_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.data
        assert data["status"] == "error"
        assert "Old password is incorrect" in data["message"]
    
    def test_change_password_unauthorized(self):
        """Test change password without authentication"""
        change_data = {
            "old_password": "testpassword123",
            "new_password": "newpassword123"
        }
        response = self.client.post(reverse('change-password'), change_data, format='json')
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        data = response.data
        # Check for general error or DRF default error
        assert "general" in data.get("errors", {}) or "detail" in data or data.get("errors") is None
    
    def test_token_refresh_success(self):
        """Test successful token refresh"""
        # Register and verify user first
        self.client.post(reverse('register'), self.test_user_data, format='json')
        user = User.objects.get(email=self.test_user_data["email"])
        user.user_profile.is_verified = True
        user.user_profile.save()
        
        # Login to get tokens
        login_data = {
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        }
        login_response = self.client.post(reverse('login'), login_data, format='json')
        refresh_token = login_response.data["data"]["refresh"]
        
        # Refresh token
        refresh_data = {"refresh": refresh_token}
        response = self.client.post(reverse('token-refresh'), refresh_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["status"] == "success"
        assert "Token refreshed successfully" in data["message"]
        assert "access" in data["data"]
    
    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        refresh_data = {"refresh": "invalidtoken"}
        response = self.client.post(reverse('token-refresh'), refresh_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.data
       


def run_auth_tests():
    """Run all authentication tests"""
    print("🧪 Running Django Authentication Tests...")
    print("=" * 60)
    
    # Test cases to run
    test_cases = [
        ("User Registration", [
            "test_register_success",
            "test_register_duplicate_email",
            "test_register_invalid_data"
        ]),
        ("OTP Verification", [
            "test_verify_otp_success",
            "test_verify_otp_invalid_code",
            "test_verify_otp_user_not_found",
            "test_verify_otp_expired"
        ]),
        ("OTP Resend", [
            "test_resend_otp_success",
            "test_resend_otp_user_not_found"
        ]),
        ("User Login", [
            "test_login_success",
            "test_login_invalid_credentials",
            "test_login_unverified_user"
        ]),
        ("Password Management", [
            "test_forgot_password_success",
            "test_forgot_password_unverified_user",
            "test_forgot_password_user_not_found",
            "test_reset_password_success",
            "test_reset_password_invalid_otp",
            "test_reset_password_unverified_user",
            "test_change_password_success",
            "test_change_password_wrong_current_password",
            "test_change_password_unauthorized"
        ]),
        ("Token Management", [
            "test_token_refresh_success",
            "test_token_refresh_invalid_token"
        ])
    ]
    
    passed = 0
    failed = 0
    
    for category, methods in test_cases:
        print(f"\n📋 Testing {category}:")
        print("-" * 40)
        
        for method_name in methods:
            try:
                print(f"  Testing {method_name}...", end=" ")
                test_instance = TestAuthEndpoints()
                test_instance.setup()
                getattr(test_instance, method_name)()
                print("✅ PASSED")
                passed += 1
            except Exception as e:
                print(f"❌ FAILED: {str(e)}")
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All authentication tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return failed == 0


if __name__ == "__main__":
    success = run_auth_tests()
    exit(0 if success else 1) 