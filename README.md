# Sistema de Estacionamento

Trabalho em grupo de migração do backend Java para **Python + Django** e do PostgreSQL para **SQLite**, preservando o frontend HTML, CSS e JavaScript e os contratos da API. O backend usa views funcionais, `JsonResponse` e serialização manual, sem Django REST Framework.

## Estado da migração

Conferido em 13/11/2026, com os ajustes finais na `main`, sobre o commit `bf52a61`, prontos para commit. O [relatório de aceite](VALIDACAO-ATIVIDADE.md) relaciona as verificações às tarefas do professor.

- Clientes, veículos, vagas, permanências e dashboard estão integrados às URLs reais do Django.
- A infraestrutura executa Django na porta 8080 e Nginx na porta 3000, com SQLite persistente e migrations automáticas.
- O fluxo de cadastro, entrada, conflitos, saída, cobrança e histórico foi validado no frontend e pela API.
- **102 testes aprovados** no Windows e no Linux/Docker, com models/migrations alinhados, frontend original preservado e sem apps de autenticação ou sessões. Consulte [DIVISAO-TRABALHO.md](DIVISAO-TRABALHO.md) para responsabilidades e conclusão das entregas.

## Executar com Docker

Pré-requisitos: Docker com suporte a containers Linux e Docker Compose v2 ou superior. No Windows, inicie o Docker Desktop.

Na raiz do repositório:

```bash
docker compose up --build -d
```

| Serviço | Endereço |
|---------|----------|
| Frontend Nginx | http://localhost:3000 |
| API Django | http://localhost:8080/api/dashboard |

A inicialização cria o diretório do banco, executa `python manage.py migrate --noinput` e inicia o servidor Django. O frontend aguarda o healthcheck do backend e usa o proxy `/api/` já existente. O projeto utiliza o servidor de desenvolvimento do Django para o trabalho acadêmico.

```bash
docker compose ps
docker compose logs -f backend
docker compose restart
docker compose down
```

### Banco e persistência

- No container, `DB_PATH=/data/db.sqlite3` e o volume nomeado `sqlite_data` fica montado em `/data`.
- O banco é criado automaticamente pelas migrations e começa vazio. Cadastre clientes e vagas pelo frontend.
- `restart`, recriação dos containers e `down` seguido de `up` preservam o volume. **`docker compose down -v` apaga o volume e os dados SQLite.**
- Os arquivos SQLite locais e `.venv` ficam fora da imagem Docker.
- O Compose atual não usa PostgreSQL nem `database/init.sql`. Dados do PostgreSQL antigo não são convertidos automaticamente para SQLite; o backend Java e o SQL original permanecem no repositório como referência.

## Executar Django localmente

Python **3.12 ou superior**; ambiente validado com Python 3.14 e Django 6.1.2, versão fixada em `requirements.txt`.

No PowerShell:

```powershell
cd backend-django
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
python manage.py runserver 8080
```

No Linux/macOS, ative o ambiente com `source .venv/bin/activate` e execute os mesmos comandos Python.

Sem `DB_PATH`, o Django usa `backend-django/db.sqlite3`. Para outro caminho, configure a variável antes dos comandos e crie a pasta de destino. Exemplo no PowerShell:

```powershell
New-Item -ItemType Directory -Force dados
$env:DB_PATH = "$PWD/dados/db.sqlite3"
python manage.py migrate
python manage.py runserver 8080
```

Para usar o frontend com o backend local, configure uma cópia do `frontend/nginx.conf` para encaminhar `backend:8080` a `127.0.0.1:8080` e sirva os arquivos estáticos com Nginx. A execução por Docker já fornece esse proxy pronto.

## API integrada

Todas as rotas abaixo aceitam URLs **com e sem barra final**, inclusive POST e PUT, sem redirecionamentos.

| Métodos | Endpoint | Função |
|---------|----------|--------|
| GET, POST | `/api/clientes` | Listar e cadastrar clientes |
| GET, PUT, DELETE | `/api/clientes/{id}` | Consultar, editar e excluir cliente |
| GET, POST | `/api/veiculos` | Listar e cadastrar veículos |
| GET, PUT, DELETE | `/api/veiculos/{id}` | Consultar, editar e excluir veículo |
| GET, POST | `/api/vagas` | Listar e cadastrar vagas |
| GET, PUT, DELETE | `/api/vagas/{id}` | Consultar, editar e excluir vaga |
| GET | `/api/vagas?status=LIVRE` | Filtrar vagas livres |
| GET | `/api/dashboard` | Indicadores do estacionamento |
| GET | `/api/permanencias` | Listar permanências e histórico |
| POST | `/api/permanencias/entrada` | Registrar entrada e ocupar vaga |
| PUT | `/api/permanencias/{id}/saida` | Finalizar, cobrar e liberar vaga |

O dashboard retorna `totalVagas`, `vagasLivres`, `vagasOcupadas` e `veiculosEstacionados`.

