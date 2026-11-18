"""Avaliador: cruza o log do proxy com o gabarito, pelo indice_medicao."""
import numpy as np
import pandas as pd


def avaliar(verdade="dados/telemetria_24h.csv", log="dados/log_decisoes.csv"):
    v = pd.read_csv(verdade)
    l = pd.read_csv(log)
    cols = ["indice_medicao", "classe_tempo_real", "classe_final", "motivo",
            "enviado_nuvem", "indice_envio"]
    m = v.merge(l[cols], on="indice_medicao", how="left")
    m["enviado_nuvem"] = m["enviado_nuvem"].fillna(False).astype(bool)
    N = len(m)

    print("=== Gabarito (linhas) x classe final do proxy (colunas) ===")
    print(pd.crosstab(m.rotulo, m.classe_final).to_string(), "\n")

    n_env = int(m.enviado_nuvem.sum())
    n_msg = int(m.indice_envio.nunique())
    print("=== Redução ===")
    print(f"medições: {N} | enviadas à nuvem: {n_env} ({100*n_env/N:.1f}%) "
          f"| mensagens (lotes): {n_msg}\n")

    print("=== Pico ===")
    p = m[m.rotulo == "pico"]
    print(p[["indice_medicao", "classe_final", "enviado_nuvem"]].to_string(index=False), "\n")

    print("=== Travamento ===")
    t = m[m.rotulo == "travamento"]
    ini = int(t.indice_medicao.min())
    det = m[(m.indice_medicao >= ini) &
            m.motivo.str.contains("idêntico", na=False)].indice_medicao.min()
    print(f"início real: {ini} | detectado em: {int(det)} (atraso {int(det)-ini} amostras)")
    print(f"amostras do travamento que chegaram à nuvem: {int(t.enviado_nuvem.sum())} de {len(t)}\n")

    print("=== Evento ===")
    e = m[m.rotulo == "evento"]
    ini = int(e.indice_medicao.min())
    det = int(m[m.classe_tempo_real == "evento"].indice_medicao.min())
    env = int(e.indice_envio.min())
    print(f"início real: {ini} | 1ª classificação como evento: {det} | "
          f"1ª amostra do evento na nuvem: {env} (atraso {env-ini} min)")
    print(f"amostras do evento que chegaram à nuvem: {int(e.enviado_nuvem.sum())} de {len(e)}")
    fora = m[(m.classe_final == "evento") & (m.rotulo != "evento")]
    print(f"classificadas como evento fora do evento real: {len(fora)}\n")

    print("=== Falsos positivos (normal classificado como outra coisa) ===")
    fp = m[(m.rotulo == "normal") & (m.classe_final != "valida")]
    print(f"{len(fp)} de {int((m.rotulo == 'normal').sum())}")
    if len(fp):
        print(fp[["indice_medicao", "classe_final", "motivo"]].head(10).to_string(index=False))
    print()

    # defasagem: idade da medição mais recente que a nuvem já tem, a cada minuto
    disp = np.full(N, -1)
    for idx, ie in m.dropna(subset=["indice_envio"])[["indice_medicao", "indice_envio"]].values:
        disp[int(ie)] = max(disp[int(ie)], int(idx))
    ultimo = np.maximum.accumulate(disp)
    idade = np.arange(N) - ultimo
    print("=== Defasagem da informação na nuvem (minutos) ===")
    print(f"média: {idade.mean():.1f} | p95: {np.percentile(idade, 95):.0f} | "
          f"máxima: {idade.max()} (no minuto {int(idade.argmax())})")
    return m


if __name__ == "__main__":
    avaliar()