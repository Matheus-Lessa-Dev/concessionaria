# Divisão do trabalho — Sistema de Estacionamento
Repositório: https://github.com/Matheus-Lessa-Dev/concessionaria
Conferência: 30/10/2026 — main, commit 46584d0bfa550d9f4fa6f1b7e9b5234f6191d780

## Objetivo

Substituir o backend Java por Python + Django e o PostgreSQL por SQLite, mantendo o frontend e os contratos da API existentes. Usar somente Django e bibliotecas padrão do Python, sem Django REST Framework.

## Situação atual

A estrutura está preparada para começar o trabalho em equipe:
- Projeto Django e app api criados.
- Models de Cliente, Veiculo, Vaga e Permanencia e migration inicial presentes.
- api registrado em INSTALLED_APPS, SQLite configurado, ALLOWED_HOSTS = ['*'] e USE_TZ = False.
- Pastas api/views e api/services com __init__.py.
- .gitignore ignora .venv, __pycache__, arquivos .pyc e db.sqlite3.
Esta conferência foi feita pela leitura dos arquivos no GitHub, sem executar o projeto.
Os endpoints, CORS e adaptação do Docker ainda precisam ser implementados.

## Matheus — configuração e integração

- Criar estacionamento/middleware.py para CORS, incluindo OPTIONS com HTTP 204.
- Configurar a dispensa de CSRF para a API e registrar o middleware.
- Criar api/urls.py e conectar em estacionamento/urls.py.
- Registrar as rotas conforme as funções dos colegas forem entregues.
- Garantir que as URLs sem barra final usadas pelo frontend funcionem, incluindo POST e PUT.
- Criar backend-django/Dockerfile e ajustar docker-compose.yml para Django na porta 8080, sem PostgreSQL.
- Configurar DB_PATH e volume persistente do SQLite; executar migrate na inicialização.
- Centralizar mudanças necessárias em models e migrations.
- Integrar as branches, atualizar o README e validar o sistema completo pelo frontend.
- Conferir criação automática do banco e persistência após docker compose restart.
Arquivos principais: estacionamento/settings.py, estacionamento/middleware.py, estacionamento/urls.py, api/urls.py, backend-django/Dockerfile e docker-compose.yml.

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

Usar uma versão de Python compatível com o Django instalado. As rotas da API só funcionarão depois de implementadas e conectadas. Enquanto o Compose não for adaptado, ele continua subindo Java + PostgreSQL.

