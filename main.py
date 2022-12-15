#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import time
from modules.retrieve_information import *
from modules.generate_visualization import *
from modules.utils import *

header()
menu()

option = input("Escolha uma das opções acima: ")

while option != '0':
    if option == '1':
        # clear_console()
        retrieve_information("", False)
    # elif option == '2':
    #     # clear_console()
    #     print("Obtendo informações...")
    #     time.sleep(5)
    #     # clear_console()
    elif option == '2':
        print("Gerando Visualizações")
        generate_visualization()
        time.sleep(5)
        sys.exit()
    else:
        print("Opção Inválida")
    header()
    menu()
    option = input("Escolha uma das opções acima: ")

clear_console()
print("Obrigado por usar o software!!")