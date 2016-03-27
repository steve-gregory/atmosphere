"""
ASGI entrypoint file for default channel layer.

get_channel_layer points to channel layer configured as 'default'
in Atmosphere's settings files.
Note from author: You can point ASGI applications at `atmosphere.asgi:channel_layer` as their channel layer.
"""

import os
from channels.asgi import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "atmosphere.settings")
channel_layer = get_channel_layer()
