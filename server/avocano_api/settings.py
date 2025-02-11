#!/usr/bin/python
#
# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import io
import os
from pathlib import Path
from urllib.parse import urlparse

import environ

from .cloudrun_helpers import MetadataError, get_service_url, get_project_id

from google.oauth2 import service_account


BASE_DIR = Path(__file__).resolve().parent.parent

# Load settings from local .env, mounted .env, or envvar.
env = environ.Env()
env.read_env(BASE_DIR / ".env")
env.read_env("/settings/.env")
env.read_env(io.StringIO(os.environ.get("DJANGO_ENV", None)))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG", default=True)

# newly added #############################
# Load Google Cloud credentials
# GS_CREDENTIALS = service_account.Credentials.from_service_account_file("gcs-service-account.json")  # Path to your GCS key


# Google Cloud Storage settings
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'media-bd80-448911-64ca'  # Replace with your actual bucket name
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
#############################################

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
    "colorfield",
    "corsheaders",
    "rest_framework",
    "django_filters",
    "drf_spectacular",
    "storages"
]

# ALLOWED_HOSTS = ["localhost"]
# CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = ['http://localhost:8081/', 'https://8081-cs-9809f857-9166-4df4-b761-58b43a5eeec7.cs-asia-southeast1-bool.cloudshell.dev']


MIDDLEWARE = [
    "avocano_api.healthchecks.HealthCheckMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "avocano_api.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Used for local dev or using Cloud Run proxy
local_hosts = ["http://localhost:8000", "http://localhost:8081"]

# Used for Cloud Shell dev with Web Preview
cloudshell_host = "https://*.cloudshell.dev"

# Used to identify the host of the deployed service
# Supports a comma separated list of full URLs
CLOUDRUN_SERVICE_URL = env("CLOUDRUN_SERVICE_URL", default=None)

# If the Cloud Run service isn't defined, try dynamically retrieving it.
if not CLOUDRUN_SERVICE_URL:
    try:
        CLOUDRUN_SERVICE_URL = get_service_url()
    except MetadataError:
        pass

if CLOUDRUN_SERVICE_URL:
    # Setup as we are running in Cloud Run & Firebase
    service_urls = CLOUDRUN_SERVICE_URL.split(",")
    ALLOWED_HOSTS = [urlparse(url).netloc for url in service_urls] + ["127.0.0.1"]

    # Firebase hosting has multiple default URLs, so add those as well.
    project_id = get_project_id()

    # If a deployment suffix is provided, presume this is being used as
    # the Firebase Site URL, rather than just the default site (project-id).
    # From variable `random_suffix` in https://github.com/GoogleCloudPlatform/terraform-dynamic-python-webapp/blob/main/infra/variables.tf#L44
    DEPLOYMENT_SUFFIX = env("DEPLOYMENT_SUFFIX", default=None)
    if DEPLOYMENT_SUFFIX:
        firebase_site_id = f"{project_id}-{DEPLOYMENT_SUFFIX}"
    else:
        firebase_site_id = project_id

    firebase_hosts = [
        f"https://{firebase_site_id}.web.app",
        f"https://{firebase_site_id}.firebaseapp.com",
    ]

    CSRF_TRUSTED_ORIGINS = service_urls + local_hosts + firebase_hosts
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    ALLOWED_HOSTS = ["*"]

else:
    # Setup as we are running on localhost, or Cloud Shell
    ALLOWED_HOSTS = ["*"]
    CSRF_TRUSTED_ORIGINS = [cloudshell_host] + local_hosts

# django-cors-headers settings
# CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOWED_ORIGIN_REGEXES = [
#     r"^http://\w+\.localhost\.$",
# ]

CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOW_DEBUG = True
# CORS_ALLOW_METHODS = [
#     'DELETE',
#     'GET',
#     'OPTIONS',
#     'PATCH',
#     'POST',
#     'PUT',
# ]

# CORS_ALLOW_HEADERS = [
#     'accept',
#     'accept-encoding',
#     'authorization',
#     'content-type',
#     'dnt',
#     'origin',
#     'user-agent',
#     'x-csrftoken',
#     'x-requested-with',
# ]

CORS_ALLOWED_ORIGINS = ["http://localhost:8081", 
    "https://8081-cs-9809f857-9166-4df4-b761-58b43a5eeec7.cs-asia-southeast1-bool.cloudshell.dev"]  # For local testing

WSGI_APPLICATION = "avocano_api.wsgi.application"


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases

# Use django-environ to parse the connection string
DATABASES = {"default": env.db()}

# If the flag as been set, configure to use proxy
if env("USE_CLOUD_SQL_AUTH_PROXY", default=None):
    DATABASES["default"]["HOST"] = "127.0.0.1"
    DATABASES["default"]["PORT"] = 5432


# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    # Any exposed endpoints can be accessed by any client that has access to the API itself.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    # For automatic OpenAPI schema.
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",

    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.JSONParser',
        #'rest_framework.parsers.FileUploadParser'
     )
}



# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Use Cloud Storage if configured, otherwise use local storage.
if GS_BUCKET_NAME := env("GS_BUCKET_NAME", default=None):
    STORAGES = {
        "default": {"BACKEND": "storages.backends.gcloud.GoogleCloudStorage"},
        "staticfiles": {"BACKEND": "storages.backends.gcloud.GoogleCloudStorage"},
    }

    GS_DEFAULT_ACL = "publicRead"
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    STATIC_ROOT = os.path.join(BASE_DIR, STATIC_URL.replace("/", ""))
    MEDIA_ROOT = os.path.join(BASE_DIR, MEDIA_URL.replace("/", ""))
