-- ─────────────────────────────────────────────────────────────────────────────
-- Schema do Sistema de Estacionamento
-- Executado automaticamente pelo PostgreSQL na primeira inicialização.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS clientes (
    id        BIGSERIAL    PRIMARY KEY,
    nome      VARCHAR(100) NOT NULL,
    cpf       VARCHAR(14)  UNIQUE NOT NULL,
    telefone  VARCHAR(20),
    email     VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS veiculos (
    id         BIGSERIAL    PRIMARY KEY,
    placa      VARCHAR(10)  UNIQUE NOT NULL,
    marca      VARCHAR(50)  NOT NULL,
    modelo     VARCHAR(50)  NOT NULL,
    cor        VARCHAR(30)  NOT NULL,
    cliente_id BIGINT       NOT NULL REFERENCES clientes(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS vagas (
    id     BIGSERIAL   PRIMARY KEY,
    numero VARCHAR(10) UNIQUE NOT NULL,
    tipo   VARCHAR(5)  NOT NULL CHECK (tipo   IN ('CARRO', 'MOTO')),
    status VARCHAR(7)  NOT NULL DEFAULT 'LIVRE' CHECK (status IN ('LIVRE', 'OCUPADA'))
);

CREATE TABLE IF NOT EXISTS permanencias (
    id                BIGSERIAL     PRIMARY KEY,
    veiculo_id        BIGINT        NOT NULL REFERENCES veiculos(id),
    vaga_id           BIGINT        NOT NULL REFERENCES vagas(id),
    data_hora_entrada TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_hora_saida   TIMESTAMP,
    valor_total       DECIMAL(10,2),
    status            VARCHAR(10)   NOT NULL DEFAULT 'ABERTO'
                                    CHECK (status IN ('ABERTO', 'FINALIZADO'))
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_permanencias_status     ON permanencias(status);
CREATE INDEX IF NOT EXISTS idx_permanencias_veiculo_id ON permanencias(veiculo_id);
CREATE INDEX IF NOT EXISTS idx_permanencias_vaga_id    ON permanencias(vaga_id);
CREATE INDEX IF NOT EXISTS idx_veiculos_cliente_id     ON veiculos(cliente_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Dados iniciais: vagas de exemplo
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO vagas (numero, tipo) VALUES
    ('A01', 'CARRO'), ('A02', 'CARRO'), ('A03', 'CARRO'),
    ('A04', 'CARRO'), ('A05', 'CARRO'), ('A06', 'CARRO'),
    ('A07', 'CARRO'), ('A08', 'CARRO'), ('A09', 'CARRO'),
    ('A10', 'CARRO'),
    ('B01', 'MOTO'),  ('B02', 'MOTO'),  ('B03', 'MOTO'),
    ('B04', 'MOTO'),  ('B05', 'MOTO')
ON CONFLICT (numero) DO NOTHING;
