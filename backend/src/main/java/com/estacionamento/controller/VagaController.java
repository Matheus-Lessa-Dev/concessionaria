package com.estacionamento.controller;

import com.estacionamento.model.Vaga;
import com.estacionamento.repository.VagaRepository;
import com.estacionamento.util.HttpUtil;
import com.estacionamento.util.JsonUtil;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.sql.SQLException;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;

public class VagaController implements HttpHandler {

    private static final String BASE = "/api/vagas";
    private static final List<String> TIPOS   = Arrays.asList("CARRO", "MOTO");
    private static final List<String> STATUSES = Arrays.asList("LIVRE", "OCUPADA");

    private final VagaRepository repository = new VagaRepository();

    @Override
    public void handle(HttpExchange exchange) throws IOException {
        if ("OPTIONS".equals(exchange.getRequestMethod())) {
            HttpUtil.sendResponse(exchange, 204, "");
            return;
        }

        String method = exchange.getRequestMethod();
        String id = HttpUtil.extractId(exchange, BASE);

        try {
            switch (method) {
                case "GET":
                    if (id == null) handleGetAll(exchange);
                    else            handleGetById(exchange, Long.parseLong(id));
                    break;
                case "POST":
                    handleCreate(exchange);
                    break;
                case "PUT":
                    if (id != null) handleUpdate(exchange, Long.parseLong(id));
                    else HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("ID obrigatório"));
                    break;
                case "DELETE":
                    if (id != null) handleDelete(exchange, Long.parseLong(id));
                    else HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("ID obrigatório"));
                    break;
                default:
                    HttpUtil.sendResponse(exchange, 405, JsonUtil.errorJson("Método não permitido"));
            }
        } catch (NumberFormatException e) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("ID inválido"));
        } catch (SQLException e) {
            HttpUtil.sendResponse(exchange, 500, JsonUtil.errorJson("Erro no banco de dados: " + e.getMessage()));
        }
    }

    private void handleGetAll(HttpExchange exchange) throws IOException, SQLException {
        String statusFilter = HttpUtil.getQueryParam(exchange, "status");
        List<Vaga> list = repository.findAll(statusFilter);
        HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(list));
    }

    private void handleGetById(HttpExchange exchange, Long id) throws IOException, SQLException {
        Optional<Vaga> opt = repository.findById(id);
        if (opt.isPresent()) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(opt.get()));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Vaga não encontrada"));
        }
    }

    private void handleCreate(HttpExchange exchange) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Vaga vaga = JsonUtil.fromJson(body, Vaga.class);

        if (!validar(exchange, vaga)) return;

        try {
            Vaga saved = repository.save(vaga);
            HttpUtil.sendResponse(exchange, 201, JsonUtil.toJson(saved));
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("unique")) {
                HttpUtil.sendResponse(exchange, 409, JsonUtil.errorJson("Número de vaga já cadastrado"));
            } else {
                throw e;
            }
        }
    }

    private void handleUpdate(HttpExchange exchange, Long id) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Vaga vaga = JsonUtil.fromJson(body, Vaga.class);
        vaga.setId(id);

        if (!validar(exchange, vaga)) return;

        if (vaga.getStatus() == null || !STATUSES.contains(vaga.getStatus())) {
            vaga.setStatus("LIVRE");
        }

        if (repository.update(vaga)) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(vaga));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Vaga não encontrada"));
        }
    }

    private void handleDelete(HttpExchange exchange, Long id) throws IOException, SQLException {
        try {
            if (repository.delete(id)) {
                HttpUtil.sendResponse(exchange, 200, JsonUtil.messageJson("Vaga excluída com sucesso"));
            } else {
                HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Vaga não encontrada"));
            }
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("foreign key")) {
                HttpUtil.sendResponse(exchange, 409,
                        JsonUtil.errorJson("Não é possível excluir vaga com permanências registradas"));
            } else {
                throw e;
            }
        }
    }

    private boolean validar(HttpExchange exchange, Vaga vaga) throws IOException {
        if (vaga.getNumero() == null || vaga.getNumero().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'numero' é obrigatório"));
            return false;
        }
        if (vaga.getTipo() == null || !TIPOS.contains(vaga.getTipo())) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'tipo' deve ser CARRO ou MOTO"));
            return false;
        }
        return true;
    }
}
