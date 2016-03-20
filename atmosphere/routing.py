from . import consumers


channel_routing = {
    "http.request": consumers.http_consumer,
    "websocket.receive": consumers.ws_message,
    "websocket.connect": consumers.ws_connect,
}
