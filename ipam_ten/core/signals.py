from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import PublicIP, AuditLog

_old_values = {}


@receiver(pre_save, sender=PublicIP)
def capture_old_public_ip(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = PublicIP.objects.get(pk=instance.pk)
            _old_values[instance.pk] = {
                "ip_address": old.ip_address,
                "status": old.status,
                "client_id": old.client_id,
                "pppoe_account_id": old.pppoe_account_id,
                "observacoes": old.observacoes,
            }
        except PublicIP.DoesNotExist:
            pass


@receiver(post_save, sender=PublicIP)
def log_public_ip_save(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            acao="create",
            entidade="PublicIP",
            entidade_id=str(instance.pk),
            valor_novo={
                "ip_address": instance.ip_address,
                "status": instance.status,
                "client_id": instance.client_id,
                "pppoe_account_id": instance.pppoe_account_id,
                "observacoes": instance.observacoes,
            },
        )
    else:
        old_data = _old_values.pop(instance.pk, None)
        AuditLog.objects.create(
            acao="update",
            entidade="PublicIP",
            entidade_id=str(instance.pk),
            valor_anterior=old_data,
            valor_novo={
                "ip_address": instance.ip_address,
                "status": instance.status,
                "client_id": instance.client_id,
                "pppoe_account_id": instance.pppoe_account_id,
                "observacoes": instance.observacoes,
            },
        )


@receiver(post_delete, sender=PublicIP)
def log_public_ip_delete(sender, instance, **kwargs):
    AuditLog.objects.create(
        acao="delete",
        entidade="PublicIP",
        entidade_id=str(instance.pk),
        valor_anterior={
            "ip_address": instance.ip_address,
            "status": instance.status,
            "client_id": instance.client_id,
            "pppoe_account_id": instance.pppoe_account_id,
            "observacoes": instance.observacoes,
        },
    )
    