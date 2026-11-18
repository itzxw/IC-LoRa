# ponte entre o gerador e o proxy

import pandas as pd
from src.borda.proxy_borda import ProxyBorda

def politica_enviar_tudo(indice, valor):
    # refere-se à politica do sensor (enviar/esperar). Por enquanto, envia tudo.
    return True


def executar(csv_in="dados/telemetria_24h.csv", log_out="dados/log_decisoes.csv",
             politica=politica_enviar_tudo):
    df = pd.read_csv(csv_in, parse_dates=["instante"])
    proxy = ProxyBorda()

    for r in df[["instante", "id_no", "indice_medicao", "valor_medido"]].itertuples(index=False):
        if politica(r.indice_medicao, r.valor_medido):                      # usa a politica do sensor para enviar (ou nao) a leitura
            proxy.receber(int(r.indice_medicao), r.instante, r.id_no, r.valor_medido)

    proxy.close()

    log = pd.DataFrame(proxy.log.values())
    log.to_csv(log_out, index=False)
    print(f"{len(df)} medições lidas | {len(log)} chegaram ao proxy | "
          f"{len(proxy.sink.lotes)} mensagens à nuvem | log em {log_out}")

    return proxy


if __name__ == "__main__":
    executar()