"""
Django settings for lastline_api project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'CHANGE_THIS_KEY_FOR_PRODUCTION'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False 
TEMPLATE_DEBUG = False 
TEMPLATE_DIRS = [ os.path.join(BASE_DIR, 'templates') ]
ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'intel',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    #'lockout.middleware.LockoutMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'request_provider.middleware.RequestProvider'
)

ROOT_URLCONF = 'lastline_api.urls'
WSGI_APPLICATION = 'lastline_api.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Helsinki'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

# Lastline PAPI client configuration file path
PAPI_CLIENTCONF = os.path.join(BASE_DIR, "config/papi_client.ini")

# Only affects 'manage.py collectstatic' when it moves file here
STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATICFILES_DIRS = (
  os.path.join(BASE_DIR, "intel/static"),
  os.path.join(BASE_DIR, "lastline_api/static"),
)
STATIC_URL = '/static/'
LOGIN_URL = '/login'
LOGOUT_URL = '/'
LOGIN_REDIRECT_URL = '/intel'

#
# Django-Lockout addon for handling failed logins
#
#LOCKOUT_MAX_ATTEMPTS = 5
#LOCKOUT_TIME = 600
#LOCKOUT_ENFORCEMENT_WINDOW = 600
#LOCKOUT_USE_USER_AGENT = False
#LOCKOUT_CACHE_PREFIX = 'lockout'
