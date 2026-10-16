package com.estacionamento.repository;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.model.Veiculo;

import java.sql.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

public class VeiculoRepository {

    private static final String SELECT_BASE =
            "SELECT v.id, v.placa, v.marca, v.modelo, v.cor, v.cliente_id, c.nome AS cliente_nome " +
            "FROM veiculos v JOIN clientes c ON c.id = v.cliente_id ";

    public List<Veiculo> findAll() throws SQLException {
        List<Veiculo> list = new ArrayList<>();
        String sql = SELECT_BASE + "ORDER BY v.placa";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            while (rs.next()) {
                list.add(mapRow(rs));
            }
        }
        return list;
    }

    public Optional<Veiculo> findById(Long id) throws SQLException {
        String sql = SELECT_BASE + "WHERE v.id = ?";
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

    public Veiculo save(Veiculo v) throws SQLException {
        String sql = "INSERT INTO veiculos (placa, marca, modelo, cor, cliente_id) VALUES (?, ?, ?, ?, ?) RETURNING id";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, v.getPlaca());
            ps.setString(2, v.getMarca());
            ps.setString(3, v.getModelo());
            ps.setString(4, v.getCor());
            ps.setLong(5, v.getClienteId());
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    v.setId(rs.getLong(1));
                }
            }
        }
        return v;
    }

    public boolean update(Veiculo v) throws SQLException {
        String sql = "UPDATE veiculos SET placa = ?, marca = ?, modelo = ?, cor = ?, cliente_id = ? WHERE id = ?";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, v.getPlaca());
            ps.setString(2, v.getMarca());
            ps.setString(3, v.getModelo());
            ps.setString(4, v.getCor());
            ps.setLong(5, v.getClienteId());
            ps.setLong(6, v.getId());
            return ps.executeUpdate() > 0;
        }
    }

    public boolean delete(Long id) throws SQLException {
        String sql = "DELETE FROM veiculos WHERE id = ?";
        try (Connection conn = DatabaseConnection.getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setLong(1, id);
            return ps.executeUpdate() > 0;
        }
    }

    private Veiculo mapRow(ResultSet rs) throws SQLException {
        Veiculo v = new Veiculo();
        v.setId(rs.getLong("id"));
        v.setPlaca(rs.getString("placa"));
        v.setMarca(rs.getString("marca"));
        v.setModelo(rs.getString("modelo"));
        v.setCor(rs.getString("cor"));
        v.setClienteId(rs.getLong("cliente_id"));
        v.setClienteNome(rs.getString("cliente_nome"));
        return v;
    }
}
