# Divisão do trabalho — Sistema de Estacionamento
Repositório: https://github.com/Matheus-Lessa-Dev/concessionaria
Conferência: 13/11/2026 — ajustes finais na main, sobre o commit bf52a61, prontos para commit.

## Objetivo

Substituir o backend Java por Python + Django e o PostgreSQL por SQLite, mantendo o frontend e os contratos da API existentes. Usar somente Django e bibliotecas padrão do Python, sem Django REST Framework.

## Situação atual

- Todas as entregas estão integradas: clientes (Eduarda), veículos (Joabe), vagas e dashboard (Ana) e permanências (C.). Veículos, permanências e testes de clientes chegaram pelos PRs #5, #6 e #7.
- Django + SQLite e Nginx iniciam pelo Docker Compose, com migrations automáticas e volume persistente.
- CORS, OPTIONS 204, dispensa de CSRF somente na API e URLs com/sem barra final estão configurados.
- Configuração de IDs alinhada à migration inicial (`BigAutoField`), sem gerar migration ou modificar dados existentes.
- 102 testes aprovados no Windows e no container Linux; check e makemigrations --check --dry-run aprovados.
- Fluxo completo validado pelas URLs reais, pelo proxy Nginx e pelo frontend em Chrome headless, com inspeção das capturas de tela.
- Entradas, saídas e edição de vagas protegidas por transações SQLite; disputas simultâneas por veículo/vaga e saída duplicada conferidas por HTTP.
- Ajustes finais nos erros 405 de clientes, validação de IDs/JSON de permanências e proteção contra liberação de vaga com permanência aberta.
- Frontend original preservado, conforme o enunciado do professor. A correção anterior de carregamento de clientes no formulário de veículo foi retirada; o fluxo original carrega Clientes antes de abrir o formulário de Veículos.
- Apps de autenticação, sessões, admin e demais apps contrib removidos de `INSTALLED_APPS`; banco novo contém somente as tabelas da API e de controle de migrations/SQLite.
- Cálculo de duração e cobrança usa apenas inteiros e `Decimal`, sem `float`. Veja o [relatório de aceite](VALIDACAO-ATIVIDADE.md).

## Matheus — configuração e integração

A infraestrutura, a integração de todas as entregas e a validação final estão concluídas na main, com as alterações ainda sem commit.

### Concluído

- [x] **FEITO** — CORS e resposta OPTIONS com HTTP 204.
- [x] **FEITO** — Dispensa de CSRF somente na API; proteção fora de `/api/` testada. Admin e login não são expostos.
- [x] **FEITO** — api/urls.py conectado às URLs do projeto; clientes, veículos, vagas, permanências e dashboard registrados.
- [x] **FEITO** — URLs com e sem barra final, incluindo POST e PUT sem redirecionamentos.
- [x] **FEITO** — Docker com Django na porta 8080 e frontend Nginx, sem serviço PostgreSQL.
- [x] **FEITO** — DB_PATH, volume SQLite persistente e migrations automáticas na inicialização.
- [x] **FEITO** — Models e migration inicial conferidos; `DEFAULT_AUTO_FIELD` corrigido para `BigAutoField`.
- [x] **FEITO** — README atualizado com execução, testes e estado da migração.
- [x] **FEITO** — Testes de integração e conferência HTTP pelo Nginx; criação automática do banco e persistência após restart e recriação dos containers.

### Finalização das pendências anteriores

- [x] **FEITO** — Conferência visual de clientes, veículos, vagas, estacionamento, histórico e dashboard.
- [x] **FEITO** — Clientes revalidados; erros 405 retornam JSON com `error` e cabeçalho `Allow`. Exclusões protegidas conferidas com relacionamentos reais.
- [x] **FEITO** — Veículos integrados, com testes e rotas com/sem barra final.
- [x] **FEITO** — Permanências integradas, com imports, serialização, erros e testes de entrada, saída e cobrança.
- [x] **FEITO** — Models/migrations revisados e configuração alinhada ao schema existente.
- [x] **FEITO** — Fluxo completo pelo frontend: cadastro → entrada → conflito → saída → cobrança → histórico e dashboard. Testes integrados com relógio controlado conferem exatamente 30 min = R$ 5, 60 min = R$ 5 e 61 min = R$ 10.
- [x] **FEITO** — Persistência de clientes, veículos, vagas, permanências, valores e IDs após restart e recriação dos containers, preservando o volume SQLite.
- [x] **FEITO** — README atualizado com resultado final e todas as rotas disponíveis.

### Entregas e ajustes concluídos

| Responsável | Situação final |
|-------------|----------------------------------------------|
| Eduarda | Clientes e testes integrados; contrato dos erros 405 corrigido na finalização. |
| Joabe | CRUD de veículos, serialização, validações e testes integrados. |
| Ana | Vagas, dashboard e testes integrados; edição de vaga preserva o status quando omitido e impede liberação com permanência aberta. |
| C. | Permanências e cobrança integradas; entrada/saída atômicas e validação de IDs e JSON reforçadas na finalização. |

**Última conferência:** 13/11/2026. 102 testes aprovados nos dois ambientes, migrations alinhadas, frontend original e API conferidos. Não há dependências técnicas pendentes das entregas dos colegas. Os dados fictícios usados na validação foram removidos ao final, preservando os demais registros.

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
- Não alterar o frontend, conforme o enunciado do professor. Consultar os controllers Java e frontend/js para manter campos JSON, formatos, filtros e comportamento.
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

Usar Python 3.12 ou superior; requirements.txt fixa Django 6.1.2 (ambiente validado com Python 3.14). Todas as rotas estão conectadas. O Compose sobe Django + SQLite e o frontend Nginx; o fluxo de entrada, saída, cobrança e histórico está disponível.

