from django.urls import path, include
from rest_framework.routers import DefaultRouter

# For now, geography will be simple - you can add viewsets later
router = DefaultRouter()

app_name = 'geography'

urlpatterns = [
    path('', include(router.urls)),
]
