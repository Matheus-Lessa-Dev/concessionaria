package com.estacionamento.repository;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.model.Vaga;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class VagaRepository {

    public List<Vaga> findAll(String statusFilter) throws SQLException {
        List<Vaga> list = new ArrayList<>();
        String sql = "SELECT id, numero, tipo, status FROM vagas";
        if (statusFilter != null && !statusFilter.isEmpty()) {
            sql += " WHERE status = ?";
        }
        sql += " ORDER BY numero";
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

    public Optional<Vaga> findById(Long id) throws SQLException {
        String sql = "SELECT id, numero, tipo, status FROM vagas WHERE id = ?";
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

    /** Used inside a transaction – SELECT FOR UPDATE to lock the row. */
    public Optional<Vaga> findByIdForUpdate(Long id, Connection conn) throws SQLException {
        String sql = "SELECT id, numero, tipo, status FROM vagas WHERE id = ? FOR UPDATE";
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

    public Vaga save(Vaga vaga) throws SQLException {
        String sql = "INSERT INTO vagas (numero, tipo, status) VALUES (?, ?, 'LIVRE') RETURNING id";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, vaga.getNumero());
            ps.setString(2, vaga.getTipo());
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    vaga.setId(rs.getLong(1));
                    vaga.setStatus("LIVRE");
                }
            }
        }
        return vaga;
    }

    public boolean update(Vaga vaga) throws SQLException {
        String sql = "UPDATE vagas SET numero = ?, tipo = ?, status = ? WHERE id = ?";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, vaga.getNumero());
            ps.setString(2, vaga.getTipo());
            ps.setString(3, vaga.getStatus());
            ps.setLong(4, vaga.getId());
            return ps.executeUpdate() > 0;
        }
    }

    /** Used inside a transaction. */
    public void updateStatus(Long id, String status, Connection conn) throws SQLException {
        String sql = "UPDATE vagas SET status = ? WHERE id = ?";
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, status);
            ps.setLong(2, id);
            ps.executeUpdate();
        }
    }

    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM vagas WHERE id = ?";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            return ps.executeUpdate() > 0;
        }
    }

    private Vaga mapRow(ResultSet rs) throws SQLException {
        Vaga v = new Vaga();
        v.setId(rs.getLong("id"));
        v.setNumero(rs.getString("numero"));
        v.setTipo(rs.getString("tipo"));
        v.setStatus(rs.getString("status"));
        return v;
    }
}
