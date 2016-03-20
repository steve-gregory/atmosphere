from . import consumers


channel_routing = {
    # If 'http.request' is not set -- It will process normally
    #"http.request": consumers.http_consumer,
    "websocket.receive": consumers.ws_refresh_instance,
    "websocket.connect": consumers.ws_connect,
    "websocket.disconnect": consumers.ws_disconnect,
    "instance-push": consumers.ws_push_instance,
}
