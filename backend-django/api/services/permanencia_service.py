import math
from datetime import datetime
from decimal import Decimal

from django.db import transaction

from ..models import Permanencia, Veiculo, Vaga


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

def _calcular_valor(entrada, saida):
    duracao = saida - entrada
    microssegundos = (
        (duracao.days * 86400 + duracao.seconds) * 1_000_000
        + duracao.microseconds
    )

    horas = max(1, math.ceil(Decimal(microssegundos) / Decimal(3_600_000_000)))

    return TARIFA_POR_HORA * Decimal(horas)



@transaction.atomic
def registrar_entrada(veiculo_id, vaga_id):
    if Permanencia.objects.filter(
        veiculo_id=veiculo_id,
        status="ABERTO"
    ).exists():
        raise ValueError(
            "Veículo já possui uma permanência em aberto."
        )

    try:
        veiculo = Veiculo.objects.get(id=veiculo_id)
    except Veiculo.DoesNotExist:
        raise LookupError("Veículo não encontrado.")

    try:
        vaga = Vaga.objects.get(id=vaga_id)
    except Vaga.DoesNotExist:
        raise LookupError("Vaga não encontrada.")

    if vaga.status != "LIVRE" or Permanencia.objects.filter(
        vaga=vaga, status="ABERTO"
    ).exists():
        raise ValueError("Vaga já está ocupada.")

    vaga.status = "OCUPADA"
    vaga.save()

    permanencia = Permanencia.objects.create(
        veiculo=veiculo,
        vaga=vaga,
        data_hora_entrada=datetime.now(),
        status="ABERTO"
    )

    return permanencia


@transaction.atomic
def registrar_saida(permanencia_id):
    try:
        permanencia = Permanencia.objects.select_related('veiculo', 'vaga').get(
            id=permanencia_id
        )
    except Permanencia.DoesNotExist:
        raise LookupError("Permanência não encontrada.")

    if permanencia.status != "ABERTO":
        raise ValueError("Permanência já foi finalizada.")

    try:
        vaga = Vaga.objects.get(id=permanencia.vaga_id)
    except Vaga.DoesNotExist:
        raise LookupError("Vaga vinculada à permanência não encontrada.")

    saida = datetime.now()

    valor = _calcular_valor(
        permanencia.data_hora_entrada,
        saida
    )

    permanencia.data_hora_saida = saida
    permanencia.valor_total = valor
    permanencia.status = "FINALIZADO"
    permanencia.save()

    vaga.status = "LIVRE"
    vaga.save()

    return permanencia


def lista_permanencias(status=None):
    permanencias = Permanencia.objects.select_related(
        "veiculo",
        "vaga"
    ).all()

    if status:
        permanencias = permanencias.filter(
            status=status.upper()
        )

    return permanencias.order_by("-data_hora_entrada")


def buscar_por_id(permanencia_id):
    try:
        return Permanencia.objects.get(id=permanencia_id)
    except Permanencia.DoesNotExist:
        raise LookupError("Permanência não encontrada.")
