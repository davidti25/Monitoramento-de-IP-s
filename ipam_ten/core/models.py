from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IPBlock(TimeStampedModel):
    nome = models.CharField(max_length=100)
    rede_cidr = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Bloco de IP"
        verbose_name_plural = "Blocos de IP"

    def __str__(self):
        return f"{self.nome} ({self.rede_cidr})"


class Client(TimeStampedModel):
    codigo_externo = models.CharField(max_length=50, blank=True, null=True)
    nome = models.CharField(max_length=255)
    documento = models.CharField(max_length=30, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PPPoEAccount(TimeStampedModel):
    username = models.CharField(max_length=120, unique=True)
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="pppoe_accounts"
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Conta PPPoE"
        verbose_name_plural = "Contas PPPoE"
        ordering = ["username"]

    def __str__(self):
        return self.username


class PublicIP(TimeStampedModel):
    class Status(models.TextChoices):
        DISPONIVEL = "disponivel", "Disponível"
        ALOCADO = "alocado", "Alocado"
        BLOQUEADO = "bloqueado", "Bloqueado"
        PROBLEMA = "problema", "Com problema"
        RESERVADO = "reservado", "Reservado"
        INCONSISTENTE = "inconsistente", "Inconsistente"

    ip_address = models.GenericIPAddressField(protocol="IPv4", unique=True)
    block = models.ForeignKey(
        IPBlock,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="ips"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="public_ips"
    )
    pppoe_account = models.ForeignKey(
        PPPoEAccount,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="public_ips"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DISPONIVEL
    )
    observacoes = models.TextField(blank=True, null=True)
    origem_importacao = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "IP Público"
        verbose_name_plural = "IPs Públicos"
        ordering = ["ip_address"]

    def __str__(self):
        return self.ip_address


class ImportLog(TimeStampedModel):
    nome_arquivo = models.CharField(max_length=255)
    total_registros = models.PositiveIntegerField(default=0)
    total_processados = models.PositiveIntegerField(default=0)
    total_erros = models.PositiveIntegerField(default=0)
    executado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    executado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Log de Importação"
        verbose_name_plural = "Logs de Importação"
        ordering = ["-executado_em"]

    def __str__(self):
        return f"{self.nome_arquivo} - {self.executado_em:%d/%m/%Y %H:%M}"


class AuditLog(models.Model):
    ACAO_CHOICES = [
        ("create", "Criação"),
        ("update", "Atualização"),
        ("delete", "Exclusão"),
        ("import", "Importação"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    acao = models.CharField(max_length=20, choices=ACAO_CHOICES)
    entidade = models.CharField(max_length=100)
    entidade_id = models.CharField(max_length=50, blank=True, null=True)
    valor_anterior = models.JSONField(blank=True, null=True)
    valor_novo = models.JSONField(blank=True, null=True)
    ip_origem = models.GenericIPAddressField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.entidade} - {self.acao} - {self.criado_em:%d/%m/%Y %H:%M}"
    