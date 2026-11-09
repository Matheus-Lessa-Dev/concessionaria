from django.contrib import admin
from django.urls import path
from . import permanencia_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/permanencias/', permanencia_views.listar, name='listar_permanencias'),
    path('api/permanencias/entrada/', permanencia_views.entrada, name='registrar_entrada'),
    path('api/permanencias/<int:permanencia_id>/saida/', permanencia_views.saida, name='registrar_saida'),
]
