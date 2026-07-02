# Django settings for crafts_project project.

from pathlib import Path
import os
try:
    import dj_database_url
except ImportError:
    dj_database_url = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if it exists
ENV_PATH = BASE_DIR / '.env'
if ENV_PATH.exists():
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                try:
                    key, val = line.split('=', 1)
                    os.environ[key] = val
                except ValueError:
                    pass


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("The SECRET_KEY environment variable is not set. Please define it in your .env file.")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't') and not os.environ.get('RENDER')

ALLOWED_HOSTS = [
    'little-creators-shop.onrender.com', 
    'littlecreators.shop',          # الدومين الجديد بدون www
    'www.littlecreators.shop',      # الدومين الجديد مع www
    '127.0.0.1', 
    'localhost',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
    'owners.apps.OwnersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'crafts_project.settings.RateLimitMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'crafts_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.theme_processor',
                'core.context_processors.cart_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'crafts_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

if not os.environ.get('DATABASE_URL'):
    raise ValueError("The DATABASE_URL environment variable is not set. Please define it in your .env file.")

DATABASES = {
    'default': dj_database_url.config(
        conn_max_age=600
    )
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ('en', 'English'),
    ('ar', 'العربية'),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

from whitenoise.storage import CompressedManifestStaticFilesStorage

class LazyCompressedManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    manifest_strict = False

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "crafts_project.settings.LazyCompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'core.CustomUser'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'store'
LOGOUT_REDIRECT_URL = 'store'

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@crafts.com'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Cache Configuration for Rate Limiting
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Security Headers & Cookies
SECURE_BROWSER_XSS_HEADER = '1; mode=block'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

# Session and CSRF Security
SESSION_COOKIE_SECURE = not DEBUG and os.environ.get('RENDER') == 'true'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG and os.environ.get('RENDER') == 'true'
CSRF_COOKIE_HTTPONLY = True

# HTTPS settings for Production (only active on Render)
if not DEBUG and os.environ.get('RENDER') == 'true':
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Logging configuration to capture errors in production console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.utils.deprecation import MiddlewareMixin

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        is_sensitive = request.method == 'POST' and any(p in request.path for p in ['/login/', '/signup/', '/checkout/', '/mock-oauth/'])
        limit, period, key = (5, 60, f"rl_s_{ip}_{request.path}") if is_sensitive else (100, 60, f"rl_g_{ip}")
        count = cache.get(key, 0)
        if count >= limit:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'error': 'Too many requests. Please try again later.'}, status=429)
            return HttpResponse("<h1>429 Too Many Requests</h1><p>Too many requests. Please wait a minute.</p>", status=429)
        cache.set(key, count + 1, timeout=period)
        return None
