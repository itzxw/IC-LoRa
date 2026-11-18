"""Proxy de borda - versão inicial.

Mesma ideia do meu antigo proxy em Go/Python (lote por tamanho ou por tempo, envio à nuvem),
mas determinístico: uma thread, relógio simulado (o instante da própria
medição) e envio simulado em memória. Cada decisão vai para um log.

"""
from src.borda.classificador import Classificador

class SinkMemoria:
    # Nuvem simulada: guarda o que seria enviado."""
    def __init__(self):
        self.lotes = []

    def enviar(self, linhas, instante):
        self.lotes.append({"instante": instante,
                           "indices": [l["indice_medicao"] for l in linhas]})


class ProxyBorda:
    def __init__(self, classificador=None, sink=None, batch_size=10,
                 flush_s=300, flush_ao_confirmar_evento=True):
        self.clf = classificador or Classificador()
        self.sink = sink or SinkMemoria()
        self.batch_size = batch_size
        self.flush_s = flush_s                         # tempo simulado, em segundos
        self.flush_evento = flush_ao_confirmar_evento        # regra de prioridade em caso de um evento critico
        self.log = {}                                 # indice -> linha do log
        self.fila = []                                # índices aguardando envio
        self.t_primeiro = None
        self.ultimo = None

    def receber(self, indice, instante, id_no, valor):
        d = self.clf.classificar(indice, valor)
        self.log[indice] = {
            "indice_medicao": indice, "instante": instante, "id_no": id_no,
            "valor_medido": valor,
            "classe_tempo_real": d.classe, "classe_final": d.classe,
            "motivo": d.motivo, "acao": d.acao,
            "enviado_nuvem": False, "indice_envio": None, "instante_envio": None,
        }
        for i in d.isolados:
            self.log[i]["motivo"] += f" | pico isolado confirmado (normalizou em {indice})"
        for i in d.liberar:                         # retidos que viraram evento
            r = self.log[i]
            r["classe_final"] = "evento"
            r["motivo"] += f" | reclassificada como evento ao confirmar em {indice}"
            self._enfileirar(i, instante)
        if d.acao == "enviar":
            self._enfileirar(indice, instante)
        self.ultimo = (indice, instante)

        if d.liberar and self.flush_evento:             # alerta imediato
            self._flush(indice, instante)
        elif len(self.fila) >= self.batch_size:         # tamanho do batch alcançado
            self._flush(indice, instante)
        elif self.fila and (instante - self.t_primeiro).total_seconds() >= self.flush_s:            # enviado por timeout
            self._flush(indice, instante)

    def _enfileirar(self, indice, instante):
        if not self.fila:
            self.t_primeiro = self.log[indice]["instante"]
        self.fila.append(indice)

    def _flush(self, indice_atual, instante):
        linhas = [self.log[i] for i in self.fila]
        self.sink.enviar(linhas, instante)
        for r in linhas:
            r["enviado_nuvem"] = True
            r["indice_envio"] = indice_atual
            r["instante_envio"] = instante
        self.fila = []
        self.t_primeiro = None

    def close(self):
        if self.fila:
            self._flush(*self.ultimo)