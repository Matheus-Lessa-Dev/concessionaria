package com.estacionamento;

import com.estacionamento.config.DatabaseConnection;
import com.estacionamento.controller.*;
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.concurrent.Executors;

public class Main {

    public static void main(String[] args) throws IOException {
        waitForDatabase();

        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);

        server.createContext("/api/clientes",    new ClienteController());
        server.createContext("/api/veiculos",    new VeiculoController());
        server.createContext("/api/vagas",       new VagaController());
        server.createContext("/api/permanencias",new PermanenciaController());
        server.createContext("/api/dashboard",   new DashboardController());

        // Thread pool para requisições concorrentes
        server.setExecutor(Executors.newFixedThreadPool(20));
        server.start();

        System.out.println("Servidor iniciado na porta 8080");

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            server.stop(0);
            System.out.println("Servidor encerrado");
        }));
    }

    private static void waitForDatabase() {
        int maxRetries = 30;
        for (int attempt = 1; attempt <= maxRetries; attempt++) {
            try (Connection conn = DatabaseConnection.getConnection()) {
                System.out.println("Conexão com o banco de dados estabelecida.");
                return;
            } catch (SQLException e) {
                System.out.println("Aguardando banco de dados... tentativa " + attempt + "/" + maxRetries);
                try {
                    Thread.sleep(2000);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        }
        throw new RuntimeException("Não foi possível conectar ao banco de dados após " + maxRetries + " tentativas.");
    }
}
