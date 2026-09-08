"""Isolated tests: no PostgreSQL credentials or model downloads required."""
SECRET_KEY = 'test-only-key-never-use-in-production'
INSTALLED_APPS = ['django.contrib.sessions', 'django.contrib.auth', 'django.contrib.contenttypes', 'chat', 'users', 'rest_framework']
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
ROOT_URLCONF = 'chat.test_urls'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
USE_TZ = True
ALLOWED_HOSTS = ['testserver', 'localhost']
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
