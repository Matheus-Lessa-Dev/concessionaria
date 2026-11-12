"""Integração das entregas pelas URLs reais, com CSRF habilitado no cliente."""

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import re_path, resolve

from api.models import Cliente, Vaga


def prova_csrf(request):
    """View sem csrf_exempt para testar a política do middleware isoladamente."""
    if request.method == 'GET':
        get_token(request)
    return JsonResponse({'metodo': request.method})


# Usadas somente nos testes do middleware, sem substituir as URLs dos demais testes.
urlpatterns = [
    re_path(r'^api/prova-csrf/?$', prova_csrf),
    re_path(r'^fora-api/prova-csrf$', prova_csrf),
    re_path(r'^api-extra/prova-csrf$', prova_csrf),
]


@override_settings(ROOT_URLCONF=__name__)
class MiddlewareCsrfTests(SimpleTestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_api_aceita_escrita_sem_token_e_sem_decorador(self):
        for sufixo in ('', '/'):
            for metodo in ('post', 'put', 'delete'):
                with self.subTest(sufixo=sufixo, metodo=metodo):
                    resposta = getattr(self.client, metodo)(
                        '/api/prova-csrf' + sufixo, {},
                        content_type='application/json',
                        HTTP_ORIGIN='http://localhost:3000',
                    )
                    self.assertEqual(resposta.status_code, 200)
                    self.assertEqual(resposta.json()['metodo'], metodo.upper())
                    self.assertEqual(resposta['Access-Control-Allow-Origin'], '*')

    def test_fora_da_api_exige_csrf_inclusive_prefixos_parecidos(self):
        for rota in ('/fora-api/prova-csrf', '/api-extra/prova-csrf'):
            for metodo in ('post', 'put', 'delete'):
                with self.subTest(rota=rota, metodo=metodo):
                    resposta = getattr(self.client, metodo)(
                        rota, {}, content_type='application/json'
                    )
                    self.assertEqual(resposta.status_code, 403)
                    self.assertEqual(resposta['Access-Control-Allow-Origin'], '*')

    def test_fora_da_api_aceita_token_csrf_valido_sem_sessao(self):
        rota = '/fora-api/prova-csrf'
        self.assertEqual(self.client.get(rota).status_code, 200)
        resposta = self.client.post(
            rota, {}, content_type='application/json',
            HTTP_X_CSRFTOKEN=self.client.cookies['csrftoken'].value,
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('sessionid', resposta.cookies)


class IntegracaoApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def test_rotas_entregues_com_e_sem_barra(self):
        rotas = {
            '/api/clientes': 'lista_clientes',
            '/api/clientes/1': 'detalhe_cliente',
            '/api/vagas': 'lista_vagas',
            '/api/vagas/1': 'detalhe_vaga',
            '/api/dashboard': 'dashboard',
        }
        for rota, nome in rotas.items():
            for sufixo in ('', '/'):
                with self.subTest(rota=rota + sufixo):
                    self.assertEqual(resolve(rota + sufixo).url_name, nome)

    def test_clientes_post_put_delete_sem_redirecionamento(self):
        for indice, sufixo in enumerate(('', '/')):
            with self.subTest(sufixo=sufixo):
                dados = {'nome': 'Cliente integração', 'cpf': f'0000000000{indice}'}
                resposta = self.client.post(
                    '/api/clientes' + sufixo, dados, content_type='application/json'
                )
                self.assertEqual(resposta.status_code, 201)
                self.assertNotIn('Location', resposta)
                detalhe = f'/api/clientes/{resposta.json()["id"]}' + sufixo
                dados['nome'] = 'Nome atualizado'
                resposta = self.client.put(detalhe, dados, content_type='application/json')
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(self.client.get(detalhe).json()['nome'], dados['nome'])
                self.assertEqual(self.client.delete(detalhe).status_code, 204)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_vagas_e_dashboard_usam_o_mesmo_banco(self):
        for indice, sufixo in enumerate(('', '/')):
            with self.subTest(sufixo=sufixo):
                resposta = self.client.post(
                    '/api/vagas' + sufixo,
                    {'numero': f'T{indice}', 'tipo': 'CARRO'},
                    content_type='application/json',
                )
                self.assertEqual(resposta.status_code, 201)
                detalhe = f'/api/vagas/{resposta.json()["id"]}' + sufixo
                resposta = self.client.put(
                    detalhe, {'numero': f'T{indice}', 'tipo': 'CARRO', 'status': 'OCUPADA'},
                    content_type='application/json',
                )
                self.assertEqual(resposta.status_code, 200)
                self.assertEqual(self.client.get('/api/vagas?status=LIVRE').json(), [])
                self.assertEqual(self.client.get('/api/dashboard' + sufixo).json(), {
                    'totalVagas': 1, 'vagasLivres': 0,
                    'vagasOcupadas': 1, 'veiculosEstacionados': 0,
                })
                self.assertEqual(self.client.delete(detalhe).status_code, 200)
        self.assertEqual(Vaga.objects.count(), 0)

    def test_preflight_cors_sem_csrf_e_sem_escrita(self):
        for rota in ('/api/clientes', '/api/vagas/', '/api/permanencias/entrada'):
            with self.subTest(rota=rota):
                resposta = self.client.options(
                    rota, HTTP_ORIGIN='http://localhost:3000',
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                    HTTP_ACCESS_CONTROL_REQUEST_HEADERS='Content-Type',
                )
                self.assertEqual(resposta.status_code, 204)
                self.assertEqual(resposta.content, b'')
                self.assertEqual(resposta['Access-Control-Allow-Origin'], '*')
                self.assertEqual(resposta['Access-Control-Allow-Headers'], 'Content-Type')
                for metodo in ('GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'):
                    self.assertIn(metodo, resposta['Access-Control-Allow-Methods'])
        self.assertEqual(Cliente.objects.count(), 0)
        self.assertEqual(Vaga.objects.count(), 0)

    def test_cors_presente_em_respostas_de_sucesso_e_erro(self):
        respostas = [
            (self.client.get('/api/dashboard'), 200),
            (self.client.get('/api/clientes/999'), 404),
            (self.client.post('/api/vagas', '{', content_type='application/json'), 400),
            (self.client.delete('/api/vagas'), 405),
        ]
        for resposta, status in respostas:
            with self.subTest(status=status):
                self.assertEqual(resposta.status_code, status)
                self.assertEqual(resposta['Access-Control-Allow-Origin'], '*')
                if status >= 400:
                    self.assertIn('error', resposta.json())

    def test_rota_desconhecida_retorna_404_json(self):
        resposta = self.client.post('/api/inexistente', {}, content_type='application/json')
        self.assertEqual(resposta.status_code, 404)
        self.assertIn('error', resposta.json())

    def test_rotas_de_admin_e_login_nao_estao_disponiveis(self):
        for rota in ('/admin/', '/admin/login/', '/accounts/login/'):
            with self.subTest(rota=rota):
                self.assertEqual(self.client.get(rota).status_code, 404)

    def test_api_nao_utiliza_sessoes_nem_autenticacao(self):
        resposta = self.client.get('/api/dashboard')
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(hasattr(resposta.wsgi_request, 'session'))
        self.assertFalse(hasattr(resposta.wsgi_request, 'user'))
        self.assertNotIn('sessionid', resposta.cookies)
