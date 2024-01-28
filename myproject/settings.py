from pathlib import Path
import os
import dj_database_url
import dj_db_conn_pool
import cloudinary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-frm2#x_bnb!#93yw4=0_imf%c7kbkkrink09w33#)ieht#u-x$'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    ALLOWED_HOSTS = ['schedule1213-7d61e308285e.herokuapp.com']
    SITE_ID = 4
    cloudinary.config()
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
else:
    ALLOWED_HOSTS = ['*']
    SITE_ID = 3
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


INSTALLED_APPS = [
    'schedule',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'schedule.middleware.CustomRedirectMiddleware',
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates"],
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

WSGI_APPLICATION = 'myproject.wsgi.application'

if DJANGO_ENV == 'production':
    redis_host = os.environ.get('REDIS_URL')
else:
    redis_host = ("schedule_redis_1", 6379)

ASGI_APPLICATION = 'myproject.asgi.application'
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [redis_host],
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}



# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

if os.environ.get('USE_HEROKU_DB') == 'true':
    db_production = dj_database_url.config(default=os.environ.get('JAWSDB_URL'))
    db_production['POOL_OPTIONS'] = {
        'pool_size': 10,
        'timeout': 300,
    }
    DATABASES = {
        'default': db_production
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'dj_db_conn_pool.backends.mysql',
            'NAME': 'django_db',
            'USER': 'django',
            'PASSWORD': 'password',
            'HOST': 'db',
            'PORT': '3306',
            'POOL_OPTIONS': {
                'pool_size': 10,
                'timeout': 300,
            },
        }
    }

AUTH_USER_MODEL = 'schedule.CustomUser'



# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'
