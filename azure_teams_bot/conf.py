"""
Basic Configuration for Azure Bots.
"""
from navconfig import config, BASE_DIR
from navconfig.logging import logging

## Disable aiohttp Logging
logging.getLogger(name='aiohttp.access').setLevel(logging.WARNING)

MS_TENANT_ID = config.get('MS_TENANT_ID')
MS_CLIENT_ID = config.get('MS_CLIENT_ID')
MS_CLIENT_SECRET = config.get('MS_CLIENT_SECRET')


BOTDEV_CLIENT_ID = config.get('BOTDEV_CLIENT_ID')
BOTDEV_CLIENT_SECRET = config.get('BOTDEV_CLIENT_SECRET')
