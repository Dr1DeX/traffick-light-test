import logging
import os
from pathlib import Path

import environ
import sentry_sdk
import structlog.contextvars
from dotenv import load_dotenv
from redis import SSLConnection
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

env = environ.Env()

load_dotenv(override=True)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY", default="change-me-daddy")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = ["*"]

# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

LOCAL_APPS = [
    "org.core",
    "org.employers"
]

THIRD_PARTY_APPS = [
    "daphne",
    "django_structlog",
    "django_ltree_field"
]

INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "django_structlog.middlewares.RequestMiddleware",
]

# SENTRY
# ------------------------------------------------------------------------------
SENTRY_DSN = env("SENTRY_DSN", default=None)
SENTRY_ENVIRONMENT = env("SENTRY_ENVIRONMENT", default="dev")  # production/dev/review-*
LOGGERS_TO_IGNORE = [
    "django_structlog.middlewares.request",
    "django_structlog.celery.receivers",
]
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(
                signals_spans=False,
                middleware_spans=False,
            ),
            # TODO: временное убираем стандартную logging интеграцию, чтобы корректно
            # отрабатывала интеграцию со structlog
            LoggingIntegration(level=logging.CRITICAL, event_level=logging.CRITICAL),
        ],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=1),
        sample_rate=env.float("SENTRY_ERROR_SAMPLE_RATE", default=1),
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
        environment=SENTRY_ENVIRONMENT,
    )

# ---- REDIS SETTINGS ----
CHANNELS_REDIS_HOST = env("CHANNELS_REDIS_HOST", default="localhost")
CHANNELS_REDIS_PORT = env.int("CHANNELS_REDIS_PORT", default=6379)
CHANNELS_REDIS_USER = env("CHANNELS_REDIS_USER", default=None)
CHANNELS_REDIS_PASSWORD = env("CHANNELS_REDIS_PASSWORD", default=None)
CHANNELS_REDIS_DB = env("CHANNELS_REDIS_DB", default=0)
CHANNELS_REDIS_SSL = env.bool("CHANNELS_REDIS_SSL", default=False)

REDIS_SSL = "rediss" if CHANNELS_REDIS_SSL else "redis"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'{REDIS_SSL}://{CHANNELS_REDIS_HOST}:{CHANNELS_REDIS_PORT}/{CHANNELS_REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

CHANNELS_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [
                dict(
                    host=CHANNELS_REDIS_HOST,
                    port=CHANNELS_REDIS_PORT,
                    username=CHANNELS_REDIS_USER,
                    password=CHANNELS_REDIS_PASSWORD,
                    **(
                        {"connection_class": SSLConnection, "ssl_check_hostname": False}
                        if CHANNELS_REDIS_SSL
                        else {}
                    )
                )
            ]
        }
    }
}

ROOT_URLCONF = 'org.urls'

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
            ],
        },
    },
]

ASGI_APPLICATION = 'org.routing.application'
WSGI_APPLICATION = 'org.entrypoints.main.wsgi.application'

APPEND_SPLASH = False

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DJANGO_MEMORY_DB = env.bool("DJANGO_MEMORY_DB", default=False)
if not DJANGO_MEMORY_DB:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env.str("POSTGRES_DB", default="org"),
            "USER": env.str("POSTGRES_USER", default="postgres"),
            "PASSWORD": env.str("POSTGRES_PASSWORD", default="postgres"),
            "HOST": env.str("POSTGRES_HOST", default="localhost"),
            "PORT": env.int("POSTGRES_PORT", default=5432),
            "TEST": {
                "NAME": "test_org"
            },
            # server-side курсоры не работают с connection pool
            "DISABLE_SERVER_SIDE_CURSORS": True,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ":memory:",
        }
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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---- LOGGING ----
DB_DEBUG = env("DJANGO_DB_DEBUG", default=False)

STRUCTLOG_PROCESSORS = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.UnicodeDecoder()
]


def default_handler():
    return "plain_console" if DEBUG else "logfmt_console"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "plain": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(),
            ],
            "foreign_pre_chain": [*STRUCTLOG_PROCESSORS],
        },
        "logfmt": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.LogfmtRenderer(),
            ],
            "foreign_pre_chain": [*STRUCTLOG_PROCESSORS],
        },
    },
    "handlers": {
        "plain_console": {
            "class": "logging.StreamHandler",
            "formatter": "plain",
        },
        "logfmt_console": {
            "class": "logging.StreamHandler",
            "formatter": "logfmt",
        },
    },
    "filters": {
        "require_db_debug_true": {
            "()": "org.utils.log.RequireDbDebugTrue",
        }
    },
    "root": {
        "level": "CRITICAL",
        "handlers": [],
    },
    "loggers": {
        "django_structlog": {
            "handlers": [default_handler()],
            "level": "INFO",
        },
        "org": {
            "level": "INFO",
            "handlers": [default_handler()],
        },
        # В целях отладки запросов к БД можно включать логирование
        # всех SQL-запросов с помощью переменной среды DJANGO_DB_DEBUG
        "django.db.backends": {
            "level": "DEBUG",
            "handlers": [default_handler()],
            "filters": ["require_db_debug_true"],
            "propagate": False,
        },
        "django.db.backends.schema": {
            "level": "DEBUG",
            "handlers": [default_handler()],
            "filters": ["require_db_debug_true"],
            "propagate": False,
        },
        "daphne": {
            "handlers": [default_handler()],
            "level": "INFO",
        },
        "gunicorn.access": {
            "level": "WARNING",
            "handlers": [default_handler()],
            "propagate": False,
        },
        "gunicorn.error": {
            "level": "INFO",
            "handlers": [default_handler()],
            "propagate": False,
        },
        "django.channels.server": {
            "level": "CRITICAL",
            "handlers": [default_handler()],
            "propagate": False,
        },
        "django.request": {
            "level": "CRITICAL",
            "handlers": [default_handler()],
            "propagate": False,
        },
    },
}

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        *STRUCTLOG_PROCESSORS,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
