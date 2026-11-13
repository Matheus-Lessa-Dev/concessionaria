"""Fluxo integrado pelo contrato do frontend e regressões das entregas finais."""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import Client, TestCase

from api.models import Cliente, Permanencia, Vaga, Veiculo
from api.services.permanencia_service import registrar_entrada, registrar_saida


class FluxoCompletoTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def enviar(self, metodo, rota, dados, status):
        resposta = getattr(self.client, metodo)(
            rota, dados, content_type='application/json'
        )
        self.assertEqual(resposta.status_code, status, resposta.content)
        self.assertNotIn('Location', resposta)
        return resposta.json()

    def cadastrar(self, sufixo=''):
        cliente = self.enviar('post', '/api/clientes' + sufixo, {
            'nome': 'Cliente integração', 'cpf': '00000000000',
        }, 201)
        veiculo = self.enviar('post', '/api/veiculos' + sufixo, {
            'placa': 'TST-0001', 'marca': 'Fiat', 'modelo': 'Uno',
            'cor': 'Branco', 'clienteId': cliente['id'],
        }, 201)
        vaga = self.enviar('post', '/api/vagas' + sufixo, {
            'numero': 'QA01', 'tipo': 'CARRO',
        }, 201)
        return cliente, veiculo, vaga

    def dashboard(self, livres, ocupadas, estacionados, sufixo=''):
        self.assertEqual(self.client.get('/api/dashboard' + sufixo).json(), {
            'totalVagas': livres + ocupadas, 'vagasLivres': livres,
            'vagasOcupadas': ocupadas, 'veiculosEstacionados': estacionados,
        })

    def executar_fluxo(self, sufixo, minutos, valor):
        cliente, veiculo, vaga = self.cadastrar(sufixo)
        self.dashboard(1, 0, 0, sufixo)
        entrada = '/api/permanencias/entrada' + sufixo
        dados = {'veiculoId': veiculo['id'], 'vagaId': vaga['id']}
        permanencia = self.enviar('post', entrada, dados, 201)
        self.assertEqual(permanencia['veiculoPlaca'], veiculo['placa'])
        self.assertEqual(permanencia['veiculoModelo'], veiculo['modelo'])
        self.assertEqual(permanencia['vagaNumero'], vaga['numero'])
        self.assertEqual(permanencia['status'], 'ABERTO')
        self.assertIsNone(permanencia['valorTotal'])
        self.dashboard(0, 1, 1, sufixo)
        self.assertEqual(self.client.get('/api/vagas?status=LIVRE').json(), [])
        self.assertIn('error', self.enviar('post', entrada, dados, 409))

        outra_vaga = self.enviar('post', '/api/vagas' + sufixo, {
            'numero': 'QA02', 'tipo': 'CARRO',
        }, 201)
        self.enviar('post', entrada, dados | {'vagaId': outra_vaga['id']}, 409)
        outro_veiculo = self.enviar('post', '/api/veiculos' + sufixo, {
            'placa': 'TST-0002', 'marca': 'Fiat', 'modelo': 'Uno',
            'cor': 'Azul', 'clienteId': cliente['id'],
        }, 201)
        self.enviar('post', entrada, dados | {'veiculoId': outro_veiculo['id']}, 409)
        self.dashboard(1, 1, 1, sufixo)

        lista = '/api/permanencias' + sufixo
        self.assertEqual(self.client.get(lista + '?status=ABERTO').json(), [permanencia])
        self.assertEqual(self.client.get(lista + '?status=FINALIZADO').json(), [])
        instante = datetime(2026, 11, 13, 12, 0)
        Permanencia.objects.filter(pk=permanencia['id']).update(
            data_hora_entrada=instante - timedelta(minutes=minutos)
        )
        saida = f'/api/permanencias/{permanencia["id"]}/saida' + sufixo
        with patch('api.services.permanencia_service.datetime') as relogio:
            relogio.now.return_value = instante
            finalizada = self.enviar('put', saida, {}, 200)
        self.assertEqual(Decimal(finalizada['valorTotal']), Decimal(valor))
        self.assertEqual(finalizada['status'], 'FINALIZADO')
        self.assertEqual(datetime.fromisoformat(finalizada['dataHoraSaida']), instante)
        self.enviar('put', saida, {}, 409)
        self.dashboard(2, 0, 0, sufixo)
        self.assertEqual(self.client.get(lista + '?status=ABERTO').json(), [])
        self.assertEqual(self.client.get(lista + '?status=FINALIZADO').json(), [finalizada])

        # As relações reais, inclusive após a saída, devem proteger o histórico.
        for recurso, objeto in (('clientes', cliente), ('veiculos', veiculo), ('vagas', vaga)):
            self.assertIn('error', self.enviar(
                'delete', f'/api/{recurso}/{objeto["id"]}' + sufixo, {}, 409
            ))
        self.assertTrue(Cliente.objects.filter(pk=cliente['id']).exists())
        self.assertEqual(Veiculo.objects.count(), 2)
        self.assertEqual(Permanencia.objects.count(), 1)

    def test_fluxo_30_minutos_sem_barra(self):
        self.executar_fluxo('', 30, '5.00')

    def test_fluxo_60_minutos_com_barra(self):
        self.executar_fluxo('/', 60, '5.00')

    def test_fluxo_61_minutos_sem_barra(self):
        self.executar_fluxo('', 61, '10.00')

    def test_editar_vaga_ocupada_nao_libera_permanencia_aberta(self):
        _, veiculo, vaga = self.cadastrar()
        self.enviar('post', '/api/permanencias/entrada', {
            'veiculoId': veiculo['id'], 'vagaId': vaga['id'],
        }, 201)
        detalhe = f'/api/vagas/{vaga["id"]}'
        dados = {'numero': 'QA01', 'tipo': 'CARRO'}
        self.enviar('put', detalhe, dados | {'status': 'LIVRE'}, 409)
        for extra in ({}, {'status': None}):
            self.assertEqual(
                self.enviar('put', detalhe, dados | extra, 200)['status'], 'OCUPADA'
            )
        self.dashboard(0, 1, 1)

    def test_ids_e_json_invalidos_na_entrada(self):
        for invalido in (None, True, 0, -1, 1.5, '', '²', '١', 'abc', 2**63, '9' * 5000):
            for campo in ('veiculoId', 'vagaId'):
                with self.subTest(campo=campo, invalido=str(invalido)[:20]):
                    self.enviar('post', '/api/permanencias/entrada', {
                        'veiculoId': 1, 'vagaId': 1, campo: invalido,
                    }, 400)
        for corpo in (b'\xff', b'{', b'[]', b'null'):
            resposta = self.client.post(
                '/api/permanencias/entrada', corpo, content_type='application/json'
            )
            self.assertEqual(resposta.status_code, 400)
            self.assertIn('error', resposta.json())

    def test_recursos_inexistentes_e_metodos_de_permanencias(self):
        _, veiculo, vaga = self.cadastrar()
        for dados in (
            {'veiculoId': veiculo['id'] + 100, 'vagaId': vaga['id']},
            {'veiculoId': veiculo['id'], 'vagaId': vaga['id'] + 100},
        ):
            self.enviar('post', '/api/permanencias/entrada', dados, 404)
        self.enviar('put', '/api/permanencias/999/saida', {}, 404)
        for metodo, rota in (
            ('get', '/api/permanencias/entrada'),
            ('post', '/api/permanencias'),
            ('post', '/api/permanencias/999/saida'),
        ):
            resposta = getattr(self.client, metodo)(rota)
            self.assertEqual(resposta.status_code, 405)
            self.assertIn('error', resposta.json())
            self.assertIn('Allow', resposta)
        self.dashboard(1, 0, 0)

    def test_falha_na_entrada_reverte_ocupacao(self):
        _, veiculo, vaga = self.cadastrar()
        with patch.object(Permanencia.objects, 'create', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                registrar_entrada(veiculo['id'], vaga['id'])
        self.assertFalse(Permanencia.objects.exists())
        self.dashboard(1, 0, 0)

    def test_falha_na_saida_reverte_cobranca_e_finalizacao(self):
        _, veiculo, vaga = self.cadastrar()
        permanencia = registrar_entrada(veiculo['id'], vaga['id'])
        with patch.object(Vaga, 'save', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                registrar_saida(permanencia.id)
        permanencia.refresh_from_db()
        self.assertEqual(permanencia.status, 'ABERTO')
        self.assertIsNone(permanencia.valor_total)
        self.assertIsNone(permanencia.data_hora_saida)
        self.dashboard(0, 1, 1)
