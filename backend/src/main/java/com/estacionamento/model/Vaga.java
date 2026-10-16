package com.estacionamento.model;

public class Vaga {
    private Long id;
    private String numero;
    private String tipo;   // CARRO | MOTO
    private String status; // LIVRE | OCUPADA

    public Vaga() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getNumero() { return numero; }
    public void setNumero(String numero) { this.numero = numero; }

    public String getTipo() { return tipo; }
    public void setTipo(String tipo) { this.tipo = tipo; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
