from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet,
    NotificationTemplateViewSet,
    NotificationPreferenceViewSet,
    PushTokenViewSet,
    AdminNotificationViewSet
)

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')
router.register(r'push-tokens', PushTokenViewSet, basename='push-token')
router.register(r'admin', AdminNotificationViewSet, basename='admin-notification')

app_name = 'notifications'

urlpatterns = [
    path('', include(router.urls)),
]
