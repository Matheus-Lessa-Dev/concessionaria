package com.estacionamento.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class Permanencia {
    private Long id;
    private Long veiculoId;
    private String veiculoPlaca;
    private String veiculoModelo;
    private Long vagaId;
    private String vagaNumero;
    private LocalDateTime dataHoraEntrada;
    private LocalDateTime dataHoraSaida;
    private BigDecimal valorTotal;
    private String status; // ABERTO | FINALIZADO

    public Permanencia() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getVeiculoId() { return veiculoId; }
    public void setVeiculoId(Long veiculoId) { this.veiculoId = veiculoId; }

    public String getVeiculoPlaca() { return veiculoPlaca; }
    public void setVeiculoPlaca(String veiculoPlaca) { this.veiculoPlaca = veiculoPlaca; }

    public String getVeiculoModelo() { return veiculoModelo; }
    public void setVeiculoModelo(String veiculoModelo) { this.veiculoModelo = veiculoModelo; }

    public Long getVagaId() { return vagaId; }
    public void setVagaId(Long vagaId) { this.vagaId = vagaId; }

    public String getVagaNumero() { return vagaNumero; }
    public void setVagaNumero(String vagaNumero) { this.vagaNumero = vagaNumero; }

    public LocalDateTime getDataHoraEntrada() { return dataHoraEntrada; }
    public void setDataHoraEntrada(LocalDateTime dataHoraEntrada) { this.dataHoraEntrada = dataHoraEntrada; }

    public LocalDateTime getDataHoraSaida() { return dataHoraSaida; }
    public void setDataHoraSaida(LocalDateTime dataHoraSaida) { this.dataHoraSaida = dataHoraSaida; }

    public BigDecimal getValorTotal() { return valorTotal; }
    public void setValorTotal(BigDecimal valorTotal) { this.valorTotal = valorTotal; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
