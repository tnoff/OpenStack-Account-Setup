# Set default values for schema

IMAGE_WAIT = False
IMAGE_WAIT_TIMEOUT = 1800
IMAGE_WAIT_INTERVAL = 5

VOLUME_WAIT = False
VOLUME_WAIT_TIMEOUT = 1800
VOLUME_WAIT_INTERVAL = 5

SERVER_WAIT = False
SERVER_WAIT_TIMEOUT = 1800
SERVER_WAIT_INTERVAL = 5

EXPORT_KEYS_IGNORE = ['_loaded', '_info', 'id', 'manager', 'links']
EXPORT_SKIP_USERS = ['nova', 'cinder', 'glance', 'neutron']
EXPORT_SKIP_PROJECTS = ['service']

EXPORT_SKIP_FLAVORS = ['OS-FLV-DISABLED:disabled']

EXPORT_SKIP_RULES = ['group', 'parent_group_id']
