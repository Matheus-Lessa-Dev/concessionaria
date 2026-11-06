from django.urls import re_path

from api.views.veiculo_views import detalhe_veiculo, lista_veiculos


urlpatterns = [
    re_path(r'^veiculos/?$', lista_veiculos, name='lista_veiculos'),
    re_path(r'^veiculos/(?P<veiculo_id>[^/]+)/?$', detalhe_veiculo, name='detalhe_veiculo'),
]
