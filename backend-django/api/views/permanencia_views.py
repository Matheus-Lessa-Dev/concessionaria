
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import permanencia_service


@require_http_methods(["POST"])
def entrada(request):
    try:
        dados = json.loads(request.body)

        veiculo_id = dados.get("veiculoId")
        vaga_id = dados.get("vagaId")

        if not veiculo_id or not vaga_id:
            return JsonResponse({
                "erro": "Campos veiculoId e vagaId são obrigatórios."
            }, status=400)

        permanencia = permanencia_service.registrar_entrada(
            veiculo_id,
            vaga_id
        )

        return JsonResponse({
            "id": permanencia.id,
            "veiculoId": permanencia.veiculo_id,
            "vagaId": permanencia.vaga_id,
            "dataHoraEntrada": permanencia.data_hora_entrada.isoformat(),
            "status": permanencia.status
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido."}, status=400)

    except LookupError as e:
        return JsonResponse({"erro": str(e)}, status=404)

    except ValueError as e:
        return JsonResponse({"erro": str(e)}, status=409)


@require_http_methods(["PUT"])
def saida(request, permanencia_id):
    try:
        permanencia = permanencia_service.registrar_saida(
            permanencia_id
        )

        return JsonResponse({
            "id": permanencia.id,
            "dataHoraEntrada": permanencia.data_hora_entrada.isoformat(),
            "dataHoraSaida": permanencia.data_hora_saida.isoformat(),
            "valorTotal": str(permanencia.valor_total),
            "status": permanencia.status
        })

    except LookupError as e:
        return JsonResponse({"erro": str(e)}, status=404)

    except ValueError as e:
        return JsonResponse({"erro": str(e)}, status=409)


@require_http_methods(["GET"])
def listar(request):
    status = request.GET.get("status")

    permanencias = permanencia_service.listar_permanencias(status)

    dados = []

    for p in permanencias:
        dados.append({
            "id": p.id,
            "veiculoId": p.veiculo_id,
            "veiculoPlaca": p.veiculo.placa,
            "veiculoModelo": p.veiculo.modelo,
            "vagaId": p.vaga_id,
            "vagaNumero": p.vaga.numero,
            "dataHoraEntrada": p.data_hora_entrada.isoformat(),
            "dataHoraSaida": (
                p.data_hora_saida.isoformat()
                if p.data_hora_saida else None
            ),
            "valorTotal": (
                str(p.valor_total)
                if p.valor_total is not None else None
            ),
            "status": p.status
        })

    return JsonResponse(dados, safe=False)
