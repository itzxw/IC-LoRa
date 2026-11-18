"""Etapa 1 - classificador de borda.

Recebe cada medição, na ordem, e devolve uma Decisao: classe, motivo e o que
fazer com ela. Nunca apaga nada: o que não vai para a nuvem continua no log.

Classes:
  valida    -> dentro do esperado
  invalida  -> impossível (fora da faixa física ou ausente)
  suspeita  -> pico isolado (ainda sem confirmação) ou possível travamento
  evento    -> desvio sustentado acima de delta
"""
import math
import statistics
from collections import deque
from dataclasses import dataclass, field


@dataclass
class Decisao:
    indice: int
    classe: str                 # valida | invalida | suspeita | evento
    motivo: str
    acao: str                   # enviar | reter | nao_enviar
    liberar: list = field(default_factory=list)    # retidos que viraram evento
    isolados: list = field(default_factory=list)   # retidos que eram picos isolados


class Classificador:
    def __init__(self, sigma=0.2, k=5.0, faixa=(-20.0, 60.0),
                 n_travamento=5, n_confirma=3, janela_base=15, min_base=5):
        self.delta = k * sigma          # limiar: desvio da linha de base
        self.faixa = faixa              # faixa física do sensor
        self.n_travamento = n_travamento
        self.n_confirma = n_confirma
        self.min_base = min_base
        self.base = deque(maxlen=janela_base)   # só valores classificados como válidos
        self.prev = None
        self.run = 0                    # tamanho da sequência de valores idênticos
        self.travado = False
        self.pendentes = []             # índices com desvio ainda sem confirmação
        self.em_evento = False

    def classificar(self, indice, valor):
        # 1) inválida: ausente ou fisicamente impossível
        v = None if valor is None else float(valor)
        lo, hi = self.faixa
        if v is None or math.isnan(v) or not (lo <= v <= hi):
            return Decisao(indice, "invalida",
                           f"ausente ou fora da faixa física [{lo}, {hi}]", "nao_enviar")

        # 2) travamento: o mesmo valor, exatamente, várias vezes seguidas
        igual = self.prev is not None and v == self.prev
        self.run = self.run + 1 if igual else 1
        self.prev = v
        if self.run >= self.n_travamento:
            self.travado = True
            return Decisao(indice, "suspeita",
                           f"valor idêntico há {self.run} amostras (possível travamento)",
                           "nao_enviar")
        if self.travado:                # o sensor voltou a variar
            self.travado = False
            self.base.clear()
            self.pendentes.clear()
            self.em_evento = False
            self.base.append(v)
            return Decisao(indice, "valida",
                           "retomada após travamento; linha de base reiniciada", "enviar")

        # 3) desvio em relação à linha de base (mediana dos últimos válidos)
        if len(self.base) >= self.min_base:
            ref = statistics.median(self.base)
            d = v - ref
            if abs(d) > self.delta:
                self.pendentes.append(indice)
                n = len(self.pendentes)
                if self.em_evento:
                    return Decisao(indice, "evento",
                                   f"evento em curso (desvio {d:+.2f})", "enviar")
                if n >= self.n_confirma:
                    self.em_evento = True
                    return Decisao(indice, "evento",
                                   f"desvio {d:+.2f} acima de delta={self.delta:.2f} "
                                   f"sustentado por {n} amostras",
                                   "enviar", liberar=self.pendentes[:-1])
                return Decisao(indice, "suspeita",
                               f"desvio {d:+.2f} acima de delta={self.delta:.2f}; "
                               f"aguardando confirmação ({n}/{self.n_confirma})", "reter")

        # 4) dentro do esperado
        motivo = "dentro de delta da linha de base"
        isolados = []
        if self.em_evento:
            motivo = "fim do evento: voltou à linha de base"
        elif self.pendentes:
            isolados = list(self.pendentes)
        elif len(self.base) < self.min_base:
            motivo = "aquecimento da linha de base"
        self.pendentes.clear()
        self.em_evento = False
        self.base.append(v)
        return Decisao(indice, "valida", motivo, "enviar", isolados=isolados)