import json
from sqlite3 import SQLITE_CONSTRAINT_FOREIGNKEY, SQLITE_CONSTRAINT_UNIQUE

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from api.models import Cliente, Veiculo


CAMPOS_TEXTO = ('placa', 'marca', 'modelo', 'cor')


def veiculo_to_dict(veiculo):
    return {
        'id': veiculo.pk,
        'placa': veiculo.placa,
        'marca': veiculo.marca,
        'modelo': veiculo.modelo,
        'cor': veiculo.cor,
        'clienteId': veiculo.cliente_id,
        'clienteNome': veiculo.cliente.nome,
    }


def _erro(mensagem, status):
    return JsonResponse({'error': mensagem}, status=status)


def _metodo_invalido(metodos):
    response = _erro('Método não permitido', 405)
    response['Allow'] = metodos
    return response


def _dados_veiculo(request):
    try:
        dados = json.loads(request.body)
    except ValueError as exc:
        raise ValueError('JSON inválido') from exc

    if not isinstance(dados, dict):
        raise ValueError('O corpo da requisição deve ser um objeto JSON')

    campos = {}
    for campo in CAMPOS_TEXTO:
        valor = dados.get(campo)
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(f"Campo '{campo}' deve ser um texto não vazio")
        limite = Veiculo._meta.get_field(campo).max_length
        if len(valor) > limite:
            raise ValueError(f"Campo '{campo}' deve ter até {limite} caracteres")
        try:
            valor.encode('utf-8')
        except UnicodeEncodeError as exc:
            raise ValueError(f"Campo '{campo}' contém caracteres inválidos") from exc
        campos[campo] = valor

    cliente_id = dados.get('clienteId')
    if type(cliente_id) is not int or not 1 <= cliente_id < 2**63:
        raise ValueError("Campo 'clienteId' deve ser um inteiro positivo válido")

    return campos, cliente_id


def _salvar_veiculo(request, veiculo_id=None):
    try:
        campos, cliente_id = _dados_veiculo(request)
    except ValueError as exc:
        return _erro(str(exc), 400)

    try:
        cliente = Cliente.objects.get(pk=cliente_id)
    except Cliente.DoesNotExist:
        return _erro('Cliente não encontrado', 404)

    try:
        with transaction.atomic():
            if veiculo_id is None:
                veiculo = Veiculo.objects.create(cliente=cliente, **campos)
                return JsonResponse(veiculo_to_dict(veiculo), status=201)

            alterados = Veiculo.objects.filter(pk=veiculo_id).update(cliente=cliente, **campos)
            if not alterados:
                return _erro('Veículo não encontrado', 404)
    except IntegrityError as exc:
        codigo = getattr(exc.__cause__, 'sqlite_errorcode', None)
        if codigo == SQLITE_CONSTRAINT_UNIQUE:
            return _erro('Placa já cadastrada', 409)
        if codigo == SQLITE_CONSTRAINT_FOREIGNKEY:
            return _erro('Cliente não encontrado', 404)
        raise

    veiculo = Veiculo(pk=veiculo_id, cliente=cliente, **campos)
    return JsonResponse(veiculo_to_dict(veiculo))


@csrf_exempt
def lista_veiculos(request):
    if request.method == 'GET':
        veiculos = Veiculo.objects.select_related('cliente').order_by('placa')
        return JsonResponse([veiculo_to_dict(veiculo) for veiculo in veiculos], safe=False)
    if request.method == 'POST':
        return _salvar_veiculo(request)
    if request.method in ('PUT', 'DELETE'):
        return _erro('ID obrigatório', 400)
    return _metodo_invalido('GET, POST, OPTIONS')


@csrf_exempt
def detalhe_veiculo(request, veiculo_id):
    if request.method not in ('GET', 'PUT', 'DELETE'):
        return _metodo_invalido('GET, PUT, DELETE, OPTIONS')

    try:
        if not veiculo_id.isascii() or not veiculo_id.removeprefix('+').removeprefix('-').isdecimal():
            raise ValueError
        veiculo_id = int(veiculo_id)
        if not -(2**63) <= veiculo_id < 2**63:
            raise ValueError
    except ValueError:
        return _erro('ID inválido', 400)

    if request.method == 'PUT':
        return _salvar_veiculo(request, veiculo_id)

    veiculos = Veiculo.objects.filter(pk=veiculo_id)
    if request.method == 'GET':
        try:
            veiculo = veiculos.select_related('cliente').get()
        except Veiculo.DoesNotExist:
            return _erro('Veículo não encontrado', 404)
        return JsonResponse(veiculo_to_dict(veiculo))

    try:
        excluidos, _ = veiculos.delete()
    except ProtectedError:
        return _erro('Não é possível excluir veículo com permanências registradas', 409)
    except IntegrityError as exc:
        if getattr(exc.__cause__, 'sqlite_errorcode', None) == SQLITE_CONSTRAINT_FOREIGNKEY:
            return _erro('Não é possível excluir veículo com permanências registradas', 409)
        raise

    if not excluidos:
        return _erro('Veículo não encontrado', 404)
    return JsonResponse({'message': 'Veículo excluído com sucesso'})
