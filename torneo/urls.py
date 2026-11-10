from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = 'torneo'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path(
        'clasificacion/',
        views.clasificacion,
        name='clasificacion',
    ),
    path('graficas/', views.graficas, name='graficas'),
    path(
        'graficas/torneo/<int:torneo_id>.png',
        views.grafica_torneo,
        name='grafica_torneo',
    ),
    path(
        'graficas/torneo/<int:torneo_id>/victorias.png',
        views.grafica_victorias_torneo,
        name='grafica_victorias_torneo',
    ),
    path(
        'zona/',
        views.zona_participante,
        name='zona_participante',
    ),
    path(
        'registro/',
        views.registro_participante,
        name='registro',
    ),
    path(
        'resultados/nuevo/',
        views.registrar_resultado,
        name='registrar_resultado',
    ),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='torneo/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]