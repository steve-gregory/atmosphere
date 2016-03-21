import logging

from channels import Channel, Group
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, transfer_user
from channels.handler import AsgiHandler

from channels.sessions import enforce_ordering
from iplantauth.models import Token

from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser


@channel_session_user
def ws_connect(message):
    """
    Router for all websocket.connect
    """
    logger = logging.getLogger(__name__)
    logger.info('WebSocket connect message = %s', message.__dict__)
    path = message.content['path']
    if 'instance' in path:
        return push_connect(message)
    return chat_connect(message)


@channel_session_user
def ws_disconnect(message):
    """
    Router for all websocket.disconnect
    """
    logger = logging.getLogger(__name__)
    logger.info('WebSocket disconnect message = %s', message.__dict__)
    path = message.channel_session['path']
    if 'instance' in path:
        return push_disconnect(message)
    return chat_disconnect(message)


@channel_session_user
def ws_receive(message):
    """
    Router for all websocket.receive
    """
    logger = logging.getLogger(__name__)
    logger.info('WebSocket receive message = %s', message.__dict__)
    path = message.channel_session['path']
    if 'instance' in path:  # /connect/instances
        return push_instance_updates(message)
    return chat_reply(message)


def user_from_token(message):
    """
    Same idea as 'session_key=12345'
    this allows troposphere to 'authenticate' its WebSockets
    """
    if hasattr(message,'content') and 'access_token' in message.content.get('query_string',''):
        token = message.content['query_string'].replace('access_token=','')
        message.channel_session['token'] = token
    if 'path' not in message.channel_session and 'path' in message.content:
        message.channel_session['path'] = message.content['path']
    if 'token' not in message.channel_session:
        return None
    user = Token.objects.get(key=message.channel_session['token']).user
    if 'username' not in message.channel_session:
        message.channel_session['username'] = user.username
    return user


def ws_push_instance(message):
    """
    Connected to instance-push
    in routing.py
    Responsible for messaging a users group
    """
    group_name = "push-%s" % message.content['username']
    payload = message.content['payload']
    Group(group_name).send({
        "content" : payload,
    })
    logger = logging.getLogger(__name__)
    logger.info('WebSocket sends message to %s = %s' % (group_name, payload))

def push_disconnect(message):
    """
    Remove a group for this user
    """
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    group_name = "push-%s" % message.channel_session['username']
    Group(group_name).discard(message.reply_channel)
    logger = logging.getLogger(__name__)
    logger.info('Remove group: %s' % group_name)


def push_connect(message):
    """
    Create a group for this user
    """
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    group_name = "push-%s" % message.channel_session['username']
    Group(group_name).add(message.reply_channel)
    logger = logging.getLogger(__name__)
    logger.info('Add group: %s' % group_name)


def push_instance_updates(message):
    """
    User has sent a request to listen for updates
    on one or more instances.
    If instance is found, publish an 'update' with
    last known value.
    """
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    logger = logging.getLogger(__name__)
    username = message.channel_session['username']
    instance_match = message.content.get('text','').split(',')
    for instance in user.current_instances:
        if instance.provider_alias in instance_match:
            #FIXME: Actual implementation would change here after testing
            logger.info("Push instance update to:%s - %s" % (username,instance.provider_alias))
            ws_push_instance_update(
                username,
                instance,
                instance.get_last_history()
            )


def ws_push_instance_update(username, instance, new_history):
    """
    Send message to channel 'instance-push'
    to notify listeners of the latest changes
    """
    channel_name = "instance-push"  # Registered in routing.py
    Channel(channel_name).send({
        "username": username,
        "payload": {
            "instance_id": instance.provider_alias,
            "status": new_history.status.name,
        }
    })

# Serves as a 'benchmark'
def chat_connect(message):
    # Add them to the right group
    user = user_from_token(message)
    Group("chat-%s" % user.username).add(message.reply_channel)


def chat_reply(message):
    user = user_from_token(message)
    # Echo back the content
    Group("chat-%s" % user.username).send(message.content)


def chat_disconnect(message):
    user = user_from_token(message)
    Group("chat-%s" % user.username).discard(message.reply_channel)
