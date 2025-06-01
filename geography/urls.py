from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AddressViewSet,
    DeliveryZoneViewSet,
    LocationHistoryViewSet,
    DeliveryRouteViewSet,
    ServiceAreaViewSet,
    GeographyUtilsViewSet
)

router = DefaultRouter()
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'delivery-zones', DeliveryZoneViewSet, basename='delivery-zone')
router.register(r'location-history', LocationHistoryViewSet, basename='location-history')
router.register(r'delivery-routes', DeliveryRouteViewSet, basename='delivery-route')
router.register(r'service-areas', ServiceAreaViewSet, basename='service-area')
router.register(r'utils', GeographyUtilsViewSet, basename='geography-utils')

app_name = 'geography'

urlpatterns = [
    path('', include(router.urls)),
]
