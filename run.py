"""Roda o projeto inteiro, na ordem certa.

    python run.py      gerador -> executor -> avaliador
"""
import os
import sys

# garante que os imports e o caminho "dados/..." funcionem de qualquer pasta
PASTA = os.path.dirname(os.path.abspath(__file__))
os.chdir(PASTA)
sys.path.insert(0, PASTA)

from src.avaliacao import avaliador
from src.avaliacao import executor
from src.gerador import gerador


def titulo(texto):
    print("\n" + "=" * 60)
    print(texto)
    print("=" * 60)


def main():
    titulo("1/3  Gerador: cria o dia de 24 h e o gabarito")
    gerador.main()

    titulo("2/3  Executor: passa o dia pelo proxy e grava o log")
    executor.executar()

    titulo("3/3  Avaliador: compara o log com o gabarito")
    avaliador.avaliar()

    titulo("Pronto. Arquivos em dados/")


if __name__ == "__main__":
    main()
