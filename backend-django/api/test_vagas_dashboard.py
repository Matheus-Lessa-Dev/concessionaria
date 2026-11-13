import json

from django.test import Client, TransactionTestCase, override_settings
from django.urls import re_path

from api.models import Cliente, Permanencia, Vaga, Veiculo
from api.views.dashboard_views import dashboard
from api.views.vaga_views import detalhe_vaga, lista_vagas, vaga_to_dict

# Rotas próprias dos testes: valem mesmo antes de o urls.py do projeto
# registrar as rotas da API.
urlpatterns = [
    re_path(r'^api/dashboard/?$', dashboard),
    re_path(r'^api/vagas/?$', lista_vagas),
    re_path(r'^api/vagas/(?P<id>\d+)/?$', detalhe_vaga),
]

CAMPOS_DASHBOARD = [
    'totalVagas',
    'vagasLivres',
    'vagasOcupadas',
    'veiculosEstacionados',
]


@override_settings(ROOT_URLCONF=__name__)
class BaseApiTest(TransactionTestCase):
    """Cliente com CSRF ligado: garante que @csrf_exempt funciona."""

    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def enviar(self, metodo, url, dados=None, bruto=None):
        if bruto is None:
            bruto = json.dumps(dados if dados is not None else {})
        return getattr(self.client, metodo)(
            url, bruto, content_type='application/json'
        )

    def corpo(self, resposta):
        return json.loads(resposta.content)

    def criar_vaga(self, numero='A1', tipo='CARRO', status='LIVRE'):
        return Vaga.objects.create(numero=numero, tipo=tipo, status=status)

    def criar_permanencia(self, vaga, status='ABERTO'):
        cliente, _ = Cliente.objects.get_or_create(
            cpf='000.000.000-00', defaults={'nome': 'Cliente Teste'}
        )
        veiculo, _ = Veiculo.objects.get_or_create(
            placa='TST0001',
            defaults={
                'marca': 'Marca',
                'modelo': 'Modelo',
                'cor': 'Preto',
                'cliente': cliente,
            },
        )
        return Permanencia.objects.create(
            veiculo=veiculo, vaga=vaga, status=status
        )


class VagaToDictTests(BaseApiTest):

    def test_retorna_somente_os_campos_do_frontend(self):
        vaga = self.criar_vaga('A1', 'MOTO', 'OCUPADA')
        self.assertEqual(
            vaga_to_dict(vaga),
            {'id': vaga.id, 'numero': 'A1', 'tipo': 'MOTO', 'status': 'OCUPADA'},
        )


class ListaVagasGetTests(BaseApiTest):

    def test_lista_vazia(self):
        r = self.client.get('/api/vagas')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.corpo(r), [])

    def test_ordena_pelo_numero(self):
        self.criar_vaga('B2')
        self.criar_vaga('A1')
        self.criar_vaga('C3')
        r = self.client.get('/api/vagas')
        self.assertEqual(
            [v['numero'] for v in self.corpo(r)], ['A1', 'B2', 'C3']
        )

    def test_filtra_por_status(self):
        self.criar_vaga('A1', status='LIVRE')
        self.criar_vaga('A2', status='OCUPADA')
        livres = self.corpo(self.client.get('/api/vagas?status=LIVRE'))
        ocupadas = self.corpo(self.client.get('/api/vagas?status=OCUPADA'))
        self.assertEqual([v['numero'] for v in livres], ['A1'])
        self.assertEqual([v['numero'] for v in ocupadas], ['A2'])

    def test_formato_dos_campos(self):
        self.criar_vaga('A1', 'MOTO')
        vaga = self.corpo(self.client.get('/api/vagas'))[0]
        self.assertEqual(set(vaga), {'id', 'numero', 'tipo', 'status'})
        self.assertEqual(vaga['tipo'], 'MOTO')

    def test_barra_final_tambem_funciona(self):
        self.assertEqual(self.client.get('/api/vagas/').status_code, 200)

    def test_metodo_nao_permitido(self):
        r = self.client.delete('/api/vagas')
        self.assertEqual(r.status_code, 405)
        self.assertIn('error', self.corpo(r))


