
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .models import Permanencia, Veiculo, Vaga


TARIFA_POR_HORA = Decimal("5.00")


def registrar_entrada(veiculo_id, vaga_id):
    with transaction.atomic():

        if Permanencia.objects.filter(
            veiculo_id=veiculo_id,
            status="ABERTO"
        ).exists():
            raise ValueError(
                "Veículo já possui uma permanência em aberto."
            )

        veiculo = Veiculo.objects.select_for_update().filter(
            id=veiculo_id
        ).first()

        if veiculo is None:
            raise LookupError("Veículo não encontrado.")

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

        minutos = int(
            (saida - permanencia.data_hora_entrada).total_seconds() // 60
        )

        horas = max(1, (minutos + 59) // 60)

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