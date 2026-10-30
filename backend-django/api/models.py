from django.db import models
from django.utils import timezone


class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'clientes'


class Veiculo(models.Model):
    placa = models.CharField(max_length=10, unique=True)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    cor = models.CharField(max_length=30)
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)

    class Meta:
        db_table = 'veiculos'


class Vaga(models.Model):
    TIPO_CHOICES = [
        ('CARRO', 'Carro'),
        ('MOTO', 'Moto'),
    ]

    STATUS_CHOICES = [
        ('LIVRE', 'Livre'),
        ('OCUPADA', 'Ocupada'),
    ]

    numero = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=5, choices=TIPO_CHOICES)
    status = models.CharField(
        max_length=7,
        choices=STATUS_CHOICES,
        default='LIVRE',
    )

    class Meta:
        db_table = 'vagas'


class Permanencia(models.Model):
    STATUS_CHOICES = [
        ('ABERTO', 'Aberto'),
        ('FINALIZADO', 'Finalizado'),
    ]

    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT)
    vaga = models.ForeignKey(Vaga, on_delete=models.PROTECT)
    data_hora_entrada = models.DateTimeField(default=timezone.now)
    data_hora_saida = models.DateTimeField(blank=True, null=True)
    valor_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='ABERTO',
        db_index=True,
    )

    class Meta:
        db_table = 'permanencias'