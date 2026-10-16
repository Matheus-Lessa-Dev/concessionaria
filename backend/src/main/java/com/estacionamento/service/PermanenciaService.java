package com.estacionamento.service;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.model.Permanencia;
import com.estacionamento.model.Vaga;
import com.estacionamento.repository.PermanenciaRepository;
import com.estacionamento.repository.VagaRepository;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.SQLException;
import java.time.LocalDateTime;
import java.time.temporal.ChronoUnit;

public class PermanenciaService {

    private static final BigDecimal TARIFA_POR_HORA = new BigDecimal("5.00");

    private final PermanenciaRepository permanenciaRepository = new PermanenciaRepository();
    private final VagaRepository vagaRepository = new VagaRepository();

    public Permanencia registrarEntrada(Long veiculoId, Long vagaId) throws SQLException {
        try (Connection conn = DatabaseConnection.getConnection()) {
            conn.setAutoCommit(false);
            try {
                // Verifica se o veículo já tem permanência aberta
                if (permanenciaRepository.existsVeiculoAberto(veiculoId, conn)) {
                    throw new IllegalStateException("Veículo já possui uma permanência em aberto.");
                }

                // Bloqueia a vaga para evitar concorrência
                Vaga vaga = vagaRepository.findByIdForUpdate(vagaId, conn)
                        .orElseThrow(() -> new IllegalArgumentException("Vaga não encontrada."));

                if ("OCUPADA".equals(vaga.getStatus())) {
                    throw new IllegalStateException("Vaga já está ocupada.");
                }

                // Marca vaga como ocupada
                vagaRepository.updateStatus(vagaId, "OCUPADA", conn);

                // Cria permanência
                Permanencia p = new Permanencia();
                p.setVeiculoId(veiculoId);
                p.setVagaId(vagaId);
                p.setDataHoraEntrada(LocalDateTime.now());
                p.setStatus("ABERTO");

                p = permanenciaRepository.save(p, conn);
                conn.commit();
                return p;

            } catch (Exception e) {
                conn.rollback();
                throw e;
            }
        }
    }

    public Permanencia registrarSaida(Long permanenciaId) throws SQLException {
        try (Connection conn = DatabaseConnection.getConnection()) {
            conn.setAutoCommit(false);
            try {
                Permanencia p = permanenciaRepository.findByIdForUpdate(permanenciaId, conn)
                        .orElseThrow(() -> new IllegalArgumentException("Permanência não encontrada."));

                if ("FINALIZADO".equals(p.getStatus())) {
                    throw new IllegalStateException("Permanência já foi finalizada.");
                }

                LocalDateTime saida = LocalDateTime.now();
                BigDecimal valor = calcularValor(p.getDataHoraEntrada(), saida);

                permanenciaRepository.finalizarPermanencia(permanenciaId, saida, valor, conn);
                vagaRepository.updateStatus(p.getVagaId(), "LIVRE", conn);

                p.setDataHoraSaida(saida);
                p.setValorTotal(valor);
                p.setStatus("FINALIZADO");

                conn.commit();
                return p;

            } catch (Exception e) {
                conn.rollback();
                throw e;
            }
        }
    }

    /**
     * Calcula o valor com base na duração.
     * Mínimo de 1 hora; frações de hora são arredondadas para cima.
     * Tarifa: R$ 5,00/hora.
     */
    private BigDecimal calcularValor(LocalDateTime entrada, LocalDateTime saida) {
        long minutos = ChronoUnit.MINUTES.between(entrada, saida);
        long horas = (minutos + 59) / 60; // arredonda para cima
        if (horas < 1) horas = 1;         // mínimo 1 hora
        return TARIFA_POR_HORA.multiply(BigDecimal.valueOf(horas));
    }
}
