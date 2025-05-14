
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rrhh.urls')),  # Incluimos las URLs de la aplicación rrhh
]