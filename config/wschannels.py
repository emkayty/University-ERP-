"""
WebSocket channels routing for real-time features.
"""

from django.urls import re_path

websocket_urlpatterns = [
    # Notifications
    # re_path(r"ws/notifications/$", consumers.NotificationsConsumer.as_asgi()),
    # Chat
    # re_path(r"ws/chat/$", consumers.ChatConsumer.as_asgi()),
    # Presence
    # re_path(r"ws/presence/$", consumers.PresenceConsumer.as_asgi()),
    # Document collaboration
    # re_path(r"ws/documents/(?P<pk>[^/]+)/$", consumers.DocumentCollaborationConsumer.as_asgi()),
]