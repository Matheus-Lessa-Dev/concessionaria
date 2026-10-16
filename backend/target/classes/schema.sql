-- Este arquivo documenta o schema; a criação real ocorre via database/init.sql

CREATE TABLE IF NOT EXISTS clientes (
    id        BIGSERIAL PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    cpf       VARCHAR(14)  UNIQUE NOT NULL,
    telefone  VARCHAR(20),
    email     VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS veiculos (
    id         BIGSERIAL PRIMARY KEY,
    placa      VARCHAR(10) UNIQUE NOT NULL,
    marca      VARCHAR(50) NOT NULL,
    modelo     VARCHAR(50) NOT NULL,
    cor        VARCHAR(30) NOT NULL,
    cliente_id BIGINT NOT NULL REFERENCES clientes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vagas (
    id     BIGSERIAL PRIMARY KEY,
    numero VARCHAR(10) UNIQUE NOT NULL,
    tipo   VARCHAR(5)  NOT NULL CHECK (tipo   IN ('CARRO', 'MOTO')),
    status VARCHAR(7)  NOT NULL DEFAULT 'LIVRE' CHECK (status IN ('LIVRE', 'OCUPADA'))
);

CREATE TABLE IF NOT EXISTS permanencias (
    id                BIGSERIAL PRIMARY KEY,
    veiculo_id        BIGINT NOT NULL REFERENCES veiculos(id),
    vaga_id           BIGINT NOT NULL REFERENCES vagas(id),
    data_hora_entrada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_hora_saida   TIMESTAMP,
    valor_total       DECIMAL(10,2),
    status            VARCHAR(10) NOT NULL DEFAULT 'ABERTO' CHECK (status IN ('ABERTO', 'FINALIZADO'))
);
