from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DriverLocationViewSet,
    DriverAvailabilityViewSet,
    DriverTaskViewSet,
    DriverEarningViewSet
)

router = DefaultRouter()
router.register(r'locations', DriverLocationViewSet, basename='driver-location')
router.register(r'availability', DriverAvailabilityViewSet, basename='driver-availability')
router.register(r'tasks', DriverTaskViewSet, basename='driver-task')
router.register(r'earnings', DriverEarningViewSet, basename='driver-earning')

app_name = 'drivers'

urlpatterns = [
    path('', include(router.urls)),
]