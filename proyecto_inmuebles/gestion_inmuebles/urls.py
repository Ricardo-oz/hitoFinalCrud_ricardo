from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('register/', views.registro, name='register'),
    path('mis-inmuebles/', views.mis_inmuebles, name='mis_inmuebles'),
    path('inmuebles/nuevo/', views.crear_inmueble, name='crear_inmueble'),
    path('inmuebles/<int:pk>/editar/', views.editar_inmueble, name='editar_inmueble'),
    path('inmuebles/<int:pk>/eliminar/', views.eliminar_inmueble, name='eliminar_inmueble'),
    path('oferta/', views.oferta, name='oferta'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),
]