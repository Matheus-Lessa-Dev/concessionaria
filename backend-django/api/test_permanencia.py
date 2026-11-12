import json
from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from api.models import Cliente, Veiculo, Vaga, Permanencia
from api.services.permanencia_service import _calcular_valor


class PermanenciaTests(TestCase):

    def setUp(self):
        self.cliente = Cliente.objects.create(
            nome="Cliente Teste",
            cpf="12345678900"
        )

        self.veiculo = self.criar_veiculo("ABC1D23")
        self.vaga = self.criar_vaga(1)

    def criar_veiculo(self, placa):
        return Veiculo.objects.create(
            placa=placa,
            marca="Fiat",
            modelo="Uno",
            cor="Branco",
            cliente=self.cliente
        )

    def criar_vaga(self, numero, status="LIVRE"):
        return Vaga.objects.create(
            numero=numero,
            tipo="CARRO",
            status=status
        )

    def criar_permanencia_aberta(self, veiculo=None, vaga=None):
        veiculo = veiculo or self.veiculo
        vaga = vaga or self.vaga

        vaga.status = "OCUPADA"
        vaga.save()

        return Permanencia.objects.create(
            veiculo=veiculo,
            vaga=vaga,
            data_hora_entrada=(
                datetime.now() - timedelta(minutes=30)
            ),
            status="ABERTO"
        )

    # TESTE 1: ENTRADA VÁLIDA

    def test_entrada_valida(self):
        response = self.client.post(
            reverse("registrar_entrada"),
            data=json.dumps({
                "veiculoId": self.veiculo.id,
                "vagaId": self.vaga.id
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)

        permanencia = Permanencia.objects.get(
            veiculo=self.veiculo
        )

        self.assertEqual(permanencia.status, "ABERTO")

        self.vaga.refresh_from_db()

        self.assertEqual(self.vaga.status, "OCUPADA")

    # TESTE 2: CONFLITO - VEÍCULO JÁ ESTACIONADO

    def test_entrada_veiculo_ja_estacionado(self):
        self.criar_permanencia_aberta()

        outra_vaga = self.criar_vaga(2)

        response = self.client.post(
            reverse("registrar_entrada"),
            data=json.dumps({
                "veiculoId": self.veiculo.id,
                "vagaId": outra_vaga.id
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 409)

        outra_vaga.refresh_from_db()

        self.assertEqual(outra_vaga.status, "LIVRE")

        self.assertEqual(
            Permanencia.objects.filter(
                veiculo=self.veiculo,
                status="ABERTO"
            ).count(),
            1
        )

    # TESTE 3: CONFLITO - VAGA OCUPADA

    def test_entrada_vaga_ocupada(self):
        self.vaga.status = "OCUPADA"
        self.vaga.save()

        outro_veiculo = self.criar_veiculo("DEF4G56")

        response = self.client.post(
            reverse("registrar_entrada"),
            data=json.dumps({
                "veiculoId": outro_veiculo.id,
                "vagaId": self.vaga.id
            }),
            content_type="application/json"
        )

        self.assertEqual(response.status_code, 409)

        self.assertFalse(
            Permanencia.objects.filter(
                veiculo=outro_veiculo
            ).exists()
        )

    # TESTE 4: SAÍDA VÁLIDA

    def test_saida_valida(self):
        permanencia = self.criar_permanencia_aberta()

        response = self.client.put(
            reverse(
                "registrar_saida",
                args=[permanencia.id]
            )
        )

        self.assertEqual(response.status_code, 200)

        permanencia.refresh_from_db()

        self.assertEqual(permanencia.status, "FINALIZADO")

        self.assertIsNotNone(permanencia.data_hora_saida)

        self.assertEqual(
            permanencia.valor_total,
            Decimal("5.00")
        )

    # TESTE 5: LIBERAÇÃO DA VAGA

    def test_saida_libera_vaga(self):
        permanencia = self.criar_permanencia_aberta()

        self.assertEqual(self.vaga.status, "OCUPADA")

        response = self.client.put(
            reverse(
                "registrar_saida",
                args=[permanencia.id]
            )
        )

        self.assertEqual(response.status_code, 200)

        self.vaga.refresh_from_db()

        self.assertEqual(self.vaga.status, "LIVRE")

    # TESTE 6: CONFLITO - SAÍDA DUPLICADA

    def test_saida_permanencia_ja_finalizada(self):
        permanencia = Permanencia.objects.create(
            veiculo=self.veiculo,
            vaga=self.vaga,
            data_hora_entrada=datetime.now() - timedelta(hours=1),
            data_hora_saida=datetime.now(),
            valor_total=Decimal("5.00"),
            status="FINALIZADO"
        )

        response = self.client.put(
            reverse(
                "registrar_saida",
                args=[permanencia.id]
            )
        )

        self.assertEqual(response.status_code, 409)

    # TESTE 7: COBRANÇA DE 30 MINUTOS

    def test_cobranca_30_minutos(self):
        entrada = datetime(2026, 1, 1, 10, 0)
        saida = entrada + timedelta(minutes=30)

        valor = _calcular_valor(entrada, saida)

        self.assertEqual(valor, Decimal("5.00"))

    # TESTE 8: COBRANÇA DE 60 MINUTOS

    def test_cobranca_60_minutos(self):
        entrada = datetime(2026, 1, 1, 10, 0)
        saida = entrada + timedelta(minutes=60)

        valor = _calcular_valor(entrada, saida)

        self.assertEqual(valor, Decimal("5.00"))

    # TESTE 9: COBRANÇA DE 61 MINUTOS

    def test_cobranca_61_minutos(self):
        entrada = datetime(2026, 1, 1, 10, 0)
        saida = entrada + timedelta(minutes=61)

        valor = _calcular_valor(entrada, saida)

        self.assertEqual(valor, Decimal("10.00"))
