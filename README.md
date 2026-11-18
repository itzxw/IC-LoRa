# IC-LoRa

## Validação contextual e transmissão adaptativa de telemetria em redes LoRa

### Requisitos

- Python 3.9 ou superior
- Pacotes: `numpy`, `pandas`, `matplotlib`

```bash
pip install numpy pandas matplotlib
```

## Como rodar

```bash
git clone https://github.com/itzxw/IC-LoRa
cd IC-LoRa
python run.py
```

No Windows, se `python` não funcionar, use `py run.py`.

O comando executa, em ordem: **gerador → proxy de borda → avaliador**. Não precisa de internet,
de conta em nuvem nem de configuração: a nuvem é simulada em memória e a semente é fixa
(42), então o resultado é sempre o mesmo.

## O que aparece na tela

1. **Gerador:** confirma que duas execuções com a mesma semente geram arquivos idênticos
   (`IDENTICOS`) e compara o desvio padrão medido com o configurado (σ = 0,2).
2. **Proxy:** quantas medições foram lidas e quantas mensagens foram enviadas à nuvem simulada.
3. **Avaliador:** compara a classificação do proxy com o gabarito (pico, travamento e evento
   injetados) e mostra falsos positivos, atraso na detecção do evento e defasagem da informação.

## Arquivos gerados (pasta `dados/`)

| Arquivo | Conteúdo |
|---|---|
| `telemetria_24h.csv` | série de 1.440 medições, com a coluna `rotulo` (o gabarito) |
| `log_decisoes.csv` | classe e motivo atribuídos pelo proxy a cada medição |
| `grafico_24h.png` | sinal com pico, travamento e evento destacados |

## Onde está cada parte

- `src/gerador/gerador.py`: gera o sinal e o gabarito
- `src/borda/classificador.py`: classifica cada medição (válida, inválida, suspeita ou evento)
- `src/borda/proxy_borda.py`: fila, lotes e log de decisões
- `src/avaliacao/`: executor (liga o gerador ao proxy) e avaliador

O proxy nunca recebe a coluna `rotulo`; só o gerador e o avaliador conhecem o gabarito.
