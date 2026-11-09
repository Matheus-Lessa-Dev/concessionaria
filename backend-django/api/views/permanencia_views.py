
import json

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from . import permanencia_service


def validar_id(valor):
    if isinstance(valor, bool):
        return False

    if isinstance(valor, int):
        return valor > 0

    if isinstance(valor, str):
        return valor.strip().isdigit() and int(valor.strip()) > 0

    return False


@require_http_methods(["POST"])
def entrada(request):
    try:
        dados = json.loads(request.body)

        if not isinstance(dados, dict):
            return JsonResponse({
                "erro": "O corpo da requisição deve ser um objeto JSON."
            }, status=400)

        veiculo_id = dados.get("veiculoId")
        vaga_id = dados.get("vagaId")

        if veiculo_id is None or vaga_id is None:
            return JsonResponse({
                "erro": "Campos veiculoId e vagaId são obrigatórios."
            }, status=400)

        if not validar_id(veiculo_id) or not validar_id(vaga_id):
            return JsonResponse({
                "erro": "veiculoId e vagaId devem ser números inteiros positivos."
            }, status=400)

        veiculo_id = int(veiculo_id)
        vaga_id = int(vaga_id)

        permanencia = permanencia_service.registrar_entrada(
            veiculo_id,
            vaga_id
        )

        return JsonResponse(
            permanencia_service.permanencia_to_dict(permanencia),
            status=201
        )

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

        return JsonResponse(
            permanencia_service.permanencia_to_dict(permanencia)
        )

    except LookupError as e:
        return JsonResponse({"erro": str(e)}, status=404)

    except ValueError as e:
        return JsonResponse({"erro": str(e)}, status=409)


@require_http_methods(["GET"])
def listar(request):
    status = request.GET.get("status")

    permanencias = permanencia_service.listar_permanencias(status)

    dados = [
        permanencia_service.permanencia_to_dict(p)
        for p in permanencias
    ]

    return JsonResponse(dados, safe=False)
