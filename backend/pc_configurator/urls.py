from django.urls import path, include
from . import views


urlpatterns = [
    path('welcome/', views.welcome, name='welcome'),
    path('components/processor/', views.select_processor, name='select_processor'),
    path('components/motherboard/', views.select_motherboard, name='select_motherboard'),
    path('components/videocard/', views.select_videocard, name='select_videocard'),
    path('components/memory/', views.select_memory, name='select_memory'),
    path('components/cooler/', views.select_cooler, name='select_cooler'),
    path('components/case/', views.select_case, name='select_case'),
    path('components/disc/', views.select_disc, name='select_disc'),
    path('components/casecooler/', views.select_casecooler, name='select_casecooler'),
    path('components/powersupply/', views.select_powersupply, name='select_powersupply'),
    path('', views.configurator, name='configurator'),
]