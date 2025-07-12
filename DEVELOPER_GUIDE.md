# Developer Guide - Django REST Framework Authentication Backend

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Response Structure](#response-structure)
4. [Authentication Flow](#authentication-flow)
5. [Email Integration](#email-integration)
6. [Testing Strategy](#testing-strategy)
7. [Development Setup](#development-setup)
8. [API Documentation](#api-documentation)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Project Overview

This is a Django REST Framework backend that provides comprehensive authentication features including:

- **User Registration** with email verification
- **JWT-based Authentication** with access and refresh tokens
- **OTP Verification** via email
- **Password Management** (forgot, reset, change)
- **Token Refresh** functionality

### Key Technologies
- Django 5.2.4
- Django REST Framework
- Simple JWT for token authentication
- SendGrid for email delivery
- Pytest for testing

## Architecture & Design Patterns

### Project Structure
```
backend-django/
├── app/                    # Main application
│   ├── models.py          # UserProfile and OTP models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   └── tests/             # Test suite
├── core/                  # Django settings
├── users/                 # Custom user model
├── utils/                 # Utility modules
│   ├── response.py        # ResponseMixin
│   └── email.py          # Email utilities
└── manage.py
```

### Design Patterns Used

1. **ResponseMixin Pattern**: Centralized response formatting
2. **Serializer-View Separation**: Clean separation of validation and response handling
3. **Exception Handling**: Graceful error handling with consistent responses
4. **OTP Pattern**: Time-based one-time passwords for verification

## Response Structure

### Unified Response Format

All API endpoints use a consistent response structure through the `ResponseMixin`:

#### Success Response
```json
{
    "status": "success",
    "message": "Operation completed successfully",
    "data": {
        // Response data here
    }
}
```

#### Error Response
```json
{
    "status": "error",
    "message": "Error description",
    "data": null
}
```

### ResponseMixin Usage

The `ResponseMixin` is used in all views to ensure consistent response formatting:

```python
from utils.response import ResponseMixin

class MyView(APIView, ResponseMixin):
    def post(self, request):
        # Success case
        return self.success_response(
            data={"key": "value"},
            message="Operation successful",
            status_code=status.HTTP_200_OK
        )
        
        # Error case
        return self.error_response(
            error_data=None,
            message="Something went wrong",
            status_code=status.HTTP_400_BAD_REQUEST
        )
```

## Authentication Flow

### 1. User Registration
```
POST /api/register
{
    "email": "user@example.com",
    "password": "securepassword",
    "first_name": "John",
    "last_name": "Doe"
}
```

**Flow:**
1. Validate user data
2. Create user and user profile
3. Generate OTP and send email
4. Return success response (201 or 202 if email fails)

### 2. Email Verification
```
POST /api/verify-otp
{
    "email": "user@example.com",
    "code": "123456"
}
```

**Flow:**
1. Validate OTP code
2. Mark user as verified
3. Mark OTP as used

### 3. User Login
```
POST /api/login
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

**Flow:**
1. Validate credentials
2. Check if user is verified
3. Generate JWT tokens
4. Return tokens with user info

### 4. Token Refresh
```
POST /api/token-refresh
{
    "refresh": "refresh_token_here"
}
```

**Flow:**
1. Validate refresh token
2. Generate new access token
3. Return new tokens

## Email Integration

### SendGrid Configuration

The project uses SendGrid for email delivery. Configure these environment variables:

```bash
SENDGRID_API_KEY=your_sendgrid_api_key
MAIL_FROM=your_verified_sender@domain.com
```

### Email Templates

Two email templates are used:

1. **OTP Verification Email** (`send_otp_email`)
2. **Password Reset Email** (`send_reset_password_email`)

### Email Error Handling

The system gracefully handles email failures:
- Registration: Returns 202 Accepted if email fails
- Resend OTP: Returns 200 OK with `otp_resent: false` if email fails
- Forgot Password: Returns 200 OK with `otp_sent: false` if email fails

## Testing Strategy

### Test Structure

Tests are organized in `app/tests/test_auth.py` with the following structure:

```python
@pytest.mark.django_db
class TestAuthEndpoints:
    @pytest.fixture(autouse=True)
    def setup(self):
        # Setup test data
        
    def test_register_success(self):
        # Test successful registration
        
    def test_register_duplicate_email(self):
        # Test duplicate email handling
```

### Test Categories

1. **User Registration Tests**
   - Successful registration
   - Duplicate email handling
   - Invalid data validation

2. **OTP Verification Tests**
   - Successful verification
   - Invalid code handling
   - Expired OTP handling

3. **Authentication Tests**
   - Successful login
   - Invalid credentials
   - Unverified user login

4. **Password Management Tests**
   - Forgot password
   - Reset password
   - Change password

5. **Token Management Tests**
   - Token refresh
   - Invalid token handling

### Running Tests

```bash
# Run all tests
pytest app/tests/test_auth.py -v

# Run specific test
pytest app/tests/test_auth.py::TestAuthEndpoints::test_register_success -v

# Run with coverage
pytest --cov=app app/tests/test_auth.py
```

## Development Setup

### Prerequisites
- Python 3.10+
- PostgreSQL (recommended) or SQLite
- SendGrid account

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd backend-django
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment setup**
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Database setup**
```bash
python manage.py migrate
```

6. **Run development server**
```bash
python manage.py runserver
```

### Environment Variables

Create a `.env` file with:

```env
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost/dbname
SENDGRID_API_KEY=your_sendgrid_api_key
MAIL_FROM=your_verified_sender@domain.com
```

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/register` | User registration | No |
| POST | `/verify-otp` | Email verification | No |
| POST | `/resend-otp` | Resend OTP | No |
| POST | `/login` | User login | No |
| POST | `/token-refresh` | Refresh JWT token | No |
| POST | `/forgot-password` | Request password reset | No |
| POST | `/reset-password` | Reset password with OTP | No |
| POST | `/change-password` | Change password | Yes |

### Authentication

Protected endpoints require JWT authentication:

```bash
Authorization: Bearer <access_token>
```

## Best Practices

### 1. Response Handling

Always use the `ResponseMixin` for consistent responses:

```python
# ✅ Good
return self.success_response(data, message="Success")

# ❌ Bad
return Response({"data": data})
```

### 2. Error Handling

Handle exceptions gracefully in views:

```python
try:
    # Your logic here
    return self.success_response(data)
except serializers.ValidationError as e:
    return self.error_response(message=str(e))
except Exception as e:
    return self.error_response(message="Internal error")
```

### 3. Email Error Handling

Always handle email failures gracefully:

```python
email_sent, otp_obj = send_otp(user)
if not email_sent:
    # Return success with flag indicating email failure
    return self.success_response(
        data={"otp_sent": False},
        message="OTP created but email failed"
    )
```

### 4. Testing

- Write tests for both success and failure scenarios
- Test email failures gracefully
- Use descriptive test names
- Test database state after operations

### 5. Security

- Never expose sensitive data in responses
- Use HTTPS in production
- Validate all input data
- Implement rate limiting for OTP endpoints

## Troubleshooting

### Common Issues

1. **SendGrid Errors**
   - Check API key configuration
   - Verify sender email is verified
   - Check SendGrid account status

2. **JWT Token Issues**
   - Verify JWT settings in `settings.py`
   - Check token expiration times
   - Ensure proper token format

3. **Database Issues**
   - Run migrations: `python manage.py migrate`
   - Check database connection
   - Verify model relationships

4. **Test Failures**
   - Check email configuration for tests
   - Verify test database setup
   - Check for missing environment variables

### Debug Mode

Enable debug mode for detailed error messages:

```python
DEBUG = True
```

### Logging

Configure logging in `settings.py` for better debugging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## Contributing

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused

### Git Workflow

1. Create feature branch from main
2. Make changes with descriptive commits
3. Write/update tests
4. Run test suite
5. Submit pull request

### Code Review Checklist

- [ ] Tests pass
- [ ] Code follows project conventions
- [ ] Response format is consistent
- [ ] Error handling is appropriate
- [ ] Documentation is updated
- [ ] No sensitive data exposed

---

## Quick Reference

### Key Files
- `utils/response.py` - ResponseMixin for consistent responses
- `utils/email.py` - Email utilities and OTP functions
- `app/views.py` - API endpoints
- `app/serializers.py` - Data validation and transformation
- `app/models.py` - Database models
- `app/tests/test_auth.py` - Test suite

### Key Classes
- `ResponseMixin` - Unified response formatting
- `CustomTokenObtainPairView` - JWT login
- `CustomTokenRefreshView` - Token refresh
- `UserRegistrationView` - User registration
- `VerifyOTPView` - OTP verification

### Environment Variables
- `SENDGRID_API_KEY` - SendGrid API key
- `MAIL_FROM` - Verified sender email
- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode flag

This guide should help new developers understand the project structure, conventions, and best practices quickly. 