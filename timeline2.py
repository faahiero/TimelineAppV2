#!/usr/bin/python3
# -*- coding: utf-8 -*-
import time
import funcoes as fncts

fncts.header()
fncts.menu()

option = input("Escolha uma das opções acima: ")

while option != '0':
    if option == '1':
        # clear_console()
        fncts.get_info_person("", False)
    # elif option == '2':
    #     # clear_console()
    #     print("Obtendo informações...")
    #     time.sleep(5)
    #     # clear_console()
    elif option == '2':
        print("Gerando Visualizações")
        fncts.generate_visualization()
        time.sleep(5)
        exit()
    else:
        print("Opção Inválida")
    fncts.header()
    fncts.menu()
    option = input("Escolha uma das opções acima: ")

fncts.clear_console()
print("Obrigado por usar o software!!")
