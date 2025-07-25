"""
Django settings for core project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from datetime import timedelta

TESTING = 'test' in sys.argv

# Load environment variables from the .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-9(qzc%oywe&l_@_v1opcmzu$b-qe@%ffn0dr%50wq8lq1fyewg'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    "rest_framework_simplejwt.token_blacklist",
    'imagekit',
    'drf_spectacular',
    'django_celery_beat',
    'mptt',
    'taggit',
    'django_filters',
    'django_json_widget',
    'simple_history',

    # First-party apps
    'accounts.apps.AccountsConfig',
    'courses.apps.CoursesConfig',
    'comments.apps.CommentsConfig',
    'VisitCounter.apps.VisitCounterConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# DATABASES
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': os.getenv('DB_NAME'),  # Your database name
        'USER': os.getenv('DB_USER'),  # Your database user
        'PASSWORD': os.getenv('DB_PASSWORD'),  # Your database password
        'HOST': os.getenv('DB_HOST'),  # Host where PostgreSQL is running
        'PORT': os.getenv('DB_PORT'),  # Leave empty for default port (5432)
    }
}

# CACHES
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv('CACHE_LOCATION'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'fa-ir'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

# Media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR / 'media')

# REST_FRAMEWORK
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "accounts.authentication.JWTCookieAuthentication",
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Simple JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    # Auth
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Auth Cookie
    "AUTH_COOKIE_ACCESS": "access_token",
    "AUTH_COOKIE_REFRESH": "refresh_token",
    "AUTH_COOKIE_DOMAIN": None,  # ".example.com" or None for standard domain cookie
    "AUTH_COOKIE_SECURE": False,  # Whether the auth cookies should be secure (https:// only).
    "AUTH_COOKIE_HTTP_ONLY": True,
    "AUTH_COOKIE_SAMESITE": "Lax",
    # The flag restricting cookie leaks on cross-site requests. 'Lax', 'Strict' or None to disable the flag.
    "AUTH_COOKIE_REFRESH_PATH": "/accounts/",
}

# IMAGES
IMAGE_SIZES = {
    "DEFAULT_ALL_IMAGE_SIZE_LIMIT": 1024,  # KB
}

# RATELIMIT
RATELIMIT_USE_CACHE = 'default'

# CELERY
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

# SPECTACULAR
SPECTACULAR_SETTINGS = {
    'TITLE': 'TPC',
    'DESCRIPTION': ('This document covers all endpoints, '
                    'request/response models, and interaction guidelines for the TPC API.'),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# OTP
OTP = {
    "EXPIRATION_TIME_SECONDS": 5,
    "LONG_TIME_SECONDS": 2 * 60 * 60,
    "LONG_MAX_REQUESTS": 2,

    "VALID_WINDOW": 1,
    # VALID_WINDOW defines how many time steps are valid for OTP
    # verification Each step is 30 seconds, and values from 0 to 5 are allowed.
}


# Internal IPs
INTERNAL_IPS = [
    "127.0.0.1",
]

# Debug toolbar

if not TESTING:
    INSTALLED_APPS = [
        *INSTALLED_APPS,
        "debug_toolbar",
    ]
    MIDDLEWARE = [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        *MIDDLEWARE,
    ]
