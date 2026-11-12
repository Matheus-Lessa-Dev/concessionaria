from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import Permanencia, Vaga


@csrf_exempt
def dashboard(request):

    if request.method == 'GET':
        return JsonResponse({
            'totalVagas': Vaga.objects.count(),
            'vagasLivres': Vaga.objects.filter(status='LIVRE').count(),
            'vagasOcupadas': Vaga.objects.filter(status='OCUPADA').count(),
            'veiculosEstacionados': Permanencia.objects.filter(
                status='ABERTO'
            ).count(),
        })

    return JsonResponse(
        {'error': 'Método não permitido'},
        status=405
    )