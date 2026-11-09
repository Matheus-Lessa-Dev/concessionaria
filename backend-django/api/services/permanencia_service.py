import math
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Permanencia, Veiculo, Vaga


TARIFA_POR_HORA = Decimal("5.00")


def permanencia_to_dict(permanencia):
    return {
        "id": permanencia.id,
        "veiculoId": permanencia.veiculo_id,
        "veiculoPlaca": permanencia.veiculo.placa,
        "veiculoModelo": permanencia.veiculo.modelo,
        "vagaId": permanencia.vaga_id,
        "vagaNumero": permanencia.vaga.numero,
        "dataHoraEntrada": permanencia.data_hora_entrada.isoformat(),
        "dataHoraSaida": (
            permanencia.data_hora_saida.isoformat()
            if permanencia.data_hora_saida else None
        ),
        "valorTotal": (
            str(permanencia.valor_total)
            if permanencia.valor_total is not None else None
        ),
        "status": permanencia.status
    }


def registrar_entrada(veiculo_id, vaga_id):
    with transaction.atomic():

        veiculo = Veiculo.objects.select_for_update().filter(
            id=veiculo_id
        ).first()

        if veiculo is None:
            raise LookupError("Veículo não encontrado.")

        if Permanencia.objects.filter(
            veiculo_id=veiculo_id,
            status="ABERTO"
        ).exists():
            raise ValueError(
                "Veículo já possui uma permanência em aberto."
            )

        vaga = Vaga.objects.select_for_update().filter(
            id=vaga_id
        ).first()

        if vaga is None:
            raise LookupError("Vaga não encontrada.")

        if vaga.status == "OCUPADA":
            raise ValueError("Vaga já está ocupada.")

        vaga.status = "OCUPADA"
        vaga.save(update_fields=["status"])

        permanencia = Permanencia.objects.create(
            veiculo=veiculo,
            vaga=vaga,
            data_hora_entrada=timezone.now(),
            status="ABERTO"
        )

        return permanencia


def registrar_saida(permanencia_id):
    with transaction.atomic():

        permanencia = Permanencia.objects.select_for_update().filter(
            id=permanencia_id
        ).first()

        if permanencia is None:
            raise LookupError("Permanência não encontrada.")

        if permanencia.status == "FINALIZADO":
            raise ValueError("Permanência já foi finalizada.")

        saida = timezone.now()

        tempo_decorrido = (
            saida - permanencia.data_hora_entrada
        ).total_seconds()

        horas = max(1, math.ceil(tempo_decorrido / 3600))

        valor = TARIFA_POR_HORA * Decimal(horas)

        permanencia.data_hora_saida = saida
        permanencia.valor_total = valor
        permanencia.status = "FINALIZADO"

        permanencia.save(update_fields=[
            "data_hora_saida",
            "valor_total",
            "status"
        ])

        vaga = Vaga.objects.select_for_update().get(
            id=permanencia.vaga_id
        )

        vaga.status = "LIVRE"
        vaga.save(update_fields=["status"])

        return permanencia


def listar_permanencias(status=None):
    permanencias = Permanencia.objects.select_related(
        "veiculo",
        "vaga"
    ).all()

    if status:
        permanencias = permanencias.filter(status=status.upper())

    return permanencias.order_by("-data_hora_entrada")


def buscar_por_id(permanencia_id):
    permanencia = Permanencia.objects.filter(
        id=permanencia_id
    ).first()

    if permanencia is None:
        raise LookupError("Permanência não encontrada.")

    return permanencia