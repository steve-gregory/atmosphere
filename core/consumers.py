"""
Core consumers..

Right now its all funneled through atmosphere/routing.py to listen to the path
/ws/push/instances -- but in a future version we would listen to something more generic
and keep pushing path decisions downward.
(See versioned API urls.py for an example)
"""
import logging
import json
from core.models import Instance
from channels import Channel, Group
from channels.auth import channel_session_user
from atmosphere.consumers import user_from_token
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)

@channel_session_user
def ws_connect(message):
    """
    Router for all websocket.connect
    """
    logger.info("WebSocket 'push_instances' connect message = %s", message.__dict__)
    return push_connect(message)


@channel_session_user
def ws_disconnect(message):
    """
    Router for websocket.disconnect
    """
    logger.info("WebSocket 'push_instances' disconnect message = %s", message.__dict__)
    return push_disconnect(message)


@channel_session_user
def ws_receive(message):
    """
    Router for all websocket.receive
    """
    logger.info("WebSocket 'push_instances' receive message = %s", message.__dict__)
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    for instance in user.current_instances:
        push_status_history_update(instance.get_last_history())
    return


def push_disconnect(message):
    """
    Remove a group for this user
    """
    user = user_from_token(message)
    if isinstance(user, AnonymousUser):
        return
    for group in Instance.websocket_groups(user):
        logger.info('Discard group: %s' % group.name)
        group.discard(message.reply_channel)
    return


def push_connect(message):
    """
    Create a group for this user
    """
    user = user_from_token(message)
    if not user or isinstance(user, AnonymousUser):
        return
    for group in Instance.websocket_groups(user):
        logger.info('User connected to group: %s-%s' % (user.username,group.name))
        group.add(message.reply_channel)
    return


def ws_push_instance_update(message):
    """
    router for the Channel: push-instance
    (see core/routing.py)
    """
    if 'data' not in message:
        raise ValueError("Bad message: Expected a top-level key 'data' that contains the Actual Message Content to send to the group.")
    if 'resource_id' not in message:
        raise ValueError("Bad message: Expected a top-level key 'resource_id' that tells the listening channel what group to publish your message to.")
    data = message.content['data']
    instance_id = message.content['resource_id']
    group_name = "push-instance-%s" % instance_id
    json_data = json.dumps(data)
    logger.info('WebSocket sending to %s message %s' % (group_name, data))
    Group(group_name).send({
        # WebSockets send either a text or binary payload each frame.
        # We do JSON over the text portion.
        "text": json_data,
    })


def push_status_history_update(new_history):
    """
    Push an instance history update
    Send message to channel 'push-instance'
      (Registered in routing.py)
    to notify listeners of the latest changes

    NOTE: This method is called *EXTERNALLY* from the normal
    channels process.
    """
    instance = new_history.instance
    # Each user has already registered
    # to listen for this message
    # via Instance.websocket_groups(user)
    # FIXME: Isolate to InstanceStatusHistory
    latest_status = new_history.status.name
    new_status = latest_status
    if 'deploying' in latest_status:
        new_status = 'active - deploying'
    elif 'networking' in latest_status:
        new_status = 'active - networking'
    elif 'deploy_error' in latest_status:
        new_status = 'active - deploy_error'
    elif 'build' in latest_status:
        new_status = 'build - scheduling'
    message_data = event_payload(
            "instance_update",
            instance.provider_alias,
            {
                "status": new_status
            }
        )
    return send_channel_message("push-instance", message_data)


def event_payload(event_name, resource_id, data):
    """
    This formalizes the message structure that the *CLIENT* will see
    """
    return {
        "resource_id": resource_id,
        "data": {
            "event": event_name,
            "resource_id": resource_id,
            "payload": data
        }
    }


def send_channel_message(channel_name, message):
    """
    Send a message out on the channel
    channel_name should be listed in routing.py!
    message should be a dict!
    """
    return Channel(channel_name).send(message)
