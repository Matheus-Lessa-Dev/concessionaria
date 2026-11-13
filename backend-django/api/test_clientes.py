import json
from unittest.mock import patch

from django.db.models import ProtectedError
from django.test import TestCase

from api.models import Cliente


class ClienteApiTests(TestCase):
    url = "/api/clientes/"
    valido = {
        "nome": "Maria Silva",
        "cpf": "123.456.789-01",
        "telefone": "45999990000",
        "email": "maria@email.com",
    }

    def _post(self, dados):
        return self.client.post(self.url, json.dumps(dados), content_type="application/json")

    def _put(self, id, dados):
        return self.client.put(f"{self.url}{id}/", json.dumps(dados), content_type="application/json")

    def _criar(self, **extra):
        return self._post({**self.valido, **extra}).json()["id"]

    # --- listagem ---
    def test_listagem_vazia(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_listagem_com_clientes(self):
        self._criar()
        self._criar(cpf="987.654.321-00", nome="João Lima")
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertEqual([c["nome"] for c in r.json()], ["Maria Silva", "João Lima"])

    # --- cadastro ---
    def test_cadastro_retorna_201_e_campos(self):
        r = self._post(self.valido)
        self.assertEqual(r.status_code, 201)
        corpo = r.json()
        self.assertEqual(set(corpo), {"id", "nome", "cpf", "telefone", "email"})
        self.assertEqual(corpo["nome"], "Maria Silva")
        self.assertEqual(corpo["cpf"], "123.456.789-01")
        self.assertTrue(Cliente.objects.filter(pk=corpo["id"]).exists())

    def test_cadastro_so_com_obrigatorios(self):
        r = self._post({"nome": "Ana", "cpf": "111.222.333-44"})
        self.assertEqual(r.status_code, 201)
        self.assertIsNone(r.json()["telefone"])
        self.assertIsNone(r.json()["email"])

    # --- consulta ---
    def test_consulta_por_id(self):
        cid = self._criar()
        r = self.client.get(f"{self.url}{cid}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["id"], cid)
        self.assertEqual(r.json()["email"], "maria@email.com")

    # --- edição ---
    def test_edicao(self):
        cid = self._criar()
        r = self._put(cid, {**self.valido, "nome": "Maria Souza", "telefone": "45988887777"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["nome"], "Maria Souza")
        self.assertEqual(Cliente.objects.get(pk=cid).telefone, "45988887777")

    def test_edicao_mantendo_o_proprio_cpf(self):
        cid = self._criar()
        self.assertEqual(self._put(cid, self.valido).status_code, 200)

    # --- exclusão ---
    def test_exclusao(self):
        cid = self._criar()
        r = self.client.delete(f"{self.url}{cid}/")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(r.content, b"")
        self.assertEqual(self.client.get(f"{self.url}{cid}/").status_code, 404)

    def test_exclusao_bloqueada_por_relacionamento_retorna_409(self):
        cid = self._criar()
        with patch.object(Cliente, "delete", side_effect=ProtectedError("bloqueado", set())):
            r = self.client.delete(f"{self.url}{cid}/")
        self.assertEqual(r.status_code, 409)
        self.assertIn("error", r.json())
        self.assertTrue(Cliente.objects.filter(pk=cid).exists())

    # --- validações (400) ---
    def test_nome_obrigatorio(self):
        for nome in ("", "   ", None):
            r = self._post({**self.valido, "nome": nome})
            self.assertEqual(r.status_code, 400)
            self.assertIn("error", r.json())
        sem_nome = {k: v for k, v in self.valido.items() if k != "nome"}
        self.assertEqual(self._post(sem_nome).status_code, 400)

    def test_cpf_obrigatorio(self):
        for cpf in ("", "   ", None):
            self.assertEqual(self._post({**self.valido, "cpf": cpf}).status_code, 400)
        sem_cpf = {k: v for k, v in self.valido.items() if k != "cpf"}
        self.assertEqual(self._post(sem_cpf).status_code, 400)

    def test_tamanhos_maximos(self):
        self.assertEqual(self._post({**self.valido, "nome": "a" * 101}).status_code, 400)
        self.assertEqual(self._post({**self.valido, "cpf": "1" * 15}).status_code, 400)
        self.assertEqual(self._post({**self.valido, "telefone": "9" * 21}).status_code, 400)
        email_longo = "a" * 95 + "@x.com"
        self.assertEqual(self._post({**self.valido, "email": email_longo}).status_code, 400)

    def test_email_invalido(self):
        self.assertEqual(self._post({**self.valido, "email": "isso-nao-e-email"}).status_code, 400)

    def test_json_invalido(self):
        r = self.client.post(self.url, "{quebrado", content_type="application/json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("error", r.json())

    def test_corpo_que_nao_e_objeto(self):
        r = self.client.post(self.url, json.dumps([1, 2]), content_type="application/json")
        self.assertEqual(r.status_code, 400)

    # --- CPF duplicado (409) ---
    def test_cpf_duplicado_no_cadastro(self):
        self._criar()
        r = self._post(self.valido)
        self.assertEqual(r.status_code, 409)
        self.assertIn("error", r.json())

    def test_cpf_duplicado_na_edicao(self):
        self._criar()
        outro = self._criar(cpf="987.654.321-00", nome="João Lima")
        r = self._put(outro, {**self.valido, "nome": "João Lima"})
        self.assertEqual(r.status_code, 409)

    # --- inexistente (404) e método (405) ---
    def test_cliente_inexistente(self):
        self.assertEqual(self.client.get(f"{self.url}999/").status_code, 404)
        self.assertEqual(self._put(999, self.valido).status_code, 404)
        self.assertEqual(self.client.delete(f"{self.url}999/").status_code, 404)

    def test_metodo_nao_permitido(self):
        for metodo, url, permitidos in (
            ('delete', self.url, 'GET, POST, OPTIONS'),
            ('post', f'{self.url}1/', 'GET, PUT, DELETE, OPTIONS'),
        ):
            resposta = getattr(self.client, metodo)(url)
            self.assertEqual(resposta.status_code, 405)
            self.assertIn('error', resposta.json())
            self.assertEqual(resposta['Allow'], permitidos)
