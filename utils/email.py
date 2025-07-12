import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import random
from django.utils import timezone
from datetime import timedelta
from app.models import OTP
from dotenv import load_dotenv
from django.contrib.auth import get_user_model

load_dotenv()
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
MAIL_FROM = os.getenv('MAIL_FROM')


def send_otp(user):
    otp_code = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=10)
    otp_obj = OTP.objects.create(user=user, code=otp_code, expires_at=expires_at)
    email_sent = send_otp_email(user.email, otp_code)
    return email_sent, otp_obj


def send_reset_password_otp(user):
    otp_code = str(random.randint(100000, 999999))
    expires_at = timezone.now() + timedelta(minutes=10)
    otp_obj = OTP.objects.create(user=user, code=otp_code, expires_at=expires_at)
    email_sent = send_reset_password_email(user.email, otp_code)
    return email_sent, otp_obj


def send_otp_email(to_email, otp_code):
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=to_email,
        subject="Email Verification - CyberAware",
        html_content=f"""
        <html>
            <body>
                <h2>Email Verification</h2>
                <p>Your verification code is: <strong>{otp_code}</strong></p>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this verification, please ignore this email.</p>
            </body>
        </html>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False 
    

def send_reset_password_email(to_email, otp_code):
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=to_email,
        subject="Reset Password - CyberAware",
        html_content=f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>You requested to reset your password.</p>
                <p>Your password reset code is: <strong>{otp_code}</strong></p>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request this password reset, please ignore this email and your password will remain unchanged.</p>
                <p><strong>Security Note:</strong> Never share this code with anyone.</p>
            </body>
        </html>
        """
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False 
    

def validate_otp(email, code=None, require_verified=True):
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None, None, "User not found."

    if require_verified and (not hasattr(user, "user_profile") or not user.user_profile.is_verified):
        return user, None, "User is not verified."

    if code is not None:
        otp_obj = OTP.objects.filter(user=user, code=code, is_used=False).order_by('-expires_at').first()
        if not otp_obj or not otp_obj.is_valid():
            return user, None, "Invalid, expired, or already used OTP."
        return user, otp_obj, None

    return user, None, None