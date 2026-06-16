"""
healthsec/settings.py
=====================
Main Django settings for the HealthSec Cyber Risk Intelligence and
Compliance Healthcare Information Monitoring System.

This file is intentionally kept as a single settings module (no split settings)
to keep the university project simple and self-contained.  Environment-specific
values are loaded from a .env file via python-dotenv.
"""

import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# python-dotenv: Load environment variables from .env if it exists            #
# --------------------------------------------------------------------------- #
from dotenv import load_dotenv

load_dotenv()  # Reads .env in the project root (same folder as manage.py)


# --------------------------------------------------------------------------- #
# Base directory – the root of the repository (contains manage.py)           #
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# Security                                                                     #
# --------------------------------------------------------------------------- #
SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    # Default insecure key used ONLY during development – override in .env
    'django-insecure-healthsec-university-project-change-me-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS', 'localhost,127.0.0.1'
).split(',')


# --------------------------------------------------------------------------- #
# Application definition                                                       #
# --------------------------------------------------------------------------- #
INSTALLED_APPS = [
    # Django built-ins
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',           # Django REST Framework for API endpoints
    'rest_framework.authtoken', # Token-based authentication
    'corsheaders',              # Cross-Origin Resource Sharing
    'channels',                 # WebSocket support for real-time alerts

    # HealthSec project apps
    'accounts',     # User authentication and role-based access control
    'monitoring',   # Healthcare information monitoring
    'risk_engine',  # Cyber risk intelligence and scoring
    'compliance',   # Regulatory compliance management (HIPAA, NDPR, etc.)
    'alerts',       # Alert generation and incident response
    'audit',        # Immutable audit log for all system activity
    'dashboard',    # Main summary dashboard
    'reports',      # PDF generation and analytics reports
]


# --------------------------------------------------------------------------- #
# Middleware stack                                                             #
# --------------------------------------------------------------------------- #
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serves static files efficiently in production
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CORS middleware must appear before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware to write every request to the audit log
    'audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'healthsec.urls'

WSGI_APPLICATION = 'healthsec.wsgi.application'
ASGI_APPLICATION = 'healthsec.asgi.application'


# --------------------------------------------------------------------------- #
# Django Channels Configuration                                              #
# --------------------------------------------------------------------------- #
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}


# --------------------------------------------------------------------------- #
# Templates                                                                    #
# --------------------------------------------------------------------------- #
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Project-wide templates folder (holds base.html and shared partials)
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,  # Also load templates from each app's templates/ folder
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Inject unread alert count into every template context
                'alerts.context_processors.unread_alerts_count',
            ],
        },
    },
]


# --------------------------------------------------------------------------- #
# Database – PostgreSQL with SQLite fallback                                  #
# --------------------------------------------------------------------------- #
_db_engine = os.environ.get('DB_ENGINE', 'sqlite')

if _db_engine == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'healthsec_db'),
            'USER': os.environ.get('DB_USER', 'healthsec_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            # Keep persistent connections alive for up to 60 seconds
            'CONN_MAX_AGE': 60,
        }
    }
else:
    # SQLite is the default for local development (no DB server needed)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# --------------------------------------------------------------------------- #
# Password validation                                                          #
# --------------------------------------------------------------------------- #
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --------------------------------------------------------------------------- #
# Custom User Model                                                            #
# --------------------------------------------------------------------------- #
# All auth references will resolve to our custom User in accounts/models.py
AUTH_USER_MODEL = 'accounts.User'


# --------------------------------------------------------------------------- #
# Internationalisation                                                         #
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'   # West Africa Time (WAT, UTC+1)
USE_I18N = True
USE_TZ = True                # Store datetimes in UTC; display in TIME_ZONE


# --------------------------------------------------------------------------- #
# Static files (CSS, JS, images)                                              #
# --------------------------------------------------------------------------- #
STATIC_URL = '/static/'
# Folder where `collectstatic` gathers files for production serving
STATIC_ROOT = BASE_DIR / 'staticfiles'
# Additional directories searched by the static files finder
STATICFILES_DIRS = [BASE_DIR / 'static']
# WhiteNoise compressed manifest storage for production cache-busting
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# --------------------------------------------------------------------------- #
# Media files (user uploads)                                                  #
# --------------------------------------------------------------------------- #
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --------------------------------------------------------------------------- #
# Email backend                                                                #
# --------------------------------------------------------------------------- #
# Console backend prints emails to stdout – safe for development.
# Switch to smtp or django-ses in production via environment variables.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@healthsec.local')

