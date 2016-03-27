from channels.routing import include


# channel_routing is the equivalent of 'urlpatterns'
# It allows you to distribute how channels are handled by consumers.
# including optional matching on message attributes.
channel_routing = [
    # Include sub-routing from the core app.
    include("core.routing.websocket_routing", path=r"^/ws/push/instances"),

    # Custom handler for message sending
    # Can't go in the include above as it's not got a `path` attribute to match on.
    include("core.routing.custom_routing"),

    # A default "http.request" route is always inserted by Django at the end of the routing list
    # that routes all unmatched HTTP requests to the Django view system.
]
