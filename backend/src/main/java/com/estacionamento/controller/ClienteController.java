package com.estacionamento.controller;

import com.estacionamento.model.Cliente;
import com.estacionamento.repository.ClienteRepository;
import com.estacionamento.util.HttpUtil;
import com.estacionamento.util.JsonUtil;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;

import java.io.IOException;
import java.sql.SQLException;
import java.util.List;
import java.util.Optional;

public class ClienteController implements HttpHandler {

    private static final String BASE = "/api/clientes";
    private final ClienteRepository repository = new ClienteRepository();

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
        List<Cliente> clientes = repository.findAll();
        HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(clientes));
    }

    private void handleGetById(HttpExchange exchange, Long id) throws IOException, SQLException {
        Optional<Cliente> opt = repository.findById(id);
        if (opt.isPresent()) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(opt.get()));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Cliente não encontrado"));
        }
    }

    private void handleCreate(HttpExchange exchange) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Cliente cliente = JsonUtil.fromJson(body, Cliente.class);

        if (cliente.getNome() == null || cliente.getNome().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'nome' é obrigatório"));
            return;
        }
        if (cliente.getCpf() == null || cliente.getCpf().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'cpf' é obrigatório"));
            return;
        }

        try {
            Cliente saved = repository.save(cliente);
            HttpUtil.sendResponse(exchange, 201, JsonUtil.toJson(saved));
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("unique")) {
                HttpUtil.sendResponse(exchange, 409, JsonUtil.errorJson("CPF já cadastrado"));
            } else {
                throw e;
            }
        }
    }

    private void handleUpdate(HttpExchange exchange, Long id) throws IOException, SQLException {
        String body = HttpUtil.readBody(exchange);
        Cliente cliente = JsonUtil.fromJson(body, Cliente.class);
        cliente.setId(id);

        if (cliente.getNome() == null || cliente.getNome().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'nome' é obrigatório"));
            return;
        }
        if (cliente.getCpf() == null || cliente.getCpf().trim().isEmpty()) {
            HttpUtil.sendResponse(exchange, 400, JsonUtil.errorJson("Campo 'cpf' é obrigatório"));
            return;
        }

        if (repository.update(cliente)) {
            HttpUtil.sendResponse(exchange, 200, JsonUtil.toJson(cliente));
        } else {
            HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Cliente não encontrado"));
        }
    }

    private void handleDelete(HttpExchange exchange, Long id) throws IOException, SQLException {
        try {
            if (repository.delete(id)) {
                HttpUtil.sendResponse(exchange, 200, JsonUtil.messageJson("Cliente excluído com sucesso"));
            } else {
                HttpUtil.sendResponse(exchange, 404, JsonUtil.errorJson("Cliente não encontrado"));
            }
        } catch (SQLException e) {
            if (e.getMessage() != null && e.getMessage().contains("foreign key")) {
                HttpUtil.sendResponse(exchange, 409,
                        JsonUtil.errorJson("Não é possível excluir cliente com veículos cadastrados"));
            } else {
                throw e;
            }
        }
    }
}
