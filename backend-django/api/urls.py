"""Rotas das views já entregues, compatíveis com o frontend original."""

from django.http import JsonResponse
from django.urls import re_path

from api.views.cliente_views import detalhe_cliente, lista_clientes
from api.views.dashboard_views import dashboard
from api.views.vaga_views import detalhe_vaga, lista_vagas


def rota_nao_encontrada(request):
    return JsonResponse({'error': 'Rota da API não encontrada.'}, status=404)


# A dispensa de CSRF é centralizada em estacionamento.middleware.ApiCsrfMiddleware.
# /? aceita POST e PUT com ou sem barra, sem redirecionar ou perder o corpo.
urlpatterns = [
    re_path(r'^clientes/?$', lista_clientes, name='lista_clientes'),
    re_path(r'^clientes/(?P<id>[0-9]+)/?$', detalhe_cliente, name='detalhe_cliente'),
    re_path(r'^vagas/?$', lista_vagas, name='lista_vagas'),
    re_path(r'^vagas/(?P<id>[0-9]+)/?$', detalhe_vaga, name='detalhe_vaga'),
    re_path(r'^dashboard/?$', dashboard, name='dashboard'),
    re_path(r'^.*$', rota_nao_encontrada),
]
