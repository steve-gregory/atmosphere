import logging

from channels import Group
from channels.sessions import channel_session
from channels.auth import channel_session_user_from_http
from channels.handler import AsgiHandler

from channels.sessions import enforce_ordering


from django.http import HttpResponse


def ws_connect(message):
    logger = logging.getLogger(__name__)
    logger.info('WebSocket connect message = %s', message.__dict__)
    pass


def ws_message(message):
    "Echoes messages back to the client"
    logger = logging.getLogger(__name__)
    logger.info('WebSocket message = %s', message.__dict__)
    message.reply_channel.send(message.content)

def http_consumer(message):
    """
    Consume "Standard HTTP" Responses
    """
    logger = logging.getLogger(__name__)
    logger.info('HTTP Response message = %s', message.__dict__)
    response = HttpResponse("Hello world! You asked for %s" % message.content['path'])
    # Encode that response into message format (ASGI)
    for chunk in AsgiHandler.encode_response(response):
        message.reply_channel.send(chunk)


# Connected to websocket.connect and websocket.keepalive
@channel_session_user_from_http
def websocket_connect(message):
    logger = logging.getLogger(__name__)
    logger.info('websocket_connect. message = %s', message)
    # transfer_user(message.http_session, message.channel_session)
    Group("notifications").add(message.reply_channel)

# Connected to websocket.keepalive
@channel_session
def websocket_keepalive(message):
    logger = logging.getLogger(__name__)
    logger.info('websocket_keepalive. message = %s', message)
    Group("notifications").add(message.reply_channel)


# Connected to websocket.disconnect
@channel_session
def websocket_disconnect(message):
    logger = logging.getLogger(__name__)
    logger.info('websocket_disconnect. message = %s', message)
    Group("notifications").discard(message.reply_channel)
