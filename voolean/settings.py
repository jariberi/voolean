# -*- coding: utf-8 -*-

import os
from voolean import personal

# Django settings for voolean project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Argentina/Cordoba'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-ar'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False
DECIMAL_SEPARATOR = '.'

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

DATE_INPUT_FORMATS = [
    '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y',  # '2006-10-25', '10/25/2006', '10/25/06'
    '%b %d %Y', '%b %d, %Y',  # 'Oct 25 2006', 'Oct 25, 2006'
    '%d %b %Y', '%d %b, %Y',  # '25 Oct 2006', '25 Oct, 2006'
    '%B %d %Y', '%B %d, %Y',  # 'October 25 2006', 'October 25, 2006'
    '%d %B %Y', '%d %B, %Y',  # '25 October 2006', '25 October, 2006'
]
DATE_FORMAT = 'd/m/Y'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/home/jorge/website/statics'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = 'http://statics.facturofacil.com.ar/' if DEBUG is False else '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/static' % os.path.split(os.path.dirname(os.path.realpath(__file__)))[0],
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f#=kz%3h8qrqv%acibdw0ln@2e9g(v1%o#k89w78^pi$4-@y&y'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'voolean.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'voolean.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '%s/templates' % os.path.split(os.path.dirname(os.path.realpath(__file__)))[0],
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'core',
    'ventas',
    'compras',
    # 'express',
    'afip_ws'
)

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': '%s/voolean.log' % os.path.dirname(os.path.realpath(__file__))
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'voolean': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

#DATOS DE LA EMPRESA, SOBREESCRIBIR EN CADA IMPLEMENTACION

PUNTO_VENTA_FAA = personal.PUNTO_VENTA_FAA
PUNTO_VENTA_FAB = personal.PUNTO_VENTA_FAB
PUNTO_VENTA_FAC = personal.PUNTO_VENTA_FAC
PUNTO_VENTA_NCA = personal.PUNTO_VENTA_NCA
PUNTO_VENTA_NCB = personal.PUNTO_VENTA_NCB
PUNTO_VENTA_NCC = personal.PUNTO_VENTA_NCC
PUNTO_VENTA_NDA = personal.PUNTO_VENTA_NDA
PUNTO_VENTA_NDB = personal.PUNTO_VENTA_NDB
PUNTO_VENTA_NDC = personal.PUNTO_VENTA_NDC


PRIVATE_KEY_FILE = personal.PRIVATE_KEY_FILE
CERT_FILE_TEST = personal.CERT_FILE_TEST
CERT_FILE_PROD = personal.CERT_FILE_PROD

# Datos de la empresa licenciada

RAZON_SOCIAL_EMPRESA = personal.RAZON_SOCIAL_EMPRESA
CUIT = personal.CUIT
INGRESOS_BRUTOS = personal.INGRESOS_BRUTOS
INICIO_ACTIVIDADES = personal.INICIO_ACTIVIDADES
DOMICILIO_COMERCIAL = personal.DOMICILIO_COMERCIAL
CIUDAD = personal.CIUDAD
PROVINCIA = personal.PROVINCIA
CODIGO_POSTAL = personal.CODIGO_POSTAL
ES_MONOTRIBUTO = personal.ES_MONOTRIBUTO
USA_FACTURA_ELECTRONICA = personal.USA_FACTURA_ELECTRONICA
CONDICION_IVA = personal.CONDICION_IVA

#ESTO NO ES PROPIO DE LA EMPRESA, PERO CADA UNA USARA UNA BD DISTINTA
DATABASES = personal.DATABASES