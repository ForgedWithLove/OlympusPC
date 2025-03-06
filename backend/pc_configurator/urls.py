from django.urls import path, include
from . import views


urlpatterns = [
    path('welcome/', views.welcome, name='welcome'),
    path('components/processor/', views.select_processor, name='select_processor'),
    path('components/motherboard/', views.select_motherboard, name='select_motherboard'),
    path('components/videocard/', views.select_videocard, name='select_videocard'),
    path('', views.configurator, name='configurator'),
]