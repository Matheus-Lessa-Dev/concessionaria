import json

from django.db import IntegrityError
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import Vaga


def vaga_to_dict(vaga):
    return {
        'id': vaga.id,
        'numero': vaga.numero,
        'tipo': vaga.tipo,
        'status': vaga.status,
    }


def validar_vaga(dados):
    if not isinstance(dados, dict):
        return JsonResponse(
            {'error': 'O corpo da requisição deve ser um objeto JSON'},
            status=400
        )

    numero = dados.get('numero')

    if not isinstance(numero, str) or not numero.strip():
        return JsonResponse(
            {'error': "Campo 'numero' é obrigatório"},
            status=400
        )

    if len(numero.strip()) > 10:
        return JsonResponse(
            {'error': "Campo 'numero' deve ter no máximo 10 caracteres"},
            status=400
        )

    if dados.get('tipo') not in ('CARRO', 'MOTO'):
        return JsonResponse(
            {'error': "Campo 'tipo' deve ser CARRO ou MOTO"},
            status=400
        )

    status = dados.get('status')

    if status is not None and status not in ('LIVRE', 'OCUPADA'):
        return JsonResponse(
            {'error': "Campo 'status' deve ser LIVRE ou OCUPADA"},
            status=400
        )

    return None


@csrf_exempt
def lista_vagas(request):

    if request.method == 'GET':
        status = request.GET.get('status')

        vagas = Vaga.objects.all()

        if status:
            vagas = vagas.filter(status=status)

        vagas = vagas.order_by('numero')

        resultado = [
            vaga_to_dict(vaga)
            for vaga in vagas
        ]

        return JsonResponse(resultado, safe=False)

    elif request.method == 'POST':
        try:
            dados = json.loads(request.body)

            erro = validar_vaga(dados)
            if erro:
                return erro

            numero = dados['numero'].strip()
            tipo = dados['tipo']

            vaga = Vaga.objects.create(
                numero=numero,
                tipo=tipo,
                status='LIVRE'
            )

            return JsonResponse(vaga_to_dict(vaga), status=201)

        except IntegrityError:
            return JsonResponse(
                {'error': 'Número de vaga já cadastrado'},
                status=409
            )

        except ValueError:
            return JsonResponse(
                {'error': 'JSON inválido'},
                status=400
            )

    return JsonResponse(
        {'error': 'Método não permitido'},
        status=405
    )

@csrf_exempt
def detalhe_vaga(request, id):

    if request.method == 'GET':
        try:
            vaga = Vaga.objects.get(id=id)
        except Vaga.DoesNotExist:
            return JsonResponse(
                {'error': 'Vaga não encontrada'},
                status=404
            )

        return JsonResponse(vaga_to_dict(vaga))

    elif request.method == 'PUT':
        try:
            dados = json.loads(request.body)
        except ValueError:
            return JsonResponse(
                {'error': 'JSON inválido'},
                status=400
            )

        erro = validar_vaga(dados)
        if erro:
            return erro

        numero = dados['numero'].strip()
        tipo = dados['tipo']
        status = dados.get('status') or 'LIVRE'

        try:
            vaga = Vaga.objects.get(id=id)
        except Vaga.DoesNotExist:
            return JsonResponse(
                {'error': 'Vaga não encontrada'},
                status=404
            )

        vaga.numero = numero
        vaga.tipo = tipo
        vaga.status = status

        try:
            vaga.save()
        except IntegrityError:
            return JsonResponse(
                {'error': 'Número de vaga já cadastrado'},
                status=409
            )

        return JsonResponse(vaga_to_dict(vaga))

    elif request.method == 'DELETE':
        try:
            vaga = Vaga.objects.get(id=id)
        except Vaga.DoesNotExist:
            return JsonResponse(
                {'error': 'Vaga não encontrada'},
                status=404
            )

        try:
            vaga.delete()
        except ProtectedError:
            return JsonResponse(
                {'error': 'Não é possível excluir vaga com permanências registradas'},
                status=409
            )

        return JsonResponse({'message': 'Vaga excluída com sucesso'})

    return JsonResponse(
        {'error': 'Método não permitido'},
        status=405
    )
