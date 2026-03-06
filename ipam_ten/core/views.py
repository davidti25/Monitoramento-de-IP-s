from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from .models import PublicIP, AuditLog


@login_required
def dashboard(request):
    total_ips = PublicIP.objects.count()
    total_alocados = PublicIP.objects.filter(status="alocado").count()
    total_disponiveis = PublicIP.objects.filter(status="disponivel").count()
    total_bloqueados = PublicIP.objects.filter(status="bloqueado").count()
    total_problema = PublicIP.objects.filter(status="problema").count()
    total_reservado = PublicIP.objects.filter(status="reservado").count()
    total_inconsistente = PublicIP.objects.filter(status="inconsistente").count()

    status_data = (
        PublicIP.objects.values("status")
        .annotate(total=Count("id"))
        .order_by("status")
    )

    ultimas_alteracoes = AuditLog.objects.all()[:10]

    context = {
        "total_ips": total_ips,
        "total_alocados": total_alocados,
        "total_disponiveis": total_disponiveis,
        "total_bloqueados": total_bloqueados,
        "total_problema": total_problema,
        "total_reservado": total_reservado,
        "total_inconsistente": total_inconsistente,
        "status_data": list(status_data),
        "ultimas_alteracoes": ultimas_alteracoes,
    }
    return render(request, "core/dashboard.html", context)
