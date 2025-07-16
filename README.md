# 🎓 Cyber Security Learning Platform - Backend API

A comprehensive Django REST Framework backend for a cyber security learning platform with JWT authentication, OTP verification, interactive modules, quizzes, and certificate generation.

## 🚀 Features

### 🔐 Authentication & Security
- **JWT Authentication** with access and refresh tokens
- **OTP Verification** for user registration and password reset
- **Auto-login** after successful OTP verification
- **Password Management** (change, reset, forgot password)
- **User Profile Management** with verification status

### 📚 Learning Management
- **Interactive Modules** with content and progress tracking
- **Module Quizzes** for knowledge assessment
- **Final Comprehensive Quiz** with scoring system
- **Progress Tracking** with completion percentages
- **User Module Progress** monitoring

### 🏆 Certificate System
- **Automatic Certificate Generation** upon passing final quiz
- **PDF Certificate Download** with professional formatting
- **Certificate Validation** and verification
- **Unique Certificate IDs** with timestamp

### 🧪 Testing & Quality
- **Comprehensive Test Suite** with pytest
- **Authentication Tests** covering all auth flows
- **API Endpoint Tests** for all views
- **Error Handling Tests** with proper validation

## 🛠️ Technology Stack

- **Framework**: Django 5.2.4
- **API**: Django REST Framework 3.16.0
- **Authentication**: JWT (djangorestframework-simplejwt 5.5.0)
- **Database**: PostgreSQL
- **Email**: SendGrid
- **PDF Generation**: ReportLab
- **Testing**: pytest & pytest-django
- **Documentation**: drf-spectacular (OpenAPI/Swagger)

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL
- SendGrid account (for email functionality)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd backend-django
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .cyber-backend
   source .cyber-backend/bin/activate  # On Windows: .cyber-backend\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   SENDGRID_API_KEY=your-sendgrid-api-key
   SENDGRID_FROM_EMAIL=your-email@domain.com
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Authentication Endpoints

#### 🔐 User Registration
```http
POST /api/register/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### 📧 OTP Verification (Auto-login)
```http
POST /api/verify-otp/
Content-Type: application/json

{
    "email": "user@example.com",
    "code": "123456"
}
```

**Response includes JWT tokens for automatic login:**
```json
{
    "status": "success",
    "message": "OTP verified successfully. You are now logged in!",
    "data": {
        "email": "user@example.com",
        "first_name": "John",
        "verified": true,
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "first_login": true
    }
}
```

#### 🔑 User Login
```http
POST /api/login/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "securepassword123"
}
```

#### 🔄 Token Refresh
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "your-refresh-token"
}
```

### Learning Management Endpoints

#### 📊 Dashboard
```http
GET /api/dashboard/
Authorization: Bearer <access_token>
```

#### 📖 Get Module
```http
GET /api/modules/{module_id}/
Authorization: Bearer <access_token>
```

#### ✅ Mark Module as Completed
```http
POST /api/modules/{module_id}/complete/
Authorization: Bearer <access_token>
```

#### 📈 User Progress
```http
GET /api/module-progress/
Authorization: Bearer <access_token>
```

### Quiz Endpoints

#### 🎯 Get Final Quiz
```http
GET /api/quiz/
Authorization: Bearer <access_token>
```

#### 📝 Submit Final Quiz
```http
POST /api/quiz/
Authorization: Bearer <access_token>
Content-Type: application/json

[
    {
        "question": "What is cybersecurity?",
        "selected_option": "Protection of digital systems"
    }
]
```

### Certificate Endpoints

#### 🏆 Get User Certificate
```http
GET /api/certificates/
Authorization: Bearer <access_token>
```

#### 📄 Download Certificate PDF
```http
GET /api/certificates/{certificate_id}/download/
Authorization: Bearer <access_token>
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Authentication tests
pytest app/tests/test_auth.py -v

# API endpoint tests
pytest app/tests/test_views.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Test Structure
- **Authentication Tests**: Registration, OTP verification, login, password management
- **API Tests**: All endpoints with proper authentication and error handling
- **Integration Tests**: Full user flows from registration to certificate generation

## 🔧 Configuration

### JWT Settings
```python
# settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
}
```


## 📁 Project Structure

```
backend-django/
├── app/
│   ├── models.py          # Database models
│   ├── views.py           # API views and endpoints
│   ├── serializers.py     # Data serialization
│   ├── admin.py           # Django admin configuration
│   └── tests/
│       ├── test_auth.py   # Authentication tests
│       └── test_views.py  # API endpoint tests
├── core/
│   ├── settings.py        # Django settings
│   ├── urls.py           # Main URL configuration
│   └── wsgi.py           # WSGI configuration
├── users/                 # Custom user app
├── utils/
│   ├── response.py       # Response mixin for consistent API responses
│   ├── email.py          # Email utilities
│   └── certificate_generator.py  # PDF certificate generation
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
└── README.md           # This file
```

## 🔒 Security Features

- **JWT Authentication** with secure token handling
- **OTP Verification** for account security
- **Password Validation** with Django's built-in validators
- **CORS Configuration** for frontend integration
- **Rate Limiting** on sensitive endpoints
- **Input Validation** and sanitization

## 📧 Email Integration

The platform uses SendGrid for:
- **Registration OTP** emails
- **Password Reset** OTP emails
- **Certificate Notifications** (future feature)

## 🏆 Certificate System

### Features
- **Automatic Generation** when user passes final quiz (80%+ score)
- **Professional PDF Format** with ReportLab
- **Unique Certificate IDs** with timestamp
- **Download Functionality** with proper headers
- **Certificate Validation** and verification

### Certificate Data
- User name and email
- Score and pass status
- Issue date
- Unique certificate ID
- Professional formatting

## 🚀 Deployment

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up proper CORS settings
- [ ] Configure static files
- [ ] Set up SSL/HTTPS
- [ ] Configure email settings
- [ ] Set up monitoring and logging

### Docker Support (Future)
```dockerfile
# Dockerfile example for containerization
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/api/schema/`

## 🔄 API Versioning

The API follows semantic versioning. Current version: `v1`

## 📊 Performance

- **Database Optimization** with select_related and prefetch_related
- **Bulk Operations** for quiz answer processing
- **Efficient Token Handling** with proper refresh mechanisms
- **Caching Ready** for future optimization

---

**Built with ❤️ using Django REST Framework**