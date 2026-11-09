import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import Vaga


@csrf_exempt
def lista_vagas(request):

    if request.method == 'GET':
        status = request.GET.get('status')

        vagas = Vaga.objects.all()

        if status:
            vagas = vagas.filter(status=status)

        vagas = vagas.order_by('numero')

        resultado = [
            {
                'id': vaga.id,
                'numero': vaga.numero,
                'tipo': vaga.tipo,
                'status': vaga.status
            }
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

            return JsonResponse(
                {
                    'id': vaga.id,
                    'numero': vaga.numero,
                    'tipo': vaga.tipo,
                    'status': vaga.status
                },
                status=201
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {'error': 'JSON inválido'},
                status=400
            )

    return JsonResponse(
        {'error': 'Método não permitido'},
        status=405
    )