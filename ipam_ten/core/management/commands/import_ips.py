from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from core.models import PublicIP, Client, PPPoEAccount, IPBlock, ImportLog


class Command(BaseCommand):
    help = "Importa IPs de um arquivo CSV"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Caminho do arquivo CSV")

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        try:
            df = pd.read_csv(
                csv_file,
                sep=";",
                encoding="utf-8-sig",
                dtype=str,
                keep_default_na=False,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao ler CSV: {e}"))
            return

        df.columns = [str(col).strip() for col in df.columns]

        ip_col = None
        pppoe_col = None
        client_col = None

        for col in df.columns:
            col_upper = col.upper().strip()
            if "IP" in col_upper:
                ip_col = col
            elif "PPPOE" in col_upper:
                pppoe_col = col
            elif "CLIENTE" in col_upper:
                client_col = col

        if not ip_col:
            self.stdout.write(self.style.ERROR("Não encontrei a coluna de IP no CSV."))
            return

        if not pppoe_col:
            self.stdout.write(self.style.ERROR("Não encontrei a coluna de PPPoE no CSV."))
            return

        if not client_col:
            self.stdout.write(self.style.ERROR("Não encontrei a coluna de cliente no CSV."))
            return

        total = 0
        processados = 0
        erros = 0

        for _, row in df.iterrows():
            total += 1

            try:
                ip = str(row.get(ip_col, "")).strip()
                raw_pppoe = str(row.get(pppoe_col, "")).strip()
                client_name = str(row.get(client_col, "")).strip()

                if not ip:
                    continue

                client = None
                if client_name:
                    client, _ = Client.objects.get_or_create(nome=client_name)

                status = "disponivel"
                observacoes = ""
                pppoe = None

                raw_pppoe_lower = raw_pppoe.lower()

                if raw_pppoe:
                    if "não localizado" in raw_pppoe_lower or "nao localizado" in raw_pppoe_lower:
                        status = "problema"
                        observacoes = raw_pppoe

                    elif "bloqueado" in raw_pppoe_lower or "aviso de bloqueio" in raw_pppoe_lower:
                        status = "bloqueado"
                        observacoes = raw_pppoe

                    else:
                        username = raw_pppoe.replace("PPPoE:", "").replace("pppoe:", "").strip()

                        if username:
                            pppoe, _ = PPPoEAccount.objects.get_or_create(
                                username=username,
                                defaults={"client": client}
                            )

                            if client and pppoe.client is None:
                                pppoe.client = client
                                pppoe.save()

                            status = "alocado"
                            observacoes = raw_pppoe

                else:
                    if client:
                        status = "alocado"
                    else:
                        status = "disponivel"

                octetos = ip.split(".")
                if len(octetos) == 4:
                    block_cidr = f"{octetos[0]}.{octetos[1]}.{octetos[2]}.0/24"
                    block_name = f"Bloco {block_cidr}"
                else:
                    block_cidr = "0.0.0.0/24"
                    block_name = "Bloco desconhecido"

                block, _ = IPBlock.objects.get_or_create(
                    rede_cidr=block_cidr,
                    defaults={"nome": block_name}
                )

                PublicIP.objects.update_or_create(
                    ip_address=ip,
                    defaults={
                        "block": block,
                        "client": client,
                        "pppoe_account": pppoe,
                        "status": status,
                        "observacoes": observacoes,
                        "origem_importacao": str(Path(csv_file).name),
                    }
                )

                processados += 1

            except Exception as e:
                erros += 1
                self.stdout.write(self.style.WARNING(f"Erro na linha {total}: {e}"))

        ImportLog.objects.create(
            nome_arquivo=str(Path(csv_file).name),
            total_registros=total,
            total_processados=processados,
            total_erros=erros,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Importação finalizada. Total: {total}, Processados: {processados}, Erros: {erros}"
            )
        )