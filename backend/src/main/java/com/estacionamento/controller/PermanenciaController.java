package com.estacionamento.controller;

import com.estacionamento.model.Permanencia;
import com.estacionamento.repository.PermanenciaRepository;
import com.estacionamento.service.PermanenciaService;
import com.estacionamento.util.HttpUtil;
import com.estacionamento.util.JsonUtil;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;

public class PermanenciaController implements HttpHandler {

    private static final String BASE = "/api/permanencias";
    private final PermanenciaService service = new PermanenciaService();
    private final PermanenciaRepository repository = new PermanenciaRepository();

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        if ("OPTIONS".equals(exchange.getRequestMethod())) {
            HttpUtil.sendResponse(exchange, 204, "");
            return;
        }

        String method = exchange.getRequestMethod();
        String path   = exchange.getRequestURI().getPath();
        // relative path after /api/permanencias
        String relative = path.substring(BASE.length());

        try {
            if ("GET".equals(method) && (relative.isEmpty() || "/".equals(relative))) {
                handleGetAll(exchange);

            } else if ("POST".equals(method) && "/entrada".equals(relative)) {
                handleEntrada(exchange);

            } else if ("PUT".equals(method) && relative.matches("/\\d+/saida")) {
                // Extract ID from /123/saida
                String[] parts = relative.split("/");
                Long id = Long.parseLong(parts[1]);
                handleSaida(exchange, id);

            } else if ("GET".equals(method) && relative.matches("/\\d+")) {
                Long id = Long.parseLong(relative.substring(1));
                handleGetById(exchange, id);

            } else {
                HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Endpoint não encontrado"));
            }

        } catch (NumberFormatException e) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("ID inválido"));
        } catch (IllegalArgumentException e) {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson(e.getMessage()));
        } catch (IllegalStateException e) {
            HttpUtil.sendResponse(exchange, 409, JsonUtil.errorJson(e.getMessage()));
        } catch (SQLException e) {
            HttpUtil.sendResponse(exchange, 500, JsonUtil.errorJson("Erro no banco de dados: " + e.getMessage()));
        }
    }

    private void handleGetAll(HttpExchange exchange) throws IOException, SQLException {
        String statusFilter = HttpUtil.getQueryParam(exchange, "status");
        List<Permanencia> list = repository.findAll(statusFilter);
        HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(list));
    }

    private void handleGetById(HttpExchange exchange, Long id) throws IOException, SQLException {
        repository.findById(id).ifPresent(p -> {
            try {
                HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(p));
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        });
    }

    private void handleEntrada(HttpExchange exchange) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        JsonObject json = new JsonParser().parse(body).getAsJsonObject();

        if (!json.has("veiculoId") || !json.has("vagaId")) {
            HttpUtil.sendResponse(exchange, 400,
                    JsonUtil.errorJson("Campos 'veiculoId' e 'vagaId' são obrigatórios"));
            return;
        }

        Long veiculoId = json.get("veiculoId").getAsLong();
        Long vagaId    = json.get("vagaId").getAsLong();

        Permanencia p = service.registrarEntrada(veiculoId, vagaId);
        HttpUtil.sendResponse(exchange, 201, JsonUtil.toJson(p));
    }

    private void handleSaida(HttpExchange exchange, Long id) throws IOException, SQLException {
        Permanencia p = service.registrarSaida(id);
        HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(p));
    }
}
