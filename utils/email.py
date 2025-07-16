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


def render_email_template(title, message, code=None, note=None):
    primary_color = "hsl(238, 80%, 8%)"
    accent_color = "hsl(27, 100%, 56%)"
    code_html = f'<p style="font-size: 1.5em; color: {accent_color}; font-weight: bold; letter-spacing: 2px; margin: 16px 0;">{code}</p>' if code else ''
    note_html = f'<p style="color: #888; font-size: 0.95em; margin-top: 20px;">{note}</p>' if note else ''
    return f'''
    <html>
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
      </head>
      <body style="background: #f7f7fa; margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: #f7f7fa; padding: 40px 0;">
          <tr>
            <td align="center">
              <table width="100%" style="max-width: 480px; background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.07); padding: 32px 24px;">
                <tr>
                  <td align="center">
                    <h2 style="color: {primary_color}; margin-bottom: 8px; font-size: 1.6em;">{title}</h2>
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <p style="color: #222; font-size: 1.08em; margin-bottom: 12px;">{message}</p>
                    {code_html}
                    {note_html}
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 24px;">
                    <p style="color: #aaa; font-size: 0.9em;">CyberAware &copy; {timezone.now().year}</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    '''


def send_otp_email(to_email, otp_code):
    html_content = render_email_template(
        title="Email Verification",
        message="Your verification code is:",
        code=otp_code,
        note="This code will expire in 10 minutes. If you didn't request this verification, please ignore this email."
    )
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=to_email,
        subject="Email Verification - CyberAware",
        html_content=html_content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return response.status_code == 202
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False 
    

def send_reset_password_email(to_email, otp_code):
    html_content = render_email_template(
        title="Password Reset Request",
        message="You requested to reset your password. Your password reset code is:",
        code=otp_code,
        note="This code will expire in 10 minutes. If you didn't request this password reset, please ignore this email and your password will remain unchanged. <br><strong>Security Note:</strong> Never share this code with anyone."
    )
    message = Mail(
        from_email=MAIL_FROM,
        to_emails=to_email,
        subject="Reset Password - CyberAware",
        html_content=html_content
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