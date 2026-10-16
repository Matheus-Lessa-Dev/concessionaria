package com.estacionamento.controller;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.util.HttpUtil;
import com.estacionamento.util.JsonUtil;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.sql.*;
import java.util.LinkedHashMap;
import java.util.Map;

public class DashboardController implements HttpHandler {

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        if ("OPTIONS".equals(exchange.getRequestMethod())) {
            HttpUtil.sendResponse(exchange, 204, "");
            return;
        }

        if (!"GET".equals(exchange.getRequestMethod())) {
            HttpUtil.sendResponse(exchange, 405, JsonUtil.errorJson("Método não permitido"));
            return;
        }

        try {
            Map<String, Long> data = getDashboardData();
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(data));
        } catch (SQLException e) {
            HttpUtil.sendResponse(exchange, 500, JsonUtil.errorJson("Erro no banco de dados: " + e.getMessage()));
        }
    }

    private Map<String, Long> getDashboardData() throws SQLException {
        Map<String, Long> data = new LinkedHashMap<>();

        try (Connection conn = DatabaseConnection.getConnection()) {
            // Estatísticas das vagas
            String sqlVagas =
                    "SELECT " +
                    "  COUNT(*) AS total_vagas, " +
                    "  SUM(CASE WHEN status = 'LIVRE'    THEN 1 ELSE 0 END) AS vagas_livres, " +
                    "  SUM(CASE WHEN status = 'OCUPADA'  THEN 1 ELSE 0 END) AS vagas_ocupadas " +
                    "FROM vagas";

            try (PreparedStatement ps = conn.prepareStatement(sqlVagas);
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    data.put("totalVagas",    rs.getLong("total_vagas"));
                    data.put("vagasLivres",   rs.getLong("vagas_livres"));
                    data.put("vagasOcupadas", rs.getLong("vagas_ocupadas"));
                }
            }

            // Veículos estacionados (permanências abertas)
            String sqlEstacionados =
                    "SELECT COUNT(*) AS veiculos_estacionados FROM permanencias WHERE status = 'ABERTO'";

            try (PreparedStatement ps = conn.prepareStatement(sqlEstacionados);
                 ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    data.put("veiculosEstacionados", rs.getLong("veiculos_estacionados"));
                }
            }
        }

        return data;
    }
}
