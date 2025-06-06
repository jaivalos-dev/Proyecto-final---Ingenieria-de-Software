from django.urls import path
from . import views, views_nomina, views_prestaciones, views_vacaciones, views_liquidaciones
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
    path('nominas/empleado/<int:nomina_id>/', views_nomina.nomina_empleado, name='nomina_empleado'),
    path('nominas/', views_nomina.nomina_list, name='nomina_list'),
    path('nominas/generar/', views_nomina.generar_nomina, name='generar_nomina'),
    path('nominas/procesar/', views_nomina.procesar_nomina, name='procesar_nomina'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/', views_nomina.nomina_detalle, name='nomina_detalle'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/eliminar/', views_nomina.eliminar_nomina, name='eliminar_nomina'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/reporte/', views_nomina.generar_reporte_nomina_pdf, name='generar_reporte_nomina_pdf'),
    path('api/puestos/<int:pk>/salario/', views.puesto_salario, name='puesto_salario'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/pagar/', views_nomina.pagar_nomina, name='pagar_nomina'),
    path('nominas/<str:fecha_generacion>/<int:tipo_nomina_id>/cancelar/', views_nomina.cancelar_nomina, name='cancelar_nomina'),
    
    # Prestaciones URLs
    path('prestaciones/', views_prestaciones.prestaciones_list, name='prestaciones_list'),
    path('prestaciones/calcular/', views_prestaciones.calcular_prestacion, name='calcular_prestacion'),
    path('prestaciones/<int:pk>/', views_prestaciones.prestacion_detalle, name='prestacion_detalle'),
    path('prestaciones/<int:pk>/pagar/', views_prestaciones.pagar_prestacion, name='pagar_prestacion'),
    path('prestaciones/<int:pk>/cancelar/', views_prestaciones.cancelar_prestacion, name='cancelar_prestacion'),
    path('prestaciones/<int:pk>/recalcular/', views_prestaciones.recalcular_prestacion, name='recalcular_prestacion'),
    path('prestaciones/<int:pk>/eliminar/', views_prestaciones.eliminar_prestacion, name='eliminar_prestacion'),

    # Vacaciones URLs
    path('vacaciones/', views_vacaciones.vacaciones_list, name='vacaciones_list'),
    path('vacaciones/actualizar/<int:vacaciones_id>/', views_vacaciones.actualizar_vacaciones, name='actualizar_vacaciones'),   
    
    # Liquidaciones URLs
    path('liquidaciones/', views_liquidaciones.liquidaciones_list, name='liquidaciones_list'),
    path('liquidaciones/calcular/', views_liquidaciones.calcular_liquidacion, name='calcular_liquidacion'),
    path('liquidaciones/<int:pk>/', views_liquidaciones.liquidacion_detalle, name='liquidacion_detalle'),
    path('liquidaciones/<int:pk>/pagar/', views_liquidaciones.pagar_liquidacion, name='pagar_liquidacion'),
    path('liquidaciones/<int:pk>/eliminar/', views_liquidaciones.eliminar_liquidacion, name='eliminar_liquidacion'),

]