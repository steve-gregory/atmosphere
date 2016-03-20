import logging

from channels import Channel, Group
from channels.sessions import channel_session
from channels.auth import http_session_user, channel_session_user, transfer_user
from channels.handler import AsgiHandler

from channels.sessions import enforce_ordering
from iplantauth.models import Token

from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser


def disconnect_from_instances(message):
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    logger = logging.getLogger(__name__)
    for inst in user.current_instances:
        group_name = "instance-push-%s" % inst.provider_alias
        Group(group_name).discard(message.reply_channel)
        logger.info('Remove group: %s' % group_name)


def connect_to_instances(message):
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    logger = logging.getLogger(__name__)
    for inst in user.current_instances:
        group_name = "instance-push-%s" % inst.provider_alias
        Group(group_name).add(message.reply_channel)
        logger.info('Add group: %s' % group_name)


def latest_instance_state(message):
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    logger = logging.getLogger(__name__)
    for instance in user.current_instances:
        group_name = "instance-push-%s" % instance.provider_alias
        Group(group_name).send({
            "instance_id": instance.provider_alias,
            "status": instance.get_last_history().status.name,

        })
        logger.info('Update group: %s' % group_name)


def ws_push_instance_update(instance, new_history):
    user = instance.created_by
    Channel("instance-push").send({
        "user": user.username,
        "payload": {
            "instance_id": instance.provider_alias,
            "status": new_history.status.name,
        }
    })

def user_from_token(message):
    if hasattr(message,'content') and 'access_token' in message.content.get('query_string',''):
        token = message.content['query_string'].replace('access_token=','')
        message.channel_session['token'] = token
    if 'token' not in message.channel_session:
        return None
    user = Token.objects.get(key=message.channel_session['token']).user
    return user

#@channel_session
@channel_session_user
def ws_connect(message):
    logger = logging.getLogger(__name__)
    logger.info('WebSocket connect message = %s', message.__dict__)
    connect_to_instances(message)
    pass


@channel_session_user
def ws_disconnect(message):
    disconnect_from_instances(message)


@channel_session_user
def ws_refresh_instance(message):
    latest_instance_state(message)



@channel_session
def ws_push_instance(message):
    Group("instance-push-%s"
          % message.content['user']).send({
        "content" : message.content['payload']
    })
