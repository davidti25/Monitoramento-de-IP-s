from django.contrib import admin
from .models import IPBlock, Client, PPPoEAccount, PublicIP, ImportLog, AuditLog


@admin.register(IPBlock)
class IPBlockAdmin(admin.ModelAdmin):
    list_display = ("nome", "rede_cidr", "ativo", "criado_em")
    search_fields = ("nome", "rede_cidr")
    list_filter = ("ativo",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo_externo", "documento", "ativo", "criado_em")
    search_fields = ("nome", "codigo_externo", "documento")
    list_filter = ("ativo",)


@admin.register(PPPoEAccount)
class PPPoEAccountAdmin(admin.ModelAdmin):
    list_display = ("username", "client", "ativo", "criado_em")
    search_fields = ("username", "client__nome")
    list_filter = ("ativo",)


@admin.register(PublicIP)
class PublicIPAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "status",
        "client",
        "pppoe_account",
        "block",
        "atualizado_em",
    )
    search_fields = (
        "ip_address",
        "client__nome",
        "pppoe_account__username",
        "observacoes",
    )
    list_filter = ("status", "block")
    autocomplete_fields = ("client", "pppoe_account", "block")


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "nome_arquivo",
        "total_registros",
        "total_processados",
        "total_erros",
        "executado_por",
        "executado_em",
    )
    search_fields = ("nome_arquivo",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("entidade", "acao", "usuario", "criado_em")
    search_fields = ("entidade", "entidade_id")
    list_filter = ("acao", "entidade")
    