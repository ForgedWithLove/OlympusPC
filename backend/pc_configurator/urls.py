from django.urls import path, include
from . import views


urlpatterns = [
    path('welcome/', views.welcome, name='welcome'),
    path('components/processor/', views.select_processor, name='select_processor'),
    path('components/motherboard/', views.select_motherboard, name='select_motherboard'),
    path('components/videocard/', views.select_videocard, name='select_videocard'),
    path('components/memory/', views.select_memory, name='select_memory'),
    path('components/cooler/', views.select_cooler, name='select_cooler'),
    path('', views.configurator, name='configurator'),
]