# Site configuration for email links
SITE_NAME = os.environ.get('SITE_NAME', 'HealthSec CRIC HMS')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'localhost:8000')


# --------------------------------------------------------------------------- #
# Session settings                                                             #
# --------------------------------------------------------------------------- #
SESSION_COOKIE_AGE = 1800           # 30 minutes in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True   # Reset timer on each request
SESSION_COOKIE_HTTPONLY = True      # JS cannot read the session cookie
SESSION_COOKIE_SAMESITE = 'Lax'    # CSRF protection for cross-site requests


# --------------------------------------------------------------------------- #
# Security headers                                                             #
# --------------------------------------------------------------------------- #
# These are all set to True in production; keep False in DEBUG to ease dev.
SECURE_BROWSER_XSS_FILTER = True              # X-XSS-Protection header
SECURE_CONTENT_TYPE_NOSNIFF = True            # X-Content-Type-Options: nosniff
X_FRAME_OPTIONS = 'DENY'                      # Clickjacking protection
CSRF_COOKIE_HTTPONLY = False                  # Must be False so JS can read it for AJAX
CSRF_COOKIE_SECURE = not DEBUG               # HTTPS only in production
SECURE_SSL_REDIRECT = not DEBUG              # Redirect HTTP → HTTPS in production
SESSION_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000  # 1 year HSTS in production
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG


# --------------------------------------------------------------------------- #
# Django REST Framework                                                        #
# --------------------------------------------------------------------------- #
REST_FRAMEWORK = {
    # Default authentication: session (for browser) + token (for API clients)
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    # Only authenticated users can access API endpoints by default
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Pagination: return 20 items per page
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Render JSON in a readable format when DEBUG is True
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    # Throttle anonymous and authenticated users to prevent abuse
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
    # ISO 8601 datetime strings
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S',
}


# --------------------------------------------------------------------------- #
# CORS (Cross-Origin Resource Sharing)                                        #
# --------------------------------------------------------------------------- #
# Whitelist of frontend origins allowed to call our API
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

# Allow cookies (session, CSRF) in cross-origin requests
CORS_ALLOW_CREDENTIALS = True

# Headers the API will accept from the client
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# --------------------------------------------------------------------------- #
# Logging                                                                      #
# --------------------------------------------------------------------------- #
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'healthsec': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': False},
    },
}


# --------------------------------------------------------------------------- #
# Default primary key field type                                              #
# --------------------------------------------------------------------------- #
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# --------------------------------------------------------------------------- #
# Login / Logout redirect URLs                                                #
# --------------------------------------------------------------------------- #
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'


# --------------------------------------------------------------------------- #
# Caching (in-memory for dev; swap to Redis / Memcached in production)        #
# --------------------------------------------------------------------------- #
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'healthsec-cache',
        'TIMEOUT': 60,              # Default TTL: 60 seconds
        'OPTIONS': {
            'MAX_ENTRIES': 2000,
        },
    }
}


# --------------------------------------------------------------------------- #
# Rate limiting (django-ratelimit)                                            #
# Applied per view — see accounts/views.py login_view for usage               #
# --------------------------------------------------------------------------- #
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'


# --------------------------------------------------------------------------- #
# Content Security Policy (basic — tighten for production)                   #
# --------------------------------------------------------------------------- #
# Allow Bootstrap/FA CDN + same-origin scripts and styles.
# Uncomment and tune once CSP middleware is added.
# CSP_DEFAULT_SRC = ("'self'",)
# CSP_SCRIPT_SRC  = ("'self'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "'unsafe-inline'")
# CSP_STYLE_SRC   = ("'self'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com", "'unsafe-inline'")
# CSP_FONT_SRC    = ("'self'", "https://cdnjs.cloudflare.com")
# CSP_IMG_SRC     = ("'self'", "data:")


# --------------------------------------------------------------------------- #
# Security hardening extras                                                   #
# --------------------------------------------------------------------------- #
REFERRER_POLICY = 'strict-origin-when-cross-origin'   # Django 4.x reads this header
SECURE_REFERRER_POLICY = 'same-origin'

# Protect against password exposure in error pages
DEBUG_PROPAGATE_EXCEPTIONS = False

# Maximum file upload size (5 MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE  = 5 * 1024 * 1024
