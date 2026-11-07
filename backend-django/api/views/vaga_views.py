import json

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

            numero = dados.get('numero')
            tipo = dados.get('tipo')

            if not numero:
                return JsonResponse(
                    {'error': "Campo 'numero' é obrigatório"},
                    status=400
                )

            if not tipo or tipo not in ['CARRO', 'MOTO']:
                return JsonResponse(
                    {'error': "Campo 'tipo' deve ser CARRO ou MOTO"},
                    status=400
                )

            vaga = Vaga.objects.create(
                numero=numero,
                tipo=tipo,
                status='LIVRE'
            )

            return JsonResponse(vaga_to_dict(vaga), status=201)

        except json.JSONDecodeError:
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
        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'JSON inválido'},
                status=400
            )

        numero = dados.get('numero')
        tipo = dados.get('tipo')
        status = dados.get('status')

        if not numero:
            return JsonResponse(
                {'error': "Campo 'numero' é obrigatório"},
                status=400
            )

        if not tipo or tipo not in ['CARRO', 'MOTO']:
            return JsonResponse(
                {'error': "Campo 'tipo' deve ser CARRO ou MOTO"},
                status=400
            )

        if status not in ['LIVRE', 'OCUPADA']:
            status = 'LIVRE'

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
        vaga.save()

        return JsonResponse(vaga_to_dict(vaga))

    elif request.method == 'DELETE':
        try:
            vaga = Vaga.objects.get(id=id)
        except Vaga.DoesNotExist:
            return JsonResponse(
                {'error': 'Vaga não encontrada'},
                status=404
            )

        vaga.delete()

        return JsonResponse({'message': 'Vaga excluída com sucesso'})

    return JsonResponse(
        {'error': 'Método não permitido'},
        status=405
    )
