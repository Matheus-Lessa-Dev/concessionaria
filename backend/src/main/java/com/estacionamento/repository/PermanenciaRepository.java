package com.estacionamento.repository;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.model.Permanencia;

import java.math.BigDecimal;
import java.sql.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class PermanenciaRepository {

    private static final String SELECT_BASE =
            "SELECT p.id, p.veiculo_id, v.placa AS veiculo_placa, v.modelo AS veiculo_modelo, " +
            "       p.vaga_id, va.numero AS vaga_numero, " +
            "       p.data_hora_entrada, p.data_hora_saida, p.valor_total, p.status " +
            "FROM permanencias p " +
            "JOIN veiculos v  ON v.id  = p.veiculo_id " +
            "JOIN vagas    va ON va.id = p.vaga_id ";

    public List<Permanencia> findAll(String statusFilter) throws SQLException {
        List<Permanencia> list = new ArrayList<>();
        String sql = SELECT_BASE;
        if (statusFilter != null && !statusFilter.isEmpty()) {
            sql += "WHERE p.status = ? ";
        }
        sql += "ORDER BY p.data_hora_entrada DESC";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            if (statusFilter != null && !statusFilter.isEmpty()) {
                ps.setString(1, statusFilter);
            }
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    list.add(mapRow(rs));
                }
            }
        }
        return list;
    }

    public Optional<Permanencia> findById(Long id) throws SQLException {
        String sql = SELECT_BASE + "WHERE p.id = ?";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return Optional.of(mapRow(rs));
                }
            }
        }
        return Optional.empty();
    }

    /** Used inside a transaction. */
    public Optional<Permanencia> findByIdForUpdate(Long id, Connection conn) throws SQLException {
        String sql = SELECT_BASE + "WHERE p.id = ? FOR UPDATE OF p";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return Optional.of(mapRow(rs));
                }
            }
        }
        return Optional.empty();
    }

    /** Used inside a transaction – check for open permanencia for this vehicle. */
    public boolean existsVeiculoAberto(Long veiculoId, Connection conn) throws SQLException {
        String sql = "SELECT 1 FROM permanencias WHERE veiculo_id = ? AND status = 'ABERTO' LIMIT 1";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, veiculoId);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next();
            }
        }
    }

    /** Used inside a transaction. */
    public Permanencia save(Permanencia p, Connection conn) throws SQLException {
        String sql = "INSERT INTO permanencias (veiculo_id, vaga_id, data_hora_entrada, status) " +
                     "VALUES (?, ?, ?, 'ABERTO') RETURNING id";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, p.getVeiculoId());
            ps.setLong(2, p.getVagaId());
            ps.setTimestamp(3, Timestamp.valueOf(p.getDataHoraEntrada()));
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    p.setId(rs.getLong(1));
                }
            }
        }
        return p;
    }

    /** Used inside a transaction. */
    public void finalizarPermanencia(Long id, LocalDateTime saida, BigDecimal valor, Connection conn)
            throws SQLException {
        String sql = "UPDATE permanencias SET data_hora_saida = ?, valor_total = ?, status = 'FINALIZADO' WHERE id = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setTimestamp(1, Timestamp.valueOf(saida));
            ps.setBigDecimal(2, valor);
            ps.setLong(3, id);
            ps.executeUpdate();
        }
    }

    private Permanencia mapRow(ResultSet rs) throws SQLException {
        Permanencia p = new Permanencia();
        p.setId(rs.getLong("id"));
        p.setVeiculoId(rs.getLong("veiculo_id"));
        p.setVeiculoPlaca(rs.getString("veiculo_placa"));
        p.setVeiculoModelo(rs.getString("veiculo_modelo"));
        p.setVagaId(rs.getLong("vaga_id"));
        p.setVagaNumero(rs.getString("vaga_numero"));

        Timestamp entrada = rs.getTimestamp("data_hora_entrada");
        if (entrada != null) p.setDataHoraEntrada(entrada.toLocalDateTime());

        Timestamp saida = rs.getTimestamp("data_hora_saida");
        if (saida != null) p.setDataHoraSaida(saida.toLocalDateTime());

        BigDecimal valor = rs.getBigDecimal("valor_total");
        p.setValorTotal(valor);
        p.setStatus(rs.getString("status"));
        return p;
    }
}
