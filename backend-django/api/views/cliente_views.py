import json

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError, RestrictedError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from api.models import Cliente

NOME_MAX = 100
CPF_MAX = 14
TELEFONE_MAX = 20
EMAIL_MAX = 100


def cliente_to_dict(cliente):
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "email": cliente.email,
    }


def _erro(mensagem, status):
    return JsonResponse({"error": mensagem}, status=status)


def _ler_json(request):
    try:
        dados = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None
    return dados if isinstance(dados, dict) else None


def _texto_opcional(valor, nome_campo, tamanho_max):
    """Retorna (valor_limpo, erro). Vazio vira None."""
    if valor is None:
        return None, None
    if not isinstance(valor, str):
        return None, f"O campo '{nome_campo}' deve ser texto."
    valor = valor.strip()
    if not valor:
        return None, None
    if len(valor) > tamanho_max:
        return None, f"O campo '{nome_campo}' deve ter no máximo {tamanho_max} caracteres."
    return valor, None


def _validar(dados):
    """Retorna (dados_limpos, erro). Em caso de sucesso, erro é None."""
    nome = dados.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        return None, "O campo 'nome' é obrigatório."
    nome = nome.strip()
    if len(nome) > NOME_MAX:
        return None, f"O campo 'nome' deve ter no máximo {NOME_MAX} caracteres."

    cpf = dados.get("cpf")
    if not isinstance(cpf, str) or not cpf.strip():
        return None, "O campo 'cpf' é obrigatório."
    cpf = cpf.strip()
    if len(cpf) > CPF_MAX:
        return None, f"O campo 'cpf' deve ter no máximo {CPF_MAX} caracteres."

    telefone, erro = _texto_opcional(dados.get("telefone"), "telefone", TELEFONE_MAX)
    if erro:
        return None, erro

    email, erro = _texto_opcional(dados.get("email"), "email", EMAIL_MAX)
    if erro:
        return None, erro
    if email is not None:
        try:
            validate_email(email)
        except ValidationError:
            return None, "O campo 'email' é inválido."

    return {"nome": nome, "cpf": cpf, "telefone": telefone, "email": email}, None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def lista_clientes(request):
    if request.method == "GET":
        clientes = Cliente.objects.all().order_by("id")
        return JsonResponse([cliente_to_dict(c) for c in clientes], safe=False)

    dados = _ler_json(request)
    if dados is None:
        return _erro("Corpo da requisição deve ser um JSON válido (objeto).", 400)

    limpos, erro = _validar(dados)
    if erro:
        return _erro(erro, 400)

    if Cliente.objects.filter(cpf=limpos["cpf"]).exists():
        return _erro("Já existe um cliente com este CPF.", 409)

    try:
        with transaction.atomic():
            cliente = Cliente.objects.create(**limpos)
    except IntegrityError:
        return _erro("Já existe um cliente com este CPF.", 409)

    return JsonResponse(cliente_to_dict(cliente), status=201)


@csrf_exempt
@require_http_methods(["GET", "PUT", "DELETE"])
def detalhe_cliente(request, id):
    try:
        cliente = Cliente.objects.get(pk=id)
    except Cliente.DoesNotExist:
        return _erro("Cliente não encontrado.", 404)

    if request.method == "GET":
        return JsonResponse(cliente_to_dict(cliente))

    if request.method == "PUT":
        dados = _ler_json(request)
        if dados is None:
            return _erro("Corpo da requisição deve ser um JSON válido (objeto).", 400)

        limpos, erro = _validar(dados)
        if erro:
            return _erro(erro, 400)

        if Cliente.objects.filter(cpf=limpos["cpf"]).exclude(pk=cliente.pk).exists():
            return _erro("Já existe um cliente com este CPF.", 409)

        for campo, valor in limpos.items():
            setattr(cliente, campo, valor)
        try:
            with transaction.atomic():
                cliente.save()
        except IntegrityError:
            return _erro("Já existe um cliente com este CPF.", 409)

        return JsonResponse(cliente_to_dict(cliente))

    # DELETE
    try:
        with transaction.atomic():
            cliente.delete()
    except (ProtectedError, RestrictedError, IntegrityError):
        return _erro(
            "Não é possível excluir o cliente porque ele possui registros relacionados.",
            409,
        )
    return HttpResponse(status=204)