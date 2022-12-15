import os
import art

# Limpar o console
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


# Arte do cabeçalho do programa
def header():
    banner = art.text2art("Wikipedia GeoHist", font="small")
    print(banner)


# Menu do programa
def menu():
    print("[1] - Buscar (Ex.: 'Machado de Assis')")
    print("[2] - Gerar visualização")
    print("[0] - Encerrar")
    print()