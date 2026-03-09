from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PublicIPForm
from .models import AuditLog, PublicIP


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


@login_required
def ip_list(request):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "").strip()

    ips = PublicIP.objects.select_related(
        "client",
        "pppoe_account",
        "block",
    ).all()

    if busca:
        ips = ips.filter(
            Q(ip_address__icontains=busca)
            | Q(client__nome__icontains=busca)
            | Q(pppoe_account__username__icontains=busca)
            | Q(observacoes__icontains=busca)
        )

    if status:
        ips = ips.filter(status=status)

    ips = ips.order_by("ip_address")

    context = {
        "ips": ips,
        "busca": busca,
        "status": status,
        "status_choices": PublicIP.Status.choices,
    }
    return render(request, "core/ip_list.html", context)


@login_required
def ip_detail(request, pk):
    ip_obj = get_object_or_404(
        PublicIP.objects.select_related("client", "pppoe_account", "block"),
        pk=pk
    )

    if request.method == "POST":
        form = PublicIPForm(request.POST, instance=ip_obj)
        if form.is_valid():
            form.save()
            return redirect("ip_list")
    else:
        form = PublicIPForm(instance=ip_obj)

    historico = AuditLog.objects.filter(
        entidade="PublicIP",
        entidade_id=str(ip_obj.pk)
    ).order_by("-criado_em")

    context = {
        "ip_obj": ip_obj,
        "form": form,
        "historico": historico,
    }
    return render(request, "core/ip_detail.html", context)