OS_USERNAME = ''
OS_PASSWORD = ''
OS_TENANT_NAME = ''
OS_AUTH_URL = ''

try:
    from tests.override_settings import *
except ImportError:
    pass
