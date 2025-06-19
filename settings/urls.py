from django.urls import path
from . import views

urlpatterns = [
    path('public/', views.public_settings, name='public_settings'),
    path('', views.get_settings, name='get_settings'),
    path('update/', views.update_settings, name='update_settings'),
]