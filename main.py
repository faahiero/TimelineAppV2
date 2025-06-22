#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import time

from modules.utils import clear_console, menu
from modules.info_gathering import fetch_data
from modules.vis_functions import generate_visualization, generate_visualization_history

while True:
    clear_console()
    menu()
    options = input("Escolha uma das opções: ")
    if options == "1":
        fetch_data("", False)
    elif options == "2":
        clear_console()
        print("Gerando visualizações")
        generate_visualization()
    elif options == "3":
        clear_console()
        print("Histórico de navegação")
        generate_visualization_history()
    elif options == "0":
        clear_console()
        print("Saindo...")
        print("Obrigado por usar o software!!")
        time.sleep(1)
        sys.exit()
    else:
        print("Opção inválida")
        time.sleep(1)

