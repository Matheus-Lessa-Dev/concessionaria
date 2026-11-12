import json

from django.http import JsonResponse

from ..services import permanencia_service


def validar_id(valor):
    if isinstance(valor, bool):
        return False

    if isinstance(valor, int):
        return valor > 0

    if isinstance(valor, str):
        return valor.strip().isdigit() and int(valor.strip()) > 0

    return False


def entrada(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Método não permitido."},
            status=405,
            headers={"Allow": "POST"}
        )

    try:
        dados = json.loads(request.body)

        if not isinstance(dados, dict):
            return JsonResponse({
                "error": "O corpo da requisição deve ser um objeto JSON."
            }, status=400)

        veiculo_id = dados.get("veiculoId")
        vaga_id = dados.get("vagaId")

        if veiculo_id is None or vaga_id is None:
            return JsonResponse({
                "error": "Campos veiculoId e vagaId são obrigatórios."
            }, status=400)

        if not validar_id(veiculo_id) or not validar_id(vaga_id):
            return JsonResponse({
                "error": "veiculoId e vagaId devem ser números inteiros positivos."
            }, status=400)

        permanencia = permanencia_service.registrar_entrada(
            int(veiculo_id),
            int(vaga_id)
        )

        return JsonResponse(
            permanencia_service.permanencia_to_dict(permanencia),
            status=201
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "JSON inválido."},
            status=400
        )

    except LookupError as e:
        return JsonResponse(
            {"error": str(e)},
            status=404
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=409
        )


def saida(request, permanencia_id):
    if request.method != "PUT":
        return JsonResponse(
            {"error": "Método não permitido."},
            status=405,
            headers={"Allow": "PUT"}
        )

    try:
        permanencia = permanencia_service.registrar_saida(
            permanencia_id
        )

        return JsonResponse(
            permanencia_service.permanencia_to_dict(permanencia),
            status=200
        )

    except LookupError as e:
        return JsonResponse(
            {"error": str(e)},
            status=404
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=409
        )


def lista_permanencias(request):
    if request.method != "GET":
        return JsonResponse(
            {"error": "Método não permitido."},
            status=405,
            headers={"Allow": "GET"}
        )

    status = request.GET.get("status")

    permanencias = permanencia_service.lista_permanencias(status)

    dados = [
        permanencia_service.permanencia_to_dict(p)
        for p in permanencias
    ]

    return JsonResponse(dados, safe=False, status=200)
