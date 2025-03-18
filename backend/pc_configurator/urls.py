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
    path('components/add/processor', views.add_processor, name='add_processor'),
    path('components/add/motherboard', views.add_motherboard, name='add_motherboard'),
    path('components/add/videocard', views.add_videocard, name='add_videocard'),
    path('components/add/memory', views.add_memory, name='add_memory'),
    path('components/add/cooler', views.add_cooler, name='add_cooler'),
    path('components/add/case', views.add_case, name='add_case'),
    path('components/add/disc', views.add_disc, name='add_disc'),
    path('components/add/casecooler', views.add_casecooler, name='add_casecooler'),
    path('components/add/powersupply', views.add_powersupply, name='add_powersupply'),
    path('components/delete/disc', views.delete_disc, name='delete_disc'),
    path('components/delete/casecooler', views.delete_casecooler, name='del_casecooler'),
    path('components/dec/casecooler', views.dec_casecooler, name='dec_casecooler'),
    path('components/inc/casecooler', views.inc_casecooler, name='inc_casecooler'),
    path("register/", views.register_request, name="register"),
    path("login/", views.login_request, name="login"),
    path("logout/", views.logout_request, name="logout"),
    path("convert/", views.convert_request, name="guest_to_user"),
    path('assemble/', views.assemble, name='assemble'),
]