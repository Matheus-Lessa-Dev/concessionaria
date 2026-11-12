# Divisão do trabalho — Sistema de Estacionamento
Repositório: https://github.com/Matheus-Lessa-Dev/concessionaria
Conferência: 12/11/2026 — base main, commit 3f9cbd7; trabalho de Matheus na branch feat/infra-django.

## Objetivo

Substituir o backend Java por Python + Django e o PostgreSQL por SQLite, mantendo o frontend e os contratos da API existentes. Usar somente Django e bibliotecas padrão do Python, sem Django REST Framework.

## Situação atual

- Clientes (Eduarda), vagas e dashboard (Ana) já estão na main e foram conectados às URLs do projeto.
- Django + SQLite e Nginx iniciam pelo Docker Compose, com migrations automáticas e volume persistente.
- CORS, OPTIONS 204, dispensa de CSRF somente na API e URLs com/sem barra final estão configurados.
- Models e migration inicial conferidos, sem alterações necessárias para as entregas atuais.
- 53 testes aprovados no Windows e no container Linux (46 existentes + 7 de integração); check e makemigrations --check --dry-run aprovados.
- HTML, assets e endpoints disponíveis conferidos por HTTP no proxy Nginx; persistência após restart confirmada.
- Veículos ainda não foi entregue. A branch de permanências precisa de ajustes do responsável antes de ser integrada.
- Frontend e arquivos de implementação dos demais integrantes não foram alterados.

## Matheus — configuração e integração

A infraestrutura e a integração das entregas disponíveis estão concluídas. A finalização depende das entregas abaixo e da validação visual.

### Concluído

- [x] **FEITO** — CORS e resposta OPTIONS com HTTP 204.
- [x] **FEITO** — Dispensa de CSRF na API, mantendo a proteção do admin.
- [x] **FEITO** — api/urls.py conectado às URLs do projeto; clientes, vagas e dashboard registrados.
- [x] **FEITO** — URLs com e sem barra final, incluindo POST e PUT sem redirecionamentos.
- [x] **FEITO** — Docker com Django na porta 8080 e frontend Nginx, sem serviço PostgreSQL.
- [x] **FEITO** — DB_PATH, volume SQLite persistente e migrations automáticas na inicialização.
- [x] **FEITO** — Models e migration inicial conferidos; nenhuma mudança necessária para as entregas atuais.
- [x] **FEITO** — README atualizado com execução, testes e estado da migração.
- [x] **FEITO** — Testes de integração e conferência HTTP pelo Nginx; criação automática do banco e persistência após restart e recriação dos containers.

### O que falta terminar

- [ ] **Conferir visualmente clientes, vagas e dashboard no frontend.** Pode ser feito agora por Matheus; a ferramenta de navegador está indisponível nesta sessão.
- [ ] **Revalidar clientes** depois que Eduarda entregar os ajustes e testes pendentes.
- [ ] **Integrar veículos e registrar suas rotas** depois da entrega de Joabe.
- [ ] **Integrar permanências e registrar suas rotas** depois dos ajustes e testes de C.
- [ ] **Revisar models/migrations das novas entregas**, aplicando somente as mudanças necessárias à integração.
- [ ] **Validar o sistema completo pelo frontend:** cadastro de veículo → entrada → conflitos → saída → cobrança → histórico e totais do dashboard. Conferir 30 min = R$ 5, 60 min = R$ 5 e 61 min = R$ 10.
- [ ] **Atualizar o README com o resultado final** após integrar e validar as entregas restantes.

### Dependências

| Responsável | O que precisa entregar para Matheus continuar |
|-------------|----------------------------------------------|
| Eduarda | Erros 405 em JSON com a chave error e testes de clientes: validações, CPF duplicado, cliente inexistente e exclusão bloqueada por relacionamentos. A implementação principal já está integrada. |
| Joabe | veiculo_views.py com lista_veiculos, detalhe_veiculo e os testes previstos. A entrega ainda não está disponível nas branches remotas conferidas. |
| C. | Corrigir os imports entre views, services, models e URLs na branch feature/funcoes_persistencia; usar error no JSON dos erros e entregar os testes de permanências e cobrança. |

**Última conferência:** 12/11/2026. Branches remotas atualizadas; 53 testes aprovados; check, makemigrations --check --dry-run e configuração Compose sem problemas. Django e Nginx em execução; páginas, assets e rotas disponíveis respondendo pelo proxy. Persistência já verificada no Windows/Docker, com os registros de teste removidos ao final.

## Eduarda — clientes