class ListaVagasPostTests(BaseApiTest):

    def test_cria_vaga_livre(self):
        r = self.enviar('post', '/api/vagas', {'numero': 'A1', 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 201)
        corpo = self.corpo(r)
        self.assertEqual(corpo['numero'], 'A1')
        self.assertEqual(corpo['status'], 'LIVRE')
        self.assertTrue(Vaga.objects.filter(id=corpo['id']).exists())

    def test_vaga_sempre_nasce_livre(self):
        r = self.enviar(
            'post', '/api/vagas',
            {'numero': 'A1', 'tipo': 'CARRO', 'status': 'OCUPADA'},
        )
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.corpo(r)['status'], 'LIVRE')

    def test_status_null_ou_ausente_e_aceito(self):
        r1 = self.enviar(
            'post', '/api/vagas',
            {'numero': 'A1', 'tipo': 'CARRO', 'status': None},
        )
        r2 = self.enviar('post', '/api/vagas', {'numero': 'A2', 'tipo': 'CARRO'})
        self.assertEqual((r1.status_code, r2.status_code), (201, 201))

    def test_remove_espacos_do_numero(self):
        r = self.enviar('post', '/api/vagas', {'numero': '  A1  ', 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(self.corpo(r)['numero'], 'A1')

    def test_numero_com_10_caracteres_e_aceito(self):
        r = self.enviar('post', '/api/vagas', {'numero': 'A' * 10, 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 201)

    def test_numero_com_11_caracteres_e_recusado(self):
        r = self.enviar('post', '/api/vagas', {'numero': 'A' * 11, 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(Vaga.objects.count(), 0)

    def test_numero_obrigatorio(self):
        casos = [
            {'tipo': 'CARRO'},
            {'numero': '', 'tipo': 'CARRO'},
            {'numero': '   ', 'tipo': 'CARRO'},
            {'numero': None, 'tipo': 'CARRO'},
            {'numero': 123, 'tipo': 'CARRO'},
        ]
        for dados in casos:
            with self.subTest(dados=dados):
                r = self.enviar('post', '/api/vagas', dados)
                self.assertEqual(r.status_code, 400)
                self.assertIn("'numero'", self.corpo(r)['error'])
        self.assertEqual(Vaga.objects.count(), 0)

    def test_tipo_deve_ser_carro_ou_moto(self):
        casos = [None, '', 'BIKE', 'carro', 'Moto', 1]
        for tipo in casos:
            with self.subTest(tipo=tipo):
                dados = {'numero': 'A1'}
                if tipo is not None:
                    dados['tipo'] = tipo
                r = self.enviar('post', '/api/vagas', dados)
                self.assertEqual(r.status_code, 400)
                self.assertIn("'tipo'", self.corpo(r)['error'])
        self.assertEqual(Vaga.objects.count(), 0)

    def test_aceita_carro_e_moto(self):
        for i, tipo in enumerate(['CARRO', 'MOTO']):
            r = self.enviar('post', '/api/vagas', {'numero': f'A{i}', 'tipo': tipo})
            self.assertEqual(r.status_code, 201)

    def test_status_invalido_e_recusado(self):
        for status in ['XYZ', '', 'livre', 123]:
            with self.subTest(status=status):
                r = self.enviar(
                    'post', '/api/vagas',
                    {'numero': 'A1', 'tipo': 'CARRO', 'status': status},
                )
                self.assertEqual(r.status_code, 400)
                self.assertIn("'status'", self.corpo(r)['error'])
        self.assertEqual(Vaga.objects.count(), 0)

    def test_corpo_invalido(self):
        casos = [b'{quebrado', b'[]', b'null', b'"texto"', b'123', b'\xff\xfe{']
        for bruto in casos:
            with self.subTest(bruto=bruto):
                r = self.enviar('post', '/api/vagas', bruto=bruto)
                self.assertEqual(r.status_code, 400)
                self.assertIn('error', self.corpo(r))

    def test_numero_duplicado_retorna_409(self):
        self.criar_vaga('A1')
        r = self.enviar('post', '/api/vagas', {'numero': 'A1', 'tipo': 'MOTO'})
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.corpo(r)['error'], 'Número de vaga já cadastrado')
        self.assertEqual(Vaga.objects.filter(numero='A1').count(), 1)

    def test_numero_duplicado_com_espacos_retorna_409(self):
        self.criar_vaga('A1')
        r = self.enviar('post', '/api/vagas', {'numero': ' A1 ', 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 409)

    def test_sistema_continua_funcionando_apos_erro(self):
        self.enviar('post', '/api/vagas', {'numero': 'A1'})
        r = self.enviar('post', '/api/vagas', {'numero': 'A1', 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 201)


class DetalheVagaGetTests(BaseApiTest):

    def test_busca_vaga_existente(self):
        vaga = self.criar_vaga('A1', 'MOTO')
        r = self.client.get(f'/api/vagas/{vaga.id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.corpo(r), vaga_to_dict(vaga))

    def test_vaga_inexistente_retorna_404(self):
        r = self.client.get('/api/vagas/99999')
        self.assertEqual(r.status_code, 404)
        self.assertEqual(self.corpo(r)['error'], 'Vaga não encontrada')

    def test_barra_final_tambem_funciona(self):
        vaga = self.criar_vaga()
        self.assertEqual(self.client.get(f'/api/vagas/{vaga.id}/').status_code, 200)

    def test_metodo_nao_permitido(self):
        vaga = self.criar_vaga()
        r = self.enviar('post', f'/api/vagas/{vaga.id}', {})
        self.assertEqual(r.status_code, 405)


class DetalheVagaPutTests(BaseApiTest):

    def test_atualiza_vaga(self):
        vaga = self.criar_vaga('A1', 'CARRO')
        r = self.enviar(
            'put', f'/api/vagas/{vaga.id}',
            {'numero': 'B2', 'tipo': 'MOTO', 'status': 'OCUPADA'},
        )
        self.assertEqual(r.status_code, 200)
        vaga.refresh_from_db()
        self.assertEqual((vaga.numero, vaga.tipo, vaga.status), ('B2', 'MOTO', 'OCUPADA'))
        self.assertEqual(self.corpo(r), vaga_to_dict(vaga))

    def test_remove_espacos_do_numero(self):
        vaga = self.criar_vaga('A1')
        r = self.enviar(
            'put', f'/api/vagas/{vaga.id}', {'numero': ' B2 ', 'tipo': 'CARRO'}
        )
        self.assertEqual(self.corpo(r)['numero'], 'B2')

    def test_status_ausente_ou_null_preserva_o_atual(self):
        vaga = self.criar_vaga('A1', status='OCUPADA')
        for extra in [{}, {'status': None}]:
            with self.subTest(extra=extra):
                vaga.status = 'OCUPADA'
                vaga.save()
                r = self.enviar(
                    'put', f'/api/vagas/{vaga.id}',
                    {'numero': 'A1', 'tipo': 'CARRO', **extra},
                )
                self.assertEqual(r.status_code, 200)
                self.assertEqual(self.corpo(r)['status'], 'OCUPADA')

    def test_status_invalido_retorna_400_e_nao_altera(self):
        vaga = self.criar_vaga('A1', status='OCUPADA')
        for status in ['XYZ', '', 'ocupada']:
            with self.subTest(status=status):
                r = self.enviar(
                    'put', f'/api/vagas/{vaga.id}',
                    {'numero': 'A1', 'tipo': 'CARRO', 'status': status},
                )
                self.assertEqual(r.status_code, 400)
        vaga.refresh_from_db()
        self.assertEqual(vaga.status, 'OCUPADA')

    def test_validacoes_de_numero_e_tipo(self):
        vaga = self.criar_vaga('A1')
        casos = [
            {'tipo': 'CARRO'},
            {'numero': '   ', 'tipo': 'CARRO'},
            {'numero': 'A' * 11, 'tipo': 'CARRO'},
            {'numero': 'A1', 'tipo': 'BIKE'},
            {'numero': 'A1'},
        ]
        for dados in casos:
            with self.subTest(dados=dados):
                r = self.enviar('put', f'/api/vagas/{vaga.id}', dados)
                self.assertEqual(r.status_code, 400)
        vaga.refresh_from_db()
        self.assertEqual((vaga.numero, vaga.tipo), ('A1', 'CARRO'))

    def test_corpo_invalido(self):
        vaga = self.criar_vaga()
        for bruto in [b'{quebrado', b'[]', b'null', b'\xff\xfe{']:
            with self.subTest(bruto=bruto):
                r = self.enviar('put', f'/api/vagas/{vaga.id}', bruto=bruto)
                self.assertEqual(r.status_code, 400)

    def test_vaga_inexistente_retorna_404(self):
        r = self.enviar('put', '/api/vagas/99999', {'numero': 'A1', 'tipo': 'CARRO'})
        self.assertEqual(r.status_code, 404)

    def test_numero_de_outra_vaga_retorna_409_e_nao_altera(self):
        self.criar_vaga('A1')
        outra = self.criar_vaga('B2')
        r = self.enviar(
            'put', f'/api/vagas/{outra.id}', {'numero': 'A1', 'tipo': 'CARRO'}
        )
        self.assertEqual(r.status_code, 409)
        self.assertEqual(self.corpo(r)['error'], 'Número de vaga já cadastrado')
        outra.refresh_from_db()
        self.assertEqual(outra.numero, 'B2')

    def test_manter_o_proprio_numero_nao_e_duplicidade(self):
        vaga = self.criar_vaga('A1', 'CARRO')
        r = self.enviar(
            'put', f'/api/vagas/{vaga.id}', {'numero': 'A1', 'tipo': 'MOTO'}
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.corpo(r)['tipo'], 'MOTO')


class DetalheVagaDeleteTests(BaseApiTest):

    def test_exclui_vaga(self):
        vaga = self.criar_vaga()
        r = self.client.delete(f'/api/vagas/{vaga.id}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.corpo(r), {'message': 'Vaga excluída com sucesso'})
        self.assertFalse(Vaga.objects.filter(id=vaga.id).exists())

    def test_vaga_inexistente_retorna_404(self):
        r = self.client.delete('/api/vagas/99999')
        self.assertEqual(r.status_code, 404)

    def test_excluir_duas_vezes_retorna_404_na_segunda(self):
        vaga = self.criar_vaga()
        self.client.delete(f'/api/vagas/{vaga.id}')
        r = self.client.delete(f'/api/vagas/{vaga.id}')
        self.assertEqual(r.status_code, 404)

    def test_bloqueada_por_permanencia_retorna_409(self):
        for status in ['ABERTO', 'FINALIZADO']:
            with self.subTest(status=status):
                vaga = self.criar_vaga(f'P-{status[:3]}')
                self.criar_permanencia(vaga, status)
                r = self.client.delete(f'/api/vagas/{vaga.id}')
                self.assertEqual(r.status_code, 409)
                self.assertEqual(
                    self.corpo(r)['error'],
                    'Não é possível excluir vaga com permanências registradas',
                )
                self.assertTrue(Vaga.objects.filter(id=vaga.id).exists())

    def test_exclui_depois_de_remover_a_permanencia(self):
        vaga = self.criar_vaga()
        permanencia = self.criar_permanencia(vaga)
        self.assertEqual(self.client.delete(f'/api/vagas/{vaga.id}').status_code, 409)
        permanencia.delete()
        self.assertEqual(self.client.delete(f'/api/vagas/{vaga.id}').status_code, 200)


class DashboardTests(BaseApiTest):

    def ler(self):
        r = self.client.get('/api/dashboard')
        self.assertEqual(r.status_code, 200)
        return self.corpo(r)

    def test_tabela_vazia_retorna_zeros(self):
        dados = self.ler()
        self.assertEqual(dados, {campo: 0 for campo in CAMPOS_DASHBOARD})

    def test_campos_na_ordem_do_java(self):
        r = self.client.get('/api/dashboard')
        self.assertEqual(list(self.corpo(r)), CAMPOS_DASHBOARD)
        self.assertEqual(r['Content-Type'], 'application/json')

    def test_conta_vagas_por_status(self):
        for i in range(3):
            self.criar_vaga(f'L{i}', status='LIVRE')
        for i in range(2):
            self.criar_vaga(f'O{i}', status='OCUPADA')
        dados = self.ler()
        self.assertEqual(dados['totalVagas'], 5)
        self.assertEqual(dados['vagasLivres'], 3)
        self.assertEqual(dados['vagasOcupadas'], 2)
        self.assertEqual(
            dados['vagasLivres'] + dados['vagasOcupadas'], dados['totalVagas']
        )

    def test_so_permanencias_abertas_contam(self):
        # 2 abertas e 1 finalizada: so o filtro correto resulta em 2
        for i in range(2):
            self.criar_permanencia(
                self.criar_vaga(f'A{i}', status='OCUPADA'), 'ABERTO'
            )
        self.criar_permanencia(self.criar_vaga('F1'), 'FINALIZADO')
        self.assertEqual(self.ler()['veiculosEstacionados'], 2)

    def test_acompanha_alteracoes_feitas_pela_api(self):
        v1 = self.criar_vaga('A1')
        self.criar_vaga('A2')
        self.assertEqual(self.ler()['vagasLivres'], 2)

        self.enviar(
            'put', f'/api/vagas/{v1.id}',
            {'numero': 'A1', 'tipo': 'CARRO', 'status': 'OCUPADA'},
        )
        dados = self.ler()
        self.assertEqual((dados['vagasLivres'], dados['vagasOcupadas']), (1, 1))

        self.client.delete(f'/api/vagas/{v1.id}')
        dados = self.ler()
        self.assertEqual((dados['totalVagas'], dados['vagasOcupadas']), (1, 0))

        self.enviar('post', '/api/vagas', {'numero': 'A3', 'tipo': 'MOTO'})
        self.assertEqual(self.ler()['totalVagas'], 2)

    def test_barra_final_tambem_funciona(self):
        self.assertEqual(self.client.get('/api/dashboard/').status_code, 200)

    def test_metodos_diferentes_de_get_retornam_405(self):
        for metodo in ['post', 'put', 'delete']:
            with self.subTest(metodo=metodo):
                r = self.enviar(metodo, '/api/dashboard', {})
                self.assertEqual(r.status_code, 405)
                self.assertIn('error', self.corpo(r))
