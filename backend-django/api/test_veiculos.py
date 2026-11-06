from django.test import Client, TestCase, override_settings
from django.urls import include, path

from api.models import Cliente, Permanencia, Vaga, Veiculo


urlpatterns = [path('api/', include('api.veiculo_urls'))]


@override_settings(ROOT_URLCONF=__name__)
class VeiculoTests(TestCase):
    url = '/api/veiculos'

    def setUp(self):
        self.cliente = Cliente.objects.create(nome='Ana', cpf='12345678900')
        self.dados = {
            'placa': 'ABC-1234',
            'marca': 'Toyota',
            'modelo': 'Corolla',
            'cor': 'Branco',
            'clienteId': self.cliente.pk,
        }
        self.client = Client(enforce_csrf_checks=True)

    def cadastrar(self, **alteracoes):
        return self.client.post(
            self.url, self.dados | alteracoes, content_type='application/json'
        )

    def _url_detalhe(self, veiculo_id):
        return f'{self.url}/{veiculo_id}'

    def test_crud_e_contrato_json(self):
        cadastro = self.cadastrar()
        self.assertEqual(cadastro.status_code, 201)
        veiculo_id = cadastro.json()['id']
        esperado = self.dados | {'id': veiculo_id, 'clienteNome': 'Ana'}
        detalhe = self._url_detalhe(veiculo_id)
        self.assertEqual(cadastro.json(), esperado)
        self.assertEqual(self.client.get(f'{detalhe}/').json(), esperado)
        self.assertEqual(self.client.get(f'{self.url}/').json(), [esperado])

        outro_cliente = Cliente.objects.create(nome='Bruno', cpf='12345678901')
        dados_editados = self.dados | {'cor': 'Azul', 'clienteId': outro_cliente.pk}
        edicao = self.client.put(detalhe, dados_editados, content_type='application/json')
        self.assertEqual(edicao.status_code, 200)
        self.assertEqual(
            edicao.json(), dados_editados | {'id': veiculo_id, 'clienteNome': 'Bruno'}
        )
        self.assertEqual(self.client.get(detalhe).json(), edicao.json())

        exclusao = self.client.delete(detalhe)
        self.assertEqual(exclusao.status_code, 200)
        self.assertEqual(exclusao.json(), {'message': 'Veículo excluído com sucesso'})
        self.assertEqual(self.client.get(detalhe).status_code, 404)

    def test_listagem_ordenada_e_cliente_carregado_na_mesma_consulta(self):
        self.cadastrar(placa='ZZZ-9999')
        self.cadastrar()
        with self.assertNumQueries(1):
            resposta = self.client.get(self.url)
        self.assertEqual([v['placa'] for v in resposta.json()], ['ABC-1234', 'ZZZ-9999'])

    def test_validacao_do_corpo(self):
        for corpo in ('', '{', '[]', 'null'):
            with self.subTest(corpo=corpo):
                resposta = self.client.post(self.url, corpo, content_type='application/json')
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('error', resposta.json())

        for campo, valor in (
            ('placa', '   '),
            ('placa', 'A' * 11),
            ('marca', 'A' * 51),
            ('modelo', 'A' * 51),
            ('cor', 'A' * 31),
            ('cor', 10),
            ('clienteId', None),
            ('clienteId', True),
            ('clienteId', -1),
            ('clienteId', 2**63),
        ):
            with self.subTest(campo=campo, valor=valor):
                resposta = self.cadastrar(**{campo: valor})
                self.assertEqual(resposta.status_code, 400)
                self.assertIn('error', resposta.json())
        self.assertFalse(Veiculo.objects.exists())

    def test_cliente_ou_veiculo_inexistente(self):
        inexistente = self.cliente.pk + 1
        self.assertEqual(self.cadastrar(clienteId=inexistente).status_code, 404)
        detalhe = self._url_detalhe(inexistente)
        self.assertEqual(self.client.get(detalhe).status_code, 404)
        self.assertEqual(self.client.delete(detalhe).status_code, 404)
        resposta = self.client.put(detalhe, self.dados, content_type='application/json')
        self.assertEqual(resposta.status_code, 404)
        self.assertEqual(self.client.get(f'{self.url}/abc').status_code, 400)

    def test_placa_duplicada_no_cadastro_e_na_edicao(self):
        self.assertEqual(self.cadastrar().status_code, 201)
        self.assertEqual(self.cadastrar().status_code, 409)
        outro = self.cadastrar(placa='DEF-5678').json()
        detalhe = self._url_detalhe(outro['id'])
        resposta = self.client.put(detalhe, self.dados, content_type='application/json')
        self.assertEqual(resposta.status_code, 409)
        self.assertEqual(self.client.get(detalhe).json()['placa'], 'DEF-5678')

    def test_permanencia_protege_exclusao(self):
        cadastro = self.cadastrar()
        veiculo_id = cadastro.json()['id']
        vaga = Vaga.objects.create(numero='A01', tipo='CARRO')
        Permanencia.objects.create(veiculo_id=veiculo_id, vaga=vaga, status='FINALIZADO')
        resposta = self.client.delete(self._url_detalhe(veiculo_id))
        self.assertEqual(resposta.status_code, 409)
        self.assertIn('error', resposta.json())
        self.assertTrue(Veiculo.objects.filter(pk=veiculo_id).exists())

    def test_metodos_e_cors(self):
        resposta = self.client.patch(self.url)
        self.assertEqual(resposta.status_code, 405)
        self.assertEqual(resposta['Allow'], 'GET, POST, OPTIONS')
        self.assertEqual(resposta['Access-Control-Allow-Origin'], '*')

        resposta = self.client.options(self.url)
        self.assertEqual(resposta.status_code, 204)
        self.assertIn('POST', resposta['Access-Control-Allow-Methods'])
        self.assertIn('Content-Type', resposta['Access-Control-Allow-Headers'])
