"""Gerador 24h, 1 leitura por minuto"""
import hashlib
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# dados de configuração do gerador
SEMENTE = 42
N = 1440                    # quantidade de leituras (24 h x 60 min)
INICIO = "2026-11-11 00:00:00"
ID_NO = "no01"
MEDIA = 25.0                # media do dia
AMPLITUDE = 3.0
PICO_DO_DIA_H = 15          # hora do pico maximo
SIGMA = 0.2                 # desvio padrao (ruido)
LIMITE_L = 30.0             # limite que define um evento

# dados das injecoes
PICO = {"indice": 6 * 60 + 30, "offset": 15.0}            # 06:30, +15 C, 1 unidade
TRAVAMENTO = {"ini": 10 * 60, "dur": 44}                   # 10:00 ate 10:44
EVENTO = {"ini": 14 * 60, "dur": 29, "offset": 5.0}        # 14:00 ate 14:29, +5 C

TRECHO_CALMO = (0, 60)      # 00:00 ate 00:59, sem injecao


def gerar(semente=SEMENTE):
    rng = np.random.default_rng(semente)       # gerador do numpy usando a nossa semente

    indice = np.arange(N)
    horas = indice / 60.0
    sinal = MEDIA + AMPLITUDE * np.sin(2 * np.pi * (horas - (PICO_DO_DIA_H - 6)) / 24)    # criacao de uma onda senoide (curva ideal)
    ruido = rng.normal(0.0, SIGMA, N)            # numeros aleatorios (- ou +) usando a normal com o dp
    valor = sinal + ruido                           # leitura bruta
    rotulo = np.array(["normal"] * N, dtype=object)

    # 1) evento, 5 C acima do limite
    e = slice(EVENTO["ini"], EVENTO["ini"] + EVENTO["dur"])
    valor[e] += EVENTO["offset"]
    rotulo[e] = "evento"

    # 2) travamento
    t = slice(TRAVAMENTO["ini"], TRAVAMENTO["ini"] + TRAVAMENTO["dur"])
    valor[t] = valor[TRAVAMENTO["ini"] - 1]
    rotulo[t] = "travamento"

    # 3) outlier
    valor[PICO["indice"]] += PICO["offset"]
    rotulo[PICO["indice"]] = "pico"

    instante = pd.date_range(INICIO, periods=N, freq="min")
    df = pd.DataFrame({
        "instante": instante.strftime("%Y-%m-%d %H:%M:%S"),
        "id_no": ID_NO,
        "indice_medicao": indice,
        "valor_medido": np.round(valor, 4),
        "rotulo": rotulo,
    })
    return df, np.round(sinal, 4)

# funcao pra verificar a igualdade dos arquivos
def sha256(caminho):
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def grafico(df, caminho):
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(df.indice_medicao / 60, df.valor_medido, lw=0.6, color="gray")
    for r, c in {"pico": "red", "travamento": "orange", "evento": "green"}.items():
        m = df.rotulo == r
        ax.scatter(df.indice_medicao[m] / 60, df.valor_medido[m], s=10, color=c, label=r)
    ax.axhline(LIMITE_L, ls="--", color="black", lw=0.8, label=f"L = {LIMITE_L} C")
    ax.set_xlabel("hour of day")
    ax.set_ylabel("temperature (C)")
    ax.set_xticks(range(0, 25, 2))
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)

# verificacao da media e dp do trecho calmo
def checar_sigma(df):
    a, b = TRECHO_CALMO
    y = df.valor_medido.values[a:b]
    x = np.arange(b - a)
    resid = y - np.polyval(np.polyfit(x, y, 2), x)
    s_trecho = resid.std(ddof=3)
    print(f"\ntrecho calmo {a}-{b} min: media={y.mean():.3f}  "
          f"sigma(residual)={s_trecho:.3f}  configurado={SIGMA}")
    return s_trecho

def main():
    os.makedirs("dados", exist_ok=True)

    # roda 2 vezes com a mesma semente
    df1, _ = gerar()
    df2, _ = gerar()
    df1.to_csv("dados/telemetria_24h.csv", index=False)
    df2.to_csv("dados/telemetria_24h_rep.csv", index=False)
    h1, h2 = sha256("dados/telemetria_24h.csv"), sha256("dados/telemetria_24h_rep.csv")
    print("sha256 run 1:", h1)
    print("sha256 run 2:", h2)
    print("IDENTICOS\n" if h1 == h2 else "DIFERENTES\n")  # verifica se tem diferenca
    os.remove("dados/telemetria_24h_rep.csv")

    print(df1.rotulo.value_counts().to_string())
    grafico(df1, "dados/grafico_24h.png")
    checar_sigma(df1)

if __name__ == "__main__":
    main()