Arquivo: backend-django/api/views/cliente_views.py
- Implementar lista_clientes: GET para listar e POST para cadastrar.
- Implementar detalhe_cliente: GET, PUT e DELETE por ID.
- Criar cliente_to_dict com id, nome, cpf, telefone e email.
- Validar nome e CPF obrigatórios e tamanhos dos campos.
- Retornar 409 para CPF duplicado, 404 para cliente inexistente e 400 para entrada inválida.
- Tratar exclusões bloqueadas por relacionamentos sem gerar erro 500.
- Testar listagem, cadastro, consulta, edição, exclusão e erros.
Rotas: /api/clientes/ e /api/clientes/<id>/

## Joabe — veículos

Arquivo: backend-django/api/views/veiculo_views.py
- Implementar lista_veiculos: GET e POST.
- Implementar detalhe_veiculo: GET, PUT e DELETE por ID.
- Criar veiculo_to_dict, mantendo os campos JSON do Java/frontend, incluindo clienteId e clienteNome.
- Usar select_related('cliente') nas consultas apropriadas.
- Validar placa, marca, modelo, cor e clienteId obrigatórios e tamanhos dos campos.
- Verificar se o cliente informado existe.
- Retornar 409 para placa duplicada, 404 para recurso inexistente e 400 para entrada inválida.
- Tratar exclusões de veículos com permanências registradas sem gerar erro 500.
- Testar operações e erros.
Rotas: /api/veiculos/ e /api/veiculos/<id>/

## Ana — vagas e dashboard

Arquivos: backend-django/api/views/vaga_views.py e dashboard_views.py
- Implementar lista_vagas: GET e POST.
- Implementar detalhe_vaga: GET, PUT e DELETE por ID.
- Criar vaga_to_dict.
- Validar numero e tipo obrigatórios; tipo somente CARRO ou MOTO.
- Validar status quando recebido: LIVRE ou OCUPADA.
- Retornar 409 para número duplicado, 404 para vaga inexistente e 400 para entrada inválida.
- Tratar exclusões bloqueadas por permanências sem gerar erro 500.
- Implementar dashboard mantendo exatamente os campos e cálculos esperados pelo frontend e backend Java.
- Testar operações, erros e totais do dashboard.
Rotas: /api/vagas/, /api/vagas/<id>/ e /api/dashboard/

## C. — permanências e regras de cobrança

Arquivos: backend-django/api/views/permanencia_views.py e api/services/permanencia_service.py
- Implementar entrada, saida e lista_permanencias.
- Criar permanencia_to_dict, incluindo veiculoPlaca, veiculoModelo e vagaNumero, com o formato esperado pelo frontend.
- Usar select_related('veiculo', 'vaga') nas consultas apropriadas.
- Na entrada, validar veiculoId e vagaId e a existência dos recursos.
- Impedir veículo com permanência aberta e entrada em vaga ocupada, retornando 409.
- Registrar entrada com status ABERTO e marcar a vaga como OCUPADA.
- Na saída, impedir nova finalização e retornar 404 se a permanência não existir.
- Calcular R$ 5,00 por hora, mínimo de uma hora, arredondando frações para cima com math.ceil e usando Decimal para valores monetários.
- Registrar saída, valor_total e status FINALIZADO; liberar a vaga.
- Testar entrada, saída, conflitos e cobrança: 30 minutos = R$ 5; 60 minutos = R$ 5; 61 minutos = R$ 10.
Rotas: POST /api/permanencias/entrada/, PUT /api/permanencias/<id>/saida/ e GET /api/permanencias/

## Combinados para todos

- Atualizar a main e criar uma branch própria antes de começar.
  Sugestões: feat/clientes, feat/veiculos, feat/vagas-dashboard, feat/permanencias e feat/infra-django.
- Cada pessoa cria os arquivos da sua parte e usa os models já existentes.
- Não alterar o frontend. Consultar os controllers Java e frontend/js para manter campos JSON, formatos, filtros e comportamento.
- Usar function-based views, JsonResponse e json.loads(request.body).
- Validar método HTTP, JSON inválido e campos; erros devem retornar JSON com a chave error e status apropriado.
- Serialização manual: cada pessoa implementa a função *_to_dict correspondente à sua parte.
- Combinar com Matheus antes de alterar settings, urls, models, migrations ou Docker.
- Abrir pull request para Matheus integrar, evitando commits diretos na main.
- Cada pessoa testa seus endpoints; Matheus organiza também o teste integrado.
- Não commitar .venv ou db.sqlite3. As migrations devem entrar no Git.

## Preparação local dos colegas

Depois de clonar o repositório, executar no PowerShell:
```powershell
cd backend-django
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver 8080
```

Usar Python 3.12 ou superior; requirements.txt fixa Django 6.1.2 (ambiente validado com Python 3.14). Clientes, vagas e dashboard já estão conectados. O Compose agora sobe Django + SQLite e o frontend Nginx; veículos e permanências aguardam as entregas indicadas acima.

