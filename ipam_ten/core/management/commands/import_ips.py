import pandas as pd
from django.core.management.base import BaseCommand
from core.models import PublicIP, Client, PPPoEAccount, IPBlock, ImportLog


class Command(BaseCommand):
    help = "Importa IPs de um arquivo CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="C:\\Users\\David Brasil\\Documents\\Monitoramento de IP's\\ipam_ten\\csv\\ips.csv")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        try:
            df = pd.read_csv(csv_file, sep=None, engine="python")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao ler CSV: {e}"))
            return

        df.columns = [str(col).strip() for col in df.columns]

        possible_ip_col = None
        for col in df.columns:
            if "ip" in col.lower():
                possible_ip_col = col
                break

        if not possible_ip_col:
            self.stdout.write(self.style.ERROR("Não encontrei coluna de IP no CSV."))
            return

        client_col = None
        obs_col = None

        for col in df.columns:
            lower = col.lower()
            if "cliente" in lower:
                client_col = col
            if "obs" in lower:
                obs_col = col

        block, _ = IPBlock.objects.get_or_create(
            rede_cidr="177.93.252.128/25",
            defaults={"nome": "Bloco Principal TEN"}
        )

        total = 0
        processados = 0
        erros = 0

        for _, row in df.iterrows():
            total += 1

            try:
                ip = str(row.get(possible_ip_col, "")).strip()
                if not ip or ip.lower() == "nan":
                    continue

                client_name = str(row.get(client_col, "")).strip() if client_col else ""
                obs_value = str(row.get(obs_col, "")).strip() if obs_col else ""

                client = None
                if client_name and client_name.lower() != "nan":
                    client, _ = Client.objects.get_or_create(nome=client_name)

                pppoe = None
                if obs_value and obs_value.lower() != "nan" and obs_value.upper() != "NÃO LOCALIZADO":
                    pppoe, _ = PPPoEAccount.objects.get_or_create(
                        username=obs_value,
                        defaults={"client": client}
                    )
                    if client and pppoe.client is None:
                        pppoe.client = client
                        pppoe.save()

                status = "disponivel"
                if obs_value.upper() == "NÃO LOCALIZADO":
                    status = "problema"
                elif client or pppoe or obs_value:
                    status = "alocado"

                PublicIP.objects.update_or_create(
                    ip_address=ip,
                    defaults={
                        "block": block,
                        "client": client,
                        "pppoe_account": pppoe,
                        "status": status,
                        "observacoes": obs_value if obs_value.lower() != "nan" else "",
                        "origem_importacao": csv_file,
                    }
                )

                processados += 1

            except Exception as e:
                erros += 1
                self.stdout.write(self.style.WARNING(f"Erro na linha {total}: {e}"))

        ImportLog.objects.create(
            nome_arquivo=csv_file,
            total_registros=total,
            total_processados=processados,
            total_erros=erros,
        )

        self.stdout.write(self.style.SUCCESS(
            f"Importação finalizada. Total: {total}, Processados: {processados}, Erros: {erros}"
        ))
        