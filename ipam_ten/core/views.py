import ipaddress

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import PublicIPForm, AccessUserCreationForm
from django.contrib.auth.models import Group
from .forms import PublicIPForm
from .models import AuditLog, PublicIP

IP_GROUP_RULES = [
    {
        "titulo": "Corporativos - Jacobina",
        "tipo": "Corporativo",
        "cidade": "Jacobina",
        "faixa": "177.93.250.0/24",
        "network": ipaddress.ip_network("177.93.250.0/24"),
    },
    {
        "titulo": "Corporativos - Capim Grosso",
        "tipo": "Corporativo",
        "cidade": "Capim Grosso",
        "faixa": "177.93.251.0/24",
        "network": ipaddress.ip_network("177.93.251.0/24"),
    },
    {
        "titulo": "Gamers - Jacobina",
        "tipo": "Gamer",
        "cidade": "Jacobina",
        "faixa": "177.93.252.0/25",
        "network": ipaddress.ip_network("177.93.252.0/25"),
    },
    {
        "titulo": "Gamers - Capim Grosso",
        "tipo": "Gamer",
        "cidade": "Capim Grosso",
        "faixa": "177.93.252.128/25",
        "network": ipaddress.ip_network("177.93.252.128/25"),
    },
    {
        "titulo": "Planos Alternativos - Jacobina",
        "tipo": "Outros motivos",
        "cidade": "Jacobina",
        "faixa": "177.93.253.0/25",
        "network": ipaddress.ip_network("177.93.253.0/25"),
    },
    {
        "titulo": "Planos Alternativos - Capim Grosso",
        "tipo": "Outros motivos",
        "cidade": "Capim Grosso",
        "faixa": "177.93.253.128/25",
        "network": ipaddress.ip_network("177.93.253.128/25"),
    },
]

def get_ip_group_info(ip_address):
    
    ip_real = ipaddress.ip_address(ip_address)

    for regra in IP_GROUP_RULES:
        if ip_real in regra["network"]:
            return regra

    return {
        "titulo": "Fora das faixas definidas",
        "tipo": "Não classificado",
        "cidade": "—",
        "faixa": "—",
    }

def build_dashboard_group_data():
    grupos_dashboard = []

    for regra in IP_GROUP_RULES:
        network = regra["network"]

        ips_do_grupo = [
            ip_obj for ip_obj in PublicIP.objects.select_related("client", "pppoe_account", "block").all()
            if ipaddress.ip_address(ip_obj.ip_address) in network
        ]

        grupos_dashboard.append({
            "titulo": regra["titulo"],
            "tipo": regra["tipo"],
            "cidade": regra["cidade"],
            "faixa": regra["faixa"],
            "total": len(ips_do_grupo),
            "disponiveis": sum(1 for ip in ips_do_grupo if ip.status == "disponivel"),
            "alocados": sum(1 for ip in ips_do_grupo if ip.status == "alocado"),
            "bloqueados": sum(1 for ip in ips_do_grupo if ip.status == "bloqueado"),
            "problema": sum(1 for ip in ips_do_grupo if ip.status == "problema"),
            "reservados": sum(1 for ip in ips_do_grupo if ip.status == "reservado"),
            "inconsistentes": sum(1 for ip in ips_do_grupo if ip.status == "inconsistente"),
        })

    return grupos_dashboard
@login_required
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

    grupos_dashboard = build_dashboard_group_data()

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
        "grupos_dashboard": grupos_dashboard,
    }
    return render(request, "core/dashboard.html", context)


@login_required
def ip_list(request):
    busca = request.GET.get("busca", "").strip()
    status = request.GET.get("status", "").strip()

    ips_qs = PublicIP.objects.select_related(
        "client",
        "pppoe_account",
        "block",
    ).all()

    if busca:
        ips_qs = ips_qs.filter(
            Q(ip_address__icontains=busca)
            | Q(client__nome__icontains=busca)
            | Q(pppoe_account__username__icontains=busca)
            | Q(observacoes__icontains=busca)
        )

    if status:
        ips_qs = ips_qs.filter(status=status)

    # Ordenação numérica correta
    ips_ordenados = sorted(
        ips_qs,
        key=lambda item: ipaddress.ip_address(item.ip_address)
    )

    # Separação por grupos
    grupos = []
    ips_usados = set()

    for regra in IP_GROUP_RULES:
        itens_do_grupo = []

        for ip_obj in ips_ordenados:
            ip_real = ipaddress.ip_address(ip_obj.ip_address)
            if ip_real in regra["network"]:
                itens_do_grupo.append(ip_obj)
                ips_usados.add(ip_obj.pk)

        grupos.append({
            "titulo": regra["titulo"],
            "tipo": regra["tipo"],
            "cidade": regra["cidade"],
            "faixa": regra["faixa"],
            "ips": itens_do_grupo,
        })

    # IPs fora das faixas definidas
    ips_sem_grupo = [ip_obj for ip_obj in ips_ordenados if ip_obj.pk not in ips_usados]

    if ips_sem_grupo:
        grupos.append({
            "titulo": "Fora das faixas definidas",
            "tipo": "Não classificado",
            "cidade": "—",
            "faixa": "—",
            "ips": ips_sem_grupo,
        })

    context = {
        "grupos": grupos,
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
            messages.success(request, f"IP {ip_obj.ip_address} atualizado com sucesso.")
            return redirect("ip_detail", pk=ip_obj.pk)
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
        "categoria_ip": get_ip_group_info(ip_obj.ip_address),
    }
    return render(request, "core/ip_detail.html", context)

def ensure_default_access_groups():
    Group.objects.get_or_create(name="Administrador")
    Group.objects.get_or_create(name="Operação")
    Group.objects.get_or_create(name="Consulta")


@login_required
def access_create(request):
    if not request.user.is_superuser:
        messages.error(request, "Você não tem permissão para acessar essa área.")
        return redirect("dashboard")

    ensure_default_access_groups()

    if request.method == "POST":
        form = AccessUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Acesso criado com sucesso.")
            return redirect("access_create")
    else:
        form = AccessUserCreationForm()

    usuarios = (
        Group.user_set.model.objects.all()
        .prefetch_related("groups")
        .order_by("username")
    )

    context = {
        "form": form,
        "usuarios": usuarios,
    }
    return render(request, "core/access_create.html", context)