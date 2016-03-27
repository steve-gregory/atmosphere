from iplantauth.models import Token


def user_from_token(message):
    """
    FIXME: is atmosphere/consumers the right place for this to live?

    NOTE: For this to work -- it must *FIRST* be hit by ws-connect.
    (The connect message contains query_string in content!)
    All other messages will only have access to 'channel_session'.

    This function uses the same idea as 'session_key=12345'
    but using already-authenticated tokens to verify the author
    of the WebSocket/Troposphere Session.
    """
    if (hasattr(message, 'content') and
            'access_token' in message.content.get('query_string', '')):
        token = message.content['query_string'].replace('access_token=', '')
        message.channel_session['token'] = token
    if 'path' not in message.channel_session and 'path' in message.content:
        message.channel_session['path'] = message.content['path']
    if 'token' not in message.channel_session:
        return None
    user = Token.objects.get(key=message.channel_session['token']).user
    if 'username' not in message.channel_session:
        message.channel_session['username'] = user.username
    return user
