from django.urls import path
from . import views, views_nomina
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth URLs
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    
    # Empleados URLs
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('empleados/nuevo/', views.empleado_nuevo, name='empleado_nuevo'),
    path('empleados/<int:pk>/', views.empleado_detalle, name='empleado_detalle'),
    path('empleados/<int:pk>/editar/', views.empleado_editar, name='empleado_editar'),
    path('empleados/<int:pk>/eliminar/', views.empleado_eliminar, name='empleado_eliminar'),

    # Nóminas URLs
    path('nominas/', views_nomina.nomina_list, name='nomina_list'),
    path('nominas/generar/', views_nomina.generar_nomina, name='generar_nomina'),
    path('nominas/procesar/', views_nomina.procesar_nomina, name='procesar_nomina'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/', views_nomina.nomina_detalle, name='nomina_detalle'),
    path('nominas/empleado/<int:nomina_id>/', views_nomina.nomina_empleado, name='nomina_empleado'),

    path('api/puestos/<int:pk>/salario/', views.puesto_salario, name='puesto_salario'),

]