A API tem dispensa de CSRF centralizada em `estacionamento.middleware.ApiCsrfMiddleware`, limitada a `/api/`. `INSTALLED_APPS` contém somente `api`: não há apps, middleware ou endpoints de autenticação, sessões e admin. O middleware CORS responde a OPTIONS com HTTP 204 e permite GET, POST, PUT, DELETE e o cabeçalho Content-Type. Rotas desconhecidas da API retornam HTTP 404 com a chave JSON `error`; os erros de método de clientes também retornam JSON e o cabeçalho `Allow`.

### Permanências e integridade

- Filtre `/api/permanencias?status=ABERTO` para veículos estacionados e `?status=FINALIZADO` para o histórico.
- Tarifa de **R$ 5 por hora**, mínimo de uma hora e frações arredondadas para cima: 30 min = R$ 5; 60 min = R$ 5; 61 min = R$ 10. O cálculo usa inteiros, `Decimal` e `math.ceil`, sem conversão para `float`.
- Entradas em vaga ocupada, veículo já estacionado e saídas duplicadas retornam 409. Recursos inexistentes retornam 404; IDs e JSON inválidos na entrada retornam 400, sempre com `error`.
- Entrada e saída são atômicas. O SQLite usa transações `IMMEDIATE` e espera de até 20 segundos pela escrita, evitando que duas operações confirmem a mesma vaga ou o mesmo veículo simultaneamente.
- Editar uma vaga preserva seu status quando omitido ou nulo. Tentar liberá-la com permanência aberta retorna 409; registre a saída pelo fluxo de permanências.
- Veículos e vagas com permanências registradas têm a exclusão bloqueada com 409, preservando o histórico. Excluir um cliente também é bloqueado quando seus veículos têm permanências. Sem permanências, os veículos do cliente são excluídos em cascata, como no banco original.
- O frontend foi mantido igual ao projeto original. Abra **Clientes antes de cadastrar um veículo**, inclusive após recarregar a página: o formulário original usa a lista de clientes carregada nessa tela.

## Validação

Na pasta `backend-django`:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

Com Docker, os mesmos comandos podem ser executados com `docker compose exec backend python manage.py ...`, a partir da raiz.

Verificações executadas em 13/11/2026:

- `check` sem problemas e `makemigrations --check --dry-run` sem alterações. `DEFAULT_AUTO_FIELD` alinhado ao `BigAutoField` da migration inicial, sem nova migration.
- **102 testes aprovados** em Windows e Linux: clientes, veículos, vagas, dashboard, permanências e integração. Incluem todas as rotas com/sem barra, tarifas de 30/60/61 minutos com relógio controlado, fração de um microssegundo após uma hora, mínimo de cobrança, múltiplos dias, exclusões protegidas por relações reais e reversão de alterações se entrada/saída falharem.
- Build e inicialização dos containers com migrations automáticas; entrypoint também testado em um container temporário sem banco prévio. Somente as quatro tabelas da API e as tabelas de controle de migrations/SQLite foram criadas, sem tabelas de autenticação ou sessões.
- Frontend original em Chrome headless pelo Nginx: cadastro de cliente, recarga da página com abertura de Clientes, cadastro de veículo e vagas, entrada, conflito exibido ao usuário, saída com R$ 5, histórico e totais do dashboard. Capturas de tela inspecionadas e nenhum erro JavaScript encontrado.
- Requisições simultâneas pelo Nginx: mesmo veículo em vagas diferentes, veículos diferentes na mesma vaga e saída duplicada. Em cada disputa, uma operação foi aceita e a outra retornou 409.
- Persistência dos registros e IDs de clientes, veículos, vagas, permanências e cobrança após `docker compose restart` e recriação dos containers, preservando o volume. Somente os registros criados para validação foram removidos ao final.

Para repetir os cenários automatizados do fluxo completo, execute `python manage.py test api.test_fluxo_completo`. O fluxo visual pode ser repetido pelo frontend: cadastre cliente, veículo e duas vagas; registre uma entrada; tente o mesmo veículo na outra vaga; registre a saída e confira o histórico e o dashboard.

## Estrutura

```text
backend-django/
  api/
    models.py
    migrations/
    urls.py
    views/                 # Endpoints dos integrantes
    services/              # Regras de negócio
    test_integracao.py
    test_fluxo_completo.py
    test_clientes.py
    test_veiculos.py
    test_permanencia.py
    test_vagas_dashboard.py
  estacionamento/
    settings.py
    middleware.py
    urls.py
  Dockerfile
  .dockerignore
  docker-entrypoint.py
  manage.py
  requirements.txt
frontend/                  # HTML, CSS, JavaScript + Nginx
backend/                   # Java original, referência para a migração
database/init.sql          # Schema e dados de exemplo do PostgreSQL original
docker-compose.yml
DIVISAO-TRABALHO.md
```
