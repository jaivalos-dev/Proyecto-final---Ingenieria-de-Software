from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth URLs
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Empleados URLs
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleado/nuevo/', views.empleado_nuevo, name='empleado_nuevo'),
    path('empleado/editar/<int:pk>/', views.empleado_editar, name='empleado_editar'),
    path('empleado/<int:pk>/', views.empleado_detalle, name='empleado_detalle'),
    path('empleado/eliminar/<int:pk>/', views.empleado_eliminar, name='empleado_eliminar'),
]