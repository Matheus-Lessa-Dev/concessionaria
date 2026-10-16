package com.estacionamento.controller;

import com.estacionamento.model.Veiculo;
import com.estacionamento.repository.VeiculoRepository;
import com.estacionamento.util.HttpUtil;
import com.estacionamento.util.JsonUtil;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class VeiculoController implements HttpHandler {

    private static final String BASE = "/api/veiculos";
    private final VeiculoRepository repository = new VeiculoRepository();

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
        List<Veiculo> list = repository.findAll();
        HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(list));
    }

    private void handleGetById(HttpExchange exchange, Long id) throws IOException, SQLException {
        Optional<Veiculo> opt = repository.findById(id);
        if (opt.isPresent()) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(opt.get()));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Veículo não encontrado"));
        }
    }

    private void handleCreate(HttpExchange exchange) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Veiculo v = JsonUtil.fromJson(body, Veiculo.class);

        if (!validar(exchange, v)) return;

        try {
            Veiculo saved = repository.save(v);
            HttpUtil.sendResponse(exchange, 201, JsonUtil.toJson(saved));
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("unique")) {
                HttpUtil.sendResponse(exchange, 409, JsonUtil.errorJson("Placa já cadastrada"));
            } else {
                throw e;
            }
        }
    }

    private void handleUpdate(HttpExchange exchange, Long id) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Veiculo v = JsonUtil.fromJson(body, Veiculo.class);
        v.setId(id);

        if (!validar(exchange, v)) return;

        if (repository.update(v)) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(v));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Veículo não encontrado"));
        }
    }

    private void handleDelete(HttpExchange exchange, Long id) throws IOException, SQLException {
        try {
            if (repository.delete(id)) {
                HttpUtil.sendResponse(exchange, 200, JsonUtil.messageJson("Veículo excluído com sucesso"));
            } else {
                HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Veículo não encontrado"));
            }
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("foreign key")) {
                HttpUtil.sendResponse(exchange, 409,
                        JsonUtil.errorJson("Não é possível excluir veículo com permanências registradas"));
            } else {
                throw e;
            }
        }
    }

    private boolean validar(HttpExchange exchange, Veiculo v) throws IOException {
        if (v.getPlaca() == null || v.getPlaca().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'placa' é obrigatório"));
            return false;
        }
        if (v.getMarca() == null || v.getMarca().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'marca' é obrigatório"));
            return false;
        }
        if (v.getModelo() == null || v.getModelo().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'modelo' é obrigatório"));
            return false;
        }
        if (v.getCor() == null || v.getCor().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'cor' é obrigatório"));
            return false;
        }
        if (v.getClienteId() == null) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'clienteId' é obrigatório"));
            return false;
        }
        return true;
    }
}
