import os.path

from django.conf import settings

# lazy init for translations
_ = lambda s: s  # noqa: E731


def pytest_configure():
    settings.configure(
        TEMPLATES=[
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
        ],
        MIDDLEWARE=[
            "django.middleware.security.SecurityMiddleware",
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.common.CommonMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            "fullctl.django.middleware.RequestAugmentation",
        ],
        INSTALLED_APPS=[
            "dal",
            "dal_select2",
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
            "django.contrib.sites",
            "django_grainy",
            "django_peeringdb",
            "django_handleref",
            "reversion",
            "rest_framework",
            # social auth
            "social_django",
            # ixctl apps
            "fullctl.django.apps.DjangoFullctlConfig",
            "django_ixctl.apps.DjangoIxctlConfig",
        ],
        DATABASE_ENGINE="django.db.backends.sqlite3",
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEBUG=False,
        DEBUG_EMAIL=True,
        SERVER_EMAIL="default@localhost",
        EMAIL_DEFAULT_FROM="default@localhost",
        EMAIL_NOREPLY="noreply@localhost",
        RELEASE_ENV="test",
        PACKAGE_VERSION="test",
        STATIC_URL="/s/test/",
        TABLE_PREFIX="peeringdb_",
        LOGIN_REDIRECT_URL="/",
        LOGOUT_REDIRECT_URL="/login",
        LOGIN_URL="/login",
        TEMPLATE_DEBUG=True,
        ABSTRACT_ONLY=False,
        AUTHENTICATION_BACKENDS=["django_grainy.backends.GrainyBackend"],
        NETOM_TEMPLATE_DIR=os.path.join(os.path.dirname(__file__), "data", "netom"),
        REST_FRAMEWORK={
            "DEFAULT_RENDERER_CLASSES": [
                "fullctl.django.rest.renderers.JSONRenderer",
            ],
            "DEFAULT_AUTHENTICATION_CLASSES": (
                "fullctl.django.rest.authentication.APIKeyAuthentication",
                "rest_framework.authentication.SessionAuthentication",
            ),
            "DEFAULT_MODEL_SERIALIZER_CLASS": (
                "rest_framework.serializers.HyperlinkedModelSerializer"
            ),
            "DEFAULT_PERMISSION_CLASSES": [
                "rest_framework.permissions.IsAuthenticated",
            ],
            "EXCEPTION_HANDLER": "fullctl.django.rest.core.exception_handler",
            "DEFAULT_THROTTLE_RATES": {"email": "1/minute"},
        },
        LOGGING={
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "stderr": {
                    "level": "DEBUG",
                    "class": "logging.StreamHandler",
                },
            },
            "loggers": {
                "": {"handlers": ["stderr"], "level": "DEBUG", "propagate": False},
            },
        },
        ROOT_URLCONF="ixctl.urls",
        USE_TZ=True,
        PEERINGDB_SYNC_STRIP_TZ=True,
        MANAGED_BY_OAUTH=False,
        COUNTRIES_OVERRIDE={
            "XK": _("Kosovo"),
        },
        TWENTYC_ENDPOINT="https://account.20c.com",
        USE_LOCAL_PERMISSIONS=True,
        SECRET_KEY="setme",
        SERVICE_KEY="secret",
    )
